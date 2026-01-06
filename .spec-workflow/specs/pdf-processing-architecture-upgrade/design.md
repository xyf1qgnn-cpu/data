# Design Document

## Overview

This design upgrades the CFST Data Extractor from text-based PDF extraction to vision-based AI analysis using Gemini 3 Flash. The architecture shift enables more accurate table recognition, handles complex formatting, and implements adaptive scanning strategies based on document length.

## Steering Document Alignment

### Technical Standards (tech.md)
- **OpenAI-Compatible APIs**: Uses same interface patterns as existing DeepSeek integration
- **Configuration-Driven**: All parameters externalized to config.json following existing config management pattern
- **Error Handling**: Maintains existing error handling patterns (try/catch, user-friendly messages)
- **Modular Design**: Preserves single-responsibility principle across components

### Project Structure (structure.md)
- **Component Isolation**: New vision processing logic contained within processing.py
- **API Abstraction**: AI provider details abstracted through OpenAI client interface
- **Configuration Management**: Extends existing config.json structure without breaking backward compatibility

## Code Reuse Analysis

### Existing Components to Leverage
- **main.py**: Core workflow orchestration remains unchanged (import → extract → validate → export)
- **models.py**: Pydantic models (SpecimenData, ExtractionResult) reused as-is
- **validation.py**: Physical validation formulas unchanged
- **styling.py**: Excel export and formatting preserved
- **Error handling patterns**: move_failed_file, move_excluded_file functions reused

### Integration Points
- **OpenAI Client**: Replace instructor-patched DeepSeek client with OpenAI-compatible Gemini client
- **Configuration Loading**: Extend load_config() to include new API and processing settings
- **PDF Processing Pipeline**: Replace extract_text_from_pdf() with vision-based process_pdf()
- **Result Processing**: Unchanged - AI returns same JSON structure for backward compatibility

## Architecture

The upgraded architecture shifts from text extraction to visual analysis:

### Current Architecture (Text-Based)
```
PDF → pdfplumber → Text → optimize_text_for_extraction() → AI → JSON → Validation → Excel
```

### New Architecture (Vision-Based)
```
PDF → pdf2image → Images → Base64 Encoding → Vision AI → JSON → Validation → Excel
                                      ↓
                              Adaptive Page Strategy
```

### Modular Design Principles
- **Single File Responsibility**: processing.py handles all PDF-to-image conversion and AI interaction
- **Configuration Separation**: Zero hardcoded values - all settings from config.json
- **Interface Consistency**: AI integration maintains same JSON input/output format
- **Error Isolation**: Processing failures isolated from main workflow

```mermaid
graph TD
    A[main.py:main()] --> B[Load Config from config.json]
    A --> C[Initialize OpenAI Client]
    D[PDF files in files/] --> E[process_pdf() in processing.py]
    E --> F{Page Count Check}
    F -->|≤ threshold| G[Convert ALL pages to images]
    F -->|> threshold| H[Convert first MAX pages]
    G --> I[Encode images to Base64]
    H --> I
    I --> J[Build Vision API Payload]
    J --> K[Send to Gemini AI]
    K --> L[Parse JSON Response]
    L --> M{is_valid check}
    M -->|false| N[Move to Excluded/]
    M -->|true| O[Extract specimen data]
    O --> P[Validation via validation.py]
    P --> Q[Export to Excel via styling.py]
    N --> R[Continue batch processing]
    Q --> R
    R --> S{More PDFs?}
    S -->|yes| D
    S -->|no| T[Archive results]

    subgraph "Configuration"
        B
        U[config.json]
        B --- U
    end

    subgraph "Vision Processing"
        E
        V[pdf2image + PIL]
        W[Base64 encoding]
        E --- V
        E --- W
    end

    subgraph "AI Integration"
        C
        J
        K
        X[OpenAI-compatible API]
        C --- X
        J --- X
        K --- X
    end
```

## Components and Interfaces

### Component 1: Configuration Manager (Extended)
**Purpose**: Centralize all settings including new vision processing parameters
**Interfaces**:
- `load_config()`: Returns expanded config dict with api_settings, processing_settings, paths
- `validate_config()`: Checks required fields (api_key, base_url, model_name) and raises clear errors
**Dependencies**: json, os
**Reuses**: Existing config loading pattern from main.py

### Component 2: Vision PDF Processor (New)
**Purpose**: Convert PDF pages to images and interact with vision AI
**Interfaces**:
- `process_pdf(pdf_path: str) -> dict`: Main entry point, returns parsed JSON
- `convert_pdf_to_images(pdf_path: str, page_limit: int) -> List[Image]`: Handles pdf2image conversion
- `encode_image_to_base64(image) -> str`: Converts PIL Image to base64 string
- `build_vision_payload(images: List, system_prompt: str) -> dict`: Constructs OpenAI vision format
- `call_vision_api(payload: dict) -> dict`: Makes API call and handles errors
**Dependencies**: pdf2image, PIL, base64, io, openai, config
**Reuses**: SYSTEM_PROMPT constant from main.py, existing error handling patterns

