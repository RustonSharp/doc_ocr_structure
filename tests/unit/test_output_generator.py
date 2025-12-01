"""
输出生成器测试
"""
import csv
import json
from pathlib import Path

import pytest

from output_generator import (
    save_ocr_raw_text,
    save_validation_list,
    save_structured_json,
    generate_output_files
)


class TestSaveOCRRawText:
    """OCR原始文本保存测试"""
    
    def test_save_ocr_raw_text(self, temp_dir):
        """测试保存OCR原始文本"""
        text = "这是OCR识别的文本内容"
        output_path = temp_dir / "ocr_raw_text.txt"
        
        save_ocr_raw_text(text, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r', encoding='utf-8') as f:
            assert f.read() == text
    
    def test_save_ocr_raw_text_creates_directory(self, temp_dir):
        """测试自动创建目录"""
        text = "测试文本"
        output_path = temp_dir / "subdir" / "ocr_raw_text.txt"
        
        save_ocr_raw_text(text, output_path)
        
        assert output_path.exists()
        assert output_path.parent.exists()


class TestSaveValidationList:
    """校验清单保存测试"""
    
    def test_save_validation_list(self, temp_dir):
        """测试保存校验清单"""
        structured_data = {
            "fields": {
                "字段1": {
                    "value": "值1",
                    "confidence": 75.0,
                    "source": "llm",
                    "needs_validation": True
                },
                "字段2": {
                    "value": "值2",
                    "confidence": 90.0,
                    "source": "nlp",
                    "needs_validation": False
                }
            },
            "validation_list": ["字段1"]
        }
        
        output_path = temp_dir / "validation_list.csv"
        save_validation_list(structured_data, output_path)
        
        assert output_path.exists()
        
        # 验证CSV内容
        with open(output_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            assert len(rows) == 2  # 表头 + 1行数据
            assert rows[0] == ["字段名", "字段值", "置信度", "数据来源", "是否需要校验"]
            assert rows[1][0] == "字段1"
            assert rows[1][2] == "75.00"
            assert rows[1][4] == "是"
    
    def test_save_validation_list_empty(self, temp_dir):
        """测试空的校验清单"""
        structured_data = {
            "fields": {},
            "validation_list": []
        }
        
        output_path = temp_dir / "validation_list.csv"
        save_validation_list(structured_data, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)
            assert len(rows) == 1  # 只有表头


class TestSaveStructuredJSON:
    """结构化JSON保存测试"""
    
    def test_save_structured_json(self, temp_dir):
        """测试保存结构化JSON"""
        result = {
            "structured_data": {
                "fields": {"field1": {"value": "value1", "confidence": 90.0}},
                "coverage": 90.0
            },
            "raw_ocr": {"text": "OCR文本"}
        }
        
        output_path = temp_dir / "structured.json"
        save_structured_json(result, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
            assert loaded == result
    
    def test_save_structured_json_preserves_chinese(self, temp_dir):
        """测试保存中文内容"""
        result = {
            "structured_data": {
                "fields": {"发票号码": {"value": "INV-001", "confidence": 90.0}}
            }
        }
        
        output_path = temp_dir / "structured.json"
        save_structured_json(result, output_path)
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "发票号码" in content


class TestGenerateOutputFiles:
    """输出文件生成测试"""
    
    def test_generate_output_files_complete(self, temp_dir):
        """测试生成所有输出文件"""
        result = {
            "raw_ocr": {
                "text": "OCR识别的文本"
            },
            "structured_data": {
                "fields": {
                    "字段1": {
                        "value": "值1",
                        "confidence": 75.0,
                        "source": "llm",
                        "needs_validation": True
                    }
                },
                "validation_list": ["字段1"]
            }
        }
        
        output_dir = temp_dir / "output"
        files = generate_output_files(result, output_dir, base_name="test")
        
        assert output_dir.exists()
        assert "ocr_raw_text" in files
        assert "validation_list" in files
        assert "structured_json" in files
        
        # 验证文件存在
        assert files["ocr_raw_text"].exists()
        assert files["validation_list"].exists()
        assert files["structured_json"].exists()
        
        # 验证文件名
        assert files["ocr_raw_text"].name == "ocr_raw_text.txt"
        assert files["validation_list"].name == "validation_list.csv"
        assert files["structured_json"].name == "test_structured.json"
    
    def test_generate_output_files_missing_ocr_text(self, temp_dir):
        """测试缺少OCR文本的情况"""
        result = {
            "structured_data": {
                "fields": {},
                "validation_list": []
            }
        }
        
        output_dir = temp_dir / "output"
        files = generate_output_files(result, output_dir, base_name="test")
        
        # OCR文本文件不应该存在
        assert "ocr_raw_text" not in files
        assert "validation_list" in files
        assert "structured_json" in files
    
    def test_generate_output_files_empty_structured_data(self, temp_dir):
        """测试空的结构化数据"""
        result = {
            "raw_ocr": {"text": "OCR文本"}
        }
        
        output_dir = temp_dir / "output"
        files = generate_output_files(result, output_dir, base_name="test")
        
        # 校验清单可能不存在，但JSON应该存在
        assert "structured_json" in files

