
"""
OCR 引擎管理器

基于 configs/ocr.json 进行多引擎的配置、切换与调用
"""

from __future__ import annotations

import io
import json
import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

import pytesseract
from PIL import Image

from logging_config import get_logger, log_performance, log_exception

logger = get_logger(__name__)


class OCREngineType(Enum):
    """受支持的 OCR 引擎类型"""

    PYTESSERACT = "pytesseract"
    GOOGLE_CLOUD_VISION = "google-cloud-vision"


class OCREngineManager:
    """根据 JSON 配置管理 OCR 引擎"""

    def __init__(self, config_path: str | Path = "configs/ocr.json") -> None:
        self.config_path = Path(config_path)
        self.config_data = self._load_config()
        self.engine_configs: Dict[str, Dict[str, Any]] = self.config_data["ocr_engines"]["engines"]

        current_engine_name = self.config_data["ocr_engines"]["current"]
        self.current_engine: OCREngineType = self._to_engine_type(current_engine_name)
        self.previous_engine: Optional[OCREngineType] = None
        
        logger.info(
            f"OCR引擎管理器初始化完成 - 当前引擎: {current_engine_name}",
            extra={"context": {"current_engine": current_engine_name, "config_path": str(config_path)}}
        )

    def switch_engine(
        self,
        engine_name: str,
        config: Optional[Dict[str, Any]] = None,
        persist: bool = False,
    ) -> bool:
        """切换引擎，可选更新配置"""
        try:
            engine_type = self._to_engine_type(engine_name)
            if engine_name not in self.engine_configs:
                raise ValueError(f"配置中不存在引擎: {engine_name}")

            previous_engine = self.current_engine.value
            if config:
                self.engine_configs[engine_name].update(config)
                logger.info(f"更新引擎配置: {engine_name}", extra={"context": {"engine": engine_name, "config": config}})

            self.previous_engine = self.current_engine
            self.current_engine = engine_type
            self.config_data["ocr_engines"]["current"] = engine_name

            if persist:
                self._save_config()
                logger.info(f"引擎切换已持久化到配置文件", extra={"context": {"engine": engine_name}})

            logger.info(
                f"OCR引擎切换成功: {previous_engine} -> {engine_name}",
                extra={"context": {"previous_engine": previous_engine, "current_engine": engine_name}}
            )
            return True
        except Exception as exc:
            log_exception(logger, f"切换OCR引擎失败: {engine_name}", extra_context={"engine_name": engine_name})
            return False

    def get_current_engine_info(self) -> Dict[str, Any]:
        """返回当前引擎的基础信息"""
        current_name = self.current_engine.value
        return {
            "current_engine": current_name,
            "previous_engine": self.previous_engine.value if self.previous_engine else None,
            "config": self.engine_configs.get(current_name, {}).copy(),
        }

    async def process_image_with_current_engine(
        self,
        image_data: bytes,
        config_file_name: Optional[str] = None,
        dictionary_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """按照当前引擎处理图片"""
        engine_name = self.current_engine.value
        image_size = len(image_data)
        
        logger.debug(
            f"开始OCR处理 - 引擎: {engine_name}, 图片大小: {image_size} bytes",
            extra={"context": {"engine": engine_name, "image_size": image_size}}
        )
        
        try:
            if self.current_engine == OCREngineType.PYTESSERACT:
                with log_performance(f"OCR处理(pytesseract)", logger, {"image_size": image_size}):
                    return await self._process_with_pytesseract(image_data, config_file_name, dictionary_path)
            if self.current_engine == OCREngineType.GOOGLE_CLOUD_VISION:
                with log_performance(f"OCR处理(google-vision)", logger, {"image_size": image_size}):
                    return await self._process_with_google_vision(image_data, config_file_name)
            raise ValueError(f"不支持的 OCR 引擎: {self.current_engine}")
        except Exception as e:
            log_exception(logger, f"OCR处理失败 - 引擎: {engine_name}", extra_context={"engine": engine_name, "image_size": image_size})
            raise

    async def _process_with_pytesseract(
        self,
        image_data: bytes,
        config_file_name: Optional[str] = None,
        dictionary_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """pytesseract 引擎实现"""
        try:
            image = Image.open(io.BytesIO(image_data))
            img_width, img_height = image.size

            engine_config = self.engine_configs[OCREngineType.PYTESSERACT.value]
            languages = engine_config.get("languages", "eng")
            oem = engine_config.get("oem", 3)
            psm = engine_config.get("psm", 6)

            custom_config = f"-l {languages} --oem {oem} --psm {psm}"

            custom_words = dictionary_path or engine_config.get("custom_words_path")
            custom_patterns = engine_config.get("custom_patterns_path")

            custom_words_path = self._resolve_path(custom_words)
            custom_patterns_path = self._resolve_path(custom_patterns)

            if custom_words_path and os.path.exists(custom_words_path):
                custom_config += f" --user-words {custom_words_path}"
            if custom_patterns_path and os.path.exists(custom_patterns_path):
                custom_config += f" --user-patterns {custom_patterns_path}"

            text = pytesseract.image_to_string(image, config=custom_config)
            data = pytesseract.image_to_data(image, config=custom_config, output_type=pytesseract.Output.DICT)

            text_blocks: list[Dict[str, Any]] = []
            confidences: list[int] = []
            for i in range(len(data["text"])):
                confidence = int(data["conf"][i])
                word_text = data["text"][i].strip()
                if confidence > 0 and word_text:
                    text_blocks.append(
                        {
                            "text": word_text,
                            "confidence": confidence,
                            "bbox": {
                                "x": data["left"][i],
                                "y": data["top"][i],
                                "width": data["width"][i],
                                "height": data["height"][i],
                                "relative_x": data["left"][i] / img_width if img_width else 0,
                                "relative_y": data["top"][i] / img_height if img_height else 0,
                                "position": self._get_position_label(
                                    data["left"][i],
                                    data["top"][i],
                                    data["width"][i],
                                    data["height"][i],
                                    img_width,
                                    img_height,
                                ),
                            },
                            "block_num": data["block_num"][i],
                            "line_num": data["line_num"][i],
                            "word_num": data["word_num"][i],
                        }
                    )
                    confidences.append(confidence)

            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            text_length = len(text.strip())
            logger.info(
                f"pytesseract OCR完成 - 文本长度: {text_length}, 置信度: {avg_confidence:.2f}, 文本块数: {len(text_blocks)}",
                extra={"context": {"text_length": text_length, "confidence": avg_confidence, "blocks": len(text_blocks), "language": languages}}
            )

            return {
                "text": text.strip(),
                "confidence": avg_confidence,
                "language": languages,
                "engine": OCREngineType.PYTESSERACT.value,
                "text_blocks": text_blocks,
                "image_size": {"width": img_width, "height": img_height},
                "structured_data": None,
            }
        except Exception as exc:
            log_exception(logger, "pytesseract处理失败", extra_context={"error": str(exc)})
            raise RuntimeError(f"pytesseract 处理失败: {exc}") from exc

    async def _process_with_google_vision(
        self,
        image_data: bytes,
        config_file_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Google Cloud Vision 实现"""
        try:
            from google.cloud import vision
        except ImportError as exc:
            raise RuntimeError("未安装 google-cloud-vision，请运行: pip install google-cloud-vision") from exc

        engine_config = self.engine_configs.get(OCREngineType.GOOGLE_CLOUD_VISION.value)
        if not engine_config:
            raise RuntimeError("配置中不存在 google-cloud-vision 引擎")

        credentials_path = self._resolve_path(engine_config.get("credentials_path"))
        if not credentials_path or not os.path.exists(credentials_path):
            raise FileNotFoundError(f"Google Cloud Vision 凭证文件不存在: {credentials_path}")

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=image_data)

        language_hints = engine_config.get("language_hints", ["zh", "en"])
        enable_text_detection = engine_config.get("enable_text_detection", True)

        text_kwargs: Dict[str, Any] = {}
        if language_hints:
            text_kwargs["image_context"] = vision.ImageContext(language_hints=language_hints)

        if enable_text_detection:
            response = client.text_detection(image=image, **text_kwargs)  # type: ignore[arg-type]
        else:
            response = client.document_text_detection(image=image, **text_kwargs)  # type: ignore[arg-type]

        if response.error.message:
            raise RuntimeError(f"Google Cloud Vision API 错误: {response.error.message}")

        texts = response.text_annotations
        full_text = texts[0].description if texts else ""

        doc_response = client.document_text_detection(image=image, **text_kwargs)  # type: ignore[arg-type]
        avg_confidence = self._compute_google_confidence(doc_response)
        language = self._collect_google_languages(doc_response)

        # 应用后处理校正（如果启用）
        enable_post_process = engine_config.get("enable_post_process", True)
        if enable_post_process:
            with log_performance("OCR后处理校正", logger):
                full_text = self._apply_post_process(full_text, engine_config)
        
        text_length = len(full_text.strip())
        logger.info(
            f"Google Cloud Vision OCR完成 - 文本长度: {text_length}, 置信度: {avg_confidence:.2f}, 语言: {language}",
            extra={"context": {"text_length": text_length, "confidence": avg_confidence, "language": language}}
        )

        return {
            "text": full_text.strip(),
            "confidence": avg_confidence,
            "language": language or "unknown",
            "engine": OCREngineType.GOOGLE_CLOUD_VISION.value,
            "structured_data": None,
        }

    def get_supported_engines(self) -> Dict[str, Dict[str, Any]]:
        """列出可用引擎及状态"""
        result: Dict[str, Dict[str, Any]] = {}
        for name, config in self.engine_configs.items():
            result[name] = {
                "description": config.get("description", "无描述"),
                "configurable": True,
                "available": self._check_engine_availability(name),
            }
        return result

    def _get_position_label(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        img_width: int,
        img_height: int,
    ) -> str:
        """根据相对位置返回九宫格标签"""
        if not img_width or not img_height:
            return "unknown"

        center_x = x + width / 2
        center_y = y + height / 2

        rel_x = center_x / img_width
        rel_y = center_y / img_height

        if rel_y < 0.33:
            vertical = "top"
        elif rel_y < 0.67:
            vertical = "middle"
        else:
            vertical = "bottom"

        if rel_x < 0.33:
            horizontal = "left"
        elif rel_x < 0.67:
            horizontal = "center"
        else:
            horizontal = "right"

        return f"{vertical}-{horizontal}"

    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"OCR 配置文件不存在: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as source:
            config_data = json.load(source)
        if "ocr_engines" not in config_data:
            raise ValueError("OCR 配置缺少 'ocr_engines' 节点")
        return config_data

    def _save_config(self) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as target:
            json.dump(self.config_data, target, ensure_ascii=False, indent=4)

    def _resolve_path(self, path_value: Optional[str]) -> Optional[str]:
        if not path_value:
            return None
        candidate = Path(path_value)
        if not candidate.is_absolute():
            # 相对于项目根目录（当前工作目录）解析，而不是相对于配置文件目录
            candidate = Path.cwd() / candidate
        return str(candidate.resolve())

    def _collect_google_languages(self, doc_response: Any) -> str:
        if not doc_response or not doc_response.full_text_annotation:
            return ""
        detected: list[str] = []
        for page in doc_response.full_text_annotation.pages:
            for prop in page.property.detected_languages:
                if prop.language_code and prop.language_code not in detected:
                    detected.append(prop.language_code)
        return ",".join(detected)

    def _compute_google_confidence(self, doc_response: Any) -> float:
        if not doc_response or not doc_response.full_text_annotation:
            return 95.0
        total = 0.0
        count = 0
        for page in doc_response.full_text_annotation.pages:
            for block in page.blocks:
                if hasattr(block, "confidence"):
                    total += block.confidence
                    count += 1
        return (total / count * 100) if count else 95.0

    def _check_engine_availability(self, engine_name: str) -> bool:
        if engine_name == OCREngineType.PYTESSERACT.value:
            try:
                pytesseract.get_tesseract_version()
                return True
            except Exception:
                return False
        if engine_name == OCREngineType.GOOGLE_CLOUD_VISION.value:
            try:
                import google.cloud.vision  # noqa: F401
            except ImportError:
                return False

            config = self.engine_configs.get(engine_name, {})
            credentials_path = self._resolve_path(config.get("credentials_path"))
            return bool(credentials_path and os.path.exists(credentials_path))
        return False

    def _to_engine_type(self, engine_name: str) -> OCREngineType:
        try:
            return OCREngineType(engine_name)
        except ValueError as exc:
            raise ValueError(f"未知的 OCR 引擎类型: {engine_name}") from exc

    def _apply_post_process(self, text: str, engine_config: Dict[str, Any]) -> str:
        """
        应用后处理校正（用于不支持自定义字典的引擎，如 Google Cloud Vision）
        
        Args:
            text: 原始 OCR 识别文本
            engine_config: 引擎配置
        
        Returns:
            校正后的文本
        """
        try:
            from ocr_post_process import create_post_processor
            
            # 检查是否启用后处理
            enable_post_process = engine_config.get("enable_post_process", True)
            if not enable_post_process:
                return text
            
            # 获取自定义词汇表路径
            custom_words_path = engine_config.get("custom_words_path")
            if not custom_words_path:
                # 尝试从 pytesseract 配置中获取
                pytesseract_config = self.engine_configs.get(OCREngineType.PYTESSERACT.value, {})
                custom_words_path = pytesseract_config.get("custom_words_path")
            
            if custom_words_path:
                custom_words_path = self._resolve_path(custom_words_path)
                if custom_words_path and os.path.exists(custom_words_path):
                    processor = create_post_processor(custom_words_path)
                    corrected_text = processor.correct_text(text, use_fuzzy_match=True)
                    logger.debug(f"后处理校正完成 - 原始长度: {len(text)}, 校正后长度: {len(corrected_text)}")
                    return corrected_text
        except Exception as e:
            # 后处理失败不影响主流程
            logger.warning(f"后处理校正失败: {e}", extra={"context": {"error": str(e)}})
        
        return text


if __name__ == "__main__":
    import asyncio

    async def main():
        manager = OCREngineManager()
        image_data = open("test_data/invoice1.png", "rb").read()
        result = await manager.process_image_with_current_engine(image_data)
        print(json.dumps(result, indent=4, ensure_ascii=False))
    asyncio.run(main())