### Component 3: Adaptive Strategy Engine (New)
**Purpose**: Determine scanning strategy based on document length
**Interfaces**:
- `get_page_count(pdf_path: str) -> int`: Uses pdf2image/pypdf to count pages
- `should_scan_all_pages(page_count: int, threshold: int) -> bool`: Decision logic
- `get_pages_to_process(page_count: int, config: dict) -> List[int]`: Returns page numbers
**Dependencies**: pdf2image or pypdf
**Reuses**: Processing thresholds from config.json

## Data Models

### Enhanced Config Structure
```python
{
  "api_settings": {
    "api_key": "string",  # Required: API key for Gemini
    "base_url": "string",  # Required: OpenAI-compatible endpoint
    "model_name": "string"  # Required: e.g., "vertex-gemini-3-flash-preview"
  },
  "processing_settings": {
    "short_paper_threshold": "int",  # Pages ≤ this: scan all (default: 15)
    "max_scan_limit": "int",  # Pages > threshold: scan this many (default: 10)
    "image_dpi": "int"  # DPI for PDF to image conversion (default: 150)
  },
  "paths": {
    "windows_source_path": "string",  # Optional: Windows PDF source
    "archive_destination": "string",  # Optional: Archive location
    "manual_review_path": "string"  # NEW: Failed extraction location
  }
}
```

### Vision API Payload Format
```python
{
  "model": "vertex-gemini-3-flash-preview",
  "messages": [
    {"role": "system", "content": "SYSTEM_PROMPT"},
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "Extract data from these pages..."},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}},
        ...
      ]
    }
  ],
  "temperature": 0.1,
  "max_tokens": 8192
}
```

## Error Handling

### Error Scenario 1: Missing Dependencies
**Description**: poppler not installed for pdf2image
**Handling**:
- Use `shutil.which()` to check for `pdftoppm` or `pdfinfo`
- Raise clear error with Chinese installation instructions:
  - Ubuntu/Debian: `sudo apt-get install poppler-utils`
  - Windows: Download from https://github.com/oschwartz10612/poppler-windows
- Halt application startup with descriptive error message

**User Impact**: Clear actionable error message prevents cryptic failures

### Error Scenario 2: Invalid API Configuration
**Description**: Missing or invalid API key/base_url/model_name
**Handling**:
- Validate config on startup: check all required fields present
- Verify API connectivity with test call (optional)
- Raise ValueError with specific missing field names

**User Impact**: Prevents runtime API failures, clear configuration guidance

### Error Scenario 3: PDF Processing Failure
**Description**: Corrupted PDF, password-protected, or unsupported format
**Handling**:
- Wrap pdf2image calls in try/except
- On failure: log warning, move to NotInput/, continue batch processing
- Record error reason in log for debugging

**User Impact**: Batch processing continues, failed files isolated for manual review

### Error Scenario 4: Zero Data Extraction
**Description**: AI returns empty Group_A/B/C arrays
**Handling**:
- Check if all groups are empty AND is_valid=true
- Log yellow warning: "⚠️ [Filename] 未提取到数据..."
- Move file to manual_review_path/ (create if not exists)
- Continue batch processing

**User Impact**: Transparent extraction failures, separate location for edge cases

### Error Scenario 5: API Rate Limits/Network Errors
**Description**: API timeout, rate limiting, network issues
**Handling**:
- Implement exponential backoff retry logic (3 attempts)
- On persistent failure: log error, move to NotInput/, continue
- Respect rate limit headers if provided by API

**User Impact**: Graceful degradation, automatic retry where appropriate

## Testing Strategy

### Unit Testing
- **Configuration Loading**: Test all config scenarios (missing fields, invalid values)
- **Image Conversion**: Test pdf2image with various PDF formats (single page, multi-page, corrupted)
- **Base64 Encoding**: Verify image encoding/decoding roundtrip
- **Page Count Detection**: Test accuracy across different PDF types
- **Adaptive Strategy**: Verify logic for different page counts and thresholds

**Key components to test**:
- `process_pdf()` - main processing logic
- `convert_pdf_to_images()` - image conversion with page limits
- `get_page_count()` - page counting accuracy
- Configuration validation functions

### Integration Testing
- **End-to-End Vision Flow**: PDF → Images → API → JSON (with test PDFs)
- **Configuration Integration**: Verify config values flow through entire pipeline
- **Error Handling**: Test each error scenario with appropriate test files
- **Batch Processing**: Multiple PDFs with mixed success/failure cases

**Key flows to test**:
- Short paper full scanning (≤15 pages)
- Long paper truncated scanning (>15 pages)
- Zero-data detection and manual review routing
- Invalid API config error handling
- Poppler missing error handling

### End-to-End Testing
**User scenarios to test**:
1. **Normal Processing**: Standard CFST paper with tables → Extracted data in Excel
2. **Short Paper**: 10-page paper → All pages scanned, data extracted
3. **Long Paper**: 50-page paper → Only first 10 pages scanned, warning logged
4. **No Data Paper**: Paper without CFST data → Moved to Manual_Review/, warning displayed
5. **Corrupted PDF**: Invalid PDF → Moved to NotInput/, error logged, processing continues
6. **Missing Config**: Invalid API key → Clear error on startup, application exits
7. **Missing Poppler**: Poppler not installed → Clear installation instructions, application exits

**Test data needs**:
- Valid CFST papers (3-5 samples)
- Short papers (<15 pages)
- Long papers (>15 pages)
- Papers without extractable data
- Corrupted/invalid PDFs
- Password-protected PDFs
