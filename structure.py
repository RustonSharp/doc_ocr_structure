import json
import re
from typing import Any, Dict

from llm import LLMService
from nlp_entity import get_entity_recognizer
from schemas import FieldConfidence, StructuredData


def _clean_text(text: str, cleaning_config: Dict[str, Any]) -> str:
    """根据配置清理文本"""
    cleaned = text
    
    if cleaning_config.get("remove_extra_spaces", False):
        # 移除多余空格，但保留换行
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r" +", " ", cleaned)
    
    if cleaning_config.get("normalize_whitespace", False):
        # 规范化空白字符
        cleaned = re.sub(r"\r\n", "\n", cleaned)
        cleaned = re.sub(r"\r", "\n", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    
    if cleaning_config.get("remove_special_chars", False):
        # 移除特殊字符（保留中文、英文、数字、基本标点）
        cleaned = re.sub(r"[^\w\s\u4e00-\u9fff，。、；：！？""''（）【】《》￥%]", "", cleaned)
    
    return cleaned.strip()


def _load_nlp_config(config_path: str = "configs/nlp.json") -> Dict[str, Any]:
    """加载NLP配置文件"""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # 返回默认配置
        return {
            "nlp_processing": {
                "enabled": True,
                "text_cleaning": {
                    "remove_extra_spaces": True,
                    "remove_special_chars": False,
                    "normalize_whitespace": True,
                },
                "keyword_extraction": {"enabled": False, "method": "regex"},
            }
        }


def _load_structure_config(config_file: str) -> Dict[str, Any]:
    """加载结构化配置文件"""
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"结构化配置文件不存在: {config_file}")


def _calculate_field_confidence(
    field_value: Any,
    field_name: str,
    ocr_text: str,
    ocr_result: Dict[str, Any],
    structure_config: Dict[str, Any],
    entities: Dict[str, Any],
) -> FieldConfidence:
    """计算字段的置信度"""
    confidence = 0.0
    source = "llm"
    needs_validation = False
    
    if field_value is None or field_value == "":
        confidence = 0.0
        needs_validation = True
    else:
        # 基础置信度：OCR 整体置信度
        ocr_confidence = ocr_result.get("confidence", 0.0)
        base_confidence = min(ocr_confidence, 95.0)  # 最高 95，留出空间给其他因素
        
        # 检查是否在 OCR 文本中找到该字段值
        field_str = str(field_value)
        if field_str in ocr_text:
            confidence = base_confidence + 5.0  # 找到匹配，加分
        else:
            confidence = base_confidence - 10.0  # 未找到，减分
        
        # 检查 NLP 实体识别结果
        field_lower = field_name.lower()
        if "日期" in field_name or "date" in field_lower:
            if entities.get("dates"):
                confidence += 5.0
                source = "nlp"
        elif "金额" in field_name or "合计" in field_name or "amount" in field_lower or "money" in field_lower:
            if entities.get("amounts"):
                confidence += 5.0
                source = "nlp"
        elif "电话" in field_name or "手机" in field_name or "phone" in field_lower:
            if entities.get("phone_numbers"):
                confidence += 5.0
                source = "nlp"
        
        # 使用正则验证（如果配置中有 pattern）
        for item in structure_config.get("items", []):
            if item.get("field") == field_name:
                pattern = item.get("pattern", "")
                if pattern:
                    try:
                        if re.search(pattern, field_str):
                            confidence += 5.0
                            source = "regex"
                    except re.error:
                        pass
                break
        
        confidence = max(0.0, min(100.0, confidence))
    
    # 判断是否需要人工校验（≤80%）
    if confidence <= 80.0:
        needs_validation = True
    
    return FieldConfidence(
        value=field_value,
        confidence=round(confidence, 2),
        source=source,
        needs_validation=needs_validation,
    )


