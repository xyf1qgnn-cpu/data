import os
import json
import shutil
import pandas as pd
from openai import OpenAI
from datetime import datetime
from typing import Optional
from validation import validate_dataframe
from styling import export_to_excel_with_styling, generate_validation_report
from processing import process_pdf, process_from_cache
from config_manager import load_and_validate_config, ConfigError, check_poppler_installation
from logger import setup_logger
import logging

# Configuration
# Base directory (script location)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# PDF files location
TARGET_DIRECTORY = os.path.join(BASE_DIR, "files")
# Location to move failed files
NOT_INPUT_DIRECTORY = os.path.join(BASE_DIR, "NotInput")
# Location to move excluded files (invalid content)
EXCLUDED_DIRECTORY = os.path.join(BASE_DIR, "Excluded")
# Output Excel location (same as script directory)
OUTPUT_DIRECTORY = BASE_DIR


# Column Mapping for Excel
COL_MAPPING = {
    "ref_no": "Ref.No.",
    "fc_value": "fc (MPa)",
    "fc_type": "type (规格备注)",
    "specimen_label": "试件标号",
    "fy": "fy (MPa)",
    "fcy150": "fcy150",
    "r_ratio": "再生骨料取代率(%)",
    "b": "b (mm)",
    "h": "h (mm)",
    "t": "t (mm)",
    "r0": "r0 (mm)",
    "L": "L (mm)",
    "e1": "e1 (mm)",
    "e2": "e2 (mm)",
    "n_exp": "Nexp (kN)"
}

