# Requirements Document

## Introduction

This spec upgrades the CFST Data Extractor's PDF processing pipeline from text-based extraction (pdfplumber) to vision-based analysis using Gemini 3 Flash AI. The upgrade improves accuracy by leveraging visual table recognition and enables adaptive processing strategies based on document length.

## Alignment with Product Vision

This feature advances the CFST Data Extractor's mission to automate experimental test data extraction from academic literature. By adopting vision-based AI analysis, the system can better handle complex table formats, cross-page data, and visual elements that text-only extraction might miss, resulting in higher quality data extraction.

## Requirements

### Requirement 1: Configuration-Driven Architecture

**User Story:** As a developer, I want all API settings and processing parameters in a centralized config file (config.json), so that the system can be easily configured without code changes.

#### Acceptance Criteria

1. WHEN the application starts THEN it SHALL load all API settings (api_key, base_url, model_name) from config.json
2. WHEN the application starts THEN it SHALL load processing parameters (short_paper_threshold, max_scan_limit, image_dpi) from config.json
3. WHEN the application starts THEN it SHALL load file paths (source, archive, manual_review) from config.json
4. IF any required config value is missing or invalid THEN the system SHALL throw a clear error message and halt execution

### Requirement 2: Visual-Based PDF Processing

**User Story:** As a CFST researcher, I want the system to analyze PDF pages visually using AI vision capabilities, so that it can accurately extract data from tables regardless of text extraction quality.

#### Acceptance Criteria

1. WHEN processing a PDF THEN the system SHALL NOT use pdfplumber for text extraction (remove dependency)
2. WHEN processing a PDF THEN the system SHALL convert pages to images using pdf2image with configurable DPI
3. WHEN processing a PDF THEN the system SHALL encode images as base64 for API transmission
4. WHEN processing a PDF THEN the system SHALL send images to Gemini AI using OpenAI-compatible vision API
5. IF pdf2image requires poppler THEN the system SHALL check for poppler installation and provide clear installation instructions if missing

### Requirement 3: Adaptive Page Scanning Strategy

**User Story:** As a researcher processing varying paper lengths, I want the system to automatically detect paper length and apply appropriate scanning strategies, so that short papers are fully analyzed while long papers are efficiently processed.

#### Acceptance Criteria

1. WHEN a PDF has ≤ short_paper_threshold pages (default 15) THEN the system SHALL process ALL pages
2. WHEN a PDF has > short_paper_threshold pages THEN the system SHALL limit processing to max_scan_limit pages (default 10)
3. WHEN determining page count THEN the system SHALL accurately count total pages before processing
4. IF page count cannot be determined THEN the system SHALL fall back to processing up to max_scan_limit pages

### Requirement 4: Zero-Data Detection and Handling

**User Story:** As a researcher, I want the system to detect when no data can be extracted from a PDF and move it to a manual review folder, so that I can handle edge cases separately without interrupting batch processing.

#### Acceptance Criteria

1. WHEN the AI returns empty Group_A, Group_B, and Group_C arrays THEN the system SHALL identify this as zero-data extraction
2. WHEN zero-data is detected THEN the system SHALL move the PDF to the manual_review_path directory (not Excluded)
3. WHEN zero-data is detected THEN the system SHALL log a yellow warning message in the UI
4. WHEN zero-data is detected THEN the system SHALL NOT halt batch processing

### Requirement 5: System Prompt Preservation

**User Story:** As the system architect, I want the existing system prompt to be used exactly as defined, so that all business rules (eccentricity definitions, strength types, group classifications) remain strictly enforced.

#### Acceptance Criteria

1. WHEN sending requests to Gemini AI THEN the system SHALL use the provided SYSTEM_PROMPT constant without modification
2. WHEN the AI processes responses THEN all geometry mapping rules (Group_A, Group_B, Group_C) SHALL be enforced
3. WHEN extracting data THEN all data field definitions (r0 calculations, e1/e2 handling, unit conversions) SHALL be preserved
4. WHEN processing responses THEN the system SHALL output JSON in the specified format with is_valid and reason fields

### Requirement 6: Dependency Management

**User Story:** As a developer deploying the system, I want clear dependency requirements and environment checks, so that I can ensure all prerequisites are met before running the application.

#### Acceptance Criteria

1. WHEN the application starts THEN it SHALL verify poppler is installed using shutil.which
2. IF poppler is not installed THEN the system SHALL display clear instructions in Chinese for installing poppler
3. WHEN importing OpenAI client THEN the system SHALL use the openai package for API calls
4. WHEN processing images THEN the system SHALL use PIL/Pillow for image handling

## Non-Functional Requirements

### Code Architecture and Modularity
- **Single Responsibility Principle**: processing.py should handle only PDF processing logic
- **Configuration Separation**: No hardcoded values in code - all settings from config.json
- **Error Handling**: Clear error messages for missing dependencies or invalid configurations
- **Code Comments**: Document API changes from text-based to vision-based processing

### Performance
- Processing time should remain reasonable (visual analysis may be slower than text extraction)
- Batch processing capability must be maintained
- Memory usage should be optimized for large PDF handling

### Reliability
- Graceful degradation when API calls fail
- Proper error handling for invalid PDFs
- Clear logging of processing decisions (page count, scanning strategy)

### Usability
- Error messages should be in Chinese for Chinese-speaking users
- Console output should clearly indicate processing strategy being used
- Failed extractions should be clearly identified and moved for manual review
