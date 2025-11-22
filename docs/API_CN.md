# API 详细文档

## 基础信息

- **Base URL**: `http://localhost:8000`
- **API 版本**: v1.0.0
- **内容类型**: `application/json` 或 `multipart/form-data`

## 接口列表

### 1. 健康检查

检查服务是否正常运行。

**请求**

```http
GET /health
```

**响应**

```json
{
  "status": "ok",
  "message": "服务运行正常"
}
```

**状态码**: `200 OK`

---

### 2. 服务信息

获取服务基本信息和可用端点。

**请求**

```http
GET /
```

**响应**

```json
{
  "service": "OCR 与文本结构化一体化工具",
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

### 3. OCR 识别和结构化处理

对单张图片或 PDF 文件进行 OCR 识别和结构化数据提取。

**请求**

```http
POST /ocr
Content-Type: multipart/form-data
```

**参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| file | File | 是 | 图片文件（JPG/PNG）或 PDF 文件 |
| save_files | boolean | 否 | 是否保存输出文件到本地，默认 `true` |

**请求示例**

```bash
curl -X POST "http://localhost:8000/ocr" \
  -F "file=@invoice.jpg" \
  -F "save_files=true"
```

**Python 示例**

```python
import requests

url = "http://localhost:8000/ocr"
files = {"file": open("invoice.jpg", "rb")}
data = {"save_files": True}

