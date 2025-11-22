"""
OCR 后处理模块：用于校正 OCR 识别结果中的专业术语
支持 Google Cloud Vision 和其他不支持自定义字典的 OCR 引擎
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any


class OCRPostProcessor:
    """OCR 后处理器，用于校正专业术语和常见错误"""

    def __init__(self, custom_words_path: Optional[str] = None):
        """
        初始化后处理器
        
        Args:
            custom_words_path: 自定义词汇表文件路径（可选）
        """
        self.custom_words: Dict[str, str] = {}
        self.common_corrections: Dict[str, str] = {}
        
        if custom_words_path:
            self.load_custom_words(custom_words_path)
        
        # 加载常见错误校正表
        self._load_common_corrections()

    def load_custom_words(self, words_path: str) -> None:
        """
        加载自定义词汇表
        
        Args:
            words_path: 词汇表文件路径
        """
        words_file = Path(words_path)
        if not words_file.exists():
            print(f"警告：自定义词汇表文件不存在: {words_path}")
            return
        
        with open(words_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if not line or line.startswith("#"):
                    continue
                
                # 支持格式：原词 -> 校正词 或 仅原词（原词作为校正词）
                if "->" in line or "→" in line:
                    parts = re.split(r"->|→", line, 1)
                    if len(parts) == 2:
                        original = parts[0].strip()
                        corrected = parts[1].strip()
                        self.custom_words[original] = corrected
                else:
                    # 仅原词，用于模糊匹配
                    self.custom_words[line] = line

    def _load_common_corrections(self) -> None:
        """加载常见 OCR 错误校正表"""
        # 常见字符识别错误
        common_errors = {
            # 数字识别错误
            "O": "0",  # 字母O误识别为数字0（在特定上下文中）
            "l": "1",  # 小写L误识别为数字1（在特定上下文中）
            "I": "1",  # 大写I误识别为数字1（在特定上下文中）
            
            # 中文常见错误（示例）
            "0": "零",
            "1": "一",
            "2": "二",
            "3": "三",
            "4": "四",
            "5": "五",
            "6": "六",
            "7": "七",
            "8": "八",
            "9": "九",
        }
        
        self.common_corrections.update(common_errors)

    def correct_text(
        self, 
        text: str, 
        use_fuzzy_match: bool = True,
        fuzzy_threshold: float = 0.8
    ) -> str:
        """
        校正文本中的专业术语和常见错误
        
        Args:
            text: 原始 OCR 识别文本
            use_fuzzy_match: 是否使用模糊匹配（用于处理部分识别错误）
            fuzzy_threshold: 模糊匹配阈值（0-1之间）
        
        Returns:
            校正后的文本
        """
        corrected_text = text
        
        # 1. 精确匹配替换
        for original, corrected in self.custom_words.items():
            # 使用单词边界匹配，避免部分匹配
            pattern = r'\b' + re.escape(original) + r'\b'
            corrected_text = re.sub(pattern, corrected, corrected_text)
        
        # 2. 模糊匹配替换（如果启用）
        if use_fuzzy_match and self.custom_words:
            corrected_text = self._fuzzy_replace(corrected_text, fuzzy_threshold)
        
        # 3. 常见错误校正
        for error, correction in self.common_corrections.items():
            # 这里可以根据上下文进行更智能的替换
            # 暂时使用简单的替换
            pass  # 常见错误校正可以根据需要实现
        
        return corrected_text

    def _fuzzy_replace(
        self, 
        text: str, 
        threshold: float = 0.8
    ) -> str:
        """
        使用模糊匹配替换文本
        
        Args:
            text: 原始文本
            threshold: 相似度阈值
        
        Returns:
            替换后的文本
        """
        try:
            from difflib import SequenceMatcher
        except ImportError:
            return text
        
        words = text.split()
        corrected_words = []
        
        for word in words:
            best_match = word
            best_ratio = 0.0
            
            # 在自定义词汇表中查找最相似的词
            for custom_word in self.custom_words.keys():
                ratio = SequenceMatcher(None, word, custom_word).ratio()
                if ratio > best_ratio and ratio >= threshold:
                    best_ratio = ratio
                    best_match = self.custom_words[custom_word]
            
            corrected_words.append(best_match)
        
        return " ".join(corrected_words)

    def correct_text_blocks(
        self, 
        text_blocks: List[Dict[str, Any]], 
        use_fuzzy_match: bool = True
    ) -> List[Dict[str, Any]]:
        """
        校正文本块列表中的文本
        
        Args:
            text_blocks: 文本块列表（包含 text 字段）
            use_fuzzy_match: 是否使用模糊匹配
        
        Returns:
            校正后的文本块列表
        """
        corrected_blocks = []
        for block in text_blocks:
            corrected_block = block.copy()
            if "text" in block:
                corrected_block["text"] = self.correct_text(
                    block["text"], 
                    use_fuzzy_match=use_fuzzy_match
                )
            corrected_blocks.append(corrected_block)
        return corrected_blocks

    def add_custom_word(self, original: str, corrected: Optional[str] = None) -> None:
        """
        动态添加自定义词汇
        
        Args:
            original: 原始词汇（或错误识别的词汇）
            corrected: 校正后的词汇（如果为None，则使用original）
        """
        self.custom_words[original] = corrected or original

    def get_correction_stats(self) -> Dict[str, int]:
        """
        获取校正统计信息
        
        Returns:
            包含校正词汇数量的字典
        """
        return {
            "custom_words_count": len(self.custom_words),
            "common_corrections_count": len(self.common_corrections),
        }


def create_post_processor(
    custom_words_path: Optional[str] = None,
    config_path: str = "configs/ocr.json"
) -> OCRPostProcessor:
    """
    创建 OCR 后处理器实例
    
    Args:
        custom_words_path: 自定义词汇表路径（可选，如果为None则从配置文件读取）
        config_path: OCR 配置文件路径
    
    Returns:
        OCRPostProcessor 实例
    """
    import json
    
    # 如果未指定路径，尝试从配置文件读取
    if custom_words_path is None:
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            pytesseract_config = config.get("ocr_engines", {}).get("engines", {}).get("pytesseract", {})
            custom_words_path = pytesseract_config.get("custom_words_path")
        except Exception:
            pass
    
    return OCRPostProcessor(custom_words_path)


if __name__ == "__main__":
    # 测试示例
    processor = create_post_processor("configs/ocr/custom_words.txt")
    
    # 测试文本
    test_text = "这是一张增值祝专用发票，发票号玛是12345678"
    
    # 校正
    corrected = processor.correct_text(test_text)
    print(f"原始文本: {test_text}")
    print(f"校正后: {corrected}")
    
    # 统计信息
    stats = processor.get_correction_stats()
    print(f"\n校正统计: {stats}")