def structure_ocr_result(ocr_result: dict, config_file: str | None = None) -> Dict[str, Any]:
    """
    基于NLP、JSON结构化配置文件和LLM，对OCR结果进行结构化处理
    
    Args:
        ocr_result: OCR识别结果字典，包含 'text' 字段和其他元数据
        config_file: 结构化配置文件的路径（可选，如果未提供则从nlp.json读取）
    
    Returns:
        结构化后的数据字典，包含置信度和校验清单
    """
    # 1. 加载NLP配置
    nlp_config = _load_nlp_config()
    nlp_processing = nlp_config.get("nlp_processing", {})
    
    if not nlp_processing.get("enabled", True):
        # 如果NLP处理被禁用，直接返回原始OCR结果
        return {"structured_data": None, "raw_ocr": ocr_result}
    
    # 2. 确定结构化配置文件路径
    if config_file is None:
        config_file = nlp_processing.get("structure_config_path")
        if not config_file:
            raise ValueError("未提供结构化配置文件路径，且nlp.json中也没有配置structure_config_path")
    
    # 3. 加载结构化配置文件
    structure_config = _load_structure_config(config_file)
    
    # 4. 提取OCR文本
    ocr_text = ocr_result.get("text", "")
    if not ocr_text:
        # 如果没有文本，返回空结构
        fields = {}
        for item in structure_config.get("items", []):
            field_name = item.get("field", "")
            fields[field_name] = FieldConfidence(
                value=None,
                confidence=0.0,
                source="llm",
                needs_validation=True,
            )
        return {
            "structured_data": StructuredData(
                fields=fields,
                coverage=0.0,
                validation_list=list(fields.keys()),
            ).model_dump(),
            "raw_ocr": ocr_result,
            "cleaned_text": "",
            "structure_config": structure_config.get("title", "未知"),
            "entities": {},
        }
    
    # 5. NLP文本清理
    text_cleaning_config = nlp_processing.get("text_cleaning", {})
    cleaned_text = _clean_text(ocr_text, text_cleaning_config)
    
    # 6. NLP 实体识别
    entities = {}
    try:
        recognizer = get_entity_recognizer()
        entities = recognizer.extract_entities(cleaned_text)
    except Exception as e:
        print(f"NLP 实体识别失败: {e}")
    
    # 7. 使用LLM提取结构化数据
    structured_data_raw = {}
    try:
        llm_service = LLMService()
        structured_data_raw = llm_service.improve_json_structure(
            ocr_text=cleaned_text,
            structure_config=structure_config,
            ocr_result=ocr_result,
        )
    except Exception as e:
        print(f"LLM结构化处理失败: {e}")
        # 返回空结构
        for item in structure_config.get("items", []):
            field_name = item.get("field", "")
            structured_data_raw[field_name] = None
    
    # 8. 计算每个字段的置信度
    fields_with_confidence = {}
    validation_list = []
    extracted_count = 0
    
    for item in structure_config.get("items", []):
        field_name = item.get("field", "")
        field_value = structured_data_raw.get(field_name)
        
        field_conf = _calculate_field_confidence(
            field_value=field_value,
            field_name=field_name,
            ocr_text=cleaned_text,
            ocr_result=ocr_result,
            structure_config=structure_config,
            entities=entities,
        )
        
        fields_with_confidence[field_name] = field_conf
        
        if field_value is not None and field_value != "":
            extracted_count += 1
        
        if field_conf.needs_validation:
            validation_list.append(field_name)
    
    # 9. 计算覆盖率
    total_fields = len(structure_config.get("items", []))
    coverage = (extracted_count / total_fields * 100) if total_fields > 0 else 0.0
    
    # 10. 构建结构化数据
    structured_data = StructuredData(
        fields={k: v.model_dump() for k, v in fields_with_confidence.items()},
        coverage=round(coverage, 2),
        validation_list=validation_list,
    )
    
    # 11. 返回结果
    return {
        "structured_data": structured_data.model_dump(),
        "raw_ocr": ocr_result,
        "cleaned_text": cleaned_text,
        "structure_config": structure_config.get("title", "未知"),
        "entities": entities,
    }
