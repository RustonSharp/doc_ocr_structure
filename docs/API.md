# API Documentation

## Basic Information

- **Base URL**: `http://localhost:8000`
- **API Version**: v1.0.0
- **Content Types**: `application/json` or `multipart/form-data`

## Endpoint List

### 1. Health Check

Check if the service is running normally.

**Request**

```http
GET /health
```

**Response**

```json
{
  "status": "ok",
  "message": "Service is running normally"
}
```

**Status Code**: `200 OK`

---

### 2. Service Information

Get basic service information and available endpoints.

**Request**

```http
GET /
```

**Response**

```json
{
  "service": "OCR and Text Structuring Integrated Tool",
  "version": "1.0.0",
  "endpoints": {
    "ocr": "/ocr",
    "batch": "/batch",
    "docs": "/docs",
    "health": "/health"
  }
}
```

---

### 3. OCR Recognition and Structured Processing

Perform OCR recognition and structured data extraction on a single image or PDF file.

**Request**

```http
POST /ocr
Content-Type: multipart/form-data
```

**Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | File | Yes | Image file (JPG/PNG) or PDF file |
| save_files | boolean | No | Whether to save output files locally, default `true` |

**Request Example**

```bash
curl -X POST "http://localhost:8000/ocr" \
  -F "file=@invoice.jpg" \
  -F "save_files=true"
```

**Python Example**

```python
import requests

url = "http://localhost:8000/ocr"
files = {"file": open("invoice.jpg", "rb")}
data = {"save_files": True}

response = requests.post(url, files=files, data=data)
result = response.json()
```

**Response Structure**

```json
{
  "result": {
    "pre_processed_image": "data:image/png;base64,...",
    "ocr_result": {
      "text": "OCR recognized text content...",
      "confidence": 85.5,
      "language": "zh,en",
      "engine": "google-cloud-vision",
      "text_blocks": [
        {
          "text": "Text block content",
          "bbox": [100, 200, 300, 250],
          "confidence": 90.0
        }
      ]
    },
    "structured_result": {
      "structured_data": {
        "fields": {
          "Invoice Number": {
            "value": "4200154350",
            "confidence": 95.5,
            "source": "ocr",
            "needs_validation": false
          },
          "Amount": {
            "value": "1000.00",
            "confidence": 88.2,
            "source": "nlp",
            "needs_validation": false
          }
        },
        "validation_list": ["Field Name 1", "Field Name 2"],
        "coverage": 85.5
      },
      "raw_ocr": {
        "text": "Raw OCR text",
        "confidence": 85.5
      },
      "cleaned_text": "Cleaned text",
      "structure_config": "Invoice",
      "entities": [
        {
          "text": "2024-01-01",
          "label": "DATE",
          "start": 100,
          "end": 110
        }
      ]
    }
  },
  "output_files": {
    "ocr_raw_text": "output/invoice_20240101_120000/ocr_raw_text.txt",
    "validation_list": "output/invoice_20240101_120000/validation_list.csv",
    "structured_json": "output/invoice_20240101_120000/invoice_20240101_120000_structured.json"
  }
}
```

**PDF File Response**

When uploading a PDF file, the response structure is slightly different:

```json
{
  "file_type": "pdf",
  "total_pages": 3,
  "results": [
    {
      "pre_processed_image": "data:image/png;base64,...",
      "ocr_result": {...},
      "structured_result": {
        "page_number": 1,
        ...
      }
    },
    {
      "pre_processed_image": "data:image/png;base64,...",
      "ocr_result": {...},
      "structured_result": {
        "page_number": 2,
        ...
      }
    }
  ]
}
```

**Status Codes**

- `200 OK`: Processing successful
- `400 Bad Request`: Request parameter error or processing failed
- `500 Internal Server Error`: Server internal error

**Error Response**

```json
{
  "detail": "Error description"
}
```

---

### 4. Batch Processing

Process multiple files or an entire folder in batch.

**Request**

```http
POST /batch
Content-Type: multipart/form-data
```

**Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| files | File[] | Yes | File list (multiple files) |
| save_files | boolean | No | Whether to save output files, default `true` |

**Request Example**

