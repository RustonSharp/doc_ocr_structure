import base64
import json
from io import BytesIO
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from llm import LLMService
from ocr import OCREngineManager, OCREngineType
from pdf_processor import is_pdf, process_pdf
from pre_preocess import pre_preocess_for_pytesseract, pre_preocess_for_google_vision
from structure import structure_ocr_result
from output_generator import generate_output_files

# 接口1：上传图片/PDF，进行预处理，ocr识别，llm处理，返回结果
# 返回结果包括：原始图片、预处理后的图片、最终结构化的数据
app = FastAPI(title="OCR 与文本结构化一体化工具")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """根路径，返回服务信息"""
    return {
        "service": "OCR 与文本结构化一体化工具",
        "version": "1.0.0",
        "endpoints": {
            "ocr": "/ocr",
            "batch": "/batch",
            "docs": "/docs",
            "health": "/health",
        }
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "message": "服务运行正常"}


async def process_single_image(
    image_data: bytes,
    is_pdf_file: bool = False,
    page_number: Optional[int] = None,
) -> dict:
    """处理单张图片或 PDF 页面"""
    # 预处理
    ocr_engine = OCREngineManager()
    
    if ocr_engine.current_engine == OCREngineType.PYTESSERACT:
        pre_processed_image = pre_preocess_for_pytesseract(image_data)
        if pre_processed_image is None:
            raise HTTPException(status_code=400, detail="预处理失败")
        processed_bytes, processed_preview = _image_to_bytes_and_data_url(pre_processed_image)
        input_bytes = processed_bytes
    else:
        pre_processed_image = pre_preocess_for_google_vision(image_data)
        if pre_processed_image is None:
            raise HTTPException(status_code=400, detail="预处理失败")
        processed_bytes, processed_preview = _image_to_bytes_and_data_url(pre_processed_image)
        input_bytes = image_data  # Google Vision 使用原始图片
    
    # OCR 识别
    ocr_result = await ocr_engine.process_image_with_current_engine(input_bytes)
    if ocr_result is None:
        raise HTTPException(status_code=400, detail="OCR识别失败")
    
    # 结构化处理
    structured_result = structure_ocr_result(ocr_result)
    
    # 如果是 PDF 页面，添加页码信息
    if is_pdf_file and page_number:
        structured_result["page_number"] = page_number
    
    return {
        "pre_processed_image": processed_preview,
        "ocr_result": ocr_result,
        "structured_result": structured_result,
    }


@app.post("/ocr")
async def ocr(file: UploadFile = File(...), save_files: bool = True):
    """
    OCR 识别和结构化处理接口
    
    Args:
        file: 上传的图片或 PDF 文件
        save_files: 是否保存输出文件到本地
    
    Returns:
        处理结果
    """
    file_data = await file.read()
    file_ext = Path(file.filename).suffix.lower() if file.filename else ""
    
    # 判断是否为 PDF
    if is_pdf(file_data) or file_ext == ".pdf":
        # 处理 PDF（使用更高的DPI以提高识别准确率）
        try:
            # 使用300 DPI以提高识别质量（可根据需要调整，300-400 DPI通常效果较好）
            pdf_pages = process_pdf(file_data, dpi=300)
            
            results = []
            for page_info in pdf_pages:
                page_result = await process_single_image(
                    page_info["image_bytes"],
                    is_pdf_file=True,
                    page_number=page_info["page_number"],
                )
                results.append(page_result)
                
                # 如果配置了保存文件
                if save_files:
                    base_name = Path(file.filename or "pdf").stem
                    output_dir = Path("output") / f"{base_name}_page_{page_info['page_number']}"
                    generate_output_files(
                        page_result["structured_result"],
                        output_dir,
                        base_name=f"{base_name}_page_{page_info['page_number']}",
                    )
            
            return {
                "file_type": "pdf",
                "total_pages": len(pdf_pages),
                "results": results,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF 处理失败: {str(e)}")
    else:
        # 处理单张图片
        try:
            result = await process_single_image(file_data)
            
            # 如果配置了保存文件
            if save_files:
                base_name = Path(file.filename or "image").stem
                output_dir = Path("output") / base_name
                files_generated = generate_output_files(
                    result["structured_result"],
                    output_dir,
                    base_name=base_name,
                )
                result["output_files"] = {
                    str(k): str(v) for k, v in files_generated.items()
                }
            
            return {
                "file_type": "image",
                "result": result,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"图片处理失败: {str(e)}")


@app.post("/batch")
async def batch_process(files: List[UploadFile] = File(...), save_files: bool = True):
    """
    批量处理接口
    
    Args:
        files: 上传的文件列表
        save_files: 是否保存输出文件
    
    Returns:
        批量处理结果
    """
    results = []
    successful = 0
    failed = 0
    
    for file in files:
        try:
            file_data = await file.read()
            file_ext = Path(file.filename).suffix.lower() if file.filename else ""
            
            if is_pdf(file_data) or file_ext == ".pdf":
                # PDF 处理（使用300 DPI以提高识别质量）
                pdf_pages = process_pdf(file_data, dpi=300)
                for page_info in pdf_pages:
                    page_result = await process_single_image(
                        page_info["image_bytes"],
                        is_pdf_file=True,
                        page_number=page_info["page_number"],
                    )
                    results.append({
                        "filename": file.filename,
                        "page": page_info["page_number"],
                        "status": "success",
                        "result": page_result["structured_result"],
                    })
                    successful += 1
                    
                    if save_files:
                        base_name = Path(file.filename or "pdf").stem
                        output_dir = Path("output") / f"{base_name}_page_{page_info['page_number']}"
                        generate_output_files(
                            page_result["structured_result"],
                            output_dir,
                            base_name=f"{base_name}_page_{page_info['page_number']}",
                        )
            else:
                # 图片处理
                result = await process_single_image(file_data)
                results.append({
                    "filename": file.filename,
                    "status": "success",
                    "result": result["structured_result"],
                })
                successful += 1
                
                if save_files:
                    base_name = Path(file.filename or "image").stem
                    output_dir = Path("output") / base_name
                    generate_output_files(
                        result["structured_result"],
                        output_dir,
                        base_name=base_name,
                    )
        except Exception as e:
            failed += 1
            results.append({
                "filename": file.filename,
                "status": "failed",
                "error": str(e),
            })
    
    return {
        "total_files": len(files),
        "successful": successful,
        "failed": failed,
        "results": results,
    }


def _image_to_bytes_and_data_url(image) -> tuple[bytes, str]:
    """将 PIL Image 转换为字节和 data URL"""
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    byte_data = buffer.getvalue()
    data_url = "data:image/png;base64," + base64.b64encode(byte_data).decode("utf-8")
    return byte_data, data_url


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