# System Prompt
SYSTEM_PROMPT = """
# 0. Relevance & Validity Check (CRITICAL)

**CRITICAL STEP**: 在提取详细数据前，请综合文字和图像信息判断文档是否符合要求。
**符合要求的标准**（必须全部满足）：

1. **对象**: 必须是钢管混凝土 (CFST) 构件。
2. **内容**: 必须包含 **试验数据 (Experimental Data/Test Results)**。
   - *Visual Hint*: 寻找包含 "Test", "Experimental" 标题的表格，或展示试件破坏模态（压溃、鼓曲）的**试验照片**。
3. **构件类型**: 必须是柱 (Columns/Stub columns)。

**拒绝情况 (Rejection)**：

- 纯有限元模拟 (FEA only) 且无试验验证 -> **拒绝**。
- 纯理论推导 (Analytical only) -> **拒绝**。
- 梁 (Beams) 或 节点 (Joints) -> **拒绝**。

**如果不符合要求**：
输出一个空的 JSON 结构，status 标记为 false：
`{ "Group_A": [], "Group_B": [], "Group_C": [], "is_valid": false, "reason": "Not experimental CFST column paper" }`

# Role 
你是一个精通钢管混凝土（CFST）试验数据的结构工程专家助手。
你正在使用先进的计算机视觉能力分析学术论文的页面图像（Images of Paper Pages）。

# Task 
分析输入的论文页面图像，提取CFST构件的试验数据。
**Core Strategy (Visual Processing)**: 

1. 扫描所有图片，定位包含几何尺寸和试验结果的表格 (Tables)。
2. 以 **Specimen Label (试件编号)** 为唯一索引（Primary Key）。
3. 如果数据分散在不同表格（例如尺寸在 Table 1，承载力在 Table 2），请根据 Specimen Label 将它们合并。

# 1. Classification & Geometry Mapping Rules (Strict) 
将构件分为三组，并严格执行几何参数映射： 
* **Group_A (Square/Rectangular)**: 方形/矩形。 
    - `b` = Width (宽度), `h` = Depth (深度). 
* **Group_B (Circular)**: 圆形。 
    - `b` = Diameter (直径 $D$), `h` = Diameter (直径 $D$). (Must satisfy `b == h`). 
* **Group_C (Round_ended)**: 圆端形/椭圆形。 
    - `b` = Major Axis (长轴), `h` = Minor Axis (短轴). (Must satisfy `b >= h`). 

# 2. Data Extraction Dictionary (Precise Definitions)
请严格基于以下定义提取数据：

* **Basic Info**:
    - `ref_no`: Leave blank (Python will auto-fill filename).
    - `specimen_label`: The unique ID/Label of the specimen.

* **Material Properties**:
    - `fc_value`: Concrete compressive strength **value** only (MPa).
    - `fc_type`: Description (e.g., "Cube 150", "Cylinder 150x300"，"prism 150×150×300mm").示例中均为标准的立方体,圆柱体或棱柱体(轴心)抗压强度。若文中未说明规格，则只描述"cube"，"cylinder"，"prism"。
    - `fy`: Yield strength of steel (MPa).
    - `r_ratio`: Recycled aggregate ratio (%). Fill `0` if normal concrete.

* **Geometric Dimensions**:
    - `b` & `h`: See Section 1 rules (mm).
    - `t`: Thickness of the steel tube (mm).
    - `r0`: External corner/radius (mm). **Calculate strictly as follows**:
        - For **Group_A**: Always fill `0`.
        - For **Group_B**: Fill `h / 2` (i.e., Radius).
        - For **Group_C**: Fill `h / 2` (Radius of the circular ends).
    - `L`: Length of the specimen (mm).

* **Loading & Results**:
    - `e1`, `e2`: Eccentricity (mm).e1为上端偏心，e2为下端偏心,如果未明确定义上下端偏心，则默认e1=e2=文中的偏心e(eccentricity). Axial = 0. 
    - `n_exp`: **Experimental** Ultimate Bearing Capacity ($N_{exp}$/Peak Load). Unit: kN. **Exclude** FEA/Calculated results.

* **Source Evidence (Visual Tracking)**:   
- `source_evidence`: **必须提供数据来源的视觉定位**。    - 格式： "Page [X], Table [Y]" 或 "Page [X] text section"。    - 目的：方便人工回溯检查。
* **Formatting**:
    - `fcy150`: Always leave as empty string `""`.
    - Remove units from numeric fields.

# 3. OCR Correction (Visual Assistant)

由于你是通过视觉识别图片中的文字，请注意以下OCR纠错，但不要改变原始数据的含义：

- 区分数字 `1` 和字母 `l/I`。
- 区分数字 `0` 和字母 `O`。
- 注意小数点 `.` 的位置（结合土木工程常识，例如 fc 不可能是 305 MPa）。

# 4. Output Format (JSON Only - STRICT RULES)
**CRITICAL OUTPUT REQUIREMENTS:**

1. **PURE JSON ONLY**: Output ONLY a raw JSON string. DO NOT wrap in Markdown code blocks (```json ... ```). DO NOT add any explanatory text before or after the JSON.

2. **reason FIELD CONSTRAINT**: The `reason` field MUST be either:
   - An empty string: `""` (preferred for valid data)
   - OR a brief explanation with MAXIMUM 10 words (e.g., "Not experimental CFST column paper")
   - DO NOT write long explanations or paragraphs in the reason field

3. **JSON Structure**:
```json
{
  "is_valid": true/false,
  "reason": "",
  "Group_A": [ ... ],
  "Group_B": [ ... ],
  "Group_C": [ ... ]
}
```

**EXAMPLES OF CORRECT OUTPUT:**
✅ `{"is_valid": true, "reason": "", "Group_A": [{"ref_no": "", "specimen_label": "C-1", ...}]}`

❌ WRONG: ```json{...}``` (Markdown wrapping)
❌ WRONG: `{"is_valid": true, "reason": "The paper provides comprehensive experimental data..."}` (Too long)
"""

def move_failed_file(file_path):
    """将失败的文件移动到 NotInput 目录"""
    if not os.path.exists(NOT_INPUT_DIRECTORY):
        os.makedirs(NOT_INPUT_DIRECTORY)
        print(f"Created directory: {NOT_INPUT_DIRECTORY}")
    
    filename = os.path.basename(file_path)
    destination = os.path.join(NOT_INPUT_DIRECTORY, filename)
    
    try:
        shutil.move(file_path, destination)
        print(f"  -> Moved failed file to: {destination}")
    except Exception as e:
        print(f"  -> Error moving file {filename}: {e}")

def move_excluded_file(file_path):
    """将不符合要求的文件移动到 Excluded 目录"""
    if not os.path.exists(EXCLUDED_DIRECTORY):
        os.makedirs(EXCLUDED_DIRECTORY)
        print(f"Created directory: {EXCLUDED_DIRECTORY}")

    filename = os.path.basename(file_path)
    destination = os.path.join(EXCLUDED_DIRECTORY, filename)

    try:
        shutil.move(file_path, destination)
        print(f"  -> Moved excluded file to: {destination}")
    except Exception as e:
        print(f"  -> Error moving file {filename}: {e}")

