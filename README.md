# CFST Data Extractor - AI-Powered Academic Literature Processor

An intelligent Python application that automatically extracts experimental test data from Concrete-Filled Steel Tube (CFST) research papers using Computer Vision + Large Language Models (LLM). The system uses a two-phase intelligent processing pipeline that combines text-based page filtering with vision-based AI analysis for optimal performance and cost efficiency.

## 🌟 Key Features

### 🤖 Vision-Based AI Processing (NEW - v4.1)
- **Two-Phase Processing**: Text scouting (pdfplumber) + Vision extraction (pdf2image + Gemini 3 Flash)
- **Smart Page Filtering**: Automatically identifies data-rich pages to reduce API costs by 30-50%
- **Intelligent Scoring**: Keyword-based scoring (Table titles +10, Data keywords +5, References -5)
- **JSON Constraint Enforcement**: Prevents token overflow with reason field limits (max 10 words)

### 📄 PDF Processing Capabilities
- **Adaptive Scanning**: Short papers (≤10 pages) fully scanned; long papers intelligently filtered
- **Multi-Format Support**: Handles scanned PDFs, text-based PDFs, and mixed content
- **Error Recovery**: Graceful fallback to simple truncation if smart filtering fails
- **Truncation Detection**: Detects and handles incomplete JSON responses

### 📊 Advanced Data Processing
- **Multi-Shape Classification**: Categorizes specimens into Group A (Rectangular/Square), Group B (Circular), and Group C (Round-ended/Elliptical)
- **Physics-Based Validation**: Implements theoretical bearing capacity formulas to validate extracted data
- **Smart Text Processing**: Optimizes text segmentation to prioritize data-rich sections
- **Manual Review Workflow**: Automatically moves problematic files for manual inspection

### 📈 Professional Output Generation
- **Excel Reports with Styling**: Generates formatted Excel files with multiple sheets and professional styling
- **Validation Reports**: Creates separate validation reports with pass/fail indicators
- **Column Reordering**: Automatically reorders columns for optimal presentation

### 🔄 Automation Workflow 4.1
- **Automated File Management**: Auto-imports PDFs from Windows folders to WSL2
- **Batch Processing**: Handles multiple PDF files in a single run with progress tracking
- **Auto-Archiving**: Automatically archives processed results to designated folders
- **Persistent State Tracking**: Maintains batch history and auto-increments batch numbers
- **Comprehensive Error Handling**: Intelligently categorizes and moves failed files (NotInput/Excluded/Manual_Review)

## 🏗️ Architecture Overview (Updated v4.1)

### Two-Phase Intelligent Processing

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   PDF Files     │───▶│ Phase 1: Text    │───▶│ Phase 2: Vision │
│  (files/ dir)   │    │ Scouting (CPU)   │    │ Extraction (API)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                                         │
         │     [extract_page_texts()]              │
         │        - 100 page PDF: <200ms          │
         │        - Keyword scoring               │
         │        - Page selection                │
         ▼                                         ▼
┌─────────────────┐                         ┌─────────────────┐
│ Smart Page      │                         │     AI Model    │
│ Selection       │                         │ (Gemini 3 Flash)│
│ - Score pages   │                         └─────────────────┘
│ - Filter refs   │                                  │
│ - Pick Top N    │                                  │
└─────────────────┘                                  ▼
         │                                  ┌─────────────────┐
         │                                  │  JSON Parsing   │
         │                                  │ + Truncation    │
         ▼                                  │ Detection       │
┌─────────────────┐                        └─────────────────┘
│ Vision API Call │                                  │
│ (Selected pages)│                                  ▼
└─────────────────┐                        ┌─────────────────┐
         ▼                                  │   Validation    │
┌─────────────────┐                        │  (Physics)      │
│  Data Models    │                        └─────────────────┘
│  (Pydantic)     │                                  │
└─────────────────┘                                  ▼
         │                                  ┌─────────────────┐
         └──────────────────────┬──────────▶│  Excel Output   │
                                  │          │ (Styled Sheets) │
                                  │          └─────────────────┘
                                  │                  │
                                  │                  ▼
