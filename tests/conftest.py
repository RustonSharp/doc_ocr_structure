"""
pytest 配置和共享 fixtures
"""
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest
from PIL import Image
import io


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_image():
    """创建测试图片"""
    # 创建一个简单的测试图片
    img = Image.new('RGB', (100, 100), color=(255, 255, 255))  # type: ignore[arg-type]
    return img


@pytest.fixture
def sample_image_bytes(sample_image):
    """创建测试图片字节数据"""
    buffer = io.BytesIO()
    sample_image.save(buffer, format='PNG')
    return buffer.getvalue()


@pytest.fixture
def sample_pdf_bytes():
    """创建测试PDF字节数据"""
    # 这是一个最小的PDF文件（仅用于测试）
    pdf_data = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
        b"xref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n"
        b"0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n174\n%%EOF"
    )
    return pdf_data


@pytest.fixture
def sample_text():
    """示例OCR文本"""
    return """
    发票号码：INV-2024-001
    日期：2024-01-15
    金额：￥1,234.56
    电话：13800138000
    邮箱：test@example.com
    """


@pytest.fixture
def mock_ocr_config(temp_dir):
    """创建模拟OCR配置文件"""
    config = {
        "ocr_engines": {
            "current": "pytesseract",
            "engines": {
                "pytesseract": {
                    "description": "Tesseract OCR",
                    "languages": "eng",
                    "oem": 3,
                    "psm": 6
                },
                "google-cloud-vision": {
                    "description": "Google Cloud Vision",
                    "credentials_path": "credentials/google_vision.json",
                    "language_hints": ["zh", "en"]
                }
            }
        }
    }
    
    config_path = temp_dir / "ocr.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    return config_path


@pytest.fixture
def mock_llm_config(temp_dir):
    """创建模拟LLM配置文件"""
    config = {
        "llm_services": {
            "current": "mock",
            "services": {
                "mock": {
                    "provider": "mock",
                    "model": "mock-model",
                    "temperature": 0.1
                }
            }
        }
    }
    
    config_path = temp_dir / "init.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    return config_path


@pytest.fixture
def mock_structure_config(temp_dir):
    """创建模拟结构化配置文件"""
    config = {
        "title": "发票",
        "description": "发票结构化配置",
        "items": [
            {
                "field": "发票号码",
                "description": "发票编号",
                "type": "text",
                "pattern": "INV-\\d+"
            },
            {
                "field": "日期",
                "description": "发票日期",
                "type": "date"
            },
            {
                "field": "金额",
                "description": "发票金额",
                "type": "number"
            }
        ]
    }
    
    config_path = temp_dir / "invoice.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    return config_path


@pytest.fixture
def mock_nlp_config(temp_dir):
    """创建模拟NLP配置文件"""
    config = {
        "nlp_processing": {
            "enabled": True,
            "text_cleaning": {
                "remove_extra_spaces": True,
                "normalize_whitespace": True,
                "remove_special_chars": False
            },
            "keyword_extraction": {
                "enabled": False
            },
            "structure_config_path": "configs/structures/origin/invoice0.json"
        }
    }
    
    config_path = temp_dir / "nlp.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    return config_path


@pytest.fixture
def sample_ocr_result():
    """示例OCR结果"""
    return {
        "text": "发票号码：INV-2024-001\n日期：2024-01-15\n金额：￥1,234.56",
        "confidence": 95.5,
        "language": "zh",
        "engine": "pytesseract",
        "text_blocks": [],
        "image_size": {"width": 800, "height": 600}
    }


@pytest.fixture
def sample_structured_result():
    """示例结构化结果"""
    return {
        "structured_data": {
            "fields": {
                "发票号码": {
                    "value": "INV-2024-001",
                    "confidence": 95.0,
                    "source": "regex",
                    "needs_validation": False
                },
                "日期": {
                    "value": "2024-01-15",
                    "confidence": 90.0,
                    "source": "nlp",
                    "needs_validation": False
                }
            },
            "coverage": 100.0,
            "validation_list": []
        },
        "raw_ocr": {
            "text": "发票号码：INV-2024-001\n日期：2024-01-15"
        },
        "cleaned_text": "发票号码：INV-2024-001\n日期：2024-01-15",
        "structure_config": "发票",
        "entities": {
            "dates": [{"text": "2024-01-15", "start": 10, "end": 20}],
            "amounts": []
        }
    }


@pytest.fixture
def mock_env_vars(monkeypatch):
    """设置模拟环境变量"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    return {
        "OPENAI_API_KEY": "test-openai-key",
        "GEMINI_API_KEY": "test-gemini-key"
    }


@pytest.fixture
def reset_logging():
    """重置日志配置"""
    import logging
    import logging_config
    
    # 保存原始配置
    original_handlers = logging.root.handlers[:]
    
    yield
    
    # 恢复原始配置
    logging.root.handlers = original_handlers