```bash
curl -X POST "http://localhost:8000/batch" \
  -F "files=@file1.jpg" \
  -F "files=@file2.pdf" \
  -F "files=@file3.png" \
  -F "save_files=true"
```

**Python Example**

```python
import requests

url = "http://localhost:8000/batch"
files = [
    ("files", open("file1.jpg", "rb")),
    ("files", open("file2.pdf", "rb")),
    ("files", open("file3.png", "rb"))
]
data = {"save_files": True}

response = requests.post(url, files=files, data=data)
result = response.json()
```

**Response Structure**

```json
{
  "total_files": 3,
  "successful": 2,
  "failed": 1,
  "results": [
    {
      "filename": "file1.jpg",
      "status": "success",
      "result": {
        "pre_processed_image": "...",
        "ocr_result": {...},
        "structured_result": {...}
      }
    },
    {
      "filename": "file2.pdf",
      "page": 1,
      "status": "success",
      "result": {...}
    },
    {
      "filename": "file3.png",
      "status": "error",
      "error": "Processing failure reason"
    }
  ]
}
```

**Status Codes**

- `200 OK`: Processing completed (may be partially successful)
- `400 Bad Request`: Request parameter error
- `500 Internal Server Error`: Server internal error

---

### 5. Regenerate Output Files

Regenerate output files based on corrected structured data.

**Request**

```http
POST /regenerate
Content-Type: application/json
```

**Request Body**

```json
{
  "structured_result": {
    "structured_data": {
      "fields": {
        "Field Name": {
          "value": "Corrected value",
          "confidence": 100.0,
          "source": "manual",
          "needs_validation": false
        }
      },
      "validation_list": []
    }
  },
  "output_dir": "output/invoice",
  "base_name": "invoice",
  "ocr_result": {
    "text": "OCR raw text"
  }
}
```

**Response**

```json
{
  "success": true,
  "message": "Output files regenerated successfully",
  "files": {
    "ocr_raw_text": "output/invoice_20240101_120000/ocr_raw_text.txt",
    "validation_list": "output/invoice_20240101_120000/validation_list.csv",
    "structured_json": "output/invoice_20240101_120000/invoice_20240101_120000_structured.json"
  }
}
```

**Status Codes**

- `200 OK`: Regeneration successful
- `400 Bad Request`: Request parameter error
- `500 Internal Server Error`: Server internal error

---

## Response Field Descriptions

### OCR Result (ocr_result)

| Field | Type | Description |
|-------|------|-------------|
| text | string | Complete text recognized by OCR |
| confidence | float | Overall confidence (0-100) |
| language | string | Detected language |
| engine | string | OCR engine used |
| text_blocks | array | Text block list (includes position information) |

### Structured Result (structured_result)

| Field | Type | Description |
|-------|------|-------------|
| structured_data | object | Structured data |
| structured_data.fields | object | Extracted fields dictionary |
| structured_data.fields[field_name].value | any | Field value |
| structured_data.fields[field_name].confidence | float | Field confidence (0-100) |
| structured_data.fields[field_name].source | string | Data source (ocr/nlp/llm/manual) |
| structured_data.fields[field_name].needs_validation | boolean | Whether manual validation is needed |
| structured_data.validation_list | array | List of field names requiring validation |
| structured_data.coverage | float | Field coverage (0-100) |
| raw_ocr | object | Raw OCR result |
| cleaned_text | string | Cleaned text |
| structure_config | string | Structure configuration name used |
| entities | array | NLP recognized entity list |

---

## Error Handling

All endpoints return standard error responses when errors occur:

```json
{
  "detail": "Error description"
}
```

Common error codes:

- `400 Bad Request`: Request parameter error, unsupported file format, preprocessing failure, etc.
- `404 Not Found`: Endpoint does not exist
- `500 Internal Server Error`: Server internal error, OCR recognition failure, LLM call failure, etc.

---

## Rate Limiting

The current version does not implement rate limiting, but it is recommended:

- Single file processing: Avoid too many concurrent requests
- Batch processing: Recommend no more than 50 files per batch
- Large files: PDF files should be less than 50MB

---

## Best Practices

