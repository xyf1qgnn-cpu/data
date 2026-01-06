# Tasks Document

- [ ] 1.1 Install pdfplumber dependency and update requirements.txt
  - Files: requirements.txt
  - Install pdfplumber>=0.10.0 package
  - Verify installation in CI/CD pipeline
  - _Leverage: existing requirements.txt structure
  - _Requirements: 2 (智能页面筛选机制)
  - _Prompt: Role: Python DevOps Engineer specializing in dependency management | Task: Install pdfplumber package and update requirements.txt following requirement 2, ensuring proper version specification and compatibility with existing packages | Restrictions: Must not break existing dependencies, use version constraints for stability, verify installation in test environment | Success: pdfplumber is installed and importable, all existing tests pass, CI/CD pipeline completes successfully

- [ ] 1.2 Create PDF text extraction utility module
  - File: processing.py (add new functions at top)
  - Implement extract_page_texts(pdf_path: str) -> Dict[int, str] function
  - Use pdfplumber to extract text from all pages
  - Add error handling for corrupted PDFs
  - _Leverage: pdfplumber library, existing processing.py structure
  - _Requirements: 2
  - _Prompt: Role: Python Developer with expertise in PDF processing | Task: Create PDF text extraction utility using pdfplumber following requirement 2, implementing a function to extract text from all PDF pages with proper error handling | Restrictions: Must handle corrupted PDFs gracefully, return empty dict on failure, maintain backward compatibility, ensure memory efficiency for large PDFs | Success: Function extracts text from all pages correctly, handles errors robustly, processes 100-page PDF in <200ms, memory usage remains stable

- [ ] 1.3 Implement page content scoring algorithm
  - File: processing.py (after extract_page_texts)
  - Implement score_page_content(text: str, config: dict) -> int function
  - Apply scoring rules: Table titles (+10), Data keywords (+5), References (-5), Normal text (+1)
  - Use compiled regex patterns for performance
  - _Leverage: re module, config.json settings
  - _Requirements: 2
  - _Prompt: Role: Python Developer specializing in text processing and pattern matching | Task: Implement page scoring algorithm following requirement 2, applying weighted scoring based on keyword matches with optimized regex compilation | Restrictions: Must pre-compile regex patterns, handle unicode characters, support configurable weights, achieve O(n) complexity where n is text length | Success: Scores are calculated accurately, performance is <1ms per page, all pattern types detected correctly, weights are configurable via config.json

- [ ] 1.4 Create main smart page filtering function
  - File: processing.py
  - Implement get_smart_pages_to_process(pdf_path: str, config: dict) -> Tuple[List[int], str, List[Dict]]
  - Integrate extract_page_texts() and score_page_content()
  - Apply logic: short papers (≤10 pages) skip filtering, select top pages by score, include page 1 mandatory
  - _Leverage: extract_page_texts(), score_page_content(), get_page_count() from existing code
  - _Requirements: 2
  - _Prompt: Role: Python Developer with expertise in algorithm implementation | Task: Create main smart filtering function orchestrating text extraction and scoring following requirement 2, implementing page selection logic with fallback strategies | Restrictions: Must handle edge cases (all negative scores, empty text extraction), respect absolute_max_pages limit of 30, maintain logging of decisions, support both filtered and unfiltered modes | Success: Function returns correct pages for all scenarios, logs are clear and informative, handles edge cases gracefully, short papers bypass filtering correctly

- [ ] 2.1 Update SYSTEM_PROMPT with JSON output constraints
  - File: main.py (modify SYSTEM_PROMPT constant)
  - Add complete SYSTEM_PROMPT with Role, Relevance Check, Task, and Output Format sections
  - Include CRITICAL OUTPUT REQUIREMENTS section with JSON_ONLY and reason_field constraints
  - Add EXAMPLES showing correct and incorrect outputs
  - _Leverage: existing SYSTEM_PROMPT content, full prompt text from design.md
  - _Requirements: 1
  - _Prompt: Role: Prompt Engineer specializing in AI instruction design | Task: Update SYSTEM_PROMPT in main.py following requirement 1 with complete structured prompt including JSON output constraints and examples | Restrictions: Must preserve all existing CFST extraction logic, add constraints without breaking existing prompts, ensure clear separation of sections, maintain backwards compatibility | Success: Prompt is comprehensive and well-structured, JSON constraints are clearly specified, examples illustrate correct/incorrect formats, all existing extraction rules preserved

