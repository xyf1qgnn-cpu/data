# Expert Detail Questions

## Q1: Should we maintain the existing 15-column structure while adding new columns?
**Default if unknown:** Yes (backward compatibility with existing downstream tools)

**Reasoning:** The current `COL_MAPPING` defines 15 specific columns that are exported to Excel. Downstream analysis tools likely depend on this exact structure. We should add new columns (`source_evidence`, `N_theory`, `xi`, `needs_manual_check`) while preserving the original 15 columns in their current positions and names.

## Q2: Should the physical validation be applied to all specimen groups (A, B, C) uniformly?
**Default if unknown:** Yes (formulas are specified as applicable to all section types)

**Reasoning:** The requirements state "上述公式适用于所有截面类型" (the above formulas apply to all section types). The physical validation formulas for $A_c$ and $A_s$ appear to be general formulas for rectangular sections with rounded corners, which should work for all three groups (square/rectangular, circular, round-ended) with appropriate parameter interpretations.

## Q3: Should we implement intelligent text segmentation or simply remove the 50,000 character limit?
**Default if unknown:** Implement intelligent segmentation (preserve beginning + appendices)

**Reasoning:** The requirement says "从截取前50,000字符改为保留全文或智能切分（保留开头+附录）" (change from truncating first 50,000 characters to preserving full text or intelligent segmentation (preserve beginning + appendices)). Intelligent segmentation that preserves key sections (beginning, tables, appendices) is better than simply removing the limit, as it balances performance with data completeness.

## Q4: Should the Excel styling use conditional formatting or pandas Styler?
**Default if unknown:** Use pandas Styler (simpler integration with existing code)

**Reasoning:** The current workflow uses `pd.ExcelWriter` with `openpyxl`. Pandas Styler integrates well with this setup and allows programmatic styling based on column values. Conditional formatting in Excel would require more complex `openpyxl` manipulation.

## Q5: Should we create a separate validation script or integrate validation into the main workflow?
**Default if unknown:** Integrate into main workflow (single execution flow)

**Reasoning:** The requirement says "导出后需添加计算列或运行脚本完成校验（而非直接结束流程）" (after export, need to add calculation columns or run script to complete validation (rather than directly ending the process)). This suggests validation should be part of the workflow, not a separate post-processing step. Integration ensures consistency and reduces manual steps.