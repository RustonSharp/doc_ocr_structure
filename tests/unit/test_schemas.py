"""
Schema 验证测试
"""
import pytest
from pydantic import ValidationError

from schemas import (
    FieldConfidence,
    StructuredData,
    OCRResult,
    ProcessingResult,
    BatchProcessingResult
)


class TestFieldConfidence:
    """FieldConfidence 模型测试"""
    
    def test_valid_field_confidence(self):
        """测试有效的字段置信度"""
        field = FieldConfidence(
            value="test_value",
            confidence=85.5,
            source="llm",
            needs_validation=False
        )
        assert field.value == "test_value"
        assert field.confidence == 85.5
        assert field.source == "llm"
        assert field.needs_validation is False
    
    def test_default_values(self):
        """测试默认值"""
        # confidence字段是必需的，必须提供
        field = FieldConfidence(value="test", confidence=0.0)
        assert field.confidence == 0.0
        assert field.source == "llm"  # 有默认值
        assert field.needs_validation is False  # 有默认值
    
    def test_confidence_range(self):
        """测试置信度范围验证"""
        # 正常范围
        field = FieldConfidence(value="test", confidence=50.0)
        assert field.confidence == 50.0
        
        # 边界值
        field_min = FieldConfidence(value="test", confidence=0.0)
        assert field_min.confidence == 0.0
        
        field_max = FieldConfidence(value="test", confidence=100.0)
        assert field_max.confidence == 100.0
        
        # 超出范围应该失败
        with pytest.raises(ValidationError):
            FieldConfidence(value="test", confidence=-1.0)
        
        with pytest.raises(ValidationError):
            FieldConfidence(value="test", confidence=101.0)


class TestStructuredData:
    """StructuredData 模型测试"""
    
    def test_valid_structured_data(self):
        """测试有效的结构化数据"""
        fields = {
            "field1": FieldConfidence(value="value1", confidence=90.0),
            "field2": FieldConfidence(value="value2", confidence=85.0)
        }
        data = StructuredData(
            fields=fields,
            coverage=87.5,
            validation_list=["field2"]
        )
        assert len(data.fields) == 2
        assert data.coverage == 87.5
        assert len(data.validation_list) == 1
    
    def test_empty_validation_list(self):
        """测试空的校验列表"""
        fields = {
            "field1": FieldConfidence(value="value1", confidence=90.0)
        }
        data = StructuredData(fields=fields, coverage=90.0)
        assert data.validation_list == []
    
    def test_coverage_range(self):
        """测试覆盖率范围验证"""
        fields = {"field1": FieldConfidence(value="value1", confidence=90.0)}
        
        # 正常范围
        data = StructuredData(fields=fields, coverage=50.0)
        assert data.coverage == 50.0
        
        # 边界值
        data_min = StructuredData(fields=fields, coverage=0.0)
        assert data_min.coverage == 0.0
        
        data_max = StructuredData(fields=fields, coverage=100.0)
        assert data_max.coverage == 100.0
        
        # 超出范围应该失败
        with pytest.raises(ValidationError):
            StructuredData(fields=fields, coverage=-1.0)
        
        with pytest.raises(ValidationError):
            StructuredData(fields=fields, coverage=101.0)


class TestOCRResult:
    """OCRResult 模型测试"""
    
    def test_valid_ocr_result(self):
        """测试有效的OCR结果"""
        result = OCRResult(
            text="识别文本",
            confidence=95.5,
            language="zh",
            engine="pytesseract",
            text_blocks=[],
            image_size={"width": 800, "height": 600}
        )
        assert result.text == "识别文本"
        assert result.confidence == 95.5
        assert result.language == "zh"
        assert result.engine == "pytesseract"
    
    def test_ocr_result_without_optional_fields(self):
        """测试不带可选字段的OCR结果"""
        result = OCRResult(
            text="识别文本",
            confidence=95.5,
            language="zh",
            engine="pytesseract"
        )
        assert result.text_blocks is None
        assert result.image_size is None
    
    def test_confidence_range(self):
        """测试置信度范围验证"""
        # 正常范围
        result = OCRResult(
            text="test",
            confidence=50.0,
            language="en",
            engine="pytesseract"
        )
        assert result.confidence == 50.0
        
        # 超出范围应该失败
        with pytest.raises(ValidationError):
            OCRResult(
                text="test",
                confidence=101.0,
                language="en",
                engine="pytesseract"
            )


class TestProcessingResult:
    """ProcessingResult 模型测试"""
    
    def test_valid_processing_result(self):
        """测试有效的处理结果"""
        structured_data = StructuredData(
            fields={"field1": FieldConfidence(value="value1", confidence=90.0)},
            coverage=90.0
        )
        ocr_result = OCRResult(
            text="识别文本",
            confidence=95.0,
            language="zh",
            engine="pytesseract"
        )
        
        result = ProcessingResult(
            structured_data=structured_data,
            ocr_result=ocr_result,
            cleaned_text="清理后的文本",
            structure_config="发票"
        )
        assert result.structured_data.coverage == 90.0
        assert result.ocr_result.text == "识别文本"
        assert result.cleaned_text == "清理后的文本"
    
    def test_processing_result_with_optional_fields(self):
        """测试带可选字段的处理结果"""
        structured_data = StructuredData(
            fields={"field1": FieldConfidence(value="value1", confidence=90.0)},
            coverage=90.0
        )
        ocr_result = OCRResult(
            text="识别文本",
            confidence=95.0,
            language="zh",
            engine="pytesseract"
        )
        
        entities = {
            "dates": [{"text": "2024-01-15", "start": 0, "end": 10}]
        }
        
        result = ProcessingResult(
            structured_data=structured_data,
            ocr_result=ocr_result,
            cleaned_text="清理后的文本",
            structure_config="发票",
            entities=entities,
            page_number=1
        )
        assert result.entities is not None
        assert result.page_number == 1


class TestBatchProcessingResult:
    """BatchProcessingResult 模型测试"""
    
    def test_valid_batch_result(self):
        """测试有效的批量处理结果"""
        result = BatchProcessingResult(
            total_files=10,
            successful=8,
            failed=2,
            results=[
                {"filename": "file1.pdf", "status": "success"},
                {"filename": "file2.pdf", "status": "failed", "error": "Error message"}
            ]
        )
        assert result.total_files == 10
        assert result.successful == 8
        assert result.failed == 2
        assert len(result.results) == 2
    
    def test_batch_result_consistency(self):
        """测试批量结果的一致性"""
        results = [
            {"filename": f"file{i}.pdf", "status": "success"}
            for i in range(5)
        ]
        result = BatchProcessingResult(
            total_files=5,
            successful=5,
            failed=0,
            results=results
        )
        assert result.total_files == result.successful + result.failed

