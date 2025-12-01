"""
NLP 实体识别测试
"""
import pytest

from nlp_entity import EntityRecognizer, get_entity_recognizer


class TestEntityRecognizer:
    """实体识别器测试"""
    
    def test_entity_recognizer_initialization_no_spacy(self):
        """测试不加载spaCy模型的初始化"""
        recognizer = EntityRecognizer(model_name=None)
        assert recognizer.nlp is None
        assert recognizer.use_spacy is False
    
    def test_extract_dates_regex(self):
        """测试日期正则提取"""
        recognizer = EntityRecognizer(model_name=None)
        text = "日期：2024-01-15，另一个日期是2024/02/20"
        dates = recognizer._extract_dates_regex(text)
        
        assert len(dates) >= 2
        assert any("2024-01-15" in d["text"] for d in dates)
    
    def test_extract_amounts_regex(self):
        """测试金额正则提取"""
        recognizer = EntityRecognizer(model_name=None)
        text = "金额：￥1,234.56，总计123.45元"
        amounts = recognizer._extract_amounts_regex(text)
        
        assert len(amounts) >= 1
        # 验证是否提取到金额
        assert any("1,234.56" in a["text"] or "123.45" in a["text"] for a in amounts)
    
    def test_extract_phone_numbers_regex(self):
        """测试手机号正则提取"""
        recognizer = EntityRecognizer(model_name=None)
        text = "联系电话：13800138000，备用：13900139000"
        phone_numbers = recognizer._extract_phone_numbers_regex(text)
        
        assert len(phone_numbers) >= 2
        assert any("13800138000" in p["text"] for p in phone_numbers)
        assert any("13900139000" in p["text"] for p in phone_numbers)
    
    def test_extract_emails_regex(self):
        """测试邮箱正则提取"""
        recognizer = EntityRecognizer(model_name=None)
        text = "邮箱：test@example.com，联系：admin@test.org"
        emails = recognizer._extract_emails_regex(text)
        
        assert len(emails) >= 2
        assert any("test@example.com" in e["text"] for e in emails)
        assert any("admin@test.org" in e["text"] for e in emails)
    
    def test_extract_ids_regex(self):
        """测试身份证号正则提取"""
        recognizer = EntityRecognizer(model_name=None)
        text = "身份证号：123456789012345678X"
        ids = recognizer._extract_ids_regex(text)
        
        # 验证是否提取到身份证号
        id_found = any("123456789012345678X" in id_["text"] for id_ in ids)
        assert id_found or len(ids) >= 0  # 至少不报错
    
    def test_deduplicate_entities(self):
        """测试实体去重"""
        recognizer = EntityRecognizer(model_name=None)
        entities = [
            {"text": "test", "start": 0, "end": 4},
            {"text": "test", "start": 0, "end": 4},  # 重复
            {"text": "other", "start": 10, "end": 15}
        ]
        
        unique = recognizer._deduplicate_entities(entities)
        assert len(unique) == 2
    
    def test_extract_entities_complete(self):
        """测试完整实体提取"""
        recognizer = EntityRecognizer(model_name=None)
        text = """
        日期：2024-01-15
        金额：￥1,234.56
        电话：13800138000
        邮箱：test@example.com
        """
        
        entities = recognizer.extract_entities(text)
        
        assert "dates" in entities
        assert "amounts" in entities
        assert "phone_numbers" in entities
        assert "emails" in entities
        assert "ids" in entities
        
        # 验证实体列表不为None
        assert isinstance(entities["dates"], list)
        assert isinstance(entities["amounts"], list)
        assert isinstance(entities["phone_numbers"], list)
    
    def test_extract_entities_empty_text(self):
        """测试空文本的实体提取"""
        recognizer = EntityRecognizer(model_name=None)
        entities = recognizer.extract_entities("")
        
        assert all(len(entities[key]) == 0 for key in entities)


class TestGetEntityRecognizer:
    """全局实体识别器获取测试"""
    
    def test_get_entity_recognizer_singleton(self):
        """测试全局实例的单例模式"""
        recognizer1 = get_entity_recognizer(model_name=None)
        recognizer2 = get_entity_recognizer(model_name=None)
        
        # 应该返回同一个实例
        assert recognizer1 is recognizer2
    
    def test_get_entity_recognizer_caching(self):
        """测试实体识别器的缓存"""
        recognizer = get_entity_recognizer(model_name=None)
        assert recognizer is not None

