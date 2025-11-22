# 根据 configs/llms/init.json 中的配置，使用 LangChain 初始化 LLM 服务
import json
import os
import re
from typing import Any, Dict

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage

load_dotenv()


class MockChatModel:
    """简易的 Mock 模型，用于本地测试"""

    def invoke(self, prompt: str) -> str:
        return f"[Mock Response] {prompt[:60]}..."


class LLMService:
    """使用 LangChain 统一管理多种 LLM Provider"""

    def __init__(self, config_path: str = "configs/llms/init.json") -> None:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        self.raw_config = config
        self.current_service = config["llm_services"]["current"]
        self.service_config = config["llm_services"]["services"][self.current_service]
        self.provider = self.service_config["provider"]
        self.model = self._build_model()

    def _build_model(self):
        if self.provider == "openai":
            api_key_value = os.getenv("OPENAI_API_KEY")
            if not api_key_value:
                raise ValueError("请设置环境变量 OPENAI_API_KEY")
            os.environ["OPENAI_API_KEY"] = api_key_value

            openai_kwargs: Dict[str, Any] = {
                "model": self.service_config["model"],
                "temperature": self.service_config.get("temperature", 0.1),
            }

            max_tokens = self.service_config.get("max_tokens")
            if max_tokens is not None:
                openai_kwargs["model_kwargs"] = {"max_tokens": max_tokens}

            return ChatOpenAI(**openai_kwargs)

        if self.provider == "google":
            api_key_value = os.getenv("GEMINI_API_KEY")
            if not api_key_value:
                raise ValueError("请设置环境变量 GEMINI_API_KEY")
            os.environ["GEMINI_API_KEY"] = api_key_value

            google_kwargs: Dict[str, Any] = {
                "model": self.service_config["model"],
                "temperature": self.service_config.get("temperature", 0.1),
            }

            max_tokens = self.service_config.get("max_tokens")
            if max_tokens is not None:
                google_kwargs["max_output_tokens"] = max_tokens

            return ChatGoogleGenerativeAI(**google_kwargs)

        if self.provider == "ollama":
            return ChatOllama(
                model=self.service_config["model"],
                temperature=self.service_config.get("temperature", 0.1),
                base_url=self.service_config.get("base_url"),
            )

        if self.provider == "mock":
            return MockChatModel()

        raise ValueError(f"不支持的 provider: {self.provider}")

    def generate_text(self, prompt: str) -> str:
        response = self.model.invoke(prompt)
        return self._extract_text(response)

    def format_json_into_professional(self, json_str: str) -> Dict[str, Any]:
        reference_json_str = self._load_reference_template()

        prompt = (
            "你是一个 OCR 数据结构化处理专家，并且非常擅长编写 JSON 结构配置。"
            "现在请将非专业用户编写的口语化 JSON 转换为更严谨的配置格式，输出必须是有效 JSON，"
            "不要添加多余解释或代码块标记。\n\n"
            f"原始输入：```json\n{json_str}\n```\n"
            f"参考输出：```json\n{reference_json_str}\n```"
        )

        result_text = self.generate_text(prompt)
        parsed = self._safe_parse_json(result_text)
        if parsed is None:
            print("LLM 返回内容不是合法 JSON：", result_text)
            return {}
        return parsed

    def improve_json_structure(
        self, ocr_text: str, structure_config: Dict[str, Any], ocr_result: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """
        根据结构化配置从OCR文本中提取结构化数据
        
        Args:
            ocr_text: OCR识别的文本内容
            structure_config: 结构化配置文件（包含要提取的字段定义）
            ocr_result: 完整的OCR结果（可选，用于提供额外上下文如位置信息）
        
        Returns:
            提取后的结构化数据字典
        """
        # 构建字段提取提示
        fields_info = []
        for item in structure_config.get("items", []):
            field_name = item.get("field", "")
            description = item.get("description", "")
            field_type = item.get("type", "text")
            pattern = item.get("pattern", "")
            
            field_desc = f"- 字段名: {field_name}\n  描述: {description}\n  类型: {field_type}"
            if pattern:
                field_desc += f"\n  正则模式: {pattern}"
            fields_info.append(field_desc)
        
        fields_text = "\n".join(fields_info)
        
        # 构建位置信息（如果有）
        position_context = ""
        if ocr_result and "text_blocks" in ocr_result:
            # 提取一些关键位置信息作为上下文
            position_context = "\n\n注意：文本块的位置信息可以帮助你更准确地定位字段。"
        
        prompt = (
            f"你是一个专业的OCR数据结构化提取专家。"
            f"请根据以下字段定义，从OCR识别的文本中提取结构化数据。\n\n"
            f"文档类型: {structure_config.get('title', '未知')}\n"
            f"文档描述: {structure_config.get('description', '')}\n\n"
            f"需要提取的字段：\n{fields_text}\n\n"
            f"OCR识别文本：\n```\n{ocr_text}\n```\n"
            f"{position_context}\n"
            f"请严格按照字段定义提取数据，输出一个JSON对象，格式如下：\n"
            f"{{"
        )
        
        # 添加字段示例
        field_examples = []
        for item in structure_config.get("items", []):
            field_name = item.get("field", "")
            field_type = item.get("type", "text")
            if field_type in ["date", "number", "小数"]:
                field_examples.append(f'  "{field_name}": null  // 如果未找到则设为null')
            else:
                field_examples.append(f'  "{field_name}": ""  // 如果未找到则设为空字符串')
        
        prompt += "\n" + ",\n".join(field_examples) + "\n"
        prompt += (
            "}\n\n"
            "要求：\n"
            "1. 只输出JSON对象，不要添加任何解释或代码块标记\n"
            "2. 如果某个字段在文本中找不到，根据字段类型设置为null或空字符串\n"
            "3. 日期字段请转换为标准格式（YYYY-MM-DD）\n"
            "4. 数字字段请提取纯数字，去除货币符号等\n"
            "5. 确保输出的JSON是有效的"
        )
        
        result_text = self.generate_text(prompt)
        parsed = self._safe_parse_json(result_text)
        
        if parsed is None:
            print("LLM 返回内容不是合法 JSON：", result_text)
            # 返回空结构
            result = {}
            for item in structure_config.get("items", []):
                field_name = item.get("field", "")
                result[field_name] = None
            return result
        
        return parsed

    def _load_reference_template(self) -> str:
        with open("configs/structures/template.json", "r", encoding="utf-8") as f:
            return f.read().strip()

    def _extract_text(self, response: Any) -> str:
        if isinstance(response, str):
            return response.strip()

        if isinstance(response, AIMessage):
            content = response.content
        else:
            content = getattr(response, "content", "")

        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            chunks = []
            for part in content:
                if isinstance(part, dict) and "text" in part:
                    chunks.append(part["text"])
                else:
                    chunks.append(str(part))
            return "\n".join(chunks).strip()

        return str(content).strip()

    def _safe_parse_json(self, text: str) -> Dict[str, Any] | None:
        cleaned = self._strip_code_fences(text)
        if not cleaned:
            return None
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return None

    def _strip_code_fences(self, text: str) -> str:
        """去除 markdown 代码块标记，提取其中的 JSON 内容"""
        cleaned = text.strip()
        if not cleaned:
            return ""

        # 使用正则表达式匹配 markdown 代码块：```json ... ``` 或 ``` ... ```
        # 支持可选的 json 语言标识符
        pattern = r'^```(?:json)?\s*\n?(.*?)\n?```\s*$'
        match = re.search(pattern, cleaned, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # 如果没有匹配到完整的代码块，尝试查找第一个 { 和最后一个 }
        # 这可以处理不完整的代码块标记
        if cleaned.startswith("```"):
            # 移除开头的 ```
            cleaned = re.sub(r'^```[a-zA-Z]*\s*\n?', '', cleaned, flags=re.IGNORECASE)
            # 移除结尾的 ```
            cleaned = re.sub(r'\n?```\s*$', '', cleaned)
            return cleaned.strip()
        
        return cleaned.strip()


if __name__ == "__main__":
    service = LLMService()
    print(f"当前 LLM Provider: {service.provider}")
    json_str = open("configs/structures/origin/invoice0.json", "r", encoding="utf-8").read()
    result = service.format_json_into_professional(json_str)
    print(json.dumps(result, indent=4, ensure_ascii=False))