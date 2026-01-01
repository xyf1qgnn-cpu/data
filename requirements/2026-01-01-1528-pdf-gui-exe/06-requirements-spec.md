# Requirements Specification

**Project**: CFST Data Extractor GUI Application
**Version**: 1.0
**Date**: 2026-01-01
**Status**: Approved
**python 路径**:~/miniconda3


## 1. Executive Summary

### Problem Statement
The existing CFST (Concrete-Filled Steel Tube) data extraction workflow is a command-line Python script that requires technical expertise to use. Users need a user-friendly Windows application with GUI interface for batch PDF processing, real-time progress tracking, and secure API key management.

### Solution Overview
Package the existing Python workflow into a standalone Windows .exe application with PySide6 GUI. The application will provide file selection, progress monitoring, dual output areas (logs/errors), and secure API key storage while preserving all existing functionality.

## 2. Functional Requirements

### FR-01: GUI Interface
- **ID**: FR-01
- **Description**: Graphical user interface with modern Windows appearance
- **Acceptance Criteria**:
  - Application launches to main window (not console)
  - Clean, professional layout with intuitive controls
  - Responsive design that scales appropriately
  - Consistent styling and color scheme

### FR-02: File Selection
- **ID**: FR-02
- **Description**: Directory selection for batch PDF processing
- **Acceptance Criteria**:
  - "Select Directory" button opens native Windows file dialog
  - Selected path displayed in readable format
  - Validation for PDF file existence in directory
  - Support for custom directory locations (default: preserve existing structure)

### FR-03: Progress Display
- **ID**: FR-03
- **Description**: Comprehensive progress tracking during batch processing
- **Acceptance Criteria**:
  - Overall progress bar showing files processed/total
  - Detailed per-file status in log area with timestamps
  - Time estimates when possible
  - Real-time updates without UI freezing

### FR-04: Dual Output Areas
- **ID**: FR-04
- **Description**: Separate display areas for logs and errors
- **Acceptance Criteria**:
  - **Log Area**: Real-time processing information, success messages, warnings
  - **Error Area**: Failed files, API errors, validation issues
  - Distinct visual styling (colors, backgrounds)
  - Auto-scroll to latest entries
  - Copy/paste support for text

### FR-05: API Key Management
- **ID**: FR-05
- **Description**: Secure input and storage of DeepSeek API key
- **Acceptance Criteria**:
  - Password-style input field with show/hide toggle
  - Secure encrypted storage using Windows Credential Manager
  - Key persists between application sessions
  - Validation for key format/connectivity
  - Clear visual indication when key is saved/loaded

### FR-06: Batch Processing
- **ID**: FR-06
- **Description**: Process all PDF files in selected directory
- **Acceptance Criteria**:
  - Process PDFs sequentially (avoid API rate limits)
  - Preserve existing workflow: extraction → validation → Excel export
  - Handle failed files (move to NotInput/)
  - Handle excluded files (move to Excluded/)
  - Support cancellation mid-process

### FR-07: Error Handling & Retry
- **ID**: FR-07
- **Description**: Robust error handling with automatic retry
- **Acceptance Criteria**:
  - Basic retry logic for API calls (3 attempts with exponential backoff)
  - Clear error messages in error area
  - Graceful handling of network issues
  - File-level error isolation (continue processing other files)

### FR-08: Settings Persistence
- **ID**: FR-08
- **Description**: Save and restore application settings
- **Acceptance Criteria**:
  - Remember last used directory
  - Save window size/position
  - Persist API key (encrypted)
  - Store custom directory preferences
  - Settings survive application updates

## 3. Technical Requirements

### TR-01: Technology Stack
- **ID**: TR-01
- **Description**: Python-based application with specific frameworks
- **Requirements**:
  - **GUI Framework**: PySide6 (Qt for Python)
  - **Packaging Tool**: PyInstaller
  - **Key Storage**: keyring + cryptography libraries
  - **Threading**: QThread with signal/slot architecture
  - **Dependencies**: Preserve existing (pdfplumber, pandas, openai, instructor, pydantic, numpy)

