# Requirements Specification: Workflow 2.0 Upgrade

## Project Overview
**Task**: Upgrade existing CFST data extraction workflow from **Workflow 1.0** to **Workflow 2.0** with structured output, physical model validation, and anomaly detection mechanisms.

**Goal**: Improve data accuracy by 70% and reduce manual intervention through automated validation and intelligent processing.

## Current State Analysis
**File**: `/home/thelya/Work/test01/data/main.py` (Workflow 1.0)
- **Input**: PDF files from `files/` directory
- **Processing**: Sequential batch processing with DeepSeek API
- **Output**: `CFST_Extracted_Data.xlsx` with sheets: Group_A, Group_B, Group_C
- **Limitations**: Manual JSON parsing, no source evidence, no physical validation, basic Excel output

## Functional Requirements

### 1. Structured Data Extraction with Instructor + Pydantic
- **Requirement**: Replace manual JSON parsing with `instructor` library and Pydantic models
- **Details**:
  - Define `SpecimenData` Pydantic model with all existing fields plus `source_evidence`
  - `source_evidence` must contain exact text from source document supporting each value
  - Use `instructor` to enforce structured output from DeepSeek API
  - Maintain backward compatibility with existing JSON structure

### 2. Physical Formula Validation ("物理安检门")
- **Requirement**: Implement theoretical capacity calculations and validation coefficient
- **Formulas**:
  - Theoretical capacity: $N_t = A_s * f_y + A_c * f_c$
  - Concrete area: $A_c = (b - 2t)(h - 2t) - (4 - \pi)r_1^2$
  - Steel area: $A_s = 2t(b + h) - 4t^2 - (4 - \pi)(r_0^2 - r_1^2)$
  - Validation coefficient: $\xi = N_{exp} / N_t$
  - Inner radius: $r_1 = \frac{h - 2t}{h} r_0$

- **Validation Rules**:
  - **Green** (0.8 < ξ < 2.5): Data correct, no manual check needed
  - **Red** (ξ > 10 or ξ < 0.1): Unit errors, batch correction required
  - **Yellow**: Manual review required

- **Implementation**:
  - Apply to all specimen groups (A, B, C) uniformly
  - Add `needs_manual_check` column: `True` if ξ not in (0.8, 2.5)
  - Add `N_theory` and `xi` calculation columns

### 3. Enhanced Excel Output with Styling
- **Requirement**: Export styled Excel with highlighting for manual review
- **Details**:
  - Maintain existing 15-column structure from `COL_MAPPING`
  - Add new columns: `source_evidence`, `N_theory`, `xi`, `needs_manual_check`
  - Position `source_evidence` next to `n_exp` for easy reference
  - Apply light red background to rows where `needs_manual_check == True`
  - Use pandas Styler for Excel styling
  - Preserve sheet names: Group_A, Group_B, Group_C

### 4. Intelligent Text Processing
- **Requirement**: Replace 50,000 character truncation with intelligent segmentation
- **Details**:
  - Preserve beginning of document (abstract, introduction, methodology)
  - Extract tables and figures (likely containing specimen data)
  - Include appendices (often containing detailed test results)
  - Exclude references section
  - Implement efficient segmentation algorithm

### 5. Integrated Workflow
- **Requirement**: Integrate validation into main processing flow
- **Details**:
  - Single execution from PDF to styled Excel
  - Validation occurs after extraction, before export
  - No separate post-processing scripts required
  - Maintain existing file movement logic (NotInput/, Excluded/)

## Technical Requirements

### 1. Dependencies
```python
# New dependencies for Workflow 2.0
instructor>=1.0.0
pydantic>=2.0.0

# Existing dependencies to maintain
pdfplumber>=0.10.0
pandas>=2.0.0
openai>=1.0.0  # For DeepSeek API
openpyxl>=3.1.0
```

### 2. Pydantic Model Structure
```python
class SpecimenData(BaseModel):
    # Existing 15 fields from COL_MAPPING
    ref_no: str
    fc_value: float
    fc_type: str
    specimen_label: str
    fy: float
    fcy150: str = ""
    r_ratio: float = 0.0
    b: float
    h: float
    t: float
    r0: float
    L: float
    e1: float = 0.0
    e2: float = 0.0
    n_exp: float

    # New field for Workflow 2.0
    source_evidence: str  # Text evidence from source document
```

### 3. File Structure Updates
```
# Modified files
main.py                          # Updated with Workflow 2.0 features

# New modules (optional)
workflow_2.0/
├── models.py                    # Pydantic models
├── validation.py                # Physical validation formulas
├── styling.py                   # Excel styling functions
└── processing.py                # Intelligent text processing
```

### 4. API Integration
- Use `instructor.patch()` to enhance OpenAI/DeepSeek client
- Maintain existing API key and base URL configuration
- Update system prompt to include source evidence requirement
- Implement error handling with retry logic

