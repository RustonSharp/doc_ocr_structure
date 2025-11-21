"""
NLP 实体识别模块：使用 spaCy 识别日期、金额、手机号等实体
"""
import re
from typing import Any, Dict, List, Optional

try:
    import spacy
    from spacy import displacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False


class EntityRecognizer:
    """实体识别器"""
    
    def __init__(self, model_name: str = "zh_core_web_sm"):
        """
        初始化实体识别器
        
        Args:
            model_name: spaCy 模型名称，默认为中文模型
                       如果未安装，可以使用 "en_core_web_sm" 或 None（仅使用正则）
        """
        self.nlp = None
        self.use_spacy = False
        
        if SPACY_AVAILABLE and model_name:
            try:
                self.nlp = spacy.load(model_name)
                self.use_spacy = True
            except OSError:
                print(f"警告: 未找到 spaCy 模型 '{model_name}'，将仅使用正则表达式")
                print(f"安装命令: python -m spacy download {model_name}")
    
    def extract_entities(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        从文本中提取实体
        
        Args:
            text: 输入文本
        
        Returns:
            包含各种实体类型的字典
        """
        entities = {
            "dates": [],
            "amounts": [],
            "phone_numbers": [],
            "emails": [],
            "ids": [],
        }
        
        # 使用 spaCy 提取（如果可用）
        if self.use_spacy and self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ in ["DATE", "TIME"]:
                    entities["dates"].append({
                        "text": ent.text,
                        "start": ent.start_char,
                        "end": ent.end_char,
                        "label": ent.label_,
                    })
        
        # 使用正则表达式补充提取
        entities["dates"].extend(self._extract_dates_regex(text))
        entities["amounts"].extend(self._extract_amounts_regex(text))
        entities["phone_numbers"].extend(self._extract_phone_numbers_regex(text))
        entities["emails"].extend(self._extract_emails_regex(text))
        entities["ids"].extend(self._extract_ids_regex(text))
        
        # 去重
        for key in entities:
            entities[key] = self._deduplicate_entities(entities[key])
        
        return entities
    
    def _extract_dates_regex(self, text: str) -> List[Dict[str, Any]]:
        """使用正则表达式提取日期"""
        dates = []
        
        # 日期格式：YYYY-MM-DD, YYYY/MM/DD, YYYY年MM月DD日
        patterns = [
            (r"\d{4}[-/]\d{1,2}[-/]\d{1,2}", "YYYY-MM-DD"),
            (r"\d{4}年\d{1,2}月\d{1,2}日", "YYYY年MM月DD日"),
            (r"\d{1,2}[-/]\d{1,2}[-/]\d{4}", "MM-DD-YYYY"),
        ]
        
        for pattern, format_type in patterns:
            for match in re.finditer(pattern, text):
                dates.append({
                    "text": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                    "label": "DATE",
                    "format": format_type,
                })
        
        return dates
    
    def _extract_amounts_regex(self, text: str) -> List[Dict[str, Any]]:
        """使用正则表达式提取金额"""
        amounts = []
        
        # 金额格式：￥123.45, ¥123.45, 123.45元, 123,456.78
        patterns = [
            (r"[￥¥]\s*\d{1,3}(?:[,，]\d{3})*(?:\.\d{2})?", "货币符号"),
            (r"\d{1,3}(?:[,，]\d{3})*(?:\.\d{2})?\s*[元圆]", "元"),
            (r"\d{1,3}(?:[,，]\d{3})*(?:\.\d{2})?", "纯数字"),
        ]
        
        for pattern, format_type in patterns:
            for match in re.finditer(pattern, text):
                amounts.append({
                    "text": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                    "label": "MONEY",
                    "format": format_type,
                })
        
        return amounts
    
    def _extract_phone_numbers_regex(self, text: str) -> List[Dict[str, Any]]:
        """使用正则表达式提取手机号"""
        phone_numbers = []
        
        # 中国手机号：11位数字，以1开头
        pattern = r"1[3-9]\d{9}"
        for match in re.finditer(pattern, text):
            phone_numbers.append({
                "text": match.group(),
                "start": match.start(),
                "end": match.end(),
                "label": "PHONE",
            })
        
        return phone_numbers
    
    def _extract_emails_regex(self, text: str) -> List[Dict[str, Any]]:
        """使用正则表达式提取邮箱"""
        emails = []
        
        pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        for match in re.finditer(pattern, text):
            emails.append({
                "text": match.group(),
                "start": match.start(),
                "end": match.end(),
                "label": "EMAIL",
            })
        
        return emails
    
    def _extract_ids_regex(self, text: str) -> List[Dict[str, Any]]:
        """使用正则表达式提取身份证号、发票号等"""
        ids = []
        
        # 18位身份证号
        id_pattern = r"\d{17}[\dXx]"
        for match in re.finditer(id_pattern, text):
            ids.append({
                "text": match.group(),
                "start": match.start(),
                "end": match.end(),
                "label": "ID_CARD",
            })
        
        # 发票号：XXX-数字格式
        invoice_pattern = r"[A-Za-z]{2,}-\d+"
        for match in re.finditer(invoice_pattern, text):
            ids.append({
                "text": match.group(),
                "start": match.start(),
                "end": match.end(),
                "label": "INVOICE_NUMBER",
            })
        
        return ids
    
    def _deduplicate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重实体列表"""
        seen = set()
        unique = []
        for entity in entities:
            key = (entity["text"], entity["start"], entity["end"])
            if key not in seen:
                seen.add(key)
                unique.append(entity)
        return unique


# 全局实例（延迟加载）
_recognizer: Optional[EntityRecognizer] = None


def get_entity_recognizer(model_name: str = "zh_core_web_sm") -> EntityRecognizer:
    """获取全局实体识别器实例"""
    global _recognizer
    if _recognizer is None:
        _recognizer = EntityRecognizer(model_name)
    return _recognizer

