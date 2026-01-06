# Tasks Document

## Phase 1: Configuration Infrastructure

- [x] 1.1 Refactor config.json structure
  - File: config.json
  - Implement new nested structure with api_settings, processing_settings, and paths
  - Update all existing config references in main.py
  - Add manual_review_path configuration
  - _Leverage: existing config.json loading pattern in main.py
  - _Requirements: 1
  - _Prompt: Role: Python Developer with expertise in configuration management and JSON schema design | Task: Refactor config.json to implement nested structure with api_settings, processing_settings, and paths sections following requirement 1, updating all references in main.py to use new structure | Restrictions: Must maintain backward compatibility for existing path configs, use clear and intuitive naming, validate required fields on load | Success: New config structure is implemented and validated, all existing config references are updated, application can load both old and new structures gracefully

- [x] 1.2 Create configuration validation module
  - File: config_manager.py (new)
  - Implement config validation with clear error messages for missing required fields
  - Add API settings validation (api_key, base_url, model_name)
  - Add processing settings validation with reasonable defaults
  - _Leverage: existing load_config() pattern from main.py
  - _Requirements: 1, 6
  - _Prompt: Role: Python Developer specializing in configuration validation and error handling | Task: Create configuration validation module following requirements 1 and 6, implementing comprehensive validation for API settings and processing parameters with clear error messages | Restrictions: Must validate all required fields, provide helpful error messages in Chinese for Chinese users, use type hints for better code quality | Success: All config validations work correctly, clear error messages guide users to fix issues, validation covers all required and optional fields

## Phase 2: Vision Processing Infrastructure

- [x] 2.1 Install and configure pdf2image and dependencies
  - Install pdf2image and pillow packages
  - Add poppler dependency check on application startup
  - Provide Chinese installation instructions for different platforms
  - _Leverage: shutil.which() for dependency checking
  - _Requirements: 6
  - _Prompt: Role: DevOps Engineer with expertise in Python package management and system dependencies | Task: Install pdf2image and configure poppler dependency checking following requirement 6, with platform-specific installation instructions | Restrictions: Must not hardcode platform assumptions, provide clear actionable instructions, handle both apt and manual installation | Success: pdf2image is installed and working, poppler check provides clear instructions, application starts successfully with dependencies met

- [x] 2.2 Create PDF image conversion utility
  - File: processing.py (modify existing)
  - Implement convert_pdf_to_images(pdf_path, page_limit) function
  - Add get_page_count(pdf_path) function using pdf2image
  - Handle image format conversion and DPI settings
  - _Leverage: pdf2image.convert_from_path(), PIL.Image
  - _Requirements: 2, 3
  - _Prompt: Role: Python Developer with expertise in PDF processing and image manipulation | Task: Create PDF image conversion utility following requirements 2 and 3, implementing functions to convert PDF pages to images and count pages accurately | Restrictions: Must handle page limits correctly, support configurable DPI, manage memory efficiently for large PDFs, provide clear error messages for invalid PDFs | Success: PDFs are converted to images correctly, page counting is accurate, memory usage is reasonable, errors are handled gracefully

- [x] 2.3 Implement base64 image encoding
  - File: processing.py (continue from task 2.2)
  - Create encode_image_to_base64(image) function
  - Handle image format conversion for optimal transmission
  - _Leverage: base64 module, io.BytesIO
  - _Requirements: 2
  - _Prompt: Role: Python Developer with expertise in data encoding and optimization | Task: Implement base64 image encoding following requirement 2, creating efficient functions to convert PIL Images to base64 strings for API transmission | Restrictions: Must optimize image size for transmission, maintain image quality, handle multiple image formats, ensure efficient memory usage | Success: Images are encoded correctly to base64, file sizes are optimized, encoding is efficient and reliable

## Phase 3: AI Integration

- [x] 3.1 Update OpenAI client initialization
  - File: main.py
  - Replace instructor-patched DeepSeek client with standard OpenAI client
  - Load credentials from config.json api_settings
  - Remove hardcoded API_KEY, BASE_URL, MODEL_NAME constants
  - _Leverage: openai.OpenAI client, config loading functions
  - _Requirements: 1, 2
  - _Prompt: Role: Python Developer with expertise in API integrations and OpenAI-compatible interfaces | Task: Update OpenAI client initialization following requirements 1 and 2, replacing hardcoded values with config.json loaded settings | Restrictions: Must remove all hardcoded constants, maintain error handling patterns, support both old and new config structures temporarily | Success: OpenAI client is initialized with config values, no hardcoded credentials remain, error handling works correctly

