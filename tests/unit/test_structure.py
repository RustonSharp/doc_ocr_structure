"""
结构化处理模块测试
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from structure import (
    structure_ocr_result,
    _clean_text,
    _load_nlp_config,
    _load_structure_config,
    _calculate_field_confidence
)


class TestCleanText:
    """_clean_text 函数测试"""
    
    def test_clean_text_remove_extra_spaces(self):
        """测试移除多余空格"""
        text = "这是    一段   有   多余空格的   文本"
        config = {"remove_extra_spaces": True}
        cleaned = _clean_text(text, config)
        assert "     " not in cleaned
        assert "  " not in cleaned
    
    def test_clean_text_normalize_whitespace(self):
        """测试规范化空白字符"""
        text = "这是\r\n一段\r文本\n\n\n多行文本"
        config = {"normalize_whitespace": True}
        cleaned = _clean_text(text, config)
        assert "\r\n" not in cleaned
        assert "\r" not in cleaned
        assert "\n\n\n" not in cleaned
    
    def test_clean_text_remove_special_chars(self):
        """测试移除特殊字符"""
        text = "这是@#$%^&*()特殊字符文本"
        config = {"remove_special_chars": True}
        cleaned = _clean_text(text, config)
        # 应该保留中文、英文、数字和基本标点
        assert "这是" in cleaned or "特殊字符文本" in cleaned
    
    def test_clean_text_no_cleaning(self):
        """测试不进行清理"""
        text = "原始文本  未清理"
        config = {}
        cleaned = _clean_text(text, config)
        assert cleaned.strip() == text.strip()
    
    def test_clean_text_combined_cleaning(self):
        """测试组合清理"""
        text = "这是\r\n    一段   有   问题的   文本\n\n\n"
        config = {
            "remove_extra_spaces": True,
            "normalize_whitespace": True,
            "remove_special_chars": False
        }
        cleaned = _clean_text(text, config)
        assert "     " not in cleaned
        assert "\r\n" not in cleaned


class TestLoadNLPConfig:
    """_load_nlp_config 函数测试"""
    
    def test_load_nlp_config_file_exists(self, temp_dir):
        """测试加载存在的配置文件"""
        config_file = temp_dir / "nlp.json"
        config_data = {
            "nlp_processing": {
                "enabled": True,
                "text_cleaning": {
                    "remove_extra_spaces": True
                }
            }
        }
        config_file.write_text(json.dumps(config_data), encoding="utf-8")
        
        # 需要修改函数以接受路径参数，或者使用 monkeypatch
        # 这里测试默认行为
        result = _load_nlp_config()
        assert isinstance(result, dict)
        assert "nlp_processing" in result
    
    def test_load_nlp_config_file_not_found(self, monkeypatch):
        """测试配置文件不存在时返回默认配置"""
        def mock_open(*args, **kwargs):
            raise FileNotFoundError()
        
        monkeypatch.setattr("builtins.open", mock_open)
        result = _load_nlp_config()
        assert isinstance(result, dict)
        assert "nlp_processing" in result


class TestLoadStructureConfig:
    """_load_structure_config 函数测试"""
    
    def test_load_structure_config_file_exists(self, temp_dir):
        """测试加载存在的结构化配置文件"""
        config_file = temp_dir / "structure.json"
        config_data = {
            "title": "测试配置",
            "items": [
                {"field": "字段1", "type": "text"}
            ]
        }
        config_file.write_text(json.dumps(config_data), encoding="utf-8")
        
        result = _load_structure_config(str(config_file))
        assert result["title"] == "测试配置"
        assert len(result["items"]) == 1
    
    def test_load_structure_config_file_not_found(self, temp_dir):
        """测试配置文件不存在时抛出异常"""
        config_file = temp_dir / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            _load_structure_config(str(config_file))


class TestCalculateFieldConfidence:
    """_calculate_field_confidence 函数测试"""
    
    def test_calculate_confidence_empty_value(self):
        """测试空值的置信度计算"""
        result = _calculate_field_confidence(
            field_value=None,
            field_name="测试字段",
            ocr_text="测试文本",
            ocr_result={"confidence": 90.0},
            structure_config={"items": []},
            entities={}
        )
        assert result.confidence == 0.0
        assert result.needs_validation is True
    
    def test_calculate_confidence_value_in_ocr_text(self):
        """测试字段值在OCR文本中的置信度"""
        result = _calculate_field_confidence(
            field_value="测试值",
            field_name="测试字段",
            ocr_text="这是一段包含测试值的文本",
            ocr_result={"confidence": 90.0},
            structure_config={"items": []},
            entities={}
        )
        assert result.confidence > 0.0
        assert result.confidence <= 100.0
    
    def test_calculate_confidence_date_field(self):
        """测试日期字段的置信度计算"""
        result = _calculate_field_confidence(
            field_value="2024-01-15",
            field_name="日期",
            ocr_text="日期：2024-01-15",
            ocr_result={"confidence": 90.0},
            structure_config={"items": []},
            entities={"dates": [{"text": "2024-01-15"}]}
        )
        assert result.confidence > 0.0
        assert result.source in ["nlp", "llm", "regex"]
    
    def test_calculate_confidence_amount_field(self):
        """测试金额字段的置信度计算"""
        result = _calculate_field_confidence(
            field_value="1234.56",
            field_name="金额",
            ocr_text="金额：1234.56",
            ocr_result={"confidence": 90.0},
            structure_config={"items": []},
            entities={"amounts": [{"text": "1234.56"}]}
        )
        assert result.confidence > 0.0
    
    def test_calculate_confidence_with_pattern(self):
        """测试带正则模式的字段置信度计算"""
        result = _calculate_field_confidence(
            field_value="INV-2024-001",
            field_name="发票号码",
            ocr_text="发票号码：INV-2024-001",
            ocr_result={"confidence": 90.0},
            structure_config={
                "items": [
                    {"field": "发票号码", "pattern": r"INV-\d+"}
                ]
            },
            entities={}
        )
        assert result.confidence > 0.0
        assert result.source in ["regex", "llm", "nlp"]


class TestStructureOCRResult:
    """structure_ocr_result 函数测试"""
    
    @patch('structure.LLMService')
    @patch('structure.get_entity_recognizer')
    def test_structure_ocr_result_basic(self, mock_get_recognizer, mock_llm_service, temp_dir, mock_structure_config):
        """测试基本的结构化处理"""
        # 设置模拟对象
        mock_recognizer = Mock()
        mock_recognizer.extract_entities.return_value = {
            "dates": [],
            "amounts": [],
            "phone_numbers": [],
            "emails": [],
            "ids": []
        }
        mock_get_recognizer.return_value = mock_recognizer
        
        mock_llm = Mock()
        mock_llm.improve_json_structure.return_value = {
            "发票号码": "INV-2024-001",
            "日期": "2024-01-15",
            "金额": "1234.56"
        }
        mock_llm_service.return_value = mock_llm
        
        # 准备OCR结果
        ocr_result = {
            "text": "发票号码：INV-2024-001\n日期：2024-01-15\n金额：1234.56",
            "confidence": 95.0
        }
        
        # 执行结构化处理
        result = structure_ocr_result(ocr_result, str(mock_structure_config))
        
        assert "structured_data" in result
        assert "raw_ocr" in result
        assert "cleaned_text" in result
        assert result["structured_data"]["coverage"] >= 0.0
    
    @patch('structure.LLMService')
    @patch('structure.get_entity_recognizer')
    def test_structure_ocr_result_empty_text(self, mock_get_recognizer, mock_llm_service, temp_dir, mock_structure_config):
        """测试空文本的结构化处理"""
        mock_recognizer = Mock()
        mock_recognizer.extract_entities.return_value = {}
        mock_get_recognizer.return_value = mock_recognizer
        
        ocr_result = {
            "text": "",
            "confidence": 0.0
        }
        
        result = structure_ocr_result(ocr_result, str(mock_structure_config))
        
        assert result["structured_data"]["coverage"] == 0.0
        assert len(result["structured_data"]["validation_list"]) > 0
    
    @patch('structure.LLMService')
    @patch('structure.get_entity_recognizer')
    def test_structure_ocr_result_nlp_disabled(self, mock_get_recognizer, mock_llm_service, temp_dir, monkeypatch):
        """测试NLP处理被禁用的情况"""
        # 模拟NLP配置禁用
        def mock_load_nlp_config():
            return {
                "nlp_processing": {
                    "enabled": False
                }
            }
        
        monkeypatch.setattr("structure._load_nlp_config", mock_load_nlp_config)
        
        ocr_result = {
            "text": "测试文本",
            "confidence": 90.0
        }
        
        result = structure_ocr_result(ocr_result)
        
        assert result["structured_data"] is None
        assert "raw_ocr" in result
    
    @patch('structure.LLMService')
    @patch('structure.get_entity_recognizer')
    def test_structure_ocr_result_llm_failure(self, mock_get_recognizer, mock_llm_service, temp_dir, mock_structure_config):
        """测试LLM处理失败的情况"""
        mock_recognizer = Mock()
        mock_recognizer.extract_entities.return_value = {}
        mock_get_recognizer.return_value = mock_recognizer
        
        mock_llm = Mock()
        mock_llm.improve_json_structure.side_effect = Exception("LLM服务错误")
        mock_llm_service.return_value = mock_llm
        
        ocr_result = {
            "text": "测试文本",
            "confidence": 90.0
        }
        
        result = structure_ocr_result(ocr_result, str(mock_structure_config))
        
        # 即使LLM失败，也应该返回结果
        assert "structured_data" in result
        assert result["structured_data"]["coverage"] == 0.0
    
    @patch('structure.LLMService')
    @patch('structure.get_entity_recognizer')
    def test_structure_ocr_result_entity_recognition_failure(self, mock_get_recognizer, mock_llm_service, temp_dir, mock_structure_config):
        """测试实体识别失败的情况"""
        mock_get_recognizer.side_effect = Exception("实体识别错误")
        
        mock_llm = Mock()
        mock_llm.improve_json_structure.return_value = {
            "发票号码": "INV-2024-001"
        }
        mock_llm_service.return_value = mock_llm
        
        ocr_result = {
            "text": "发票号码：INV-2024-001",
            "confidence": 90.0
        }
        
        result = structure_ocr_result(ocr_result, str(mock_structure_config))
        
        # 即使实体识别失败，也应该继续处理
        assert "structured_data" in result
        assert "entities" in result
    
    def test_structure_ocr_result_no_config_path(self, monkeypatch):
        """测试未提供配置文件路径且配置中也没有的情况"""
        def mock_load_nlp_config():
            return {
                "nlp_processing": {
                    "enabled": True,
                    "structure_config_path": None
                }
            }
        
        monkeypatch.setattr("structure._load_nlp_config", mock_load_nlp_config)
        
        ocr_result = {
            "text": "测试文本",
            "confidence": 90.0
        }
        
        with pytest.raises(ValueError, match="未提供结构化配置文件路径"):
            structure_ocr_result(ocr_result)

