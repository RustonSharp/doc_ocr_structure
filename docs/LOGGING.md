# 日志系统使用指南

本项目已集成统一的日志管理系统，便于问题追踪和性能分析。

## 日志功能特性

### 1. 统一日志格式
- 所有日志都采用统一的格式，包含时间戳、模块名、日志级别和详细信息
- 支持详细格式（包含文件名、行号、函数名）和标准格式两种模式

### 2. 性能分析
- 自动记录各个操作的执行时间
- 独立的性能日志文件，方便性能分析
- 支持上下文管理器装饰器，轻松记录函数执行时间

### 3. 问题追踪
- 详细记录异常堆栈信息
- 包含上下文信息（文件名、参数、状态等）
- 错误日志单独记录，便于快速定位问题

### 4. 日志文件管理
- 按日期自动轮转日志文件
- 应用日志保留30天，错误日志保留90天
- 日志文件自动压缩和管理

## 日志文件位置

所有日志文件保存在 `logs/` 目录下：

- `logs/app.log` - 应用主日志（所有级别的日志）
- `logs/error.log` - 错误日志（仅ERROR及以上级别）
- `logs/performance.log` - 性能日志（性能相关日志）

## 配置日志系统

### 环境变量配置

可以通过环境变量配置日志系统：

```bash
# 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
export LOG_LEVEL=INFO

# 是否记录到文件 (true/false)
export LOG_TO_FILE=true

# 是否输出到控制台 (true/false)
export LOG_TO_CONSOLE=true

# 是否使用详细格式 (true/false)
export LOG_DETAILED_FORMAT=false
```

### 代码中配置

在代码中也可以动态配置日志系统：

```python
from logging_config import setup_logging

# 配置日志
setup_logging(
    log_level="INFO",        # 日志级别
    log_to_file=True,        # 记录到文件
    log_to_console=True,     # 输出到控制台
    detailed_format=False    # 是否使用详细格式
)
```

## 使用日志记录器

### 基本使用

```python
from logging_config import get_logger

# 获取日志记录器（通常使用模块名）
logger = get_logger(__name__)

# 记录不同级别的日志
logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")
```

### 记录带上下文的信息

```python
logger.info(
    "处理文件",
    extra={"context": {
        "filename": "test.pdf",
        "file_size": 1024,
        "status": "processing"
    }}
)
```

### 记录异常

```python
from logging_config import log_exception

try:
    # 可能出错的代码
    process_file()
except Exception as e:
    log_exception(
        logger,
        "处理文件失败",
        extra_context={"filename": "test.pdf"}
    )
```

## 性能日志

### 使用上下文管理器

```python
from logging_config import log_performance

# 自动记录执行时间
with log_performance("OCR处理", logger, {"engine": "pytesseract"}):
    result = ocr_process(image_data)
```

### 使用装饰器

```python
from logging_config import log_function_performance

@log_function_performance("OCR识别", log_args=True)
def process_image(image_data):
    # 函数实现
    return result
```

### 异步函数支持

装饰器自动支持异步函数：

```python
@log_function_performance("异步OCR处理")
async def async_process_image(image_data):
    # 异步函数实现
    return await ocr_process(image_data)
```

## 日志级别说明

- **DEBUG**: 详细的调试信息，通常只在开发时使用
- **INFO**: 一般信息，记录程序正常运行的关键步骤
- **WARNING**: 警告信息，程序可以继续运行，但需要注意
- **ERROR**: 错误信息，程序遇到错误但仍可继续
- **CRITICAL**: 严重错误，可能导致程序无法继续运行

## 日志记录的模块

以下模块已集成日志记录：

1. **main.py** - API请求、启动流程、文件处理
2. **ocr.py** - OCR引擎切换、OCR处理过程、性能分析
3. **structure.py** - 结构化处理、NLP实体识别
4. **llm.py** - LLM调用、响应时间、错误追踪
5. **pdf_processor.py** - PDF处理、页面解析
6. **nlp_entity.py** - 实体识别、spaCy模型加载
7. **pre_preocess.py** - 图像预处理、倾斜校正

