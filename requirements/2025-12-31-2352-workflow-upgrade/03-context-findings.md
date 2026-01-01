# Context Findings

## Current Workflow 1.0 Analysis (`/home/thelya/Work/test01/data/main.py`)

### Architecture Overview
- **Input**: PDF files from `files/` directory
- **Processing**: Sequential batch processing of all PDFs
- **Output**: `CFST_Extracted_Data.xlsx` with sheets: Group_A, Group_B, Group_C
- **API**: DeepSeek (OpenAI-compatible) with manual JSON parsing

### Key Components Identified

#### 1. Data Structure (Current)
```python
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
```

#### 2. System Prompt (137 lines)
- Extensive validation rules for CFST relevance
- Three specimen groups with geometric mapping rules
- Manual JSON schema definition
- Basic error handling through `is_valid` field

#### 3. Processing Flow
1. PDF text extraction with `pdfplumber`
2. Text truncation to 50,000 characters (line 164)
3. API call with system prompt
4. Manual JSON parsing and validation
5. Excel export with column renaming

### Limitations Identified for Workflow 2.0

#### 1. **Manual JSON Handling**
- Raw `json.loads()` without schema validation
- No type checking or data validation
- Error-prone parsing

#### 2. **Missing Source Evidence**
- No `source_evidence` field for data provenance
- Cannot trace extracted values back to source text

#### 3. **No Physical Validation**
- No theoretical capacity calculations
- No anomaly detection for unit errors
- No automated quality checks

#### 4. **Basic Output Format**
- Simple Excel without styling
- No highlighting for suspicious data
- Fixed column order

#### 5. **Performance Issues**
- Hard 50,000 character truncation
- No intelligent text segmentation
- Sequential processing only

## Workflow 2.0 Requirements Analysis

### 1. Pydantic Model Structure
Based on current fields plus new requirements:
```python
class SpecimenData(BaseModel):
    # Existing fields from COL_MAPPING
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

### 2. Physical Validation Formulas
**Theoretical Capacity Calculation:**
- $N_t = A_s * f_y + A_c * f_c$
- $A_c = (b - 2t)(h - 2t) - (4 - \pi)r_1^2$
- $A_s = 2t(b + h) - 4t^2 - (4 - \pi)(r_0^2 - r_1^2)$
- $r_1 = r_0 - t$ (inner radius)

**Validation Coefficient:**
- $\xi = N_{exp} / N_t$

**Traffic Light System:**
- Green (0.8 < ξ < 2.5): Data correct
- Red (ξ > 10 or ξ < 0.1): Unit errors, batch correction
- Yellow: Manual review required

### 3. Enhanced Output Requirements
- Add `needs_manual_check` column to DataFrame
- Apply light red background to rows needing manual review
- Position `source_evidence` next to `n_exp` for easy reference
- Maintain backward compatibility with existing Excel structure

### 4. Performance Improvements
- Replace 50,000 character truncation with intelligent segmentation
- Preserve beginning + appendices to prevent data loss
- Consider batch processing optimizations

## Technical Implementation Plan

### File Modifications Required

#### 1. **New Dependencies**
```python
# Add to requirements
instructor>=1.0.0
pydantic>=2.0.0
```

#### 2. **Main Script Updates** (`main.py`)
- Replace manual JSON parsing with instructor + Pydantic
- Add physical validation functions
- Implement DataFrame styling for Excel output
- Update text extraction to handle full documents

#### 3. **New Module Structure**
```
workflow_2.0/
├── models.py          # Pydantic models
├── validation.py      # Physical validation formulas
├── styling.py         # Excel styling functions
└── processing.py      # Enhanced text processing
```

### Integration Points

#### 1. **Backward Compatibility**
- Maintain existing `COL_MAPPING` structure
- Keep same Excel sheet names (Group_A, Group_B, Group_C)
- Preserve file movement logic (NotInput/, Excluded/)

#### 2. **Error Handling**
- Enhanced validation with Pydantic
- Structured error reporting
- Retry logic for API failures

#### 3. **Performance Considerations**
- Intelligent text segmentation for large PDFs
- Batch processing optimizations
- Memory management for large datasets

## Key Technical Decisions

### 1. **Instructor vs Native Structured Outputs**
- **Current**: DeepSeek API (OpenAI-compatible)
- **Option A**: Use `instructor` library for structured outputs
- **Option B**: Switch to Claude API for native structured outputs
- **Recommendation**: Start with `instructor` for minimal disruption

### 2. **Text Processing Strategy**
- **Current**: First 50,000 characters
- **New**: Intelligent segmentation preserving key sections
- **Implementation**: Extract beginning + tables + appendices

### 3. **Validation Integration**
- **Where**: Post-extraction, before Excel export
- **Scope**: All specimens across all groups
- **Output**: New columns + styling + manual check flags

### 4. **Excel Styling Approach**
- **Library**: pandas + openpyxl styling
- **Target**: `needs_manual_check == True` rows
- **Style**: Light red background fill

## Migration Risks and Mitigations

### 1. **API Compatibility**
- **Risk**: Instructor library may not work with DeepSeek
- **Mitigation**: Test with sample data before full migration

### 2. **Performance Impact**
- **Risk**: Physical validation adds computation overhead
- **Mitigation**: Implement efficient vectorized calculations

### 3. **Data Quality**
- **Risk**: New validation may flag legitimate data
- **Mitigation**: Conservative thresholds with manual override

### 4. **Backward Compatibility**
- **Risk**: Existing downstream tools may break
- **Mitigation**: Maintain existing column structure and naming

## Next Steps for Implementation

1. **Phase 1**: Define Pydantic models and test instructor integration
2. **Phase 2**: Implement physical validation formulas
3. **Phase 3**: Add Excel styling and enhanced output
4. **Phase 4**: Update text processing for full documents
5. **Phase 5**: Testing and validation with existing data