### TR-02: Packaging & Distribution
- **ID**: TR-02
- **Description**: Standalone Windows .exe with all dependencies
- **Requirements**:
  - Single-file executable (or executable + support files)
  - Application icon and version metadata
  - No Python installation required on target systems
  - Handle dependency inclusion (especially pdfplumber data files)
  - Test on clean Windows installations

### TR-03: Performance Requirements
- **ID**: TR-03
- **Description**: Responsive GUI during long-running operations
- **Requirements**:
  - UI remains responsive during PDF processing
  - Progress updates at reasonable intervals (not per-character)
  - Memory-efficient processing (one PDF at a time)
  - Startup time < 5 seconds on typical hardware
  - Handle 50+ PDF files in batch without degradation

### TR-04: Security Requirements
- **ID**: TR-04
- **Description**: Secure handling of sensitive data
- **Requirements**:
  - API key encrypted before storage
  - Use Windows Credential Manager where available
  - No hardcoded credentials in executable
  - Secure deletion of temporary files
  - No sensitive data in log files

### TR-05: Compatibility Requirements
- **ID**: TR-05
- **Description**: Target platform and backward compatibility
- **Requirements**:
  - **Target OS**: Windows 10/11 (64-bit)
  - **Python Version**: 3.8+ compatibility
  - **Backward Compatibility**: Preserve existing directory structure and file formats
  - **Output Format**: Excel with existing styling and validation highlighting

## 4. Implementation Hints

### File Structure
```
CFST_Data_Extractor/
├── main_gui.py              # Main GUI application
├── core_processor.py        # Adapted processing logic
├── secure_storage.py        # API key management
├── requirements.txt         # Python dependencies
├── app.ico                  # Application icon
├── config.ini               # Application settings
└── spec/                    # PyInstaller configuration
    └── cfst_extractor.spec
```

### Key Integration Points
1. **main.py Adaptation**: Convert `main()` function to work with GUI signals
2. **Thread Wrapper**: Create `ProcessingThread(QThread)` class
3. **Signal Definitions**: Progress, log, error, completion signals
4. **Configuration Layer**: Settings management with encryption

### PyInstaller Configuration
```bash
pyinstaller --name="CFST Data Extractor" \
            --windowed \
            --icon=app.ico \
            --add-data="config.ini;." \
            --hidden-import=instructor \
            --hidden-import=pydantic \
            --collect-all=pdfplumber \
            --add-binary="lib/*;lib" \
            main_gui.py
```

### Threading Pattern
```python
class ProcessingThread(QThread):
    progress = Signal(int, int)  # current, total
    log_message = Signal(str)    # info messages
    error_message = Signal(str)  # error messages
    file_complete = Signal(str, bool)  # filename, success
    finished = Signal(dict)      # final results

    def run(self):
        # Adapted from existing main.py logic
        # Emit signals for UI updates
```

## 5. Acceptance Criteria

### AC-01: Installation
- [ ] .exe file runs on clean Windows 10/11 installation
- [ ] No Python or additional software installation required
- [ ] Application icon appears correctly
- [ ] Version information accessible via Properties

### AC-02: Basic Functionality
- [ ] GUI launches without console window
- [ ] File selection dialog works correctly
- [ ] API key input accepts and saves credentials
- [ ] Settings persist between application sessions

### AC-03: Processing Workflow
- [ ] Batch processes all PDFs in selected directory
- [ ] Progress bar updates in real-time
- [ ] Log area shows detailed processing information
- [ ] Error area displays failed/excluded files
- [ ] Excel output matches command-line version exactly

### AC-04: Error Handling
- [ ] API failures trigger automatic retry (3 attempts)
- [ ] Network issues handled gracefully
- [ ] Invalid PDF files moved to NotInput/
- [ ] Excluded files moved to Excluded/
- [ ] UI remains responsive during errors

### AC-05: Performance
- [ ] UI updates without freezing during processing
- [ ] Memory usage stays within reasonable limits
- [ ] Processing speed comparable to command-line version
- [ ] Handles 50+ PDF batch without issues

