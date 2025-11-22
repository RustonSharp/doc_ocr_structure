# OCR 与文本结构化一体化工具

## 功能特性

- ✅ 支持单张图片（JPG/PNG）和 PDF 文件
- ✅ 多 OCR 引擎支持（pytesseract、Google Cloud Vision）
- ✅ 自动图像预处理（倾斜校正、去噪、水印抑制）
- ✅ NLP 实体识别（日期、金额、手机号等）
- ✅ LLM 智能结构化提取
- ✅ 字段置信度评估（0-100）
- ✅ 待校验字段清单生成
- ✅ 可视化界面修正功能
- ✅ 批量处理支持

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 安装 spaCy 中文模型（可选，用于 NLP 实体识别）

```bash
python -m spacy download zh_core_web_sm
```

如果没有安装中文模型，系统会自动使用正则表达式进行实体识别。

### 3. 配置环境变量

创建 `.env` 文件并配置：

```env
# OpenAI API（如果使用 OpenAI）
OPENAI_API_KEY=your_openai_api_key

# Google Gemini API（如果使用 Google）
GEMINI_API_KEY=your_gemini_api_key
```

### 4. 启动后端服务

```bash
python main.py
```

服务将在 `http://localhost:8000` 启动。

### 5. 访问前端界面

有两种方式：

#### 方式一：使用 HTTP 服务器（推荐）

```bash
# 在项目根目录下运行
cd frontend
python -m http.server 8080
```

然后访问：`http://localhost:8080`

#### 方式二：直接打开 HTML 文件

直接打开 `frontend/index.html`，但需要确保：
- 后端服务已启动
- 浏览器允许跨域请求（可能需要配置）

**注意**：如果直接打开 HTML 文件（file:// 协议），可能会遇到 CORS 错误。建议使用方式一。

## API 接口

### 快速参考

- **健康检查**: `GET /health`
- **OCR 处理**: `POST /ocr`
- **批量处理**: `POST /batch`
- **重新生成**: `POST /regenerate`

### API 文档

启动服务后，访问以下地址查看完整文档：

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

详细 API 文档请参考：[docs/API_CN.md](docs/API_CN.md)

## 输出文件

处理完成后，如果设置了 `save_files=true`，会在 `output/` 目录下生成：

- `{filename}_ocr_raw_text.txt` - OCR 原始文本
- `{filename}_validation_list.csv` - 待校验字段清单
- `{filename}_structured.json` - 结构化 JSON 结果

## 配置文件

详细配置说明请参考：[docs/CONFIGURATION_CN.md](docs/CONFIGURATION_CN.md)

### 快速参考

- **OCR 配置**: `configs/ocr.json` - OCR 引擎配置
- **LLM 配置**: `configs/llms/init.json` - LLM 服务配置
- **NLP 配置**: `configs/nlp.json` - NLP 处理配置
- **结构化配置**: `configs/structures/origin/` - 字段提取规则

## 常见问题

### 1. "Failed to fetch" 错误

**原因**：
- 后端服务未启动
- 前端使用 file:// 协议打开（CORS 限制）
- 网络连接问题

**解决方案**：
1. 确保后端服务已启动：`python main.py`
2. 使用 HTTP 服务器访问前端：`python -m http.server 8080`
3. 检查浏览器控制台的详细错误信息

### 2. PDF 处理失败

**原因**：
- 未安装 PDF 处理库

**解决方案**：
```bash
pip install pdf2image PyMuPDF
# Windows 还需要安装 poppler
# 下载地址：https://github.com/oschwartz10612/poppler-windows/releases
```

### 3. spaCy 模型未找到

**原因**：
- 未下载中文模型

**解决方案**：
```bash
python -m spacy download zh_core_web_sm
```

或者系统会自动使用正则表达式进行实体识别。

### 4. Google Cloud Vision 认证失败

**原因**：
- 凭证文件路径不正确
- 凭证文件无效

**解决方案**：
1. 检查 `configs/ocr.json` 中的 `credentials_path`
2. 确保 `credentials/google_vision.json` 文件存在且有效

## 项目结构

```
doc_ocr/
├── main.py                 # FastAPI 主服务
├── ocr.py                  # OCR 引擎管理
├── structure.py            # 结构化处理
├── llm.py                  # LLM 服务
├── pdf_processor.py        # PDF 处理
├── nlp_entity.py           # NLP 实体识别
├── output_generator.py     # 输出文件生成
├── schemas.py              # Pydantic Schema
├── pre_preocess.py         # 图像预处理
├── configs/                # 配置文件目录
│   ├── ocr.json
│   ├── nlp.json
│   └── llms/
├── frontend/               # 前端文件
│   ├── index.html
│   ├── app.js
│   └── styles.css
└── output/                # 输出文件目录（自动创建）
```

## 集成指南

### Django 集成

详细集成步骤请参考：[docs/INTEGRATION_CN.md#django-集成](docs/INTEGRATION_CN.md#django-集成)

快速开始：

```python
from utils.ocr_client import ocr_client

# 处理文件
result = ocr_client.process_image(uploaded_file)
structured_data = result['result']['structured_result']['structured_data']
```

### 其他框架

- **Flask**: [docs/INTEGRATION_CN.md#flask-集成](docs/INTEGRATION_CN.md#flask-集成)
- **FastAPI**: [docs/INTEGRATION_CN.md#fastapi-集成](docs/INTEGRATION_CN.md#fastapi-集成)
- **独立脚本**: [docs/INTEGRATION_CN.md#独立-python-脚本](docs/INTEGRATION_CN.md#独立-python-脚本)

完整集成文档：[docs/INTEGRATION_CN.md](docs/INTEGRATION_CN.md)

## 开发说明

- 所有功能通过函数/类方法暴露
- 配置通过 JSON 文件传入，避免硬编码
- 使用 Pydantic 定义输出 Schema
- 代码结构清晰，易于维护和扩展

## 文档索引

### 中文文档

- [API 详细文档](docs/API_CN.md) - 完整的 API 接口说明和示例
- [配置文档](docs/CONFIGURATION_CN.md) - 所有配置文件的详细说明
- [集成指南](docs/INTEGRATION_CN.md) - 集成到不同项目的详细案例

### English Documentation

- [API Documentation](docs/API.md) - Complete API interface documentation and examples
- [Configuration Documentation](docs/CONFIGURATION.md) - Detailed documentation for all configuration files
- [Integration Guide](docs/INTEGRATION.md) - Detailed cases for integrating into different projects

## 许可证

MIT License