- [ ] 2.2 Implement JSON response parsing with truncation detection
  - File: processing.py
  - Modify call_vision_api() or create parse_ai_response() function
  - Detect truncated JSON by checking for unclosed braces or cut-off strings
  - Implement fallback: if detected as truncated, move to Manual_Review
  - _Leverage: json module, existing API response handling
  - _Requirements: 1
  - _Prompt: Role: Python Developer with expertise in error handling and API response parsing | Task: Implement JSON parsing with truncation detection following requirement 1, detecting and handling incomplete AI responses gracefully | Restrictions: Must not crash on malformed JSON, provide clear error messages, move failed files to Manual_Review directory, continue batch processing on failure | Success: Truncated JSON is detected accurately, failed files moved correctly, batch processing continues, error logs are informative

- [ ] 2.3 Add JSON parse error handling in main processing loop
  - File: main.py (in PDF processing loop)
  - Wrap process_pdf() call in try/except for JSONDecodeError
  - On JSON parse failure: log ERROR with filename and truncated content, move to Manual_Review
  - Ensure batch processing continues
  - _Leverage: existing JSON parsing, move_failed_file pattern
  - _Requirements: 1
  - _Prompt: Role: Python Developer with expertise in exception handling and batch processing | Task: Add JSON parsing error handling to main processing loop in main.py following requirement 1, implementing graceful failure and continuation | Restrictions: Must catch specific JSONDecodeError, log at ERROR level with helpful details, preserve failed file content, ensure other PDFs continue processing | Success: JSON errors are caught and logged, failed files moved to Manual_Review, remaining PDFs process successfully, system is resilient to API failures

- [ ] 3.1 Extend config.json schema with page filtering settings
  - File: config.json
  - Add processing_settings.enable_smart_filtering: true
  - Add processing_settings.absolute_max_pages: 30
  - Add processing_settings.page_filtering section with all weights, patterns, and options
  - Add comments explaining each configuration option
  - _Leverage: existing config.json structure from design.md
  - _Requirements: 2
  - _Prompt: Role: Configuration Management Specialist | Task: Extend config.json schema with comprehensive page filtering settings following requirement 2 and design.md specifications, including all weights, patterns, and system limits | Restrictions: Must maintain backward compatibility with existing configs, use clear section organization, include inline comments, validate numeric ranges and pattern formats | Success: config.json validates successfully, all settings are documented, default values are sensible, structure is extensible for future additions

- [ ] 3.2 Add config validation for new page filtering settings
  - File: config_manager.py
  - Add validation rules for page_filtering configuration
  - Validate: weight values are numeric, patterns are valid regex, max_selected_pages is positive
  - Provide clear error messages for invalid configurations
  - _Leverage: existing config validation patterns in config_manager.py
  - _Requirements: 1, 2
  - _Prompt: Role: Python Developer specializing in configuration validation | Task: Add configuration validation rules for new page filtering settings following requirements 1 and 2, implementing comprehensive validation with helpful error messages | Restrictions: Must integrate with existing validation functions, provide Chinese error messages where appropriate, validate all configuration options, maintain validation performance | Success: Validation catches all configuration errors, error messages guide users to fix issues, config loading fails fast with clear diagnostics, validation is efficient

- [ ] 4.1 Update pdf2image conversion calls to support page selection
  - File: processing.py
  - Modify convert_pdf_to_images() to accept selected_pages parameter
  - Update get_pages_to_process() to use get_smart_pages_to_process()
  - Ensure configuration drives behavior (enable_smart_filtering flag)
  - _Leverage: existing convert_pdf_to_images(), get_pages_to_process(), process_pdf() functions
  - _Requirements: 2
  - _Prompt: Role: Python Developer with expertise in function modification and integration | Task: Update pdf2image conversion logic to support selective page processing following requirement 2, modifying existing functions to accept page lists and configuration-driven behavior | Restrictions: Must maintain backward compatibility when filtering is disabled, ensure function signatures remain clean, preserve existing DPI and format options, test with both filtered and unfiltered modes | Success: Functions accept page selection parameters, configuration controls filtering behavior, both modes work correctly, existing tests pass

