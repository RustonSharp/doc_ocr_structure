# 配置文档

本文档详细说明所有配置文件的格式和选项。

## 目录结构

```
configs/
├── ocr.json                    # OCR 引擎配置
├── nlp.json                    # NLP 处理配置
├── llms/
│   └── init.json              # LLM 服务配置
├── ocr/
│   ├── custom_words.txt       # 自定义词汇（OCR 后处理）
│   ├── custom_patterns.txt    # 自定义模式（Tesseract）
│   └── README.md             # OCR 配置说明
└── structures/
    ├── template.json          # 结构化配置模板
    ├── origin/               # 原始配置文件
    ├── temp/                 # 临时配置文件
    └── new/                  # 处理后的配置文件
```

---

## OCR 配置 (`configs/ocr.json`)

配置 OCR 引擎和相关参数。

### 配置结构

```json
{
  "ocr_engines": {
    "current": "google-cloud-vision",
    "engines": {
      "pytesseract": {
        "provider": "pytesseract",
        "description": "基于 Tesseract 的本地 OCR 引擎",
        "languages": "chi_sim+eng",
        "oem": 3,
        "psm": 6,
        "custom_words_path": "configs/ocr/custom_words.txt",
        "custom_patterns_path": "configs/ocr/custom_patterns.txt"
      },
      "google-cloud-vision": {
        "provider": "google-cloud-vision",
        "description": "Google Cloud Vision API，高精度 OCR 服务",
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

### 字段说明

#### 全局配置

- `current`: 当前使用的 OCR 引擎名称（`pytesseract` 或 `google-cloud-vision`）

#### Tesseract 配置 (pytesseract)

| 字段 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| provider | string | 引擎提供者，固定为 `pytesseract` | - |
| description | string | 引擎描述 | - |
| languages | string | 识别语言，多个用 `+` 连接 | `chi_sim+eng` |
| oem | int | OCR Engine Mode (0-3) | 3 |
| psm | int | Page Segmentation Mode (0-13) | 6 |
| custom_words_path | string | 自定义词汇文件路径 | - |
| custom_patterns_path | string | 自定义模式文件路径 | - |

**PSM 模式说明**:
- `0`: 仅方向和脚本检测
- `1`: 自动页面分割，使用 OSD
- `3`: 完全自动页面分割（默认）
- `6`: 假设统一的文本块
- `11`: 稀疏文本
- `13`: 原始行，不进行页面分割

**OEM 模式说明**:
- `0`: 仅传统引擎
- `1`: 仅 LSTM 引擎
- `2`: LSTM + 传统引擎
- `3`: 默认（基于可用内容）

#### Google Cloud Vision 配置

| 字段 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| provider | string | 引擎提供者，固定为 `google-cloud-vision` | - |
| description | string | 引擎描述 | - |
| language_hints | array | 语言提示列表 | `["zh", "en"]` |
| enable_text_detection | boolean | 启用文本检测 | `true` |
| credentials_path | string | Google Cloud 凭证文件路径 | - |
| enable_post_process | boolean | 启用后处理（自定义词汇校正） | `true` |
| custom_words_path | string | 自定义词汇文件路径 | - |

### 自定义词汇文件 (`configs/ocr/custom_words.txt`)

每行一个词汇，格式：

```
原始词汇|校正后词汇
```

示例：

```
发票号码|发票号码
纳税人识别号|纳税人识别号
金额|金额
```

如果不需要校正，只写原始词汇：

```
发票号码
纳税人识别号
```

### 自定义模式文件 (`configs/ocr/custom_patterns.txt`)

Tesseract 自定义模式，每行一个模式：

```
发票号码: \d{8,12}
金额: \d+\.\d{2}
日期: \d{4}-\d{2}-\d{2}
```

---

## LLM 配置 (`configs/llms/init.json`)

配置 LLM 服务提供商和模型。

### 配置结构

```json
{
  "llm_services": {
    "current": "openai",
    "services": {
      "openai": {
        "provider": "openai",
        "description": "OpenAI GPT 模型",
        "model": "gpt-4o-mini",
        "temperature": 0.1,
        "max_tokens": 4000,
        "api_key_env": "OPENAI_API_KEY"
      },
      "google": {
        "provider": "google",
        "description": "Google Gemini 模型",
        "model": "gemini-1.5-flash",
        "temperature": 0.1,
        "max_tokens": 4000,
        "api_key_env": "GEMINI_API_KEY"
      },
      "ollama": {
        "provider": "ollama",
        "description": "本地 Ollama 模型",
        "model": "qwen2.5:7b",
        "temperature": 0.1,
        "base_url": "http://localhost:11434"
      }
    }
  }
}
```

### 字段说明

#### 全局配置

- `current`: 当前使用的 LLM 服务名称

#### OpenAI 配置

| 字段 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| provider | string | 服务提供者，固定为 `openai` | - |
| model | string | 模型名称 | `gpt-4o-mini` |
| temperature | float | 温度参数（0-2） | 0.1 |
| max_tokens | int | 最大输出 token 数 | 4000 |
| api_key_env | string | API Key 环境变量名 | `OPENAI_API_KEY` |

#### Google Gemini 配置

| 字段 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| provider | string | 服务提供者，固定为 `google` | - |
| model | string | 模型名称 | `gemini-1.5-flash` |
| temperature | float | 温度参数（0-2） | 0.1 |
| max_tokens | int | 最大输出 token 数 | 4000 |
| api_key_env | string | API Key 环境变量名 | `GEMINI_API_KEY` |

#### Ollama 配置

| 字段 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| provider | string | 服务提供者，固定为 `ollama` | - |
| model | string | 模型名称 | `qwen2.5:7b` |
| temperature | float | 温度参数（0-2） | 0.1 |
| base_url | string | Ollama 服务地址 | `http://localhost:11434` |