┌─────────────────┐     ┌────────┴─────────┐┌───────────────┐
│   Auto-Import   │     │ Manual Review    ││ Archive &     │
│ (Windows Path)  │     │ (Problem files)  ││ State Update  │
└─────────────────┘     └──────────────────┘└───────────────┘
```

### System Limits & Configuration
```json
{
  "short_paper_threshold": 10,      // Scan all pages if ≤ 10 pages
  "max_scan_limit": 10,             // Fallback scan limit if extraction fails
  "absolute_max_pages": 30,         // System hard limit for processing
  "enable_smart_filtering": true,   // Enable/disable intelligent filtering
  "page_filtering": {
    "max_selected_pages": 8,        // Pages to select after filtering
    "mandatory_include_first_page": true,  // Always include page 1
    "weights": {"table_weight": 10, "data_weight": 5, "reference_weight": -5}
  }
}
```

## 📁 Project Structure (Updated v4.1)

```
CFST-Data-Extractor/
├── main.py                      # Main workflow orchestration
├── models.py                    # Pydantic data models
├── validation.py                # Physics-based validation
├── styling.py                   # Excel export and styling
├── processing.py                # Vision processing + smart filtering
├── config.json                  # Configuration with smart filtering settings
├── config_manager.py            # Configuration validation
├── state.json                   # Batch state tracking
├── files/                       # Input PDF directory
├── NotInput/                    # Failed/unreadable files
├── Excluded/                    # Invalid/irrelevant files
├── Manual_Review/               # Files requiring manual inspection (NEW)
├── tests/                       # Unit and integration tests (NEW)
│   ├── test_page_scoring.py
│   ├── test_smart_filtering.py
│   └── test_json_parsing.py
├── requirements.txt             # Dependencies
└── README.md                    # This documentation
```


### Automation Configuration (config.json)
```json
{
  "windows_source_path": "/mnt/e/Documents/data_unextracted",
  "archive_destination": "/mnt/e/Documents/data_extracted",
  "auto_cleanup": true,
  "auto_increment": true,
  "delete_existing_before_import": true,
  "cleanup_after_archive": true
}
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- WSL2 (Windows Subsystem for Linux) for Windows users
- Internet connection for API calls

### Installation Steps

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd CFST-Data-Extractor
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   Key dependencies:
   - `openai` - For LLM API integration
   - `instructor` - For structured LLM outputs
   - `pydantic` - For data validation and serialization
   - `pdfplumber` - For PDF text extraction
   - `pandas` - For data manipulation
   - `openpyxl` - For Excel file generation

3. **Configure API Access**
   - Obtain an API key from your LLM provider
   - Update the `API_KEY` variable in `main.py`
   - Ensure the `BASE_URL` points to your API endpoint

4. **Set Up File Paths**
   - Configure source and destination paths in `config.json`
   - Ensure the Windows paths are correctly mapped in WSL2

### Running the Application

#### Command Line Mode (Workflow 4.0)
```bash
python main.py
```

The application will:
1. Automatically import PDFs from the configured Windows folder
2. Process each PDF through the AI extraction pipeline
3. Validate extracted data using physics formulas
4. Generate Excel reports with styling
5. Archive results and update state tracking

## 📊 Data Model Specifications

### SpecimenData Model
Each extracted specimen contains 16 standardized fields:

| Field | Description | Unit |
|-------|-------------|------|
| ref_no | Reference number (filename) | - |
| fc_value | Concrete compressive strength | MPa |
| fc_type | Concrete type specification | - |
| specimen_label | Unique specimen identifier | - |
| fy | Steel yield strength | MPa |
| r_ratio | Recycled aggregate ratio | % |
| b | Width/Diameter/Major axis | mm |
| h | Depth/Minor axis | mm |
| t | Steel tube thickness | mm |
| r0 | External corner radius | mm |
| L | Specimen length | mm |
| e1 | Eccentricity 1 | mm |
| e2 | Eccentricity 2 | mm |
| n_exp | Experimental bearing capacity | kN |
| source_evidence | Extracted text evidence | - |

### Validation Rules
- **Group Classification**: Based on cross-sectional shape
- **Physics Validation**: Theoretical bearing capacity calculation
- **Data Consistency**: Dimensional and material property checks

## 🎯 Use Cases

1. **Academic Research**: Extract test data from multiple papers for meta-analysis
2. **Database Building**: Create comprehensive CFST test databases
3. **Quality Control**: Validate published experimental data
4. **Literature Review**: Systematic data extraction from research papers

## 🔍 Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Check internet connectivity
   - Verify API key is valid and not expired
   - Ensure BASE_URL is correct

2. **PDF Processing Errors**
   - Ensure PDFs are text-based (not scanned images)
   - Check PDF permissions and encryption
   - Verify files are not corrupted

3. **Excel Generation Issues**
   - Ensure write permissions in output directory
   - Check if Excel file is already open
   - Verify pandas and openpyxl versions are compatible

4. **Automation Workflow Problems**
   - Verify Windows path mappings in WSL2
   - Check directory permissions
   - Ensure state.json is writable

### Performance Optimization

- **Batch Size**: Process 10-20 PDFs per batch for optimal performance
- **API Rate Limiting**: Implement delays between API calls if needed
- **Memory Management**: Monitor memory usage for large PDFs

## 🔒 Security Considerations

- API keys are stored in plain text in the current version
- Consider implementing secure key storage for production use
- Ensure sensitive data in PDFs is handled appropriately

## 🔄 Version History

- **Workflow 4.0 (Current)**: Full automation with file management
- **Workflow 3.0**: GUI application with Windows executable
- **Workflow 2.0**: Physics validation and Excel styling
- **Workflow 1.0**: Basic PDF extraction

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- DeepSeek AI for providing the LLM capabilities
- The CFST research community for the academic literature
- Open-source libraries that made this project possible

---

**Note**: This tool is designed for academic research purposes. Always verify extracted data against original sources before use in critical applications.