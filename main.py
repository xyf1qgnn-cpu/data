import os
import json
import shutil
import pdfplumber
import pandas as pd
from openai import OpenAI
import instructor
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from models import SpecimenData, ExtractionResult
from validation import validate_dataframe, get_validation_summary
from styling import export_to_excel_with_styling, generate_validation_report, reorder_columns_for_export
from parallel_processor import process_directory_parallel, process_directory_sequential

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

API_KEY = "sk-TcRezCA6VhsQ5bQvUwQxB0A6HkqKYOmpddeIGC9JKYPC6bEU"  # Replace with your actual API key
BASE_URL = "https://api.silra.cn/v1"
MODEL_NAME = "deepseek-chat"

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
# 0. Input Format Note
The provided text is in **Markdown format** extracted from a PDF document. The last page (references) has been removed. The text may contain:
- Markdown headings (#, ##, ###)
- Tables in Markdown table syntax
- Lists and formatting

When extracting data from tables, use the preserved table structure to accurately map data to specimen labels.

# 0. Relevance & Validity Check (CRITICAL)
在提取数据前，必须先判断文档是否符合要求。
**符合要求的标准**（必须全部满足）：
1. **对象**: 必须是 **钢管混凝土 (CFST)** 柱构件。
   - **核心特征**: 外部为单层钢管 (Single Skin Steel Tube)，内部核心区域主要填充混凝土。
   - **允许包含 (Allowed Variations)**:
     - 再生骨料混凝土 (RAC-filled)。
     - 不锈钢/高强钢 (Stainless/High-strength steel)。
     - 带内部加劲肋 (With internal stiffeners/ribs)。
     - 核心含型钢 (Steel-reinforced / SR-CFST)。
2. **内容**: 必须包含 **试验数据 (Experimental Data)**。
3. **构件类型**: 必须是柱 (Columns/Stub columns)。

**拒绝情况**：
- 拒绝 CFDST: 如果是中空夹层/双层管 (Double Skin / CFDST / SRCDST)，即包含内管和外管的，**直接拒绝**。
- 如果是纯有限元模拟 (FEA only) 且无试验验证 -> **拒绝**。
- 如果是纯理论推导 (Analytical/Derivation only) -> **拒绝**。
- 如果是梁 (Beams) 或 节点 (Joints) -> **拒绝**。

**如果不符合要求**：
请直接输出一个空的 JSON 结构，并附带 status 标记：
`{ "Group_A": [], "Group_B": [], "Group_C": [], "is_valid": false, "reason": "Not experimental CFST column paper" }`

# Role 
你是一个精通钢管混凝土（CFST）试验数据的结构工程专家助手。 

# Task 
从输入的学术文献文本中提取CFST构件的试验数据，并根据截面形状将其分类整理为结构化的JSON数据。 

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

* **Source Evidence (NEW for Workflow 2.0)**:
    - `source_evidence`: **必须为每个数值提供源文档中的确切文本证据**
    - 例如：如果 `fc_value = 30.5`，source_evidence 应为 "混凝土抗压强度为 30.5 MPa"
    - 证据应直接来自源文档文本，不要修改或解释
    - 每个字段的证据应分开，用分号分隔

* **Formatting**:
    - `fcy150`: Always leave as empty string `""`.
    - Remove units from numeric fields.

# 3. Output Format (JSON Only) 
Output a JSON object with keys: "Group_A", "Group_B", "Group_C", "is_valid", "reason". 

**JSON Schema:** 
{ 
  "is_valid": true,
  "reason": "Valid CFST experimental data",
  "Group_A": [ 
    { 
      "ref_no": "", 
      "specimen_label": "String", 
      "fc_value": Number, 
      "fc_type": "String", 
      "fy": Number, 
      "fcy150": "", 
      "r_ratio": Number, 
      "b": Number, 
      "h": Number, 
      "t": Number, 
      "r0": Number, 
      "L": Number, 
      "e1": Number, 
      "e2": Number, 
      "n_exp": Number 
    } 
  ], 
  "Group_B": [], 
  "Group_C": [] 
} 
"""

def extract_text_from_pdf(pdf_path):
    """提取PDF为Markdown格式，并移除最后一页（参考文献）"""
    print(f"Processing PDF: {os.path.basename(pdf_path)}...")
    markdown_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            # 遍历所有页面，除了最后一页
            for i, page in enumerate(pdf.pages):
                if i < total_pages - 1:  # 跳过最后一页
                    try:
                        # 使用 extract_markdown() 而不是 extract_text()
                        page_markdown = page.extract_markdown()
                        if page_markdown:
                            markdown_text += page_markdown + "\n\n"
                    except AttributeError:
                        # 如果 pdfplumber 版本不支持 extract_markdown，回退到 extract_text
                        page_text = page.extract_text()
                        if page_text:
                            markdown_text += page_text + "\n\n"
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
    return markdown_text

def extract_data_with_ai(client, text):
    """调用DeepSeek API提取数据（使用instructor结构化输出）"""
    if not text.strip():
        print("Warning: Extracted text is empty.")
        return None

    try:
        # Simple length check - truncate if too long
        if len(text) > 50000:
            print(f"  - Warning: Text is {len(text)} chars, truncating to 50000")
            processed_text = text[:50000]
        else:
            processed_text = text

        # Use instructor to get structured output
        result = client.chat.completions.create(
            model=MODEL_NAME,
            response_model=ExtractionResult,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "Extract data from this text:\n" + processed_text}
            ],
            temperature=0.1,
            max_tokens=8192
        )

        # Convert Pydantic model to dict for backward compatibility
        return result.model_dump()
    except Exception as e:
        print(f"Error calling API: {e}")
        return None

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

def load_config():
    """Load configuration from config.json"""
    config_path = os.path.join(BASE_DIR, "config.json")
    default_config = {
        "windows_source_path": "/mnt/c/Users/username/Documents/PDF_Source",
        "archive_destination": "/mnt/e/Documents/data_extracted",
        "auto_cleanup": True,
        "auto_increment": True,
        "delete_existing_before_import": True,
        "cleanup_after_archive": True
    }

    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys exist
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                print(f"Configuration loaded from {config_path}")
                return config
        else:
            print(f"Configuration file not found at {config_path}, using defaults")
            # Create default config file
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            return default_config
    except Exception as e:
        print(f"Error loading configuration: {e}, using defaults")
        return default_config

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
    source_path = config.get("windows_source_path", "")
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

    for root, dirs, files in os.walk(source_path):
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
    archive_dest = config.get("archive_destination", "")
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

def get_pending_directories(config, state):
    """Get list of directories that need to be processed in polling mode"""
    source_path = config.get("polling_source_path", "/mnt/e/Documents/data_unextracted")
    processed_dirs = state.get("polling_processed_dirs", [])

    if not os.path.exists(source_path):
        print(f"Error: Polling source path does not exist: {source_path}")
        return []

    pending = []
    for item in os.listdir(source_path):
        item_path = os.path.join(source_path, item)
        if os.path.isdir(item_path) and item_path not in processed_dirs:
            # Check if directory contains PDF files
            pdf_files = [f for f in os.listdir(item_path) if f.lower().endswith('.pdf')]
            if pdf_files:
                pending.append({
                    "source_path": item_path,
                    "name": item,
                    "pdf_count": len(pdf_files)
                })

    # Sort by name to ensure consistent processing order
    return sorted(pending, key=lambda x: x["name"])

def cleanup_directory(dir_info, config):
    """Clean up after processing a directory: delete Excel and move source if configured"""
    cleanup_actions = []

    # 1. Delete local Excel file if configured
    if config.get("delete_excel_after_archive", True):
        excel_file = os.path.join(OUTPUT_DIRECTORY, "CFST_Extracted_Data.xlsx")
        if os.path.exists(excel_file):
            try:
                os.remove(excel_file)
                cleanup_actions.append("Deleted local Excel file")
                print(f"  ✓ Deleted local Excel file")
            except Exception as e:
                print(f"  ✗ Error deleting Excel file: {e}")

    # 2. Move source directory if configured
    if config.get("move_source_after_processing", True):
        processed_location = config.get("processed_dirs_location", "/mnt/e/Documents/processed_directories")
        source_path = dir_info["source_path"]
        dir_name = os.path.basename(source_path)

        # Create processed location directory if it doesn't exist
        if not os.path.exists(processed_location):
            try:
                os.makedirs(processed_location)
                print(f"  Created processed directories location: {processed_location}")
            except Exception as e:
                print(f"  ✗ Error creating processed location: {e}")
                return cleanup_actions

        # Move the directory
        dest_path = os.path.join(processed_location, dir_name)

        # Handle duplicate directory names
        if os.path.exists(dest_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_path = f"{dest_path}_{timestamp}"

        try:
            shutil.move(source_path, dest_path)
            cleanup_actions.append(f"Moved to {dest_path}")
            print(f"  ✓ Moved processed directory to: {dest_path}")
        except Exception as e:
            print(f"  ✗ Error moving directory: {e}")

    return cleanup_actions

def mark_directory_processed(dir_info, state):
    """Mark a directory as processed in state.json"""
    if "polling_processed_dirs" not in state:
        state["polling_processed_dirs"] = []

    # Add to processed list if not already there
    if dir_info["source_path"] not in state["polling_processed_dirs"]:
        state["polling_processed_dirs"].append(dir_info["source_path"])

    state["current_processing_dir"] = None
    state["last_polling_check"] = datetime.now().isoformat()

    save_state(state)
    print(f"  ✓ Updated state: marked {dir_info['name']} as processed")

def export_results_to_excel(validated_data, output_file):
    """Export validated data to Excel with styling"""
    success = export_to_excel_with_styling(validated_data, output_file, COL_MAPPING)

    if success:
        # Print summary statistics
        total_specimens = sum(len(df) for df in validated_data.values() if df is not None and not df.empty)
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

        return True
    else:
        print("❌ Excel export failed")
        return False

def process_target_directory(target_dir, config, mode="sequential"):
    """
    Process a single target directory containing PDF files

    Args:
        target_dir: Path to directory containing PDFs
        config: Configuration dictionary
        mode: Processing mode - "sequential" or "parallel"

    Returns:
        dict: Processing results and statistics
    """
    print(f"\n=== Processing Directory: {os.path.basename(target_dir)} ===")

    # Use temporary files directory for processing
    temp_files_dir = TARGET_DIRECTORY

    # Clear existing files in temp directory
    if os.path.exists(temp_files_dir):
        for f in os.listdir(temp_files_dir):
            f_path = os.path.join(temp_files_dir, f)
            try:
                if os.path.isfile(f_path):
                    os.remove(f_path)
            except Exception as e:
                print(f"Warning: Could not clear {f_path}: {e}")
    else:
        os.makedirs(temp_files_dir)

    # Copy PDFs from target directory to temp location
    pdf_files = [f for f in os.listdir(target_dir) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print(f"No PDF files found in {target_dir}")
        return None

    print(f"Found {len(pdf_files)} PDF files")

    for pdf_file in pdf_files:
        src = os.path.join(target_dir, pdf_file)
        dst = os.path.join(temp_files_dir, pdf_file)
        try:
            shutil.copy2(src, dst)
        except Exception as e:
            print(f"Error copying {pdf_file}: {e}")
            return None

    # Process based on mode
    if mode == "parallel":
        max_workers = config.get("max_concurrent_files", 10)
        processing_result = process_directory_parallel(temp_files_dir, max_workers)
    else:
        processing_result = process_directory_sequential(temp_files_dir)

    if not processing_result or "results" not in processing_result:
        print("❌ Processing failed")
        return None

    # Validate and prepare data for export
    print("\nApplying physical validation...")
    validated_data = {}

    processed_data = processing_result["results"]
    for group, items in processed_data.items():
        if items:
            df = pd.DataFrame(items)

            # Ensure all expected columns exist
            for col in COL_MAPPING.keys():
                if col not in df.columns:
                    df[col] = "" if col == "fcy150" else 0.0

            # Log missing data summary
            critical_fields = ['fc_value', 'fy', 'b', 'h', 't', 'n_exp']
            missing_data_fields = []
            for field in critical_fields:
                if field in df.columns:
                    missing_count = df[field].isna().sum()
                    if missing_count > 0:
                        missing_data_fields.append(f"{field}: {missing_count}")
            if missing_data_fields:
                print(f"  ⚠️  Missing data detected - {', '.join(missing_data_fields)} records")

            # Apply physical validation
            df_validated = validate_dataframe(df)
            validated_data[group] = df_validated

            # Generate validation report
            report = generate_validation_report(df_validated, group)
            print(report)
        else:
            validated_data[group] = pd.DataFrame()

    # Export to Excel
    output_file = os.path.join(OUTPUT_DIRECTORY, "CFST_Extracted_Data.xlsx")
    success = export_results_to_excel(validated_data, output_file)

    if success:
        print(f"✅ Extraction complete for {os.path.basename(target_dir)}")
        return {
            "validated_data": validated_data,
            "output_file": output_file,
            "summary": processing_result.get("summary", {})
        }
    else:
        print(f"❌ Extraction failed for {os.path.basename(target_dir)}")
        return None

def main():
    # Load config and state
    config = load_config()
    state = load_state()

    # Initialize OpenAI client for DeepSeek with instructor patch
    global client
    client = instructor.patch(OpenAI(api_key=API_KEY, base_url=BASE_URL))

    # Check if polling mode is enabled
    if config.get("polling_mode", False):
        print("\n" + "="*60)
        print("POLLING MODE ENABLED")
        print("="*60)

        # Get list of directories to process
        pending_dirs = get_pending_directories(config, state)

        if not pending_dirs:
            print("\n✅ No directories to process. All pending directories have been completed.")
            print(f"Processed directories: {len(state.get('polling_processed_dirs', []))}")
            return

        print(f"\nFound {len(pending_dirs)} directories to process:")
        for i, dir_info in enumerate(pending_dirs, 1):
            print(f"  {i}. {dir_info['name']} ({dir_info['pdf_count']} PDFs)")

        # Process each directory
        for i, dir_info in enumerate(pending_dirs, 1):
            print("\n" + "="*60)
            print(f"Processing [{i}/{len(pending_dirs)}]: {dir_info['name']}")
            print("="*60)

            # Update state: set current processing directory
            state["current_processing_dir"] = dir_info["source_path"]
            save_state(state)

            # Determine processing mode
            mode = "parallel" if config.get("parallel_processing", False) else "sequential"
            max_workers = config.get("max_concurrent_files", 10)

            print(f"Mode: {mode}")
            if mode == "parallel":
                print(f"Max concurrent files: {max_workers}")

            # Process the directory
            result = process_target_directory(dir_info["source_path"], config, mode)

            if result:
                # Archive results
                print("\n--- Archive Phase ---")
                archive_success = archive_results(config, state)

                if archive_success:
                    print(f"  ✓ Archived results for {dir_info['name']}")
                else:
                    print(f"  ⚠️  Archive failed for {dir_info['name']}")

                # Cleanup: delete Excel and move source directory
                print("\n--- Cleanup Phase ---")
                cleanup_actions = cleanup_directory(dir_info, config)

                # Mark as processed
                mark_directory_processed(dir_info, state)

                print(f"\n✅ Completed {dir_info['name']}")
            else:
                print(f"\n❌ Failed to process {dir_info['name']}")
                # Continue to next directory even if this one failed

        print("\n" + "="*60)
        print("POLLING COMPLETE")
        print("="*60)
        print(f"\nProcessed {len(pending_dirs)} directories successfully.")

    else:
        # Legacy mode: Process files in TARGET_DIRECTORY
        print("\n=== Starting PDF Automation Workflow (Legacy Mode) ===")
        print(f"Batch #{state.get('batch_number', 1)} - Last archive: {state.get('last_archive_date', 'Never')}")

        # Import PDFs from Windows if auto_cleanup is enabled
        if config.get("auto_cleanup", True):
            import_success = import_pdfs_from_windows(config)
            if not import_success:
                print("PDF import failed or no PDFs found. Exiting workflow.")
                return

        # Run the legacy processing workflow
        run_legacy_workflow(config, state)

def run_legacy_workflow(config, state):
    """Legacy sequential processing workflow for backward compatibility"""
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

        # 1. Read PDF
        text = extract_text_from_pdf(file_path)

        if not text.strip():
             print(f"  - Extraction failed: Empty text for {filename}")
             move_failed_file(file_path)
             continue

        # 2. AI Extraction
        print(f"  - Calling AI extraction for {filename}...")
        json_data = extract_data_with_ai(client, text)

        if json_data:
            # Check validity first
            is_valid = json_data.get("is_valid", True) # Default to True if not present, but prompt asks for it

            if not is_valid:
                reason = json_data.get("reason", "No reason provided")
                print(f"  - File excluded: {filename}. Reason: {reason}")
                move_excluded_file(file_path)
                continue

            # 3. Post-processing & Ref.No Injection
            success = False
            for group in ["Group_A", "Group_B", "Group_C"]:
                if group in json_data and isinstance(json_data[group], list):
                    for item in json_data[group]:
                        item["ref_no"] = filename  # Force assign filename
                        all_data[group].append(item)
                    if json_data[group]: # If we found any items in any group
                         success = True

            print(f"  - Successfully processed {filename}")
        else:
            print(f"  - Failed to extract data for {filename} (API Error or Invalid JSON)")
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

            # Log missing data summary
            critical_fields = ['fc_value', 'fy', 'b', 'h', 't', 'n_exp']
            missing_data_fields = []
            for field in critical_fields:
                if field in df.columns:
                    missing_count = df[field].isna().sum()
                    if missing_count > 0:
                        missing_data_fields.append(f"{field}: {missing_count}")
            if missing_data_fields:
                print(f"  ⚠️  Missing data detected - {', '.join(missing_data_fields)} records")

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