response = requests.post(url, files=files, data=data)
result = response.json()
```

**响应结构**

```json
{
  "result": {
    "pre_processed_image": "data:image/png;base64,...",
    "ocr_result": {
      "text": "OCR识别的文本内容...",
      "confidence": 85.5,
      "language": "zh,en",
      "engine": "google-cloud-vision",
      "text_blocks": [
        {
          "text": "文本块内容",
          "bbox": [100, 200, 300, 250],
          "confidence": 90.0
        }
      ]
    },
    "structured_result": {
      "structured_data": {
        "fields": {
          "发票号码": {
            "value": "4200154350",
            "confidence": 95.5,
            "source": "ocr",
            "needs_validation": false
          },
          "金额": {
            "value": "1000.00",
            "confidence": 88.2,
            "source": "nlp",
            "needs_validation": false
          }
        },
        "validation_list": ["字段名1", "字段名2"],
        "coverage": 85.5
      },
      "raw_ocr": {
        "text": "原始OCR文本",
        "confidence": 85.5
      },
      "cleaned_text": "清理后的文本",
      "structure_config": "发票",
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

**PDF 文件响应**

当上传 PDF 文件时，响应结构略有不同：

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

**状态码**

- `200 OK`: 处理成功
- `400 Bad Request`: 请求参数错误或处理失败
- `500 Internal Server Error`: 服务器内部错误

**错误响应**

```json
{
  "detail": "错误描述信息"
}
```

---

### 4. 批量处理

批量处理多个文件或整个文件夹。

**请求**

```http
POST /batch
Content-Type: multipart/form-data
```

**参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| files | File[] | 是 | 文件列表（多个文件） |
| save_files | boolean | 否 | 是否保存输出文件，默认 `true` |

**请求示例**

```bash
curl -X POST "http://localhost:8000/batch" \
  -F "files=@file1.jpg" \
  -F "files=@file2.pdf" \
  -F "files=@file3.png" \
  -F "save_files=true"
```

**Python 示例**

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

**响应结构**

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
      "error": "处理失败原因"
    }
  ]
}
```

**状态码**

- `200 OK`: 处理完成（可能部分成功）
- `400 Bad Request`: 请求参数错误
- `500 Internal Server Error`: 服务器内部错误

---

### 5. 重新生成输出文件

根据修正后的结构化数据重新生成输出文件。

**请求**

```http
POST /regenerate
Content-Type: application/json
```

**请求体**

```json
{
  "structured_result": {
    "structured_data": {
      "fields": {
        "字段名": {
          "value": "修正后的值",
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
    "text": "OCR原始文本"
  }
}
```

**响应**

```json
{
  "success": true,
  "message": "输出文件已重新生成",
  "files": {
    "ocr_raw_text": "output/invoice_20240101_120000/ocr_raw_text.txt",
    "validation_list": "output/invoice_20240101_120000/validation_list.csv",
    "structured_json": "output/invoice_20240101_120000/invoice_20240101_120000_structured.json"
  }
}
```

**状态码**

- `200 OK`: 重新生成成功
- `400 Bad Request`: 请求参数错误
- `500 Internal Server Error`: 服务器内部错误

---

## 响应字段说明

### OCR 结果 (ocr_result)

| 字段 | 类型 | 说明 |
|------|------|------|
| text | string | OCR 识别的完整文本 |
| confidence | float | 整体置信度（0-100） |
| language | string | 检测到的语言 |
| engine | string | 使用的 OCR 引擎 |
| text_blocks | array | 文本块列表（包含位置信息） |

### 结构化结果 (structured_result)

| 字段 | 类型 | 说明 |
|------|------|------|
| structured_data | object | 结构化数据 |
| structured_data.fields | object | 提取的字段字典 |
| structured_data.fields[field_name].value | any | 字段值 |
| structured_data.fields[field_name].confidence | float | 字段置信度（0-100） |
| structured_data.fields[field_name].source | string | 数据来源（ocr/nlp/llm/manual） |
| structured_data.fields[field_name].needs_validation | boolean | 是否需要人工校验 |
| structured_data.validation_list | array | 需要校验的字段名列表 |
| structured_data.coverage | float | 字段覆盖率（0-100） |
| raw_ocr | object | 原始 OCR 结果 |
| cleaned_text | string | 清理后的文本 |
| structure_config | string | 使用的结构化配置名称 |
| entities | array | NLP 识别的实体列表 |

---

## 错误处理

所有接口在发生错误时都会返回标准的错误响应：

```json
{
  "detail": "错误描述信息"
}
```

常见错误码：

- `400 Bad Request`: 请求参数错误、文件格式不支持、预处理失败等
- `404 Not Found`: 接口不存在
- `500 Internal Server Error`: 服务器内部错误、OCR 识别失败、LLM 调用失败等

---

## 速率限制

当前版本未实现速率限制，但建议：

- 单文件处理：避免并发请求过多
- 批量处理：建议每次不超过 50 个文件
- 大文件：PDF 文件建议小于 50MB

---

## 最佳实践

1. **错误处理**: 始终检查响应状态码和错误信息
2. **超时设置**: 设置合理的请求超时时间（建议 60 秒）
3. **文件大小**: 单文件建议小于 10MB，PDF 建议小于 50MB
4. **批量处理**: 大量文件建议分批处理
5. **保存文件**: 生产环境建议设置 `save_files=true` 以便后续查看

---

## 完整示例

### Python 完整示例

```python
import requests
import json
from pathlib import Path

class OCRClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def health_check(self):
        """健康检查"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def process_image(self, image_path, save_files=True):
        """处理单张图片"""
        url = f"{self.base_url}/ocr"
        with open(image_path, "rb") as f:
            files = {"file": f}
            data = {"save_files": save_files}
            response = requests.post(url, files=files, data=data, timeout=60)
            response.raise_for_status()
            return response.json()
    
    def process_pdf(self, pdf_path, save_files=True):
        """处理 PDF 文件"""
        return self.process_image(pdf_path, save_files)
    
    def batch_process(self, file_paths, save_files=True):
        """批量处理"""
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
        """重新生成输出文件"""
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

# 使用示例
if __name__ == "__main__":
    client = OCRClient()
    
    # 健康检查
    health = client.health_check()
    print(f"服务状态: {health['status']}")
    
    # 处理单张图片
    result = client.process_image("invoice.jpg")
    print(f"识别结果: {result['result']['ocr_result']['text'][:100]}...")
    
    # 批量处理
    files = ["file1.jpg", "file2.pdf", "file3.png"]
    batch_result = client.batch_process(files)
    print(f"批量处理: 成功 {batch_result['successful']}, 失败 {batch_result['failed']}")
```

### JavaScript/TypeScript 示例

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
      throw new Error(`请求失败: ${response.statusText}`);
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
      throw new Error(`请求失败: ${response.statusText}`);
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
      throw new Error(`请求失败: ${response.statusText}`);
    }
    
    return await response.json();
  }
}

// 使用示例
const client = new OCRClient();

// 处理文件
const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
fileInput.addEventListener('change', async (e) => {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (file) {
    try {
      const result = await client.processImage(file);
      console.log("识别结果:", result);
    } catch (error) {
      console.error("处理失败:", error);
    }
  }
});
```

---

## 更多信息

- 完整的 API 文档（Swagger UI）: `http://localhost:8000/docs`
- ReDoc 文档: `http://localhost:8000/redoc`

