# 测试快速开始

## 快速运行

### 1. 安装测试依赖

```bash
pip install -r requirements-test.txt
```

### 2. 运行所有测试

```bash
pytest
```

### 3. 运行特定测试

```bash
# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 运行特定文件
pytest tests/unit/test_schemas.py

# 运行特定测试函数
pytest tests/unit/test_schemas.py::TestFieldConfidence::test_valid_field_confidence
```

### 4. 查看覆盖率

```bash
pytest --cov=. --cov-report=html
```

然后打开 `htmlcov/index.html` 查看覆盖率报告。

## 测试结构

```
tests/
├── conftest.py              # 共享的 fixtures
├── unit/                    # 单元测试
│   ├── test_schemas.py      # Schema 验证测试
│   ├── test_output_generator.py
│   ├── test_nlp_entity.py
│   └── test_ocr.py
└── integration/             # 集成测试
    └── test_api.py
```

## 测试标记

使用标记来分类测试：

```bash
# 只运行单元测试
pytest -m unit

# 排除慢速测试
pytest -m "not slow"

# 排除需要API密钥的测试
pytest -m "not requires_api"
```

## 编写新测试

### 基本测试示例

```python
import pytest

def test_example():
    # Arrange
    input_value = "test"
    
    # Act
    result = function_under_test(input_value)
    
    # Assert
    assert result == expected_value
```

### 使用 Fixtures

```python
def test_with_fixture(sample_image):
    result = process_image(sample_image)
    assert result is not None
```

### 使用 Mock

```python
from unittest.mock import patch

@patch('module.external_api')
def test_with_mock(mock_api):
    mock_api.return_value = {"result": "success"}
    result = function_using_api()
    assert result == expected
```

## 常见问题

### Q: 测试失败怎么办？

A: 查看详细的错误信息：
```bash
pytest -v --tb=long
```

### Q: 如何跳过某些测试？

A: 使用 `@pytest.mark.skip`：
```python
@pytest.mark.skip(reason="需要真实API密钥")
def test_requires_api():
    pass
```

### Q: 如何并行运行测试？

A: 使用 `pytest-xdist`：
```bash
pytest -n auto
```

## 更多信息

详细文档请参考：[测试指南](../docs/TESTING.md)