### AC-06: Security
- [ ] API key encrypted in storage
- [ ] No credentials in log files or error messages
- [ ] Temporary files securely deleted
- [ ] Windows Credential Manager used if available

## 6. Assumptions & Constraints

### Assumptions
1. Users have valid DeepSeek API keys with sufficient credits
2. PDF files contain CFST experimental data in supported formats
3. Windows 10/11 64-bit is the target platform
4. Internet connectivity required for API calls
5. Users understand basic file operations (directory selection)

### Constraints
1. **Platform**: Windows-only (.exe format specified)
2. **Export Format**: Excel only (preserve existing styling)
3. **Preview Mode**: Not included in initial version
4. **Additional Formats**: No CSV/JSON export in v1.0
5. **Advanced Features**: No machine learning enhancements

### Dependencies
- **External**: DeepSeek API service availability
- **Internal**: Existing Python workflow must remain functional
- **Technical**: PyInstaller compatibility with all dependencies
- **Legal**: Compliance with Qt (PySide6) LGPL licensing

## 7. Success Metrics

### Quantitative
- **Manual Review Reduction**: Maintain 70% reduction target from existing workflow
- **Processing Speed**: Comparable to command-line version (±10%)
- **Error Rate**: < 5% of files require manual intervention
- **Memory Usage**: < 500MB for typical batch processing
- **Startup Time**: < 5 seconds on target hardware

### Qualitative
- **Usability**: Non-technical users can operate application
- **Reliability**: Consistent results across multiple runs
- **Professionalism**: Application appears polished and trustworthy
- **Documentation**: Clear instructions for API key setup and usage
- **Support**: Error messages help users resolve common issues

## 8. Future Enhancements (Post v1.0)

### Phase 2 Features
1. **Preview Mode**: Extract text without API calls for testing
2. **Additional Export Formats**: CSV, JSON options
3. **Advanced Settings**: Model selection, temperature control
4. **Batch Resume**: Continue interrupted processing
5. **Report Generation**: Summary statistics and charts

### Phase 3 Features
1. **Multi-language Support**: Chinese/English interface
2. **Cloud Integration**: Save results to cloud storage
3. **Template System**: Custom extraction templates
4. **API Monitoring**: Usage statistics and cost tracking
5. **Plugin Architecture**: Extensible processing pipelines

## 9. Risk Assessment

### High Risk
- **Dependency Packaging**: pdfplumber and pandas may have issues in PyInstaller
- **Threading Deadlocks**: Improper signal/slot usage could freeze UI
- **API Key Security**: Encryption implementation vulnerabilities

### Medium Risk
- **Performance Degradation**: GUI overhead reduces processing speed
- **Anti-Virus False Positives**: Packaged .exe flagged as suspicious
- **Windows Compatibility**: DLL issues on some systems

### Low Risk
- **Feature Scope**: Well-defined requirements reduce scope creep
- **Code Quality**: Existing workflow is tested and stable
- **User Acceptance**: GUI addresses known usability issues

### Mitigation Strategies
1. **Early Packaging Tests**: Verify PyInstaller configuration before full development
2. **Threading Code Review**: Peer review of QThread implementation
3. **Security Audit**: Review encryption and storage implementation
4. **Beta Testing**: Test on multiple Windows configurations
5. **Rollback Plan**: Maintain command-line version as backup

## 10. Implementation Timeline

### Phase 1: Foundation (Week 1-2)
- GUI framework setup and basic window
- File selection and API key input
- Settings persistence system

### Phase 2: Integration (Week 3-4)
- Adapt existing processing logic for threading
- Implement progress reporting via signals
- Add error handling and retry logic

### Phase 3: Packaging (Week 5)
- PyInstaller configuration and testing
- Dependency inclusion verification
- Clean Windows VM testing

### Phase 4: Polish (Week 6)
- Application icon and metadata
- User documentation
- Final testing and bug fixes

### Phase 5: Deployment (Week 7)
- Create installer package (optional)
- User acceptance testing
- Production release

---

**Approval Signatures**:

- **Product Owner**: ________________________ Date: _________
- **Technical Lead**: ________________________ Date: _________
- **Quality Assurance**: _____________________ Date: _________