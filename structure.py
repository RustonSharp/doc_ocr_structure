import json
import re
from typing import Any, Dict

from llm import LLMService


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


def structure_ocr_result(ocr_result: dict, config_file: str | None = None) -> Dict[str, Any]:
    """
    基于NLP、JSON结构化配置文件和LLM，对OCR结果进行结构化处理
    
    Args:
        ocr_result: OCR识别结果字典，包含 'text' 字段和其他元数据
        config_file: 结构化配置文件的路径（可选，如果未提供则从nlp.json读取）
    
    Returns:
        结构化后的数据字典
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
        result = {}
        for item in structure_config.get("items", []):
            field_name = item.get("field", "")
            result[field_name] = None
        return {"structured_data": result, "raw_ocr": ocr_result}
    
    # 5. NLP文本清理
    text_cleaning_config = nlp_processing.get("text_cleaning", {})
    cleaned_text = _clean_text(ocr_text, text_cleaning_config)
    
    # 6. 使用LLM提取结构化数据
    try:
        llm_service = LLMService()
        structured_data = llm_service.improve_json_structure(
            ocr_text=cleaned_text,
            structure_config=structure_config,
            ocr_result=ocr_result,
        )
    except Exception as e:
        print(f"LLM结构化处理失败: {e}")
        # 返回空结构
        structured_data = {}
        for item in structure_config.get("items", []):
            field_name = item.get("field", "")
            structured_data[field_name] = None
    
    # 7. 返回结果
    return {
        "structured_data": structured_data,
        "raw_ocr": ocr_result,
        "cleaned_text": cleaned_text,
        "structure_config": structure_config.get("title", "未知"),
    }