- [ ] 4.2 Modify process_pdf() to integrate smart filtering
  - File: processing.py
  - Update process_pdf() to call get_smart_pages_to_process() before image conversion
  - Pass selected pages to convert_pdf_to_images()
  - Log page selection decisions and scores to console
  - _Leverage: process_pdf() existing structure, get_smart_pages_to_process(), logging utilities
  - _Requirements: 2
  - _Prompt: Role: Python Developer with expertise in workflow orchestration | Task: Modify process_pdf() main function to integrate smart page filtering following requirement 2, orchestrating text extraction, scoring, and selective image conversion | Restrictions: Must preserve existing API structure, maintain same return format, ensure logging is clear and informative, handle both short and long papers correctly | Success: process_pdf() uses smart filtering when enabled, logs page selections, maintains return format compatibility, all processing paths tested

- [ ] 5.1 Write unit tests for page scoring algorithm
  - File: tests/test_page_scoring.py (new)
  - Test score_page_content() with various inputs: table pages, data pages, reference pages, mixed content
  - Verify scoring accuracy and performance
  - Test with both English and Chinese text
  - _Leverage: pytest framework, score_page_content() function
  - _Requirements: 2
  - _Prompt: Role: QA Engineer with expertise in unit testing | Task: Write comprehensive unit tests for page scoring algorithm following requirement 2, covering all scoring scenarios and edge cases | Restrictions: Must test in isolation without PDF dependencies, cover all pattern types, verify performance benchmarks (<1ms per page), include unicode text tests | Success: All scoring scenarios pass tests, edge cases handled correctly, performance meets requirements, tests are maintainable and well-documented

- [ ] 5.2 Write unit tests for smart page selection logic
  - File: tests/test_smart_filtering.py (new)
  - Test get_smart_pages_to_process() with mock data
  - Verify short papers bypass filtering
  - Verify top pages selected by score
  - Test edge cases: all negative scores, empty extraction, tied scores
  - _Leverage: pytest, unittest.mock, get_smart_pages_to_process()
  - _Requirements: 2
  - _Prompt: Role: QA Engineer specializing in algorithm testing | Task: Write unit tests for smart page selection logic following requirement 2, testing all decision paths and edge cases | Restrictions: Must mock pdfplumber and external dependencies, test both filtered and unfiltered modes, verify page 1 always included, test edge cases thoroughly | Success: All selection logic paths covered, edge cases handled correctly, tests demonstrate correct behavior for all scenarios, test suite runs quickly

- [ ] 5.3 Write unit tests for JSON parsing error handling
  - File: tests/test_json_parsing.py (new)
  - Test truncated JSON detection
  - Test successful parsing of valid JSON
  - Test malformed JSON error handling
  - Verify Manual_Review file movement on failure
  - _Leverage: pytest, mock responses, existing test fixtures
  - _Requirements: 1
  - _Prompt: Role: QA Engineer with expertise in error handling testing | Task: Write unit tests for JSON parsing and error handling following requirement 1, covering success and failure scenarios | Restrictions: Must mock API responses, test truncation detection accuracy, verify logging and file operations, test continuation after failure | Success: Truncated JSON detected correctly, valid JSON parsed successfully, error handling tested comprehensively, file movements and logging verified

- [ ] 6.1 Create integration test for two-phase processing workflow
  - File: tests/test_integration.py (new or add to existing)
  - Test complete workflow: PDF → text extraction → scoring → page selection → image conversion → AI processing
  - Use real PDF samples (create test fixtures if needed)
  - Verify cost savings and data accuracy
  - _Leverage: pytest, test PDFs in fixtures/, process_pdf() function
  - _Requirements: 1, 2
  - _Prompt: Role: Integration Test Engineer | Task: Create comprehensive integration test for two-phase processing workflow following requirements 1 and 2, testing complete pipeline from PDF intake to AI response | Restrictions: Must use realistic test PDFs with known content, verify page selection accuracy, measure performance impact, ensure data extraction quality is maintained | Success: Integration test validates entire workflow, demonstrates cost savings, confirms data accuracy, performance benchmarks are met