- [x] 3.2 Create vision API payload builder
  - File: processing.py
  - Implement build_vision_payload(images, system_prompt) function
  - Construct OpenAI-compatible vision format with image_url elements
  - Add text instruction for multi-page analysis
  - _Leverage: SYSTEM_PROMPT constant from main.py
  - _Requirements: 2, 5
  - _Prompt: Role: Python Developer specializing in API payload construction and prompt engineering | Task: Create vision API payload builder following requirements 2 and 5, constructing OpenAI-compatible vision format with system prompt and multiple images | Restrictions: Must follow OpenAI vision API specification, maintain system prompt exactly as provided, optimize token usage, handle multiple images efficiently | Success: Payload is correctly formatted for vision API, system prompt is preserved, all images are included, token usage is optimized

- [x] 3.3 Implement vision API call function
  - File: processing.py
  - Create call_vision_api(payload, client) function
  - Handle API errors with exponential backoff retry
  - Parse JSON response and handle parsing errors
  - _Leverage: openai.OpenAI client, json parsing
  - _Requirements: 2, 4
  - _Prompt: Role: Python Developer with expertise in API integration and error handling | Task: Implement vision API call function following requirements 2 and 4, with error handling and retry logic | Restrictions: Must implement exponential backoff, handle network errors gracefully, parse JSON responses correctly, maintain batch processing on failures | Success: API calls work reliably, errors are handled with retries, JSON parsing is robust, failures don't stop batch processing

## Phase 4: Adaptive Processing Strategy

- [x] 4.1 Implement adaptive page scanning logic
  - File: processing.py
  - Create should_scan_all_pages(page_count, threshold) function
  - Create get_pages_to_process(page_count, config) function
  - Implement decision logic for short vs long papers
  - _Leverage: processing_settings from config.json
  - _Requirements: 3
  - _Prompt: Role: Python Developer with expertise in algorithm design and configuration-driven logic | Task: Implement adaptive page scanning logic following requirement 3, creating functions to determine scanning strategy based on page count and thresholds | Restrictions: Must use config values, handle edge cases (page count unknown), log decisions clearly, maintain batch processing efficiency | Success: Logic correctly determines scanning strategy, decisions are logged, edge cases handled, efficiency is maintained

- [x] 4.2 Create main process_pdf() function
  - File: processing.py
  - Implement main entry point orchestrating entire vision processing flow
  - Integrate page counting, image conversion, encoding, API calls
  - Return parsed JSON in same format as existing extract_data_with_ai()
  - _Leverage: All functions from tasks 2.2, 2.3, 3.2, 3.3, 4.1
  - _Requirements: 2, 3, 4, 5
  - _Prompt: Role: Senior Python Developer with expertise in orchestration and integration | Task: Create main process_pdf() function following requirements 2, 3, 4, and 5, orchestrating entire vision processing pipeline | Restrictions: Must maintain same return format as existing function, handle all error scenarios, log processing steps clearly, integrate all components seamlessly | Success: process_pdf() works end-to-end, maintains compatibility with existing code, handles errors gracefully, logs are clear and informative

## Phase 5: Error Handling and Edge Cases

- [x] 5.1 Implement zero-data detection and handling
  - File: main.py
  - Add check for empty Group_A, Group_B, and Group_C arrays
  - Move files to manual_review_path with yellow warning message
  - Create manual review directory if it doesn't exist
  - _Leverage: move_failed_file pattern
  - _Requirements: 4
  - _Prompt: Role: Python Developer with expertise in edge case handling and user experience | Task: Implement zero-data detection and handling following requirement 4, creating logic to detect empty extraction results and move files appropriately | Restrictions: Must check all groups are empty, use colored warning messages, move to new manual_review_path, continue batch processing | Success: Zero-data cases are detected correctly, files moved to appropriate location, warnings are clear and colored, batch processing continues

- [x] 5.2 Add comprehensive error handling
  - File: main.py and processing.py
  - Wrap vision processing calls in try/except blocks
  - Add specific error messages for different failure types
  - Ensure failed files continue to NotInput/ in appropriate cases
  - _Leverage: existing move_failed_file and move_excluded_file functions
  - _Requirements: 2, 4, 6
  - _Prompt: Role: Python Developer with expertise in defensive programming and error handling | Task: Add comprehensive error handling throughout vision processing pipeline following requirements 2, 4, and 6 | Restrictions: Must not let errors stop batch processing, provide specific error messages, differentiate between different failure types, maintain existing error handling patterns | Success: All errors are handled gracefully, batch processing continues, error messages are clear and actionable, files are moved to appropriate directories

## Phase 6: Integration and Cleanup

- [x] 6.1 Update main.py to use vision processing
  - File: main.py
  - Replace extract_text_from_pdf() and extract_data_with_ai() calls with process_pdf()
  - Update workflow orchestration to handle new processing pipeline
  - Update imports and remove unused imports (pdfplumber, processing.optimize_text_for_extraction)
  - _Leverage: process_pdf() from processing.py
  - _Requirements: 1, 2, 3, 4, 5
  - _Prompt: Role: Python Developer with expertise in refactoring and integration | Task: Update main.py to use new vision processing pipeline following requirements 1, 2, 3, 4, and 5, replacing text-based extraction with vision-based processing | Restrictions: Must maintain existing workflow structure, remove unused imports and code, preserve error handling patterns, ensure backward compatibility where possible | Success: main.py uses new vision processing, old text extraction code is removed, workflow functions correctly, all features work as expected

