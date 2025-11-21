"""
输出文件生成模块：生成 ocr_raw_text.txt 和 validation_list.csv
"""
import csv
import json
from pathlib import Path
from typing import Any, Dict, Optional


def save_ocr_raw_text(text: str, output_path: str | Path) -> None:
    """
    保存 OCR 原始文本到文件
    
    Args:
        text: OCR 识别的文本
        output_path: 输出文件路径
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)


def save_validation_list(
    structured_data: Dict[str, Any],
    output_path: str | Path,
    threshold: float = 80.0,
) -> None:
    """
    生成并保存待人工校验清单（CSV 格式）
    
    Args:
        structured_data: 结构化数据字典（包含 fields 和 validation_list）
        output_path: 输出 CSV 文件路径
        threshold: 置信度阈值（≤此值的字段需要校验）
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fields = structured_data.get("fields", {})
    validation_list = structured_data.get("validation_list", [])
    
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        # 写入表头
        writer.writerow(["字段名", "字段值", "置信度", "数据来源", "是否需要校验"])
        
        # 写入需要校验的字段
        for field_name in validation_list:
            field_info = fields.get(field_name, {})
            writer.writerow([
                field_name,
                str(field_info.get("value", "")),
                f"{field_info.get('confidence', 0.0):.2f}",
                field_info.get("source", "unknown"),
                "是" if field_info.get("needs_validation", False) else "否",
            ])
        
        # 如果 validation_list 为空，但仍有低置信度字段，也写入
        if not validation_list:
            for field_name, field_info in fields.items():
                if field_info.get("confidence", 100.0) <= threshold:
                    writer.writerow([
                        field_name,
                        str(field_info.get("value", "")),
                        f"{field_info.get('confidence', 0.0):.2f}",
                        field_info.get("source", "unknown"),
                        "是",
                    ])


def save_structured_json(
    result: Dict[str, Any],
    output_path: str | Path,
) -> None:
    """
    保存结构化 JSON 结果
    
    Args:
        result: 完整的处理结果
        output_path: 输出 JSON 文件路径
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


def generate_output_files(
    result: Dict[str, Any],
    output_dir: str | Path,
    base_name: str = "result",
) -> Dict[str, Path]:
    """
    生成所有输出文件
    
    Args:
        result: 完整的处理结果
        output_dir: 输出目录
        base_name: 文件名基础（不含扩展名）
    
    Returns:
        生成的文件路径字典
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    files = {}
    
    # 1. OCR 原始文本
    ocr_text = result.get("raw_ocr", {}).get("text", "")
    if ocr_text:
        # 根据需求，文件名应该是 ocr_raw_text.txt（不带前缀）
        ocr_txt_path = output_dir / "ocr_raw_text.txt"
        save_ocr_raw_text(ocr_text, ocr_txt_path)
        files["ocr_raw_text"] = ocr_txt_path
    
    # 2. 校验清单
    structured_data = result.get("structured_data", {})
    if structured_data:
        # 根据需求，文件名应该是 validation_list.csv（不带前缀）
        validation_csv_path = output_dir / "validation_list.csv"
        save_validation_list(structured_data, validation_csv_path)
        files["validation_list"] = validation_csv_path
    
    # 3. 结构化 JSON（保留带前缀的文件名，便于区分不同文件）
    json_path = output_dir / f"{base_name}_structured.json"
    save_structured_json(result, json_path)
    files["structured_json"] = json_path
    
    return files

