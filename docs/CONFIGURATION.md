# Configuration Documentation

This document provides detailed descriptions of all configuration file formats and options.

## Directory Structure

```
configs/
├── ocr.json                    # OCR engine configuration
├── nlp.json                    # NLP processing configuration
├── llms/
│   └── init.json              # LLM service configuration
├── ocr/
│   ├── custom_words.txt       # Custom words (OCR post-processing)
│   ├── custom_patterns.txt    # Custom patterns (Tesseract)
│   └── README.md             # OCR configuration guide
└── structures/
    ├── template.json          # Structure configuration template
    ├── origin/               # Original configuration files
    ├── temp/                 # Temporary configuration files
    └── new/                  # Processed configuration files
```

---

## OCR Configuration (`configs/ocr.json`)

Configure OCR engines and related parameters.

### Configuration Structure

```json
{
  "ocr_engines": {
    "current": "google-cloud-vision",
    "engines": {
      "pytesseract": {
        "provider": "pytesseract",
        "description": "Local OCR engine based on Tesseract",
        "languages": "chi_sim+eng",
        "oem": 3,
        "psm": 6,
        "custom_words_path": "configs/ocr/custom_words.txt",
        "custom_patterns_path": "configs/ocr/custom_patterns.txt"
      },
      "google-cloud-vision": {
        "provider": "google-cloud-vision",
        "description": "Google Cloud Vision API, high-precision OCR service",
        "language_hints": ["zh", "en"],
        "enable_text_detection": true,
        "credentials_path": "credentials/google_vision.json",
        "enable_post_process": true,
        "custom_words_path": "configs/ocr/custom_words.txt"
      }
    }
  }
}
```

### Field Descriptions

#### Global Configuration

- `current`: Name of the currently used OCR engine (`pytesseract` or `google-cloud-vision`)

#### Tesseract Configuration (pytesseract)

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| provider | string | Engine provider, fixed as `pytesseract` | - |
| description | string | Engine description | - |
| languages | string | Recognition languages, multiple connected with `+` | `chi_sim+eng` |
| oem | int | OCR Engine Mode (0-3) | 3 |
| psm | int | Page Segmentation Mode (0-13) | 6 |
| custom_words_path | string | Custom words file path | - |
| custom_patterns_path | string | Custom patterns file path | - |

**PSM Mode Descriptions**:
- `0`: Orientation and script detection only
- `1`: Automatic page segmentation with OSD
- `3`: Fully automatic page segmentation (default)
- `6`: Assume uniform text block
- `11`: Sparse text
- `13`: Raw line, no page segmentation

**OEM Mode Descriptions**:
- `0`: Legacy engine only
- `1`: LSTM engine only
- `2`: LSTM + Legacy engine
- `3`: Default (based on available content)

#### Google Cloud Vision Configuration

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| provider | string | Engine provider, fixed as `google-cloud-vision` | - |
| description | string | Engine description | - |
| language_hints | array | Language hints list | `["zh", "en"]` |
| enable_text_detection | boolean | Enable text detection | `true` |
| credentials_path | string | Google Cloud credentials file path | - |
| enable_post_process | boolean | Enable post-processing (custom word correction) | `true` |
| custom_words_path | string | Custom words file path | - |

### Custom Words File (`configs/ocr/custom_words.txt`)

One word per line, format:

```
Original word|Corrected word
```

Example:

```
Invoice Number|Invoice Number
Tax ID|Tax ID
Amount|Amount
```

If no correction is needed, just write the original word:

```
Invoice Number
Tax ID
```

### Custom Patterns File (`configs/ocr/custom_patterns.txt`)

Tesseract custom patterns, one pattern per line:

```
Invoice Number: \d{8,12}
Amount: \d+\.\d{2}
Date: \d{4}-\d{2}-\d{2}
```

---

## LLM Configuration (`configs/llms/init.json`)

Configure LLM service providers and models.

### Configuration Structure

```json
{
  "llm_services": {
    "current": "openai",
    "services": {
      "openai": {
        "provider": "openai",
        "description": "OpenAI GPT model",
        "model": "gpt-4o-mini",
        "temperature": 0.1,
        "max_tokens": 4000,
        "api_key_env": "OPENAI_API_KEY"
      },
      "google": {
        "provider": "google",
        "description": "Google Gemini model",
        "model": "gemini-1.5-flash",
        "temperature": 0.1,
        "max_tokens": 4000,
        "api_key_env": "GEMINI_API_KEY"
      },
      "ollama": {
        "provider": "ollama",
        "description": "Local Ollama model",
        "model": "qwen2.5:7b",
        "temperature": 0.1,
        "base_url": "http://localhost:11434"
      }
    }
  }
}
```

### Field Descriptions

#### Global Configuration

- `current`: Name of the currently used LLM service

#### OpenAI Configuration

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| provider | string | Service provider, fixed as `openai` | - |
| model | string | Model name | `gpt-4o-mini` |
| temperature | float | Temperature parameter (0-2) | 0.1 |
| max_tokens | int | Maximum output token count | 4000 |
| api_key_env | string | API Key environment variable name | `OPENAI_API_KEY` |

#### Google Gemini Configuration

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| provider | string | Service provider, fixed as `google` | - |
| model | string | Model name | `gemini-1.5-flash` |
| temperature | float | Temperature parameter (0-2) | 0.1 |
| max_tokens | int | Maximum output token count | 4000 |
| api_key_env | string | API Key environment variable name | `GEMINI_API_KEY` |