1. **Error Handling**: Always check response status codes and error messages
2. **Timeout Settings**: Set reasonable request timeout (recommended 60 seconds)
3. **File Size**: Single files should be less than 10MB, PDFs should be less than 50MB
4. **Batch Processing**: For large numbers of files, process in batches
5. **Save Files**: In production, set `save_files=true` for later review

---

## Complete Examples

### Python Complete Example

```python
import requests
import json
from pathlib import Path

class OCRClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def health_check(self):
        """Health check"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def process_image(self, image_path, save_files=True):
        """Process a single image"""
        url = f"{self.base_url}/ocr"
        with open(image_path, "rb") as f:
            files = {"file": f}
            data = {"save_files": save_files}
            response = requests.post(url, files=files, data=data, timeout=60)
            response.raise_for_status()
            return response.json()
    
    def process_pdf(self, pdf_path, save_files=True):
        """Process PDF file"""
        return self.process_image(pdf_path, save_files)
    
    def batch_process(self, file_paths, save_files=True):
        """Batch processing"""
        url = f"{self.base_url}/batch"
        files = []
        for path in file_paths:
            files.append(("files", open(path, "rb")))
        
        data = {"save_files": save_files}
        try:
            response = requests.post(url, files=files, data=data, timeout=300)
            response.raise_for_status()
            return response.json()
        finally:
            for _, f in files:
                f.close()
    
    def regenerate_output(self, structured_result, output_dir, base_name, ocr_result=None):
        """Regenerate output files"""
        url = f"{self.base_url}/regenerate"
        payload = {
            "structured_result": structured_result,
            "output_dir": output_dir,
            "base_name": base_name
        }
        if ocr_result:
            payload["ocr_result"] = ocr_result
        
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        return response.json()

# Usage example
if __name__ == "__main__":
    client = OCRClient()
    
    # Health check
    health = client.health_check()
    print(f"Service status: {health['status']}")
    
    # Process single image
    result = client.process_image("invoice.jpg")
    print(f"Recognition result: {result['result']['ocr_result']['text'][:100]}...")
    
    # Batch processing
    files = ["file1.jpg", "file2.pdf", "file3.png"]
    batch_result = client.batch_process(files)
    print(f"Batch processing: {batch_result['successful']} succeeded, {batch_result['failed']} failed")
```

### JavaScript/TypeScript Example

```typescript
class OCRClient {
  constructor(private baseUrl: string = "http://localhost:8000") {}
  
  async healthCheck(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/health`);
    return await response.json();
  }
  
  async processImage(file: File, saveFiles: boolean = true): Promise<any> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("save_files", String(saveFiles));
    
    const response = await fetch(`${this.baseUrl}/ocr`, {
      method: "POST",
      body: formData
    });
    
    if (!response.ok) {
      throw new Error(`Request failed: ${response.statusText}`);
    }
    
    return await response.json();
  }
  
  async batchProcess(files: File[], saveFiles: boolean = true): Promise<any> {
    const formData = new FormData();
    files.forEach(file => {
      formData.append("files", file);
    });
    formData.append("save_files", String(saveFiles));
    
    const response = await fetch(`${this.baseUrl}/batch`, {
      method: "POST",
      body: formData
    });
    
    if (!response.ok) {
      throw new Error(`Request failed: ${response.statusText}`);
    }
    
    return await response.json();
  }
  
  async regenerateOutput(
    structuredResult: any,
    outputDir: string,
    baseName: string,
    ocrResult?: any
  ): Promise<any> {
    const payload: any = {
      structured_result: structuredResult,
      output_dir: outputDir,
      base_name: baseName
    };
    
    if (ocrResult) {
      payload.ocr_result = ocrResult;
    }
    
    const response = await fetch(`${this.baseUrl}/regenerate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });
    
    if (!response.ok) {
      throw new Error(`Request failed: ${response.statusText}`);
    }
    
    return await response.json();
  }
}

// Usage example
const client = new OCRClient();

// Process file
const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
fileInput.addEventListener('change', async (e) => {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (file) {
    try {
      const result = await client.processImage(file);
      console.log("Recognition result:", result);
    } catch (error) {
      console.error("Processing failed:", error);
    }
  }
});
```

---

## More Information

- Complete API documentation (Swagger UI): `http://localhost:8000/docs`
- ReDoc documentation: `http://localhost:8000/redoc`