### 环境变量配置

在 `.env` 文件中配置 API Key：

```env
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
```

或在系统环境变量中设置。

---

## NLP 配置 (`configs/nlp.json`)

配置 NLP 处理选项和结构化配置文件路径。

### 配置结构

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

### 字段说明

| 字段 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| use_spacy | boolean | 是否使用 spaCy 进行实体识别 | `true` |
| spacy_model | string | spaCy 模型名称 | `zh_core_web_sm` |
| fallback_to_regex | boolean | spaCy 不可用时是否回退到正则表达式 | `true` |
| structure_config_path | string | 结构化配置文件目录路径 | `configs/structures/origin` |
| confidence_threshold | float | 字段置信度阈值（低于此值需要校验） | 80.0 |

---

## 结构化配置 (`configs/structures/origin/`)

定义要提取的字段规则。每个文档类型一个 JSON 文件。

### 配置模板 (`configs/structures/template.json`)

```json
{
  "title": "文档类型名称",
  "description": "文档描述",
  "items": [
    {
      "field": "字段名",
      "description": "字段描述",
      "type": "字段类型",
      "pattern": "正则表达式模式（可选）",
      "required": true,
      "validation": {
        "min_length": 0,
        "max_length": 100,
        "format": "格式要求"
      }
    }
  ]
}
```

### 字段类型

- `text`: 文本类型
- `number`: 数字类型
- `date`: 日期类型
- `金额`: 金额类型
- `小数`: 小数类型

### 配置示例：发票 (`invoice0.json`)

```json
{
  "title": "发票",
  "description": "增值税普通发票",
  "items": [
    {
      "field": "发票号码",
      "description": "发票号码",
      "type": "text",
      "pattern": "\\d{8,12}",
      "required": true
    },
    {
      "field": "开票日期",
      "description": "发票开票日期",
      "type": "date",
      "pattern": "\\d{4}-\\d{2}-\\d{2}",
      "required": true
    },
    {
      "field": "金额",
      "description": "发票金额",
      "type": "金额",
      "pattern": "\\d+\\.\\d{2}",
      "required": true
    },
    {
      "field": "纳税人识别号",
      "description": "纳税人识别号",
      "type": "text",
      "pattern": "[A-Z0-9]{15,20}",
      "required": false
    }
  ]
}
```

### 配置示例：简历 (`resume0.json`)

```json
{
  "title": "简历",
  "description": "个人简历",
  "items": [
    {
      "field": "姓名",
      "description": "候选人姓名",
      "type": "text",
      "required": true
    },
    {
      "field": "手机号",
      "description": "联系电话",
      "type": "text",
      "pattern": "1[3-9]\\d{9}",
      "required": true
    },
    {
      "field": "邮箱",
      "description": "电子邮箱",
      "type": "text",
      "pattern": "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}",
      "required": false
    },
    {
      "field": "工作年限",
      "description": "工作经验年限",
      "type": "number",
      "required": false
    }
  ]
}
```

### 配置文件管理

系统会自动管理三个目录：

- `origin/`: 原始配置文件（用户编辑）
- `temp/`: 临时配置文件（系统生成）
- `new/`: 处理后的配置文件（LLM 优化）

**工作流程**:
1. 用户在 `origin/` 中创建/编辑配置文件
2. 系统启动时检查 `origin/` 和 `temp/` 的差异
3. 如果有差异，使用 LLM 优化配置文件并保存到 `new/`
4. 处理时使用 `new/` 中的配置文件

---

## 环境变量

### `.env` 文件示例

```env
# OpenAI API Key
OPENAI_API_KEY=sk-...

# Google Gemini API Key
GEMINI_API_KEY=...

# 其他环境变量
LOG_LEVEL=INFO
```

### 系统环境变量

也可以在系统环境变量中设置：

```bash
# Linux/Mac
export OPENAI_API_KEY=sk-...
export GEMINI_API_KEY=...

# Windows
set OPENAI_API_KEY=sk-...
set GEMINI_API_KEY=...
```

---

## 配置验证

系统启动时会自动验证配置：

1. **OCR 配置**: 检查引擎配置是否正确，凭证文件是否存在
2. **LLM 配置**: 检查 API Key 是否设置
3. **结构化配置**: 检查配置文件格式是否正确

如果配置有误，系统会在启动时输出错误信息。

---

## 配置最佳实践

1. **OCR 引擎选择**:
   - 高精度需求：使用 Google Cloud Vision
   - 本地部署：使用 Tesseract
   - 成本考虑：Tesseract 免费，Google Vision 按量付费

2. **LLM 模型选择**:
   - 高精度：GPT-4 或 Gemini Pro
   - 成本优化：GPT-4o-mini 或 Gemini Flash
   - 本地部署：Ollama

3. **结构化配置**:
   - 字段描述要清晰明确
   - 正则表达式要准确
   - 合理设置 `required` 字段

4. **自定义词汇**:
   - 添加专业术语
   - 定期更新词汇表
   - 注意大小写敏感

---

## 配置更新

修改配置后，需要重启服务才能生效：

```bash
# 停止服务
# Ctrl+C 或 kill <pid>

# 重新启动
python main.py
```

某些配置（如结构化配置）会在启动时自动检查和更新。

