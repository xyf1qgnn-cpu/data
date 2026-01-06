# CFST Data Extractor - AI-Powered Academic Literature Processor

An intelligent Python application that automatically extracts experimental test data from Concrete-Filled Steel Tube (CFST) research papers using Large Language Models (LLM). The system processes PDF documents, validates extracted data using physics-based formulas, and generates professional Excel reports with data categorization.

## 🌟 Key Features

### 🤖 AI-Powered Data Extraction
- **Intelligent PDF Parsing**: Automatically extracts structured test data from academic PDFs
- **LLM Integration**: Uses DeepSeek AI model via OpenAI-compatible API for intelligent text analysis
- **Structured Output**: Employs Pydantic models for consistent data extraction

### 📊 Advanced Data Processing
- **Multi-Shape Classification**: Categorizes specimens into Group A (Rectangular/Square), Group B (Circular), and Group C (Round-ended/Elliptical)
- **Physics-Based Validation**: Implements theoretical bearing capacity formulas to validate extracted data
- **Smart Text Processing**: Optimizes text segmentation to prioritize data-rich sections

### 📈 Professional Output Generation
- **Excel Reports with Styling**: Generates formatted Excel files with multiple sheets and professional styling
- **Validation Reports**: Creates separate validation reports with pass/fail indicators
- **Column Reordering**: Automatically reorders columns for optimal presentation

### 🔄 Automation Workflow 4.0
- **Automated File Management**: Auto-imports PDFs from Windows folders to WSL2
- **Batch Processing**: Handles multiple PDF files in a single run
- **Auto-Archiving**: Automatically archives processed results to designated folders
- **Persistent State Tracking**: Maintains batch history and auto-increments batch numbers
- **Error Handling**: Intelligently moves failed/invalid files to appropriate directories

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   PDF Files     │───▶│  AI Extraction   │───▶│   Validation    │
│  (files/ dir)   │    │  (LLM Pipeline)  │    │  (Physics Form.)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Auto-Import    │    │  Data Models     │    │  Excel Output   │
│ (Windows Path)  │    │  (Pydantic)      │    │ (Styled Sheets) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
CFST-Data-Extractor/
├── main.py                 # Main application entry point (Workflow 4.0)
├── models.py              # Pydantic data models for structured extraction
├── validation.py          # Physics-based validation formulas
├── styling.py             # Excel styling and export functionality
├── processing.py          # Intelligent text preprocessing
├── config.json            # Automation workflow configuration
├── state.json             # Batch state tracking and history
├── files/                 # Input directory for PDF files
├── NotInput/              # Directory for failed/unreadable files
├── Excluded/              # Directory for invalid/irrelevant files
├── CFST_Extracted_Data.xlsx    # Generated Excel output
└── README.md              # This documentation
```

## 🔧 Configuration

### API Configuration
The system uses DeepSeek AI model via OpenAI-compatible API:
```python
API_KEY = "your-api-key-here"  # Replace with your actual API key
BASE_URL = "https://api.silra.cn/v1"
MODEL_NAME = "deepseek-chat"
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