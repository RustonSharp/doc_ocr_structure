import base64
import json
import re
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from llm import LLMService
from ocr import OCREngineManager, OCREngineType
from pdf_processor import is_pdf, process_pdf
from pre_preocess import pre_preocess_for_pytesseract, pre_preocess_for_google_vision
from structure import structure_ocr_result
from output_generator import generate_output_files
from structure_config import clean_json_file, check_structure_config, update_structure_config

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


def generate_timestamped_name(base_name: str, is_pdf: bool = False, page_number: Optional[int] = None) -> tuple[str, str]:
    """
    生成带时间戳的文件名和目录名
    
    Args:
        base_name: 基础文件名（不含扩展名）
        is_pdf: 是否为PDF文件
        page_number: PDF页码（可选）
    
    Returns:
        (output_dir_name, base_name_with_timestamp) 元组
    """
    # 生成时间戳：YYYYMMDD_HHMMSS
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if is_pdf and page_number is not None:
        # PDF文件：base_name_page_N_YYYYMMDD_HHMMSS
        dir_name = f"{base_name}_page_{page_number}_{timestamp}"
        file_base_name = f"{base_name}_page_{page_number}_{timestamp}"
    else:
        # 单图片：base_name_YYYYMMDD_HHMMSS
        dir_name = f"{base_name}_{timestamp}"
        file_base_name = f"{base_name}_{timestamp}"
    
    return dir_name, file_base_name


@app.on_event("startup")
async def startup_event():
    """应用启动时执行清理操作"""
    print("正在清理 JSON 配置文件...")
    clean_json_file()
    print("JSON 配置文件清理完成")
    print("正在检查结构化配置文件...")
    updated_json_file_name_list = check_structure_config()
    print("结构化配置文件检查完成")
    if len(updated_json_file_name_list) > 0:
        print("正在更新结构化配置文件，数量：", len(updated_json_file_name_list))
        update_structure_config(updated_json_file_name_list)
        print("结构化配置文件更新完成，数量：", len(updated_json_file_name_list))
    else:
        print("结构化配置文件无需更新")

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
        # Google Vision 也使用预处理后的图片（倾斜校正后的），以提高识别准确率
        input_bytes = processed_bytes
    
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
                    dir_name, file_base_name = generate_timestamped_name(
                        base_name, is_pdf=True, page_number=page_info['page_number']
                    )
                    output_dir = Path("output") / dir_name
                    generate_output_files(
                        page_result["structured_result"],
                        output_dir,
                        base_name=file_base_name,
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
                dir_name, file_base_name = generate_timestamped_name(base_name, is_pdf=False)
                output_dir = Path("output") / dir_name
                files_generated = generate_output_files(
                    result["structured_result"],
                    output_dir,
                    base_name=file_base_name,
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
                        "result": page_result,  # 返回完整结果，包括预处理图片、OCR结果等
                    })
                    successful += 1
                    
                    if save_files:
                        base_name = Path(file.filename or "pdf").stem
                        dir_name, file_base_name = generate_timestamped_name(
                            base_name, is_pdf=True, page_number=page_info['page_number']
                        )
                        output_dir = Path("output") / dir_name
                        generate_output_files(
                            page_result["structured_result"],
                            output_dir,
                            base_name=file_base_name,
                        )
            else:
                # 图片处理
                result = await process_single_image(file_data)
                results.append({
                    "filename": file.filename,
                    "status": "success",
                    "result": result,  # 返回完整结果，包括预处理图片、OCR结果等
                })
                successful += 1
                
                if save_files:
                    base_name = Path(file.filename or "image").stem
                    dir_name, file_base_name = generate_timestamped_name(base_name, is_pdf=False)
                    output_dir = Path("output") / dir_name
                    generate_output_files(
                        result["structured_result"],
                        output_dir,
                        base_name=file_base_name,
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


@app.post("/regenerate")
async def regenerate_output(request: Request):
    """
    重新生成输出文件（用于字段修正后）
    
    Request Body (JSON):
        structured_result: 修正后的结构化结果
        output_dir: 输出目录路径
        base_name: 文件名基础（不含扩展名）
        ocr_result: OCR识别结果（可选，用于保存原始文本）
    
    Returns:
        生成的文件路径信息
    """
    try:
        # 从请求体中读取JSON数据
        body = await request.json()
        structured_result = body.get("structured_result", {})
        output_dir = body.get("output_dir", "")
        base_name = body.get("base_name", "result")
        ocr_result = body.get("ocr_result")
        
        if not structured_result:
            raise HTTPException(status_code=400, detail="缺少 structured_result 参数")
        if not base_name:
            raise HTTPException(status_code=400, detail="缺少 base_name 参数")
        
        # 从base_name中提取原始文件名（去掉可能的时间戳和页码）
        # base_name格式可能是: invoice1_20240101_120000 或 invoice1_page_1_20240101_120000
        base_name_clean = re.sub(r'_\d{8}_\d{6}$', '', base_name)
        # 如果包含_page_N，提取页码
        page_match = re.search(r'_page_(\d+)(?:_\d{8}_\d{6})?$', base_name_clean)
        if page_match:
            page_number = int(page_match.group(1))
            base_name_only = re.sub(r'_page_\d+(?:_\d{8}_\d{6})?$', '', base_name_clean)
            dir_name, file_base_name = generate_timestamped_name(
                base_name_only, is_pdf=True, page_number=page_number
            )
        else:
            dir_name, file_base_name = generate_timestamped_name(base_name_clean, is_pdf=False)
        
        # 使用新的时间戳生成输出目录
        output_path = Path("output") / dir_name
        
        # 构建完整的结果对象（格式需要匹配 generate_output_files 的期望）
        # structured_result 应该包含 structured_data 字段
        # 如果 structured_result 本身就是一个包含 structured_data 的对象，直接使用
        # 否则需要检查数据格式
        result = {}
        
        # 检查 structured_result 的格式
        if "structured_data" in structured_result:
            # 如果 structured_result 已经包含 structured_data，直接使用
            result["structured_data"] = structured_result["structured_data"]
        else:
            # 如果 structured_result 本身就是 structured_data，包装它
            result["structured_data"] = structured_result
        
        # 添加 OCR 原始文本（如果有）
        if ocr_result:
            ocr_text = ocr_result.get("text", "")
            if ocr_text:
                result["raw_ocr"] = {"text": ocr_text}
        
        # 添加其他字段（如果有）
        if "cleaned_text" in structured_result:
            result["cleaned_text"] = structured_result["cleaned_text"]
        if "structure_config" in structured_result:
            result["structure_config"] = structured_result["structure_config"]
        if "entities" in structured_result:
            result["entities"] = structured_result["entities"]
        
        # 生成输出文件
        files_generated = generate_output_files(
            result,
            output_path,
            base_name=base_name,
        )
        
        return {
            "success": True,
            "message": "输出文件已重新生成",
            "files": {
                str(k): str(v) for k, v in files_generated.items()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"重新生成输出文件失败: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


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