### 5. Performance Requirements
- Intelligent text segmentation must handle large PDFs efficiently
- Physical validation should use vectorized pandas operations
- Batch processing of multiple files must remain efficient
- Memory usage should be optimized for large datasets

## Non-Functional Requirements

### 1. Backward Compatibility
- **Must maintain**: Existing Excel column structure and sheet names
- **Must maintain**: File movement logic (NotInput/, Excluded/)
- **Must maintain**: Batch processing workflow
- **Can change**: Internal data structures and validation logic

### 2. Performance
- Processing time per PDF should not increase by more than 50%
- Memory usage should remain within reasonable limits
- Excel export with styling should not significantly impact performance

### 3. Accuracy
- Physical validation should correctly identify unit errors (ξ > 10 or ξ < 0.1)
- Source evidence should accurately trace values to source text
- False positive rate for manual checks should be minimized

### 4. Usability
- Styled Excel should clearly highlight data needing manual review
- Source evidence should be easily accessible for verification
- Error messages should be clear and actionable

## Implementation Plan

### Phase 1: Foundation (Week 1)
1. Install new dependencies (`instructor`, `pydantic`)
2. Define Pydantic models matching existing structure
3. Test `instructor` integration with DeepSeek API
4. Update system prompt to include source evidence requirement

### Phase 2: Validation Engine (Week 2)
1. Implement physical validation formulas
2. Add calculation columns to DataFrame
3. Implement traffic light system logic
4. Test validation with sample data

### Phase 3: Enhanced Output (Week 3)
1. Implement pandas Styler for Excel highlighting
2. Position `source_evidence` next to `n_exp`
3. Test Excel export with styling
4. Validate backward compatibility

### Phase 4: Intelligent Processing (Week 4)
1. Implement intelligent text segmentation
2. Replace 50,000 character truncation
3. Optimize performance for large PDFs
4. Test with various document structures

### Phase 5: Integration & Testing (Week 5)
1. Integrate all components into main workflow
2. Test end-to-end with existing PDF files
3. Validate accuracy improvements
4. Performance benchmarking
5. Documentation and deployment

## Acceptance Criteria

### Must Have
1. ✅ Uses `instructor` and Pydantic for structured data extraction
2. ✅ Includes `source_evidence` field with text from source document
3. ✅ Implements physical validation formulas correctly
4. ✅ Adds `N_theory`, `xi`, `needs_manual_check` columns
5. ✅ Applies light red background to rows needing manual review
6. ✅ Positions `source_evidence` next to `n_exp` in output
7. ✅ Implements intelligent text segmentation
8. ✅ Maintains backward compatibility with existing Excel format
9. ✅ Integrates validation into main workflow (no separate script)

### Should Have
1. ⚡ Efficient performance for large PDFs
2. ⚡ Clear error messages and logging
3. ⚡ Robust error handling with retry logic
4. ⚡ Comprehensive test coverage

### Could Have
1. 🔄 Batch correction suggestions for unit errors
2. 🔄 Advanced text segmentation with ML
3. 🔄 Performance optimizations for very large datasets

## Risks and Mitigations

### 1. API Compatibility Risk
- **Risk**: `instructor` library may not work with DeepSeek API
- **Mitigation**: Test with sample API calls before full implementation
- **Fallback**: Maintain legacy JSON parsing as fallback option

### 2. Performance Risk
- **Risk**: Physical validation adds computation overhead
- **Mitigation**: Use vectorized pandas operations
- **Monitoring**: Profile performance and optimize bottlenecks

### 3. Accuracy Risk
- **Risk**: Validation may flag legitimate data as suspicious
- **Mitigation**: Conservative thresholds with manual override option
- **Validation**: Test with known good/bad datasets

### 4. Backward Compatibility Risk
- **Risk**: Downstream tools may break with changes
- **Mitigation**: Maintain exact column names and sheet structure
- **Testing**: Validate with existing downstream workflows

## Success Metrics

1. **Data Accuracy**: Reduce manual review by 70% (target)
2. **Processing Time**: < 50% increase over Workflow 1.0
3. **Error Detection**: Correctly identify >90% of unit errors
4. **User Satisfaction**: Clear highlighting and source evidence tracing
5. **Maintainability**: Clean code structure with comprehensive tests

## Assumptions

1. DeepSeek API remains compatible with `instructor` library
2. Existing PDF files follow typical academic paper structure
3. Downstream tools only depend on Excel column names, not positions
4. Physical validation formulas are correct for all section types
5. Performance requirements allow for some computation overhead

## Open Questions

1. Specific implementation details for intelligent text segmentation
2. Exact styling parameters for light red background
3. Handling of missing or incomplete data in validation
4. Logging and monitoring requirements
5. Deployment and rollout strategy