I will update `main.py` to implement the "Pre-Check" mechanism to filter out irrelevant papers and handle them by moving them to an `Excluded` folder.

**1. Configuration Updates**
- Define `EXCLUDED_DIRECTORY = r"C:\Users\LEGION\Desktop\data\Excluded"`

**2. System Prompt Updates**
- Insert the **`# 0. Relevance & Validity Check (CRITICAL)`** section at the very beginning of the `SYSTEM_PROMPT`.
- Update the **`# 3. Output Format`** section to include the `is_valid` (boolean) and `reason` (string) fields in the JSON schema for both valid and invalid scenarios.
    - *Valid Case*: `"is_valid": true`
    - *Invalid Case*: `"is_valid": false, "reason": "..."`

**3. Python Logic Updates**
- Add a new helper function `move_excluded_file(file_path)` to handle file relocation.
- Modify the `main()` processing loop:
    - Parse the `is_valid` field from the returned JSON.
    - **If `is_valid` is `False`**:
        - Print the rejection reason.
        - Call `move_excluded_file` to move the PDF to the `Excluded` folder.
        - Skip data extraction for this file.
    - **If `is_valid` is `True`** (or default to True if data is present):
        - Proceed with the existing logic to inject `ref_no` and append data to `all_data`.

**4. Execution**
- Run the updated script to process the files, automatically filtering irrelevant ones to `Excluded`, failed ones to `NotInput`, and valid ones to the Excel file.