- [ ] 6.2 Create integration test for JSON constraint effectiveness
  - File: tests/test_integration.py
  - Test AI responses adhere to JSON constraints
  - Verify reason field is empty or ≤10 words in practice
  - Ensure no markdown wrapping in responses
  - Track token usage reduction
  - _Leverage: pytest, test_process_pdf.py patterns, real API calls
  - _Requirements: 1
  - _Prompt: Role: Integration Test Engineer focusing on API behavior | Task: Create integration test validating JSON constraint effectiveness following requirement 1, measuring actual AI response compliance | Restrictions: Must test with real API calls, verify multiple response samples, measure token usage before/after, ensure constraints are effective | Success: AI responses comply with constraints, reason fields are properly limited, no markdown wrapping, token usage reduced measurably

- [ ] 7.1 Update processing.py module docstring and comments
  - File: processing.py
  - Add comprehensive docstring explaining vision-based processing
  - Add inline comments for complex scoring logic
  - Document function parameters and return types
  - _Leverage: existing code, design.md documentation
  - _Requirements: 1, 2
  - _Prompt: Role: Technical Writer with Python expertise | Task: Update processing.py documentation following requirements 1 and 2, adding comprehensive docstrings and inline comments explaining vision-based processing and scoring logic | Restrictions: Must follow existing documentation style, explain complex algorithms clearly, maintain documentation consistency, use Google or Sphinx docstring format | Success: Docstrings are complete and informative, inline comments explain non-obvious logic, parameters and return types are documented, documentation enhances code maintainability

- [ ] 7.2 Update main.py inline documentation
  - File: main.py
  - Add comments explaining JSON constraint additions to SYSTEM_PROMPT
  - Document error handling logic for JSON parsing failures
  - Update function docstrings for modified behavior
  - _Leverage: existing code structure, full SYSTEM_PROMPT from design.md
  - _Requirements: 1
  - _Prompt: Role: Technical Writer specializing in inline documentation | Task: Update main.py inline documentation following requirement 1, explaining JSON constraints and error handling additions | Restrictions: Must not clutter code with excessive comments, focus on non-obvious logic, maintain consistency with existing style, explain error handling patterns clearly | Success: Comments explain constraint rationale, error handling logic is documented, code is maintainable and self-documenting where appropriate

- [ ] 7.3 Update README.md with new architecture description
  - File: README.md
  - Document two-phase processing approach (text scouting + vision extraction)
  - Explain smart page filtering benefits
  - Add configuration examples for page filtering
  - Document JSON constraint improvements
  - _Leverage: existing README.md structure, design.md descriptions
  - _Requirements: 1, 2
  - _Prompt: Role: Technical Documentation Specialist | Task: Update README.md following requirements 1 and 2, documenting new two-phase architecture and smart page filtering with examples | Restrictions: Must maintain existing README organization, write for user audience (not developers), include clear examples, update any outdated architecture descriptions | Success: README accurately reflects new architecture, configuration examples are helpful, benefits of improvements are explained, users can understand and use new features

- [ ] 8.1 Run full test suite and verify all tests pass
  - Execute: pytest tests/
  - Verify all unit tests pass
  - Verify integration tests pass
  - Check test coverage >80%
  - _Leverage: pytest, coverage.py, existing test suite
  - _Requirements: all
  - _Prompt: Role: QA Lead with expertise in test execution and coverage analysis | Task: Run complete test suite and verify all tests pass following all requirements, ensuring comprehensive coverage | Restrictions: Must achieve >80% code coverage, all tests must pass, no flaky tests, performance benchmarks must be met, ensure tests run in isolation | Success: All tests pass reliably, coverage exceeds 80%, performance requirements are verified, test suite is maintainable and documented

- [ ] 8.2 Perform manual testing with real PDF samples
  - Test with minimum 5 real CFST papers
  - Include mix of short (≤10 pages) and long (>10 pages) papers
  - Verify data extraction accuracy is maintained or improved
  - Confirm cost savings (fewer pages processed for long papers)
  - Validate JSON constraints are effective
  - Document any edge cases or issues found
  - _Leverage: files/ directory with real PDFs, main.py process_pdf()
  - _Requirements: all
  - _Prompt: Role: QA Engineer with domain expertise in CFST research papers | Task: Perform manual testing with real CFST PDF samples following all requirements, validating accuracy and cost improvements | Restrictions: Must use real research papers, test diverse paper structures and lengths, verify extraction quality manually, document all findings, ensure system is production-ready | Success: All test papers process successfully, data extraction accuracy is verified, cost savings are demonstrated, edge cases are identified and handled, system is ready for production use