## 查看和分析日志

### 查看应用日志

```bash
# 查看最新的日志
tail -f logs/app.log

# 查看错误日志
tail -f logs/error.log

# 查看性能日志
tail -f logs/performance.log
```

### 搜索特定内容

```bash
# 搜索错误
grep "ERROR" logs/app.log

# 搜索特定文件处理
grep "test.pdf" logs/app.log

# 搜索性能信息
grep "耗时" logs/performance.log
```

### 分析性能

性能日志包含执行时间信息，可以使用工具进行分析：

```bash
# 查看所有性能记录
grep "耗时" logs/performance.log | awk '{print $NF}'

# 找出最慢的操作
grep "耗时" logs/performance.log | sort -k2 -n -r | head -10
```

## 最佳实践

### 1. 选择合适的日志级别

- 使用 DEBUG 记录详细的调试信息
- 使用 INFO 记录关键业务步骤
- 使用 WARNING 记录潜在问题
- 使用 ERROR 记录错误情况

### 2. 包含足够的上下文信息

```python
# 好的日志记录
logger.info(
    "OCR处理完成",
    extra={"context": {
        "engine": "pytesseract",
        "text_length": 1024,
        "confidence": 95.5,
        "processing_time": 1.23
    }}
)

# 不好的日志记录
logger.info("处理完成")  # 缺少上下文信息
```

### 3. 使用性能日志监控

对于耗时操作，始终使用性能日志：

```python
# 自动记录执行时间
with log_performance("关键操作", logger, {"operation_id": "123"}):
    perform_critical_operation()
```

### 4. 避免记录敏感信息

不要在日志中记录：
- 密码、API密钥
- 完整的用户个人隐私信息
- 敏感的财务数据

### 5. 及时清理旧日志

虽然日志会自动轮转，但建议定期检查和清理过旧的日志文件。

## 故障排查示例

### 查看API请求日志

```bash
# 查看所有API请求
grep "请求开始\|请求完成" logs/app.log

# 查看失败的请求
grep "请求失败" logs/app.log

# 查看慢请求（超过5秒）
grep "请求完成" logs/app.log | grep -E "耗时: [5-9]\.[0-9]+秒|耗时: [0-9]{2,}\.[0-9]+秒"
```

### 查看OCR处理问题

```bash
# 查看OCR处理日志
grep "OCR处理" logs/app.log

# 查看OCR错误
grep "OCR.*失败" logs/app.log

# 查看OCR性能
grep "OCR处理" logs/performance.log
```

### 查看LLM调用问题

```bash
# 查看LLM调用日志
grep "LLM" logs/app.log

# 查看LLM错误
grep "LLM.*失败" logs/app.log

# 查看LLM响应时间
grep "LLM" logs/performance.log | grep "耗时"
```

## 常见问题

### Q: 日志文件太大怎么办？

A: 日志系统已配置按日期自动轮转，旧日志会自动压缩。如果磁盘空间不足，可以手动删除 `logs/` 目录下的旧日志文件。

### Q: 如何只记录错误日志？

A: 设置环境变量 `LOG_LEVEL=ERROR`，或者在代码中调用 `setup_logging(log_level="ERROR")`。

### Q: 如何禁用文件日志，只输出到控制台？

A: 设置环境变量 `LOG_TO_FILE=false`，或者在代码中调用 `setup_logging(log_to_file=False)`。

### Q: 日志文件在哪里？

A: 所有日志文件保存在项目根目录下的 `logs/` 目录中。该目录会在首次运行应用时自动创建。

### Q: 如何查看特定时间段的日志？

A: 由于日志按日期轮转，每天的日志文件会有时间戳。可以使用 `grep` 结合时间戳搜索：

```bash
grep "2024-01-01" logs/app.log.2024-01-01
```

## 相关文件

- `logging_config.py` - 日志配置模块
- `logs/` - 日志文件目录
- `.gitignore` - 已配置忽略日志文件

