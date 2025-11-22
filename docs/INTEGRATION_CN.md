# 集成案例文档

本文档提供将 OCR 模块集成到不同项目中的详细示例。

## 目录

- [Django 集成](#django-集成)
- [Flask 集成](#flask-集成)
- [FastAPI 集成](#fastapi-集成)
- [独立 Python 脚本](#独立-python-脚本)
- [微服务架构](#微服务架构)

---

## Django 集成

### 方案一：作为独立服务调用（推荐）

将 OCR 服务作为独立的 FastAPI 服务运行，Django 通过 HTTP 请求调用。

#### 1. 安装依赖

```bash
pip install requests
```

#### 2. 创建 OCR 客户端

在 Django 项目中创建 `utils/ocr_client.py`:

```python
import requests
from typing import Optional, Dict, Any
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class OCRClient:
    """OCR 服务客户端"""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or getattr(
            settings, 'OCR_SERVICE_URL', 'http://localhost:8000'
        )
        self.timeout = getattr(settings, 'OCR_SERVICE_TIMEOUT', 60)
    
    def health_check(self) -> bool:
        """检查 OCR 服务是否可用"""
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"OCR 服务健康检查失败: {e}")
            return False
    
    def process_image(
        self,
        image_file,
        save_files: bool = False
    ) -> Dict[str, Any]:
        """
        处理图片文件
        
        Args:
            image_file: Django UploadedFile 或文件对象
            save_files: 是否保存输出文件
        
        Returns:
            处理结果字典
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
            logger.error(f"OCR 处理失败: {e}")
            raise
    
    def process_pdf(
        self,
        pdf_file,
        save_files: bool = False
    ) -> Dict[str, Any]:
        """处理 PDF 文件"""
        return self.process_image(pdf_file, save_files)
    
    def batch_process(
        self,
        files: list,
        save_files: bool = False
    ) -> Dict[str, Any]:
        """
        批量处理文件
        
        Args:
            files: 文件列表
            save_files: 是否保存输出文件
        
        Returns:
            批量处理结果
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
            logger.error(f"批量处理失败: {e}")
            raise


# 全局客户端实例
ocr_client = OCRClient()
```

#### 3. 配置 Django Settings

在 `settings.py` 中添加：

```python
# OCR 服务配置
OCR_SERVICE_URL = os.getenv('OCR_SERVICE_URL', 'http://localhost:8000')
OCR_SERVICE_TIMEOUT = int(os.getenv('OCR_SERVICE_TIMEOUT', 60))
```

#### 4. 创建视图

在 `views.py` 中：

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
    """处理上传的文档"""
    if 'file' not in request.FILES:
        return JsonResponse(
            {"error": "未找到文件"},
            status=400
        )
    
    file = request.FILES['file']
    
    try:
        # 调用 OCR 服务
        result = ocr_client.process_image(file, save_files=False)
        
        # 提取结构化数据
        structured_data = result.get('result', {}).get(
            'structured_result', {}
        ).get('structured_data', {})
        
        # 保存到数据库（示例）
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
        logger.error(f"处理文档失败: {e}")
        return JsonResponse(
            {"error": str(e)},
            status=500
        )


@csrf_exempt
@require_http_methods(["POST"])
def batch_process_documents(request):
    """批量处理文档"""
    if 'files' not in request.FILES:
        return JsonResponse(
            {"error": "未找到文件"},
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
        logger.error(f"批量处理失败: {e}")
        return JsonResponse(
            {"error": str(e)},
            status=500
        )
```

#### 5. 配置 URL

在 `urls.py` 中：

```python
from django.urls import path
from . import views

urlpatterns = [
    path('api/ocr/process/', views.process_document, name='process_document'),
    path('api/ocr/batch/', views.batch_process_documents, name='batch_process'),
]
```

#### 6. 创建模型（可选）

在 `models.py` 中：

```python
from django.db import models
import json


class Document(models.Model):
    """文档模型"""
    file = models.FileField(upload_to='documents/')
    ocr_text = models.TextField(blank=True)
    structured_data = models.JSONField(default=dict)
    confidence = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def get_field_value(self, field_name: str):
        """获取字段值"""
        fields = self.structured_data.get('fields', {})
        field_info = fields.get(field_name, {})
        return field_info.get('value')
    
    def get_validation_list(self):
        """获取需要校验的字段列表"""
        return self.structured_data.get('validation_list', [])
```

#### 7. 创建表单

在 `forms.py` 中：

```python
from django import forms


class DocumentUploadForm(forms.Form):
    """文档上传表单"""
    file = forms.FileField(
        label='选择文件',
        help_text='支持 JPG、PNG 和 PDF 格式',
        widget=forms.FileInput(attrs={
            'accept': 'image/*,.pdf',
            'class': 'form-control'
        })
    )
```

#### 8. 创建模板

在 `templates/ocr/upload.html` 中：

```html
<!DOCTYPE html>
<html>
<head>
    <title>文档 OCR 处理</title>
</head>
<body>
    <h1>上传文档</h1>
    <form method="post" enctype="multipart/form-data" id="uploadForm">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit">上传并处理</button>
    </form>
    
    <div id="result" style="display: none;">
        <h2>处理结果</h2>
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
                alert('处理失败: ' + result.error);
            }
        });
    </script>
</body>
</html>
```

#### 9. 使用 Celery 异步处理（可选）

对于大量文件处理，可以使用 Celery 异步任务：

```python
# tasks.py
from celery import shared_task
from utils.ocr_client import ocr_client
from .models import Document
import logging

logger = logging.getLogger(__name__)


@shared_task
def process_document_async(document_id: int):
    """异步处理文档"""
    try:
        document = Document.objects.get(id=document_id)
        
        # 打开文件
        with document.file.open('rb') as f:
            result = ocr_client.process_image(f, save_files=False)
        
        # 更新文档
        document.ocr_text = result['result']['ocr_result']['text']
        document.structured_data = result['result']['structured_result']['structured_data']
        document.confidence = result['result']['structured_result']['structured_data'].get('coverage', 0.0)
        document.save()
        
        return {"success": True, "document_id": document_id}
    except Exception as e:
        logger.error(f"异步处理文档失败: {e}")
        return {"success": False, "error": str(e)}
```

在视图中调用：

```python
from .tasks import process_document_async

def upload_document(request):
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = Document.objects.create(file=form.cleaned_data['file'])
            # 异步处理
            process_document_async.delay(document.id)
            return redirect('document_list')
    else:
        form = DocumentUploadForm()
    return render(request, 'ocr/upload.html', {'form': form})
```

---

### 方案二：直接导入模块（不推荐）

如果需要在同一进程中运行，可以直接导入 OCR 模块。

#### 1. 安装依赖

确保所有 OCR 服务的依赖都已安装。

#### 2. 导入模块

```python
import sys
sys.path.append('/path/to/doc_ocr')

from ocr import OCREngineManager
from structure import structure_ocr_result
from pre_preocess import pre_preocess_for_google_vision
```

#### 3. 使用

```python
def process_image_direct(image_data: bytes):
    """直接处理图片"""
    # 预处理
    pre_processed_image = pre_preocess_for_google_vision(image_data)
    
    # OCR 识别
    ocr_engine = OCREngineManager()
    ocr_result = await ocr_engine.process_image_with_current_engine(
        pre_processed_image
    )
    
    # 结构化处理
    structured_result = structure_ocr_result(ocr_result)
    
    return structured_result
```

**注意**: 这种方式会导致 Django 和 OCR 服务耦合，不推荐用于生产环境。

---

## Flask 集成

### 1. 创建 OCR 客户端

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

### 2. 创建路由

```python
# app/routes.py
from flask import Blueprint, request, jsonify
from app.utils.ocr_client import OCRClient

ocr_bp = Blueprint('ocr', __name__)
ocr_client = OCRClient()

@ocr_bp.route('/api/ocr/process', methods=['POST'])
def process_document():
    if 'file' not in request.files:
        return jsonify({"error": "未找到文件"}), 400
    
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

### 3. 注册蓝图

```python
# app/__init__.py
from app.routes import ocr_bp

app.register_blueprint(ocr_bp)
```

---

## FastAPI 集成

如果已有 FastAPI 项目，可以直接导入 OCR 模块。

### 1. 导入模块

```python
from ocr import OCREngineManager
from structure import structure_ocr_result
from pre_preocess import pre_preocess_for_google_vision
```

### 2. 创建路由

```python
from fastapi import APIRouter, UploadFile, File
from typing import Dict, Any

router = APIRouter()

@router.post("/process")
async def process_document(file: UploadFile = File(...)) -> Dict[str, Any]:
    """处理文档"""
    image_data = await file.read()
    
    # 预处理
    pre_processed_image = pre_preocess_for_google_vision(image_data)
    
    # OCR 识别
    ocr_engine = OCREngineManager()
    ocr_result = await ocr_engine.process_image_with_current_engine(
        pre_processed_image
    )
    
    # 结构化处理
    structured_result = structure_ocr_result(ocr_result)
    
    return {
        "success": True,
        "data": structured_result
    }
```

---

## 独立 Python 脚本

### 示例脚本

```python
#!/usr/bin/env python3
"""OCR 处理脚本"""
import requests
import sys
from pathlib import Path

def process_file(file_path: str, service_url: str = "http://localhost:8000"):
    """处理单个文件"""
    url = f"{service_url}/ocr"
    
    with open(file_path, 'rb') as f:
        files = {"file": f}
        data = {"save_files": True}
        response = requests.post(url, files=files, data=data, timeout=60)
        response.raise_for_status()
        return response.json()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python ocr_script.py <文件路径>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not Path(file_path).exists():
        print(f"文件不存在: {file_path}")
        sys.exit(1)
    
    try:
        result = process_file(file_path)
        structured_data = result['result']['structured_result']['structured_data']
        
        print("处理成功！")
        print("\n结构化数据:")
        for field_name, field_info in structured_data['fields'].items():
            print(f"  {field_name}: {field_info['value']} (置信度: {field_info['confidence']:.2f}%)")
    except Exception as e:
        print(f"处理失败: {e}")
        sys.exit(1)
```

使用：

```bash
python ocr_script.py invoice.jpg
```

---

## 微服务架构

### Docker Compose 配置

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

## 最佳实践

1. **错误处理**: 始终包含完整的错误处理逻辑
2. **超时设置**: 设置合理的请求超时时间
3. **异步处理**: 对于大量文件，使用异步任务队列
4. **缓存**: 对于重复处理的文件，考虑使用缓存
5. **日志记录**: 记录所有 OCR 处理操作
6. **监控**: 监控 OCR 服务的健康状态和性能

---

## 故障排查

### 常见问题

1. **连接失败**: 检查 OCR 服务是否运行，URL 是否正确
2. **超时**: 增加超时时间或优化文件大小
3. **内存不足**: 对于大文件，考虑流式处理
4. **API Key 错误**: 检查环境变量配置

### 调试技巧

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 在请求中添加日志
logger.debug(f"发送请求到: {url}")
logger.debug(f"响应状态: {response.status_code}")
logger.debug(f"响应内容: {response.text}")
```

---

## 性能优化

1. **连接池**: 使用 `requests.Session()` 复用连接
2. **并发处理**: 使用 `asyncio` 或 `concurrent.futures` 并发处理
3. **批量处理**: 使用批量接口而不是多次单文件请求
4. **缓存结果**: 对相同文件缓存处理结果

---

## 安全考虑

1. **文件大小限制**: 限制上传文件大小
2. **文件类型验证**: 验证文件类型和内容
3. **API 认证**: 在生产环境中添加 API 认证
4. **敏感信息**: 不要在日志中记录敏感信息

