# Discovery Questions

## Q1: Is the current Workflow 1.0 (main.py) actively used in production?
**Default if unknown:** Yes (based on the presence of input files and recent updates)

**Reasoning:** The codebase has a working `main.py` with input files in the `files/` directory, suggesting it's actively used. The requirements mention upgrading from "Workflow 1.0" to "Workflow 2.0", indicating an existing production workflow.

## Q2: Does the current workflow handle sensitive or proprietary data?
**Default if unknown:** Yes (better to be secure by default)

**Reasoning:** The workflow processes PDF documents which may contain proprietary research data or experimental results. The requirements mention data accuracy and traceability, suggesting the data has value and requires careful handling.

## Q3: Is backward compatibility required for existing output formats?
**Default if unknown:** Yes (maintain existing Excel structure with enhancements)

**Reasoning:** The current workflow outputs to `CFST_Extracted_Data.xlsx` with specific sheet names and column mappings. Users likely rely on this format for downstream analysis, so we should maintain the existing structure while adding new columns and features.

## Q4: Are there performance or scalability requirements for processing large PDFs?
**Default if unknown:** Yes (intelligent text segmentation needed)

**Reasoning:** The requirements mention moving from 50,000 character truncation to "保留全文或智能切分" (preserve full text or intelligent segmentation). This suggests performance considerations for handling large documents efficiently.

## Q5: Is there a need for batch processing of multiple files?
**Default if unknown:** Yes (current workflow already processes multiple files)

**Reasoning:** The current `main.py` processes all PDFs in the `files/` directory sequentially. The requirements mention "批量修正" (batch correction) for unit errors, indicating batch processing is part of the workflow.