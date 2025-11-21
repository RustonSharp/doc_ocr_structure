"""
使用 Pydantic 定义输出 Schema
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FieldConfidence(BaseModel):
    """字段置信度信息"""
    value: Any = Field(description="字段值")
    confidence: float = Field(ge=0, le=100, description="置信度（0-100）")
    source: str = Field(default="llm", description="数据来源：llm, nlp, regex")
    needs_validation: bool = Field(default=False, description="是否需要人工校验")


class StructuredData(BaseModel):
    """结构化数据"""
    fields: Dict[str, FieldConfidence] = Field(description="提取的字段及其置信度")
    coverage: float = Field(ge=0, le=100, description="字段覆盖率（0-100）")
    validation_list: List[str] = Field(default_factory=list, description="待校验字段列表")


class OCRResult(BaseModel):
    """OCR 识别结果"""
    text: str = Field(description="识别出的文本")
    confidence: float = Field(ge=0, le=100, description="整体置信度")
    language: str = Field(description="检测到的语言")
    engine: str = Field(description="使用的 OCR 引擎")
    text_blocks: Optional[List[Dict[str, Any]]] = Field(default=None, description="文本块信息")
    image_size: Optional[Dict[str, int]] = Field(default=None, description="图片尺寸")


class ProcessingResult(BaseModel):
    """完整的处理结果"""
    structured_data: StructuredData = Field(description="结构化数据")
    ocr_result: OCRResult = Field(description="OCR 识别结果")
    cleaned_text: str = Field(description="清理后的文本")
    structure_config: str = Field(description="使用的结构化配置标题")
    entities: Optional[Dict[str, List[Dict[str, Any]]]] = Field(
        default=None, description="NLP 识别的实体"
    )
    page_number: Optional[int] = Field(default=None, description="PDF 页码（如果是 PDF）")


class BatchProcessingResult(BaseModel):
    """批量处理结果"""
    total_files: int = Field(description="总文件数")
    successful: int = Field(description="成功处理数")
    failed: int = Field(description="失败数")
    results: List[Dict[str, Any]] = Field(description="每个文件的处理结果")

