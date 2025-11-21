"""
PDF 处理模块：支持图片型 PDF 和混合图文 PDF
"""
import io
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from pdf2image import convert_from_bytes, convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

from PIL import Image


def is_pdf(file_data: bytes) -> bool:
    """检查文件是否为 PDF"""
    return file_data[:4] == b"%PDF"


def process_pdf(
    pdf_data: bytes, 
    dpi: int = 300,  # 提高DPI以提高识别准确率
    first_page: Optional[int] = None,
    last_page: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    处理 PDF 文件，支持图片型 PDF 和混合图文 PDF
    
    Args:
        pdf_data: PDF 文件的字节数据
        dpi: 转换图片时的 DPI（默认 200）
        first_page: 起始页码（从 1 开始，None 表示从第一页开始）
        last_page: 结束页码（None 表示到最后一页）
    
    Returns:
        包含每页图片和文本的列表
    """
    pages = []
    
    # 方法1：使用 PyMuPDF 提取文本和图片（适合混合图文 PDF）
    if PYMUPDF_AVAILABLE:
        try:
            doc = fitz.open(stream=pdf_data, filetype="pdf")
            total_pages = len(doc)
            
            start_page = (first_page - 1) if first_page else 0
            end_page = (last_page - 1) if last_page else (total_pages - 1)
            
            for page_num in range(start_page, min(end_page + 1, total_pages)):
                page = doc[page_num]
                
                # 提取文本
                text = page.get_text()
                # 确保 text 是字符串类型（page.get_text() 返回 str，但类型检查器可能不识别）
                # 使用类型转换确保类型检查器理解这是字符串
                text_str: str = str(text) if text is not None else ""
                
                # 转换为图片（使用高质量设置）
                # 使用更高的缩放因子以提高图片质量
                zoom = dpi / 72.0
                mat = fitz.Matrix(zoom, zoom)
                # 使用抗锯齿和高质量渲染
                pix = page.get_pixmap(matrix=mat, alpha=False)
                # 转换为PNG格式，确保高质量
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                
                # 确保图片模式正确（RGB）
                if image.mode != "RGB":
                    image = image.convert("RGB")
                
                # pyright: ignore[reportAttributeAccessIssue]
                has_text = bool(text_str.strip())
                # pyright: ignore[reportAttributeAccessIssue]
                is_image_only = not bool(text_str.strip())
                
                pages.append({
                    "page_number": page_num + 1,
                    "image": image,
                    "image_bytes": img_data,
                    "text": text_str,
                    "has_text": has_text,
                    "is_image_only": is_image_only,
                })
            
            doc.close()
            return pages
        except Exception as e:
            print(f"PyMuPDF 处理失败: {e}，尝试使用 pdf2image")
    
    # 方法2：使用 pdf2image（适合图片型 PDF）
    if PDF2IMAGE_AVAILABLE:
        try:
            # pdf2image 的 convert_from_bytes 接受 Optional[int]，但类型检查器可能不识别
            # 明确处理 None 值以避免类型错误
            if first_page is not None and last_page is not None:
                images = convert_from_bytes(
                    pdf_data, dpi=dpi, first_page=first_page, last_page=last_page
                )  # type: ignore[arg-type]
            elif first_page is not None:
                images = convert_from_bytes(
                    pdf_data, dpi=dpi, first_page=first_page
                )  # type: ignore[arg-type]
            elif last_page is not None:
                images = convert_from_bytes(
                    pdf_data, dpi=dpi, last_page=last_page
                )  # type: ignore[arg-type]
            else:
                images = convert_from_bytes(pdf_data, dpi=dpi)
            
            for idx, image in enumerate(images):
                page_num = (first_page - 1 + idx) if first_page else (idx + 1)
                
                # 确保图片模式正确（RGB）
                if image.mode != "RGB":
                    image = image.convert("RGB")
                
                # 将图片转换为字节（使用高质量PNG）
                buffer = io.BytesIO()
                # 使用高质量PNG保存，最小压缩
                image.save(buffer, format="PNG", optimize=False, compress_level=1)
                img_bytes = buffer.getvalue()
                
                pages.append({
                    "page_number": page_num,
                    "image": image,
                    "image_bytes": img_bytes,
                    "text": "",  # pdf2image 不提取文本
                    "has_text": False,
                    "is_image_only": True,
                })
            
            return pages
        except Exception as e:
            print(f"pdf2image 处理失败: {e}")
            raise RuntimeError(f"PDF 处理失败: {e}")
    
    raise RuntimeError("未安装 PDF 处理库，请安装: pip install pdf2image PyMuPDF")


def process_pdf_file(
    pdf_path: str | Path,
    dpi: int = 200,
    first_page: Optional[int] = None,
    last_page: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    从文件路径处理 PDF
    
    Args:
        pdf_path: PDF 文件路径
        dpi: 转换图片时的 DPI
        first_page: 起始页码
        last_page: 结束页码
    
    Returns:
        包含每页图片和文本的列表
    """
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
    return process_pdf(pdf_data, dpi=dpi, first_page=first_page, last_page=last_page)