#### Ollama Configuration

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| provider | string | Service provider, fixed as `ollama` | - |
| model | string | Model name | `qwen2.5:7b` |
| temperature | float | Temperature parameter (0-2) | 0.1 |
| base_url | string | Ollama service address | `http://localhost:11434` |

### Environment Variable Configuration

Configure API Key in `.env` file:

```env
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
```

Or set in system environment variables.

---

## NLP Configuration (`configs/nlp.json`)

Configure NLP processing options and structure configuration file paths.

### Configuration Structure

```json
{
  "nlp": {
    "use_spacy": true,
    "spacy_model": "zh_core_web_sm",
    "fallback_to_regex": true,
    "structure_config_path": "configs/structures/origin",
    "confidence_threshold": 80.0
  }
}
```

### Field Descriptions

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| use_spacy | boolean | Whether to use spaCy for entity recognition | `true` |
| spacy_model | string | spaCy model name | `zh_core_web_sm` |
| fallback_to_regex | boolean | Whether to fallback to regex if spaCy is unavailable | `true` |
| structure_config_path | string | Structure configuration file directory path | `configs/structures/origin` |
| confidence_threshold | float | Field confidence threshold (fields below this value require validation) | 80.0 |

---

## Structure Configuration (`configs/structures/origin/`)

Define field extraction rules. One JSON file per document type.

### Configuration Template (`configs/structures/template.json`)

```json
{
  "title": "Document Type Name",
  "description": "Document description",
  "items": [
    {
      "field": "Field Name",
      "description": "Field description",
      "type": "Field type",
      "pattern": "Regular expression pattern (optional)",
      "required": true,
      "validation": {
        "min_length": 0,
        "max_length": 100,
        "format": "Format requirements"
      }
    }
  ]
}
```

### Field Types

- `text`: Text type
- `number`: Number type
- `date`: Date type
- `amount`: Amount type
- `decimal`: Decimal type

### Configuration Example: Invoice (`invoice0.json`)

```json
{
  "title": "Invoice",
  "description": "VAT Invoice",
  "items": [
    {
      "field": "Invoice Number",
      "description": "Invoice number",
      "type": "text",
      "pattern": "\\d{8,12}",
      "required": true
    },
    {
      "field": "Invoice Date",
      "description": "Invoice date",
      "type": "date",
      "pattern": "\\d{4}-\\d{2}-\\d{2}",
      "required": true
    },
    {
      "field": "Amount",
      "description": "Invoice amount",
      "type": "amount",
      "pattern": "\\d+\\.\\d{2}",
      "required": true
    },
    {
      "field": "Tax ID",
      "description": "Tax identification number",
      "type": "text",
      "pattern": "[A-Z0-9]{15,20}",
      "required": false
    }
  ]
}
```

### Configuration Example: Resume (`resume0.json`)

```json
{
  "title": "Resume",
  "description": "Personal resume",
  "items": [
    {
      "field": "Name",
      "description": "Candidate name",
      "type": "text",
      "required": true
    },
    {
      "field": "Phone",
      "description": "Contact phone",
      "type": "text",
      "pattern": "1[3-9]\\d{9}",
      "required": true
    },
    {
      "field": "Email",
      "description": "Email address",
      "type": "text",
      "pattern": "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}",
      "required": false
    },
    {
      "field": "Years of Experience",
      "description": "Work experience years",
      "type": "number",
      "required": false
    }
  ]
}
```

### Configuration File Management

The system automatically manages three directories:

- `origin/`: Original configuration files (user edited)
- `temp/`: Temporary configuration files (system generated)
- `new/`: Processed configuration files (LLM optimized)

**Workflow**:
1. User creates/edits configuration files in `origin/`
2. System checks differences between `origin/` and `temp/` on startup
3. If differences exist, use LLM to optimize configuration files and save to `new/`
4. Use configuration files from `new/` during processing

---

## Environment Variables

### `.env` File Example

```env
# OpenAI API Key
OPENAI_API_KEY=sk-...

# Google Gemini API Key
GEMINI_API_KEY=...

# Other environment variables
LOG_LEVEL=INFO
```

### System Environment Variables

Can also be set in system environment variables:

```bash
# Linux/Mac
export OPENAI_API_KEY=sk-...
export GEMINI_API_KEY=...

# Windows
set OPENAI_API_KEY=sk-...
set GEMINI_API_KEY=...
```

---

## Configuration Validation

The system automatically validates configuration on startup:

1. **OCR Configuration**: Check if engine configuration is correct, if credential files exist
2. **LLM Configuration**: Check if API Key is set
3. **Structure Configuration**: Check if configuration file format is correct

If configuration is incorrect, the system will output error messages on startup.

---

## Configuration Best Practices

1. **OCR Engine Selection**:
   - High precision requirements: Use Google Cloud Vision
   - Local deployment: Use Tesseract
   - Cost considerations: Tesseract is free, Google Vision is pay-per-use

2. **LLM Model Selection**:
   - High precision: GPT-4 or Gemini Pro
   - Cost optimization: GPT-4o-mini or Gemini Flash
   - Local deployment: Ollama

3. **Structure Configuration**:
   - Field descriptions should be clear and explicit
   - Regular expressions should be accurate
   - Reasonably set `required` fields

4. **Custom Words**:
   - Add professional terminology
   - Regularly update vocabulary
   - Note case sensitivity

---

## Configuration Updates

After modifying configuration, restart the service for changes to take effect:

```bash
# Stop service
# Ctrl+C or kill <pid>

# Restart
python main.py
```

Some configurations (such as structure configurations) are automatically checked and updated on startup.