def move_to_manual_review(file_path, config):
    """将提取失败的文件移动到 Manual_Review 目录"""
    paths = config.get("paths", {})
    manual_review_path = paths.get("manual_review_path", "./Manual_Review")

    if not os.path.exists(manual_review_path):
        os.makedirs(manual_review_path, exist_ok=True)
        print(f"  创建目录: {manual_review_path}")

    filename = os.path.basename(file_path)
    destination = os.path.join(manual_review_path, filename)

    try:
        shutil.move(file_path, destination)
        print(f"  -> Moved to Manual_Review: {destination}")
    except Exception as e:
        print(f"  -> Error moving file {filename}: {e}")

def load_state():
    """Load state from state.json"""
    state_path = os.path.join(BASE_DIR, "state.json")
    default_state = {
        "batch_number": 1,
        "last_archive_date": datetime.now().strftime("%Y-%m-%d"),
        "total_archives": 0,
        "last_import_date": datetime.now().strftime("%Y-%m-%d")
    }

    try:
        if os.path.exists(state_path):
            with open(state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
                # Ensure all required keys exist
                for key, value in default_state.items():
                    if key not in state:
                        state[key] = value
                print(f"State loaded from {state_path}")
                return state
        else:
            print(f"State file not found at {state_path}, creating default")
            # Create default state file
            with open(state_path, 'w', encoding='utf-8') as f:
                json.dump(default_state, f, indent=2, ensure_ascii=False)
            return default_state
    except Exception as e:
        print(f"Error loading state: {e}, using defaults")
        return default_state

def save_state(state):
    """Save state to state.json"""
    state_path = os.path.join(BASE_DIR, "state.json")
    try:
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        print(f"State saved to {state_path}")
    except Exception as e:
        print(f"Error saving state: {e}")

def import_pdfs_from_windows(config):
    """Import PDFs from Windows folder to files/ directory"""
    print("\n=== PDF Import Automation ===")

    # Check if source path exists
    source_path = config.get("paths", {}).get("windows_source_path", "")
    if not source_path or not os.path.exists(source_path):
        print(f"Error: Source path does not exist: {source_path}")
        return False

    # Delete existing PDFs if configured
    if config.get("delete_existing_before_import", True):
        print("Deleting existing PDFs in files/ directory...")
        pdf_files = [f for f in os.listdir(TARGET_DIRECTORY) if f.lower().endswith('.pdf')]
        deleted_count = 0
        for pdf_file in pdf_files:
            try:
                os.remove(os.path.join(TARGET_DIRECTORY, pdf_file))
                deleted_count += 1
            except Exception as e:
                print(f"  Warning: Could not delete {pdf_file}: {e}")
        print(f"  Deleted {deleted_count} existing PDF files")

    # Copy PDFs from Windows source
    print(f"Copying PDFs from {source_path} to {TARGET_DIRECTORY}...")
    copied_count = 0
    error_count = 0

    for root, _, files in os.walk(source_path):
        for file in files:
            if file.lower().endswith('.pdf'):
                source_file = os.path.join(root, file)
                dest_file = os.path.join(TARGET_DIRECTORY, file)

                # Handle duplicate filenames
                counter = 1
                base_name, ext = os.path.splitext(file)
                while os.path.exists(dest_file):
                    new_name = f"{base_name}_{counter}{ext}"
                    dest_file = os.path.join(TARGET_DIRECTORY, new_name)
                    counter += 1

                try:
                    shutil.copy2(source_file, dest_file)
                    copied_count += 1
                    print(f"  ✓ Copied: {file}")
                except Exception as e:
                    error_count += 1
                    print(f"  ✗ Error copying {file}: {e}")

    print(f"\nImport summary: {copied_count} PDFs copied, {error_count} errors")

    # Update last import date in state
    state = load_state()
    state["last_import_date"] = datetime.now().strftime("%Y-%m-%d")
    save_state(state)

    return copied_count > 0

def archive_results(config, state):
    """Archive processing results to Windows destination"""
    print("\n=== Batch Processing Archiving ===")

    # Check if archive destination exists
    archive_dest = config.get("paths", {}).get("archive_destination", "")
    if not archive_dest or not os.path.exists(archive_dest):
        print(f"Error: Archive destination does not exist: {archive_dest}")
        return False

    # Create archive folder name
    today = datetime.now().strftime("%Y-%m-%d")
    batch_num = state.get("batch_number", 1)
    archive_folder_name = f"Dataset ({batch_num}) {today}"
    archive_path = os.path.join(archive_dest, archive_folder_name)

    # Create archive folder
    try:
        os.makedirs(archive_path, exist_ok=True)
        print(f"Created archive folder: {archive_path}")
    except Exception as e:
        print(f"Error creating archive folder: {e}")
        return False

    # Copy folders and files
    items_to_copy = [
        ("files", os.path.join(archive_path, "files")),
        ("Excluded", os.path.join(archive_path, "Excluded")),
        ("NotInput", os.path.join(archive_path, "NotInput"))
    ]

    copied_items = 0
    for source_name, dest_path in items_to_copy:
        source_path = os.path.join(BASE_DIR, source_name)
        if os.path.exists(source_path) and os.listdir(source_path):
            try:
                shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
                copied_items += 1
                print(f"  ✓ Copied {source_name}/ folder")
            except Exception as e:
                print(f"  ✗ Error copying {source_name}/: {e}")

    # Copy Excel output
    excel_file = os.path.join(BASE_DIR, "CFST_Extracted_Data.xlsx")
    if os.path.exists(excel_file):
        try:
            dest_excel = os.path.join(archive_path, "CFST_Extracted_Data.xlsx")
            shutil.copy2(excel_file, dest_excel)
            copied_items += 1
            print(f"  ✓ Copied CFST_Extracted_Data.xlsx")
        except Exception as e:
            print(f"  ✗ Error copying Excel file: {e}")

    if copied_items == 0:
        print("Warning: No items to archive")
        return False

    # Update state
    state["batch_number"] = batch_num + 1
    state["last_archive_date"] = today
    state["total_archives"] = state.get("total_archives", 0) + 1
    save_state(state)

    print(f"\nArchive complete: {copied_items} items archived to {archive_path}")
    print(f"Batch number incremented to: {state['batch_number']}")

    # Clean source folders if configured
    if config.get("cleanup_after_archive", True):
        print("\nCleaning source folders...")
        for source_name, _ in items_to_copy:
            source_path = os.path.join(BASE_DIR, source_name)
            if os.path.exists(source_path):
                for item in os.listdir(source_path):
                    item_path = os.path.join(source_path, item)
                    try:
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                    except Exception as e:
                        print(f"  Warning: Could not clean {item_path}: {e}")
        print("  Source folders cleaned")

    return True

def archive_cache(
    cache_dir: str,
    pdf_name: str,
    batch_number: int
) -> Optional[str]:
    """
    将cache目录归档到指定位置

    Args:
        cache_dir: cache目录路径
        pdf_name: PDF文件名（用于命名zip文件）
        batch_number: 批次号

    Returns:
        归档文件路径（成功）或 None（失败）
    """
    # Get archive base path from config
    config = load_and_validate_config()
    archive_base = config.get("paths", {}).get("archive_destination", "/mnt/e/Documents/data_extracted")

    if not archive_base or not os.path.exists(archive_base):
        print(f"归档目标不存在: {archive_base}")
        return None

    # Create archive directory path
    date_str = datetime.now().strftime("%Y-%m-%d")
    archive_dir = os.path.join(archive_base, f"Dataset ({batch_number}) {date_str}")

    try:
        # Create archive directory
        os.makedirs(archive_dir, exist_ok=True)

        # Create zip file path (without .zip extension for make_archive)
        zip_path = os.path.join(archive_dir, f"{pdf_name}_images")

        # Check if zip already exists
        if os.path.exists(f"{zip_path}.zip"):
            print(f"归档已存在，跳过: {zip_path}.zip")
            # Still remove the cache directory if zip exists
            if os.path.exists(cache_dir):
                shutil.rmtree(cache_dir)
            return f"{zip_path}.zip"

        # Create zip archive
        shutil.make_archive(zip_path, 'zip', cache_dir)

        # Verify zip was created and delete cache
        if os.path.exists(f"{zip_path}.zip"):
            # Delete cache directory after successful archiving
            if os.path.exists(cache_dir):
                shutil.rmtree(cache_dir)
            print(f"归档成功: {zip_path}.zip")
            return f"{zip_path}.zip"
        else:
            print(f"归档失败: zip文件未创建")
            return None

    except Exception as e:
        print(f"归档失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None



def main():
    # Add command-line argument parsing
    import argparse

    parser = argparse.ArgumentParser(description='CFST PDF数据提取工具')
    parser.add_argument(
        '--mode',
        choices=['full', 'extract_only', 'process_from_cache'],
        default='full',
        help='运行模式: full=完整处理, extract_only=仅提取图片, process_from_cache=从cache处理'
    )
    parser.add_argument(
        '--cache-dir',
        type=str,
        help='cache目录路径（process_from_cache模式时使用）'
    )
    parser.add_argument(
        '--pdf-name',
        type=str,
        help='PDF文件名（process_from_cache模式时使用）'
    )

    args = parser.parse_args()

    # Handle process_from_cache mode
    if args.mode == 'process_from_cache':
        if not args.cache_dir or not args.pdf_name:
            print("错误：process_from_cache模式需要--cache-dir和--pdf-name参数")
            return False

        if not os.path.exists(args.cache_dir):
            print(f"错误：cache目录不存在: {args.cache_dir}")
            return False

        print("=== Process from Cache Mode ===")
        print(f"cache目录: {args.cache_dir}")
        print(f"PDF名称: {args.pdf_name}")

        # Setup logger
        log_file = f"./logs/CacheProcess_{args.pdf_name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
        os.makedirs("./logs", exist_ok=True)
        logger = setup_logger(log_file=log_file, console_level=logging.INFO, file_level=logging.DEBUG)

        # Load config and client
        config = load_and_validate_config()
        api_key = config['api_settings']['api_key']
        base_url = config['api_settings']['base_url']
        client = OpenAI(api_key=api_key, base_url=base_url)

        # Scan for image files
        image_paths = sorted([
            os.path.join(args.cache_dir, f)
            for f in os.listdir(args.cache_dir)
            if f.endswith('.jpg')
        ])

        if not image_paths:
            print(f"错误：cache目录中没有找到jpg图片: {args.cache_dir}")
            return False

        print(f"找到 {len(image_paths)} 张图片")

        # Process from cache
        json_data = process_from_cache(args.cache_dir, args.pdf_name, image_paths, client, config, SYSTEM_PROMPT)

        if json_data:
            print("✅ 从cache处理成功")

            # Load state for batch number
            state = load_state()
            batch_number = state.get('batch_number', 1)

            # Archive cache
            print("归档cache...")
            archive_result = archive_cache(args.cache_dir, args.pdf_name, batch_number)

            if archive_result:
                print(f"✅ 归档成功: {archive_result}")
            else:
                print("⚠️  归档失败")

            return True
        else:
            print("❌ 从cache处理失败")
            return False

    # Handle extract_only mode
    elif args.mode == 'extract_only':
        print("=== Extract Only Mode ===")

        # Load config and setup
        config = load_and_validate_config()
        client = None  # No API needed for extract_only

        # Process PDFs
        pdf_files = [f for f in os.listdir(TARGET_DIRECTORY) if f.lower().endswith('.pdf')]

        if not pdf_files:
            print(f"没有找到PDF文件: {TARGET_DIRECTORY}")
            return False

        print(f"找到 {len(pdf_files)} 个PDF文件")

        for filename in pdf_files:
            file_path = os.path.join(TARGET_DIRECTORY, filename)
            print(f"\n--- 提取图片: {filename} ---")

            cache_result = process_pdf(file_path, client, config, SYSTEM_PROMPT, mode="extract_only")

            if cache_result:
                cache_dir = cache_result["cache_dir"]
                print(f"✅ 提取成功: {cache_dir}")
            else:
                print(f"❌ 提取失败")

        print("\n=== 提取完成 ===")
        return True

    # Default full mode
    # Load state first to get batch number for logging
    state = load_state()
    batch_number = state.get('batch_number', 1)

    # Setup logger with batch-based log file
    log_file = f"./logs/Batch-{batch_number}_{datetime.now().strftime('%Y-%m-%d')}.log"
    logger = setup_logger(log_file=log_file, console_level=logging.INFO, file_level=logging.DEBUG)

    # Log batch start information (file only)
    logger.info("=" * 60)
    logger.info(f"CFST Data Extractor - Batch #{batch_number}")
    logger.info(f"日志文件: {log_file}")
    logger.info("=" * 60)

    # Check dependencies first
    poppler_ok, poppler_msg = check_poppler_installation()
    if not poppler_ok:
        logger.error(f"Poppler检查失败: {poppler_msg}")
        print(poppler_msg)
        return

    # Load config and state
    try:
        config_path = os.path.join(BASE_DIR, "config.json")
        config = load_and_validate_config(config_path)
        logger.debug(f"配置加载成功: {config}")
    except ConfigError as e:
        logger.error(f"配置错误: {e}")
        print(f"配置错误: {e}")
        print("请检查 config.json 文件并修复上述问题")
        return
    except Exception as e:
        logger.error(f"加载配置时出错: {e}")
        print(f"加载配置时出错: {e}")
        return

    logger.info("系统初始化完成，开始处理PDF文件")

    # Import PDFs from Windows if configured
    if config.get("auto_cleanup", True):
        logger.info("=== Starting PDF Automation Workflow ===")
        print("\n=== Starting PDF Automation Workflow ===")
        print(f"Batch #{state.get('batch_number', 1)} - Last archive: {state.get('last_archive_date', 'Never')}")

        # Import PDFs
        import_success = import_pdfs_from_windows(config)
        if not import_success:
            logger.warning("PDF import failed or no PDFs found. Exiting workflow.")
            print("PDF import failed or no PDFs found. Exiting workflow.")
            return

    # Initialize OpenAI client with config settings
    try:
        api_settings = config.get("api_settings", {})
        api_key = api_settings.get("api_key")
        base_url = api_settings.get("base_url")
        model_name = api_settings.get("model_name")

        # Initialize OpenAI client without instructor patching for now
        # We'll use standard OpenAI client for vision API
        client = OpenAI(api_key=api_key, base_url=base_url)

        logger.info(f"OpenAI client initialized with model: {model_name}")
        print(f"OpenAI client initialized with model: {model_name}")

    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        print(f"Failed to initialize OpenAI client: {e}")
        return

    # Storage for processed data
    all_data = {
        "Group_A": [],
        "Group_B": [],
        "Group_C": []
    }

    # Verify directory exists
    if not os.path.exists(TARGET_DIRECTORY):
        print(f"Directory not found: {TARGET_DIRECTORY}")
        return

    # Iterate over files
    pdf_files = [f for f in os.listdir(TARGET_DIRECTORY) if f.lower().endswith('.pdf')]

    if not pdf_files:
        print(f"No PDF files found in {TARGET_DIRECTORY}")
        return

    print(f"Found {len(pdf_files)} PDF files in {TARGET_DIRECTORY}")

    for filename in pdf_files:
        file_path = os.path.join(TARGET_DIRECTORY, filename)
        pdf_name = os.path.splitext(filename)[0]

        try:
            # Stage 1: Extract images to cache
            print(f"\n--- Processing {filename} ---")
            print("阶段1: 提取图片...")
            cache_result = process_pdf(file_path, client, config, SYSTEM_PROMPT, mode="extract_only")

            if not cache_result:
                print(f"  ❌ 阶段1失败: 图片提取失败")
                move_failed_file(file_path)
                continue

            cache_info = cache_result
            cache_dir = cache_info["cache_dir"]
            image_paths = cache_info["image_paths"]

            print(f"  ✅ 阶段1完成: 提取了{len(image_paths)}张图片")

            # Stage 2: Process from cache
            print("阶段2: 从cache调用API...")
            json_data = process_from_cache(cache_dir, pdf_name, image_paths, client, config, SYSTEM_PROMPT)

            if not json_data:
                print(f"  ❌ 阶段2失败: API调用失败")
                # Don't move PDF to NotInput - keep it for retry, but don't archive cache
                continue

            print("  ✅ 阶段2完成: API调用成功")

            # Check validity first
            is_valid = json_data.get("is_valid", True)

            if not is_valid:
                reason = json_data.get("reason", "No reason provided")
                print(f"  - ⚠️  文件被排除: {filename}. 原因: {reason}")
                move_excluded_file(file_path)
                continue

            # Zero-data detection and handling
            group_a = json_data.get("Group_A", [])
            group_b = json_data.get("Group_B", [])
            group_c = json_data.get("Group_C", [])

            if not group_a and not group_b and not group_c:
                print(f"  - ⚠️  警告: {filename} 未提取到数据，可能是跨页或非常规格式。")
                print(f"      将文件移动到 Manual_Review 文件夹...")
                move_to_manual_review(file_path, config)
                continue

            # Post-processing & Ref.No Injection
            success = False
            for group in ["Group_A", "Group_B", "Group_C"]:
                if group in json_data and isinstance(json_data[group], list):
                    for item in json_data[group]:
                        item["ref_no"] = filename  # Force assign filename
                        all_data[group].append(item)
                    if json_data[group]: # If we found any items in any group
                         success = True

            if success:
                print(f"  - ✅ 成功处理 {filename}")

                # Stage 3: Archive cache
                print("阶段3: 归档cache...")
                archive_result = archive_cache(cache_dir, pdf_name, batch_number)

                if archive_result:
                    print(f"  ✅ 阶段3完成: 归档到 {os.path.basename(archive_result)}")
                else:
                    print(f"  ⚠️  阶段3警告: 归档失败，保留cache")

            else:
                print(f"  - ⚠️  警告: {filename} 数据为空")
                move_to_manual_review(file_path, config)

        except json.JSONDecodeError as e:
            # JSON parsing/truncation error - move to Manual_Review
            print(f"  - ❌ JSON解析失败: {filename}")
            print(f"    错误: {str(e)}")
            print(f"    截断内容预览: {e.doc[:200]}...")
            move_to_manual_review(file_path, config)

        except Exception as e:
            print(f"  - ❌ 处理失败: {filename} - {str(e)}")
            move_failed_file(file_path)

    # 4. Apply physical validation and prepare for export
    print("\nApplying physical validation...")
    validated_data = {}
    validation_reports = []

    for group, items in all_data.items():
        if items:
            df = pd.DataFrame(items)

            # Ensure all expected columns exist
            for col in COL_MAPPING.keys():
                if col not in df.columns:
                    df[col] = "" if col == "fcy150" else 0.0

            # Apply physical validation
            df_validated = validate_dataframe(df)
            validated_data[group] = df_validated

            # Generate validation report
            report = generate_validation_report(df_validated, group)
            validation_reports.append(report)
            print(report)
        else:
            validated_data[group] = pd.DataFrame()

    # 5. Save to Excel with styling
    output_file = os.path.join(OUTPUT_DIRECTORY, "CFST_Extracted_Data.xlsx")
    print(f"\nSaving data to {output_file}...")

    success = export_to_excel_with_styling(validated_data, output_file, COL_MAPPING)

    if success:
        print("Extraction complete. Data saved with validation and styling.")

        # Print summary statistics
        total_specimens = sum(len(df) for df in validated_data.values() if df is not None)
        total_manual_check = sum(
            df['needs_manual_check'].sum() if df is not None and 'needs_manual_check' in df.columns else 0
            for df in validated_data.values()
        )

        print(f"\n=== Overall Summary ===")
        print(f"Total specimens extracted: {total_specimens}")
        print(f"Specimens needing manual check: {total_manual_check}")
        if total_specimens > 0:
            percentage = (total_manual_check / total_specimens) * 100
            print(f"Manual check rate: {percentage:.1f}%")

            # Calculate expected reduction in manual review
            expected_reduction = 70  # Target from requirements
            current_rate = percentage
            if current_rate > 0:
                reduction_achieved = min(100, (100 - current_rate) / 100 * 100)
                print(f"Manual review reduction achieved: {reduction_achieved:.1f}% (target: {expected_reduction}%)")
    else:
        print("Extraction complete but Excel export failed.")

    # Archive results if configured
    if config.get("auto_increment", True) and success:
        print("\n=== Starting Archive Process ===")
        archive_success = archive_results(config, state)
        if archive_success:
            print("Workflow complete: Import → Extract → Archive")
        else:
            print("Workflow complete: Import → Extract (Archive failed)")

if __name__ == "__main__":
    main()
