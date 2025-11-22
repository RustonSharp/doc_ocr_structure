# OCR and Text Structuring Integrated Tool

## Features

- ✅ Support for single images (JPG/PNG) and PDF files
- ✅ Multiple OCR engine support (pytesseract, Google Cloud Vision)
- ✅ Automatic image preprocessing (skew correction, denoising, watermark suppression)
- ✅ NLP entity recognition (dates, amounts, phone numbers, etc.)
- ✅ LLM intelligent structured extraction
- ✅ Field confidence assessment (0-100)
- ✅ Validation list generation for fields requiring review
- ✅ Visual interface for field correction
- ✅ Batch processing support

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install spaCy Chinese Model (Optional, for NLP entity recognition)

```bash
python -m spacy download zh_core_web_sm
```

If the Chinese model is not installed, the system will automatically use regular expressions for entity recognition.

### 3. Configure Environment Variables

Create a `.env` file and configure:

```env
# OpenAI API (if using OpenAI)
OPENAI_API_KEY=your_openai_api_key

# Google Gemini API (if using Google)
GEMINI_API_KEY=your_gemini_api_key
```

### 4. Start Backend Service

```bash
python main.py
```

The service will start at `http://localhost:8000`.

### 5. Access Frontend Interface

There are two ways:

#### Method 1: Using HTTP Server (Recommended)

```bash
# Run in the project root directory
cd frontend
python -m http.server 8080
```

Then visit: `http://localhost:8080`

#### Method 2: Open HTML File Directly

Open `frontend/index.html` directly, but ensure:
- Backend service is running
- Browser allows cross-origin requests (may need configuration)

**Note**: If opening the HTML file directly (file:// protocol), you may encounter CORS errors. Method 1 is recommended.

## API Endpoints

### Quick Reference

- **Health Check**: `GET /health`
- **OCR Processing**: `POST /ocr`
- **Batch Processing**: `POST /batch`
- **Regenerate Output**: `POST /regenerate`

### API Documentation

After starting the service, visit the following addresses to view complete documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

Detailed API documentation: [docs/API.md](docs/API.md)

## Output Files

After processing, if `save_files=true` is set, the following files will be generated in the `output/` directory:

- `{filename}_ocr_raw_text.txt` - OCR raw text
- `{filename}_validation_list.csv` - Validation list for fields requiring review
- `{filename}_structured.json` - Structured JSON result

## Configuration Files

Detailed configuration documentation: [docs/CONFIGURATION.md](docs/CONFIGURATION.md)

### Quick Reference

- **OCR Configuration**: `configs/ocr.json` - OCR engine configuration
- **LLM Configuration**: `configs/llms/init.json` - LLM service configuration
- **NLP Configuration**: `configs/nlp.json` - NLP processing configuration
- **Structure Configuration**: `configs/structures/origin/` - Field extraction rules

## Common Issues

### 1. "Failed to fetch" Error

**Causes**:
- Backend service not started
- Frontend opened with file:// protocol (CORS restrictions)
- Network connection issues

**Solutions**:
1. Ensure backend service is started: `python main.py`
2. Use HTTP server to access frontend: `python -m http.server 8080`
3. Check browser console for detailed error messages

### 2. PDF Processing Failure

**Causes**:
- PDF processing libraries not installed

**Solutions**:
```bash
pip install pdf2image PyMuPDF
# Windows also requires poppler installation
# Download: https://github.com/oschwartz10612/poppler-windows/releases
```

### 3. spaCy Model Not Found

**Causes**:
- Chinese model not downloaded

**Solutions**:
```bash
python -m spacy download zh_core_web_sm
```

Or the system will automatically use regular expressions for entity recognition.

### 4. Google Cloud Vision Authentication Failure

**Causes**:
- Incorrect credential file path
- Invalid credential file

**Solutions**:
1. Check `credentials_path` in `configs/ocr.json`
2. Ensure `credentials/google_vision.json` file exists and is valid

## Project Structure

```
doc_ocr/
├── main.py                 # FastAPI main service
├── ocr.py                  # OCR engine management
├── structure.py            # Structured processing
├── llm.py                  # LLM service
├── pdf_processor.py        # PDF processing
├── nlp_entity.py           # NLP entity recognition
├── output_generator.py     # Output file generation
├── schemas.py              # Pydantic Schema
├── pre_preocess.py         # Image preprocessing
├── configs/                # Configuration directory
│   ├── ocr.json
│   ├── nlp.json
│   └── llms/
├── frontend/               # Frontend files
│   ├── index.html
│   ├── app.js
│   └── styles.css
└── output/                # Output directory (auto-created)
```

## Integration Guide

### Django Integration

Detailed integration steps: [docs/INTEGRATION.md#django-integration](docs/INTEGRATION.md#django-integration)

Quick start:

```python
from utils.ocr_client import ocr_client

# Process file
result = ocr_client.process_image(uploaded_file)
structured_data = result['result']['structured_result']['structured_data']
```

### Other Frameworks

- **Flask**: [docs/INTEGRATION.md#flask-integration](docs/INTEGRATION.md#flask-integration)
- **FastAPI**: [docs/INTEGRATION.md#fastapi-integration](docs/INTEGRATION.md#fastapi-integration)
- **Standalone Script**: [docs/INTEGRATION.md#standalone-python-script](docs/INTEGRATION.md#standalone-python-script)

Complete integration documentation: [docs/INTEGRATION.md](docs/INTEGRATION.md)

## Development Notes

- All functionality exposed through functions/class methods
- Configuration passed through JSON files, avoiding hardcoding
- Pydantic used to define output schemas
- Clear code structure, easy to maintain and extend

## Documentation Index

### English Documentation

- [API Documentation](docs/API.md) - Complete API interface documentation and examples
- [Configuration Documentation](docs/CONFIGURATION.md) - Detailed documentation for all configuration files
- [Integration Guide](docs/INTEGRATION.md) - Detailed cases for integrating into different projects

### 中文文档 (Chinese Documentation)

- [API 详细文档](docs/API_CN.md) - 完整的 API 接口说明和示例
- [配置文档](docs/CONFIGURATION_CN.md) - 所有配置文件的详细说明
- [集成指南](docs/INTEGRATION_CN.md) - 集成到不同项目的详细案例

## License

MIT License

