import os
import json
import shutil
import pdfplumber
import pandas as pd
from openai import OpenAI
import instructor
from models import SpecimenData, ExtractionResult
from validation import validate_dataframe, get_validation_summary
from styling import export_to_excel_with_styling, generate_validation_report, reorder_columns_for_export
from processing import optimize_text_for_extraction

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

API_KEY = "sk-3a5200989e7d4575a30f9ef910afd0eb"  # Replace with your actual API key
BASE_URL = "https://api.deepseek.com"
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
# 0. Relevance & Validity Check (CRITICAL)
在提取数据前，必须先判断文档是否符合要求。
**符合要求的标准**（必须全部满足）：
1. **对象**: 必须是钢管混凝土 (CFST) 构件。
2. **内容**: 必须包含 **试验数据 (Experimental Data/Test Results)**。
3. **构件类型**: 必须是柱 (Columns/Stub columns)。

**拒绝情况**：
- 如果是纯有限元模拟 (FEA only) 且无试验验证 -> **拒绝**。
- 如果是纯理论推导 (Analytical/Derivation only) -> **拒绝**。
- 如果是综述文章 (Review Paper) -> **拒绝**。
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
    """提取PDF全文文本"""
    print(f"Processing PDF: {os.path.basename(pdf_path)}...")
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
    return text

def extract_data_with_ai(client, text):
    """调用DeepSeek API提取数据（使用instructor结构化输出）"""
    if not text.strip():
        print("Warning: Extracted text is empty.")
        return None

    try:
        # Optimize text for extraction using intelligent segmentation
        optimized_text = optimize_text_for_extraction(text)
        print(f"  - Text optimized: {len(text)} -> {len(optimized_text)} characters")

        # Use instructor to get structured output
        result = client.chat.completions.create(
            model=MODEL_NAME,
            response_model=ExtractionResult,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "Extract data from this text:\n" + optimized_text}
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

def main():
    # Initialize OpenAI client for DeepSeek with instructor patch
    client = instructor.patch(OpenAI(api_key=API_KEY, base_url=BASE_URL))
    
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

if __name__ == "__main__":
    main()
