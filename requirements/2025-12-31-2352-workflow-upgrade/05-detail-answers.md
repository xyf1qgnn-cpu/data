# Detail Answers

## Q1: Should we maintain the existing 15-column structure while adding new columns?
**Answer:** Yes

**Implications:** We must preserve the original 15 columns defined in `COL_MAPPING` with their exact names and order. New columns (`source_evidence`, `N_theory`, `xi`, `needs_manual_check`) should be added at the end or in appropriate positions without disrupting the existing structure. The `source_evidence` field should be positioned next to `n_exp` as specified in requirements.

## Q2: Should the physical validation be applied to all specimen groups (A, B, C) uniformly?
**Answer:** Yes

**Implications:** The same physical validation formulas apply to all three specimen groups. We need to ensure the formulas work correctly for all section types:
- Group_A (Square/Rectangular): $b$ = width, $h$ = depth
- Group_B (Circular): $b = h$ = diameter
- Group_C (Round-ended): $b$ = major axis, $h$ = minor axis

The formulas for $A_c$ and $A_s$ should handle all cases with appropriate parameter interpretations.

## Q3: Should we implement intelligent text segmentation or simply remove the 50,000 character limit?
**Answer:** Intelligent segmentation

**Implications:** We need to implement intelligent text segmentation that preserves:
- Beginning of document (abstract, introduction, methodology)
- Tables and figures (likely containing specimen data)
- Appendices (often containing detailed test results)
- References section can be excluded

This is more complex than simply removing the limit but provides better data completeness while managing token limits.

## Q4: Should the Excel styling use conditional formatting or pandas Styler?
**Answer:** pandas Styler

**Implications:** Use pandas Styler for Excel output styling. This integrates well with the existing `pd.ExcelWriter` workflow. We need to:
- Apply light red background to rows where `needs_manual_check == True`
- Ensure styling is preserved when writing to Excel
- Maintain compatibility with `openpyxl` engine

## Q5: Should we create a separate validation script or integrate validation into the main workflow?
**Answer:** Integrate into main workflow

**Implications:** Physical validation should be part of the main processing flow, not a separate post-processing step. This means:
- Validation happens after data extraction but before Excel export
- Validation results are added as new columns to the DataFrame
- Styling is applied based on validation results
- Single execution flow from PDF to styled Excel output

## Summary of Technical Decisions:

1. **Column Structure**: Preserve existing 15 columns, add new columns with `source_evidence` next to `n_exp`
2. **Validation Scope**: Apply same physical formulas to all specimen groups (A, B, C)
3. **Text Processing**: Implement intelligent segmentation preserving beginning + tables + appendices
4. **Excel Styling**: Use pandas Styler for light red background on rows needing manual check
5. **Workflow Integration**: Integrate validation into main processing flow, not separate script

## Implementation Constraints:

1. **Backward Compatibility**: Must not break existing downstream tools relying on current Excel format
2. **Performance**: Intelligent segmentation must be efficient for large PDFs
3. **Accuracy**: Physical validation formulas must be correctly implemented for all section types
4. **Usability**: Styled Excel output should clearly highlight data needing manual review