# Context Findings

**Phase**: Context Gathering
**Date**: 2026-01-01 15:28
**Status**: Complete

## 1. Existing Workflow Analysis

### Core Files Identified:
1. **`/home/thelya/Work/test01/data/main.py`** - Main entry point
2. **`/home/thelya/Work/test01/data/processing.py`** - Intelligent text segmentation
3. **`/home/thelya/Work/test01/data/models.py`** - Pydantic data models
4. **`/home/thelya/Work/test01/data/validation.py`** - Physical validation formulas
5. **`/home/thelya/Work/test01/data/styling.py`** - Excel styling functions

### Workflow Summary:
1. **PDF Reading**: Uses `pdfplumber` to extract text from PDFs in `files/` directory
2. **Text Optimization**: Intelligent segmentation to focus on data-rich sections
3. **AI Extraction**: Calls DeepSeek API with structured prompt for CFST data extraction
4. **Validation**: Applies physical formulas to validate extracted data
5. **Export**: Creates styled Excel file with highlighting for manual review
6. **File Management**: Moves failed files to `NotInput/`, excluded files to `Excluded/`

### Key Dependencies:
- `pdfplumber` - PDF text extraction
- `pandas` - Data manipulation and Excel export
- `openai` - DeepSeek API client (configured for `https://api.deepseek.com`)
- `instructor` - Structured output from LLMs
- `pydantic` - Data validation and models
- `numpy` - Numerical calculations

## 2. Current API Integration

### Hardcoded Configuration (main.py:26-28):
```python
API_KEY = "sk-3a5200989e7d4575a30f9ef910afd0eb"  # Needs to be moved to GUI
BASE_URL = "https://api.deepseek.com"
MODEL_NAME = "deepseek-chat"
```

### System Prompt:
- Extensive 148-line prompt for CFST data extraction
- Includes validity checks, classification rules, and extraction definitions
- Requires preservation in GUI version

## 3. GUI Framework Research Findings

### Recommended Stack:
1. **GUI Framework**: **PySide6** (Qt for Python)
   - Professional Windows-native appearance
   - Excellent threading support via QThread
   - Rich widget set (file dialogs, progress bars, text areas)
   - LGPL licensed, free for commercial use

2. **Packaging Tool**: **PyInstaller**
   - Creates standalone Windows .exe
   - Good dependency detection
   - Supports adding icons and version info
   - Active development and community support

### Alternative Considered: Tkinter
- **Pros**: Built into Python, lightweight
- **Cons**: Limited modern widgets, weaker threading support
- **Decision**: Not recommended for professional application

## 4. Technical Implementation Details

### Threading Architecture:
```python
# Recommended pattern for background processing
class ProcessingThread(QThread):
    progress = Signal(int)  # Progress updates
    log_message = Signal(str)  # Real-time logs
    error_message = Signal(str)  # Error information
    finished = Signal(bool)  # Completion signal

    def run(self):
        # Wrap existing main.py logic here
        # Emit signals for UI updates
```

### GUI Components Required:
1. **File Selection**: QFileDialog for directory selection
2. **Progress Bar**: QProgressBar (determinate/indeterminate modes)
3. **Text Areas**: Two QTextEdit widgets (logs + errors)
4. **API Key Input**: QLineEdit with password masking
5. **Control Buttons**: Start, Stop, Settings

### Secure API Key Storage:
**Recommended**: `keyring` + `cryptography` libraries
- Uses Windows Credential Manager
- Encrypts API key before storage
- Survives application updates

## 5. Packaging Considerations

### PyInstaller Configuration:
```bash
pyinstaller --name="CFST Data Extractor" \
            --windowed \
            --icon=app.ico \
            --add-data="config.ini;." \
            --hidden-import=instructor \
            --hidden-import=pydantic \
            --collect-all=pdfplumber \
            main_gui.py
```

### Dependency-Specific Notes:
1. **pdfplumber**: Requires `--collect-all` for data files
2. **pandas/numpy**: Large libraries, consider compression
3. **OpenAI/instructor**: May need `--hidden-import`
4. **PySide6**: Use `--windowed` flag for GUI apps

### File Path Handling in Packaged App:
```python
# Use sys._MEIPASS for bundled files
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
```

## 6. Integration Points

### Existing Code to Preserve:
1. **PDF Processing Logic** (`extract_text_from_pdf()`)
2. **AI Extraction Logic** (`extract_data_with_ai()`)
3. **Validation Formulas** (`validate_dataframe()`)
4. **Excel Export** (`export_to_excel_with_styling()`)
5. **File Management** (`move_failed_file()`, `move_excluded_file()`)

### Code to Modify:
1. **API Key Handling**: Remove hardcoded key, add GUI input
2. **Progress Reporting**: Replace `print()` with signal emissions
3. **Error Handling**: Route errors to GUI error area
4. **Configuration**: Move constants to GUI-configurable settings

## 7. Performance Considerations

### Batch Processing:
- Process PDFs sequentially to avoid API rate limits
- Show progress per file and overall
- Allow cancellation mid-process

### Memory Management:
- Process one PDF at a time
- Clear extracted text after processing
- Monitor memory usage for large PDFs

### User Experience:
- Show estimated time remaining
- Provide clear error messages
- Allow retry for failed files
- Save intermediate progress

## 8. Testing Requirements

### Pre-Packaging Tests:
1. GUI functionality on development machine
2. Threading and signal/slot connections
3. API key storage and retrieval
4. File operations with various PDFs

### Post-Packaging Tests:
1. Clean Windows VM installation
2. Dependency inclusion verification
3. Performance comparison with script version
4. Error handling in packaged environment

## 9. Risk Assessment

### High Risk Areas:
1. **Dependency Packaging**: pdfplumber and pandas may have issues
2. **Threading Deadlocks**: Improper signal/slot usage
3. **API Key Security**: Encryption implementation
4. **File Path Resolution**: Differences between dev and packaged

### Mitigation Strategies:
1. Test PyInstaller configuration early
2. Use Qt's thread-safe signal mechanism
3. Implement secure key storage with fallback
4. Use `sys._MEIPASS` for resource access

## 10. Next Steps

### Phase 1: GUI Development
1. Create PySide6 main window structure
2. Implement basic widgets and layouts
3. Add file selection and API key input

### Phase 2: Integration
1. Adapt existing processing logic for threading
2. Implement signal-based progress reporting
3. Add secure API key storage

### Phase 3: Packaging
1. Create PyInstaller spec file
2. Test dependency inclusion
3. Build and test .exe on clean system

### Phase 4: Polish
1. Add application icon and metadata
2. Implement settings persistence
3. Create user documentation