- [ ] 6.2 Clean up unused code and dependencies
  - Files: main.py, processing.py
  - Remove extract_text_from_pdf() function
  - Remove extract_data_with_ai() function
  - Remove unused imports (pdfplumber from main.py)
  - Update requirements.txt to remove pdfplumber, add pdf2image, pillow
  - _Leverage: git for version control, careful code review
  - _Requirements: 1, 2
  - _Prompt: Role: Python Developer with expertise in code cleanup and dependency management | Task: Clean up unused code and dependencies following requirements 1 and 2, removing text-based extraction functions and updating dependencies | Restrictions: Must not break existing functionality, keep code history in git, update documentation, ensure all imports are cleaned up | Success: Unused code is removed, dependencies are updated, code is cleaner and more maintainable, documentation is updated

- [ ] 6.3 Update documentation and add comments
  - File: main.py, processing.py, config.json
  - Update docstrings to reflect vision-based processing
  - Add inline comments explaining new logic and parameters
  - Update README.md with new architecture description
  - Add configuration examples in config.json comments
  - _Leverage: existing docstring patterns
  - _Requirements: 1, 2, 3, 4
  - _Prompt: Role: Technical Writer with expertise in code documentation and user guides | Task: Update documentation and add comments following requirements 1, 2, 3, and 4, explaining the new vision-based architecture | Restrictions: Must maintain existing documentation style, explain complex logic clearly, update all relevant documentation, use consistent terminology | Success: Documentation is clear and comprehensive, comments explain complex logic, users can understand the new architecture, configuration examples are helpful

## Phase 7: Testing and Validation

- [ ] 7.1 Test short paper processing (≤15 pages)
  - Use sample short CFST paper
  - Verify all pages are converted and processed
  - Check that extraction works correctly
  - Verify results in Excel output
  - _Requirements: 3
  - _Prompt: Role: QA Engineer with expertise in functional testing and validation | Task: Test short paper processing following requirement 3, verifying that papers with ≤15 pages are fully scanned and processed correctly | Restrictions: Must use real CFST papers, verify page counting accuracy, confirm all pages are processed, validate extraction quality | Success: Short papers are processed correctly, all pages are scanned, extraction works as expected, results are accurate

- [ ] 7.2 Test long paper processing (>15 pages)
  - Use sample long CFST paper (>15 pages)
  - Verify only first 10 pages are processed (configurable)
  - Check that warning is logged about truncation
  - Validate that extraction still works with partial scanning
  - _Requirements: 3
  - _Prompt: Role: QA Engineer with expertise in boundary testing and performance validation | Task: Test long paper processing following requirement 3, verifying that papers with >15 pages are truncated correctly and warnings are logged | Restrictions: Must test with actual long papers, verify truncation logic, confirm warnings appear, ensure extraction quality is maintained | Success: Long papers are truncated correctly, warnings are logged, processing is efficient, extraction quality is acceptable

- [ ] 7.3 Test zero-data detection
  - Use non-CFST paper or paper without extractable data
  - Verify yellow warning is displayed
  - Check that file is moved to Manual_Review/ directory
  - Confirm batch processing continues
  - _Requirements: 4
  - _Prompt: Role: QA Engineer with expertise in edge case testing and error handling | Task: Test zero-data detection following requirement 4, verifying that papers without extractable data are handled correctly | Restrictions: Must test with various non-CFST papers, verify warning messages, confirm file movement, ensure no processing interruption | Success: Zero-data cases are detected correctly, warnings are clear, files moved to correct location, batch processing continues

- [ ] 7.4 Test dependency checks
  - Test without poppler installed
  - Verify clear error message in Chinese
  - Test with invalid API configuration
  - Verify appropriate error messages
  - _Requirements: 6
  - _Prompt: Role: QA Engineer with expertise in system testing and error validation | Task: Test dependency checks following requirement 6, verifying that missing dependencies and invalid configurations produce clear error messages | Restrictions: Must test on clean environment, verify error messages are actionable, test various configuration errors, ensure proper application shutdown | Success: Error messages are clear and helpful, users can understand and fix issues, application exits gracefully on critical errors

- [ ] 7.5 Validate JSON output format
  - Test that AI returns correct JSON structure
  - Verify is_valid and reason fields are present
  - Check that all specimen groups follow correct schema
  - Validate numeric fields have units removed
  - _Requirements: 5
  - _Prompt: Role: QA Engineer with expertise in data validation and schema verification | Task: Validate JSON output format following requirement 5, verifying that AI responses match expected schema and all fields are correctly formatted | Restrictions: Must verify all JSON fields, check data types, validate numeric field formatting, ensure schema compliance | Success: JSON output matches expected format, all fields are present and correctly typed, numeric fields are formatted properly, validation passes
