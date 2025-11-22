# Integration Guide

This document provides detailed examples for integrating the OCR module into different projects.

## Table of Contents

- [Django Integration](#django-integration)
- [Flask Integration](#flask-integration)
- [FastAPI Integration](#fastapi-integration)
- [Standalone Python Script](#standalone-python-script)
- [Microservices Architecture](#microservices-architecture)

---

## Django Integration

### Option 1: Call as Independent Service (Recommended)

Run the OCR service as an independent FastAPI service, and Django calls it via HTTP requests.

#### 1. Install Dependencies

```bash
pip install requests
```

#### 2. Create OCR Client

Create `utils/ocr_client.py` in your Django project:

```python
import requests
from typing import Optional, Dict, Any
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class OCRClient:
    """OCR Service Client"""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or getattr(
            settings, 'OCR_SERVICE_URL', 'http://localhost:8000'
        )
        self.timeout = getattr(settings, 'OCR_SERVICE_TIMEOUT', 60)
    
    def health_check(self) -> bool:
        """Check if OCR service is available"""
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"OCR service health check failed: {e}")
            return False
    
    def process_image(
        self,
        image_file,
        save_files: bool = False
    ) -> Dict[str, Any]:
        """
        Process image file
        
        Args:
            image_file: Django UploadedFile or file object
            save_files: Whether to save output files
        
        Returns:
            Processing result dictionary
        """
        try:
            url = f"{self.base_url}/ocr"
            files = {"file": image_file}
            data = {"save_files": save_files}
            
            response = requests.post(
                url,
                files=files,
                data=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"OCR processing failed: {e}")
            raise
    
    def process_pdf(
        self,
        pdf_file,
        save_files: bool = False
    ) -> Dict[str, Any]:
        """Process PDF file"""
        return self.process_image(pdf_file, save_files)
    
    def batch_process(
        self,
        files: list,
        save_files: bool = False
    ) -> Dict[str, Any]:
        """
        Batch process files
        
        Args:
            files: File list
            save_files: Whether to save output files
        
        Returns:
            Batch processing result
        """
        try:
            url = f"{self.base_url}/batch"
            file_list = [("files", f) for f in files]
            data = {"save_files": save_files}
            
            response = requests.post(
                url,
                files=file_list,
                data=data,
                timeout=self.timeout * len(files)
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Batch processing failed: {e}")
            raise


# Global client instance
ocr_client = OCRClient()
```

#### 3. Configure Django Settings

Add to `settings.py`:

```python
# OCR Service Configuration
OCR_SERVICE_URL = os.getenv('OCR_SERVICE_URL', 'http://localhost:8000')
OCR_SERVICE_TIMEOUT = int(os.getenv('OCR_SERVICE_TIMEOUT', 60))
```

#### 4. Create Views

In `views.py`:

```python
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.files.uploadedfile import UploadedFile
from utils.ocr_client import ocr_client
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def process_document(request):
    """Process uploaded document"""
    if 'file' not in request.FILES:
        return JsonResponse(
            {"error": "File not found"},
            status=400
        )
    
    file = request.FILES['file']
    
    try:
        # Call OCR service
        result = ocr_client.process_image(file, save_files=False)
        
        # Extract structured data
        structured_data = result.get('result', {}).get(
            'structured_result', {}
        ).get('structured_data', {})
        
        # Save to database (example)
        # document = Document.objects.create(
        #     file=file,
        #     ocr_text=result['result']['ocr_result']['text'],
        #     structured_data=structured_data
        # )
        
        return JsonResponse({
            "success": True,
            "data": structured_data,
            "ocr_text": result['result']['ocr_result']['text']
        })
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        return JsonResponse(
            {"error": str(e)},
            status=500
        )


@csrf_exempt
@require_http_methods(["POST"])
def batch_process_documents(request):
    """Batch process documents"""
    if 'files' not in request.FILES:
        return JsonResponse(
            {"error": "Files not found"},
            status=400
        )
    
    files = request.FILES.getlist('files')
    
    try:
        result = ocr_client.batch_process(files, save_files=False)
        
        return JsonResponse({
            "success": True,
            "total": result['total_files'],
            "successful": result['successful'],
            "failed": result['failed'],
            "results": result['results']
        })
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        return JsonResponse(
            {"error": str(e)},
            status=500
        )
```

#### 5. Configure URLs

In `urls.py`:

```python
from django.urls import path
from . import views

urlpatterns = [
    path('api/ocr/process/', views.process_document, name='process_document'),
    path('api/ocr/batch/', views.batch_process_documents, name='batch_process'),
]
```

#### 6. Create Model (Optional)

In `models.py`:

```python
from django.db import models
import json


class Document(models.Model):
    """Document Model"""
    file = models.FileField(upload_to='documents/')
    ocr_text = models.TextField(blank=True)
    structured_data = models.JSONField(default=dict)
    confidence = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def get_field_value(self, field_name: str):
        """Get field value"""
        fields = self.structured_data.get('fields', {})
        field_info = fields.get(field_name, {})
        return field_info.get('value')
    
    def get_validation_list(self):
        """Get list of fields requiring validation"""
        return self.structured_data.get('validation_list', [])
```

#### 7. Create Form

In `forms.py`:

```python
from django import forms


class DocumentUploadForm(forms.Form):
    """Document Upload Form"""
    file = forms.FileField(
        label='Select File',
        help_text='Supports JPG, PNG, and PDF formats',
        widget=forms.FileInput(attrs={
            'accept': 'image/*,.pdf',
            'class': 'form-control'
        })
    )
```

#### 8. Create Template

In `templates/ocr/upload.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Document OCR Processing</title>
</head>
<body>
    <h1>Upload Document</h1>
    <form method="post" enctype="multipart/form-data" id="uploadForm">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit">Upload and Process</button>
    </form>
    
    <div id="result" style="display: none;">
        <h2>Processing Result</h2>
        <pre id="resultContent"></pre>
    </div>
    
    <script>
        document.getElementById('uploadForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const response = await fetch('/api/ocr/process/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                }
            });
            
            const result = await response.json();
            if (result.success) {
                document.getElementById('result').style.display = 'block';
                document.getElementById('resultContent').textContent = 
                    JSON.stringify(result.data, null, 2);
            } else {
                alert('Processing failed: ' + result.error);
            }
        });
    </script>
</body>
</html>
```

#### 9. Use Celery for Async Processing (Optional)

For processing large numbers of files, use Celery async tasks:

```python
# tasks.py
from celery import shared_task
from utils.ocr_client import ocr_client
from .models import Document
import logging

logger = logging.getLogger(__name__)


@shared_task
def process_document_async(document_id: int):
    """Asynchronously process document"""
    try:
        document = Document.objects.get(id=document_id)
        
        # Open file
        with document.file.open('rb') as f:
            result = ocr_client.process_image(f, save_files=False)
        
        # Update document
        document.ocr_text = result['result']['ocr_result']['text']
        document.structured_data = result['result']['structured_result']['structured_data']
        document.confidence = result['result']['structured_result']['structured_data'].get('coverage', 0.0)
        document.save()
        
        return {"success": True, "document_id": document_id}
    except Exception as e:
        logger.error(f"Async document processing failed: {e}")
        return {"success": False, "error": str(e)}
```

Call in view:

```python
from .tasks import process_document_async

def upload_document(request):
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = Document.objects.create(file=form.cleaned_data['file'])
            # Async processing
            process_document_async.delay(document.id)
            return redirect('document_list')
    else:
        form = DocumentUploadForm()
    return render(request, 'ocr/upload.html', {'form': form})
```

---

### Option 2: Direct Module Import (Not Recommended)

If you need to run in the same process, you can directly import the OCR module.

#### 1. Install Dependencies

Ensure all OCR service dependencies are installed.

#### 2. Import Module

```python
import sys
sys.path.append('/path/to/doc_ocr')

from ocr import OCREngineManager
from structure import structure_ocr_result
from pre_preocess import pre_preocess_for_google_vision
```

#### 3. Usage

```python
def process_image_direct(image_data: bytes):
    """Directly process image"""
    # Preprocessing
    pre_processed_image = pre_preocess_for_google_vision(image_data)
    
    # OCR recognition
    ocr_engine = OCREngineManager()
    ocr_result = await ocr_engine.process_image_with_current_engine(
        pre_processed_image
    )
    
    # Structured processing
    structured_result = structure_ocr_result(ocr_result)
    
    return structured_result
```

**Note**: This approach couples Django and OCR service, not recommended for production.

---

## Flask Integration

### 1. Create OCR Client

```python
# app/utils/ocr_client.py
import requests
from flask import current_app

class OCRClient:
    def __init__(self):
        self.base_url = current_app.config.get('OCR_SERVICE_URL', 'http://localhost:8000')
    
    def process_image(self, image_file, save_files=False):
        url = f"{self.base_url}/ocr"
        files = {"file": image_file}
        data = {"save_files": save_files}
        response = requests.post(url, files=files, data=data, timeout=60)
        response.raise_for_status()
        return response.json()
```

### 2. Create Routes

```python
# app/routes.py
from flask import Blueprint, request, jsonify
from app.utils.ocr_client import OCRClient

ocr_bp = Blueprint('ocr', __name__)
ocr_client = OCRClient()

@ocr_bp.route('/api/ocr/process', methods=['POST'])
def process_document():
    if 'file' not in request.files:
        return jsonify({"error": "File not found"}), 400
    
    file = request.files['file']
    try:
        result = ocr_client.process_image(file, save_files=False)
        return jsonify({
            "success": True,
            "data": result['result']['structured_result']['structured_data']
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

### 3. Register Blueprint

```python
# app/__init__.py
from app.routes import ocr_bp

app.register_blueprint(ocr_bp)
```

---

## FastAPI Integration

If you already have a FastAPI project, you can directly import the OCR module.

### 1. Import Module

```python
from ocr import OCREngineManager
from structure import structure_ocr_result
from pre_preocess import pre_preocess_for_google_vision
```

### 2. Create Routes

```python
from fastapi import APIRouter, UploadFile, File
from typing import Dict, Any

router = APIRouter()

@router.post("/process")
async def process_document(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Process document"""
    image_data = await file.read()
    
    # Preprocessing
    pre_processed_image = pre_preocess_for_google_vision(image_data)
    
    # OCR recognition
    ocr_engine = OCREngineManager()
    ocr_result = await ocr_engine.process_image_with_current_engine(
        pre_processed_image
    )
    
    # Structured processing
    structured_result = structure_ocr_result(ocr_result)
    
    return {
        "success": True,
        "data": structured_result
    }
```

---

## Standalone Python Script

### Example Script

```python
#!/usr/bin/env python3
"""OCR Processing Script"""
import requests
import sys
from pathlib import Path

def process_file(file_path: str, service_url: str = "http://localhost:8000"):
    """Process a single file"""
    url = f"{service_url}/ocr"
    
    with open(file_path, 'rb') as f:
        files = {"file": f}
        data = {"save_files": True}
        response = requests.post(url, files=files, data=data, timeout=60)
        response.raise_for_status()
        return response.json()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ocr_script.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not Path(file_path).exists():
        print(f"File does not exist: {file_path}")
        sys.exit(1)
    
    try:
        result = process_file(file_path)
        structured_data = result['result']['structured_result']['structured_data']
        
        print("Processing successful!")
        print("\nStructured Data:")
        for field_name, field_info in structured_data['fields'].items():
            print(f"  {field_name}: {field_info['value']} (Confidence: {field_info['confidence']:.2f}%)")
    except Exception as e:
        print(f"Processing failed: {e}")
        sys.exit(1)
```

Usage:

```bash
python ocr_script.py invoice.jpg
```

---

## Microservices Architecture

### Docker Compose Configuration

```yaml
version: '3.8'

services:
  ocr-service:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - ./configs:/app/configs
      - ./output:/app/output
      - ./credentials:/app/credentials
    restart: unless-stopped

  django-app:
    build: ./django-app
    ports:
      - "8001:8000"
    environment:
      - OCR_SERVICE_URL=http://ocr-service:8000
    depends_on:
      - ocr-service
    restart: unless-stopped
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

---

## Best Practices

1. **Error Handling**: Always include complete error handling logic
2. **Timeout Settings**: Set reasonable request timeout
3. **Async Processing**: For large numbers of files, use async task queues
4. **Caching**: Consider caching for repeatedly processed files
5. **Logging**: Log all OCR processing operations
6. **Monitoring**: Monitor OCR service health status and performance

---

## Troubleshooting

### Common Issues

1. **Connection Failure**: Check if OCR service is running, if URL is correct
2. **Timeout**: Increase timeout or optimize file size
3. **Out of Memory**: For large files, consider streaming processing
4. **API Key Error**: Check environment variable configuration

### Debugging Tips

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add logging to requests
logger.debug(f"Sending request to: {url}")
logger.debug(f"Response status: {response.status_code}")
logger.debug(f"Response content: {response.text}")
```

---

## Performance Optimization

1. **Connection Pool**: Use `requests.Session()` to reuse connections
2. **Concurrent Processing**: Use `asyncio` or `concurrent.futures` for concurrent processing
3. **Batch Processing**: Use batch endpoints instead of multiple single-file requests
4. **Cache Results**: Cache processing results for identical files

---

## Security Considerations

1. **File Size Limits**: Limit upload file size
2. **File Type Validation**: Validate file type and content
3. **API Authentication**: Add API authentication in production
4. **Sensitive Information**: Do not log sensitive information

