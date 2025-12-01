# 单元测试方案

本文档提供了完整的单元测试方案，帮助确保代码质量和稳定性。

## 测试框架选择

### 核心测试框架
- **pytest** - Python 测试框架（推荐）
- **pytest-asyncio** - 异步测试支持
- **pytest-cov** - 代码覆盖率
- **pytest-mock** - Mock 支持

### Mock 和 Fixture
- **unittest.mock** - 标准库 Mock
- **pytest-mock** - pytest Mock 集成
- **responses** - HTTP 请求 Mock

### 测试数据
- **faker** - 生成测试数据
- **pytest-fixtures** - 测试夹具

## 安装测试依赖

创建 `requirements-test.txt`：

```bash
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
pytest-xdist>=3.3.0  # 并行测试
responses>=0.23.0
faker>=19.0.0
httpx>=0.24.0  # 用于 FastAPI 测试客户端
```

安装：
```bash
pip install -r requirements-test.txt
```

## 测试目录结构

```
doc_ocr/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # pytest 配置和共享 fixtures
│   ├── unit/                    # 单元测试
│   │   ├── __init__.py
│   │   ├── test_ocr.py
│   │   ├── test_structure.py
│   │   ├── test_llm.py
│   │   ├── test_pdf_processor.py
│   │   ├── test_nlp_entity.py
│   │   ├── test_preprocess.py
│   │   ├── test_output_generator.py
│   │   ├── test_schemas.py
│   │   └── test_logging_config.py
│   ├── integration/             # 集成测试
│   │   ├── __init__.py
│   │   ├── test_api.py
│   │   └── test_end_to_end.py
│   ├── fixtures/                # 测试数据
│   │   ├── images/
│   │   ├── pdfs/
│   │   ├── configs/
│   │   └── responses/
│   └── utils/                   # 测试工具
│       ├── __init__.py
│       └── helpers.py
├── pytest.ini                   # pytest 配置文件
└── .coveragerc                  # 覆盖率配置
```

## 配置文件

### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --tb=short
    --cov=.
    --cov-report=html
    --cov-report=term-missing
    --cov-exclude=tests/*
    --cov-exclude=__pycache__/*
    --cov-exclude=*.pyc
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
    requires_api: Tests that require external API keys
    requires_ocr: Tests that require OCR engines
asyncio_mode = auto
```

### .coveragerc

```ini
[run]
source = .
omit = 
    tests/*
    */__pycache__/*
    */venv/*
    */env/*
    */site-packages/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
```

## 测试用例设计原则

### 1. 单元测试
- **独立性**：每个测试应该独立，不依赖其他测试
- **可重复性**：测试结果应该一致
- **快速执行**：单元测试应该快速完成
- **Mock 外部依赖**：OCR引擎、LLM API等

### 2. 集成测试
- 测试模块间的协作
- 测试完整的业务流程
- 使用真实的配置文件

### 3. 测试覆盖率目标
- **整体覆盖率**：≥80%
- **核心模块覆盖率**：≥90%
- **工具函数覆盖率**：100%

## 各模块测试重点

### OCR 模块 (test_ocr.py)
- ✅ OCR引擎管理器初始化
- ✅ 引擎切换功能
- ✅ 配置文件加载和验证
- ✅ 路径解析功能
- ✅ Mock OCR 处理结果

### 结构化处理 (test_structure.py)
- ✅ 文本清理功能
- ✅ 字段置信度计算
- ✅ 结构化数据构建
- ✅ NLP配置加载
- ✅ 覆盖率计算

### LLM 服务 (test_llm.py)
- ✅ LLM服务初始化
- ✅ 不同Provider支持
- ✅ JSON解析和清理
- ✅ Prompt构建
- ✅ Mock LLM响应

### PDF 处理 (test_pdf_processor.py)
- ✅ PDF文件检测
- ✅ 页面提取
- ✅ DPI设置
- ✅ 错误处理

### NLP 实体识别 (test_nlp_entity.py)
- ✅ 实体识别器初始化
- ✅ 日期提取
- ✅ 金额提取
- ✅ 手机号提取
- ✅ 实体去重

### 图像预处理 (test_preprocess.py)
- ✅ 倾斜校正
- ✅ 图像转换
- ✅ 参数处理

### 输出生成器 (test_output_generator.py)
- ✅ 文件生成
- ✅ 路径处理
- ✅ CSV格式
- ✅ JSON格式

### Schema 验证 (test_schemas.py)
- ✅ Pydantic模型验证
- ✅ 字段约束
- ✅ 默认值

### API 端点 (test_api.py)
- ✅ 健康检查
- ✅ OCR处理接口
- ✅ 批量处理接口
- ✅ 错误处理
- ✅ 请求验证

## 运行测试

### 运行所有测试
```bash
pytest
```

### 运行特定目录
```bash
pytest tests/unit/
pytest tests/integration/
```

### 运行特定文件
```bash
pytest tests/unit/test_ocr.py
```

### 运行特定测试
```bash
pytest tests/unit/test_ocr.py::test_ocr_engine_initialization
```

### 运行并查看覆盖率
```bash
pytest --cov=. --cov-report=html
```

### 并行运行测试
```bash
pytest -n auto
```

### 只运行单元测试（排除集成测试）
```bash
pytest -m unit
```

### 运行快速测试（排除慢速测试）
```bash
pytest -m "not slow"
```

## CI/CD 集成

### GitHub Actions 示例

创建 `.github/workflows/tests.yml`：

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run tests
      run: pytest --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## 测试最佳实践

### 1. 命名约定
- 测试文件：`test_*.py`
- 测试类：`Test*`
- 测试函数：`test_*`
- Fixture：描述性名称

### 2. 测试结构（AAA模式）
```python
def test_example():
    # Arrange - 准备测试数据
    data = {"key": "value"}
    
    # Act - 执行被测试的功能
    result = function_under_test(data)
    
    # Assert - 验证结果
    assert result == expected
```

### 3. Fixture 使用
```python
@pytest.fixture
def sample_image():
    # 创建测试图片
    return create_test_image()

def test_with_fixture(sample_image):
    result = process_image(sample_image)
    assert result is not None
```

### 4. Mock 外部依赖
```python
@patch('module.external_api')
def test_with_mock(mock_api):
    mock_api.return_value = {"result": "success"}
    result = function_using_api()
    assert result == expected
```

### 5. 参数化测试
```python
@pytest.mark.parametrize("input,expected", [
    ("test1", "result1"),
    ("test2", "result2"),
])
def test_multiple_cases(input, expected):
    assert function(input) == expected
```

### 6. 异常测试
```python
def test_exception():
    with pytest.raises(ValueError, match="error message"):
        function_that_raises()
```

## 持续改进

### 测试指标
- 代码覆盖率
- 测试执行时间
- 测试通过率
- 测试稳定性

### 定期审查
- 检查测试覆盖率报告
- 审查失败的测试
- 优化慢速测试
- 补充缺失的测试用例

## 相关资源

- [pytest 文档](https://docs.pytest.org/)
- [pytest-asyncio 文档](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov 文档](https://pytest-cov.readthedocs.io/)
- [unittest.mock 文档](https://docs.python.org/3/library/unittest.mock.html)

