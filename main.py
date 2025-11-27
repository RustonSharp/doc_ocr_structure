import base64
import json
import re
import time
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from llm import LLMService
from ocr import OCREngineManager, OCREngineType
from pdf_processor import is_pdf, process_pdf
from pre_preocess import pre_preocess_for_pytesseract, pre_preocess_for_google_vision
from structure import structure_ocr_result
from output_generator import generate_output_files
from structure_config import clean_json_file, check_structure_config, update_structure_config
from logging_config import get_logger, log_performance, log_exception

# 接口1：上传图片/PDF，进行预处理，ocr识别，llm处理，返回结果
# 返回结果包括：原始图片、预处理后的图片、最终结构化的数据
app = FastAPI(title="OCR 与文本结构化一体化工具")

# 获取日志记录器
logger = get_logger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件，记录所有API请求"""
    
    async def dispatch(self, request, call_next):
        start_time = time.time()
        
        # 记录请求信息
        logger.info(
            f"请求开始: {request.method} {request.url.path}",
            extra={
                "context": {
                    "method": request.method,
                    "path": str(request.url.path),
                    "client": request.client.host if request.client else "unknown",
                    "query_params": dict(request.query_params),
                }
            }
        )
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # 记录响应信息
            logger.info(
                f"请求完成: {request.method} {request.url.path} - 状态码: {response.status_code} - 耗时: {process_time:.3f}秒",
                extra={
                    "context": {
                        "method": request.method,
                        "path": str(request.url.path),
                        "status_code": response.status_code,
                        "process_time": process_time,
                    }
                }
            )
            
            return response
        except Exception as e:
            process_time = time.time() - start_time
            log_exception(
                logger,
                f"请求失败: {request.method} {request.url.path} - 耗时: {process_time:.3f}秒",
                extra_context={
                    "method": request.method,
                    "path": str(request.url.path),
                    "process_time": process_time,
                }
            )
            raise


app.add_middleware(LoggingMiddleware)


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
    logger.info("应用启动，开始初始化...")
    
    try:
        with log_performance("清理JSON配置文件", logger):
            clean_json_file()
        
        with log_performance("检查结构化配置文件", logger):
            updated_json_file_name_list = check_structure_config()
        
        if len(updated_json_file_name_list) > 0:
            logger.info(f"发现需要更新的配置文件: {len(updated_json_file_name_list)}个")
            with log_performance("更新结构化配置文件", logger, {"count": len(updated_json_file_name_list)}):
                update_structure_config(updated_json_file_name_list)
        else:
            logger.info("结构化配置文件无需更新")
        
        logger.info("应用初始化完成")
    except Exception as e:
        log_exception(logger, "应用启动初始化失败", extra_context={"error": str(e)})
        raise

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
    logger.debug("健康检查请求")
    return {"status": "ok", "message": "服务运行正常"}


async def process_single_image(
    image_data: bytes,
    is_pdf_file: bool = False,
    page_number: Optional[int] = None,
) -> dict:
    """处理单张图片或 PDF 页面"""
    context_info = {
        "is_pdf": is_pdf_file,
        "page_number": page_number,
        "image_size": len(image_data),
    }
    
    with log_performance("处理单张图片", logger, context_info):
        # 初始化OCR引擎
        ocr_engine = OCREngineManager()
        engine_info = ocr_engine.get_current_engine_info()
        logger.info(f"使用OCR引擎: {engine_info['current_engine']}", extra={"context": engine_info})
        
        # 预处理
        with log_performance("图像预处理", logger, {"engine": engine_info['current_engine']}):
            if ocr_engine.current_engine == OCREngineType.PYTESSERACT:
                pre_processed_image = pre_preocess_for_pytesseract(image_data)
                if pre_processed_image is None:
                    logger.error("图像预处理失败 (pytesseract)")
                    raise HTTPException(status_code=400, detail="预处理失败")
                processed_bytes, processed_preview = _image_to_bytes_and_data_url(pre_processed_image)
                input_bytes = processed_bytes
            else:
                pre_processed_image = pre_preocess_for_google_vision(image_data)
                if pre_processed_image is None:
                    logger.error("图像预处理失败 (google vision)")
                    raise HTTPException(status_code=400, detail="预处理失败")
                processed_bytes, processed_preview = _image_to_bytes_and_data_url(pre_processed_image)
                # Google Vision 也使用预处理后的图片（倾斜校正后的），以提高识别准确率
                input_bytes = processed_bytes
        
        # OCR 识别
        with log_performance("OCR识别", logger, {"engine": engine_info['current_engine']}):
            ocr_result = await ocr_engine.process_image_with_current_engine(input_bytes)
            if ocr_result is None:
                logger.error("OCR识别失败", extra={"context": {"engine": engine_info['current_engine']}})
                raise HTTPException(status_code=400, detail="OCR识别失败")
            
            logger.info(
                f"OCR识别完成 - 文本长度: {len(ocr_result.get('text', ''))}, 置信度: {ocr_result.get('confidence', 0):.2f}",
                extra={"context": {"engine": engine_info['current_engine'], "confidence": ocr_result.get('confidence', 0)}}
            )
        
        # 结构化处理
        with log_performance("结构化处理", logger):
            structured_result = structure_ocr_result(ocr_result)
            logger.info(
                f"结构化处理完成 - 覆盖率: {structured_result.get('structured_data', {}).get('coverage', 0):.2f}%",
                extra={"context": {"coverage": structured_result.get('structured_data', {}).get('coverage', 0)}}
            )
        
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
    filename = file.filename or "unknown"
    file_data = await file.read()
    file_ext = Path(filename).suffix.lower()
    file_size = len(file_data)
    
    logger.info(
        f"收到OCR处理请求 - 文件名: {filename}, 大小: {file_size} bytes, 保存文件: {save_files}",
        extra={"context": {"filename": filename, "file_size": file_size, "save_files": save_files}}
    )
    
    # 判断是否为 PDF
    if is_pdf(file_data) or file_ext == ".pdf":
        # 处理 PDF（使用更高的DPI以提高识别准确率）
        try:
            with log_performance("PDF处理", logger, {"filename": filename, "save_files": save_files}):
                # 使用300 DPI以提高识别质量（可根据需要调整，300-400 DPI通常效果较好）
                pdf_pages = process_pdf(file_data, dpi=300)
                logger.info(f"PDF解析完成 - 总页数: {len(pdf_pages)}", extra={"context": {"total_pages": len(pdf_pages)}})
                
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
                        base_name = Path(filename).stem
                        dir_name, file_base_name = generate_timestamped_name(
                            base_name, is_pdf=True, page_number=page_info['page_number']
                        )
                        output_dir = Path("output") / dir_name
                        with log_performance("生成输出文件", logger, {"base_name": file_base_name}):
                            generate_output_files(
                                page_result["structured_result"],
                                output_dir,
                                base_name=file_base_name,
                            )
                        logger.info(f"输出文件已保存 - 目录: {output_dir}", extra={"context": {"output_dir": str(output_dir)}})
                
                return {
                    "file_type": "pdf",
                    "total_pages": len(pdf_pages),
                    "results": results,
                }
        except Exception as e:
            log_exception(logger, f"PDF处理失败: {filename}", extra_context={"filename": filename, "file_size": file_size})
            raise HTTPException(status_code=500, detail=f"PDF 处理失败: {str(e)}")
    else:
        # 处理单张图片
        try:
            with log_performance("图片处理", logger, {"filename": filename, "save_files": save_files}):
                result = await process_single_image(file_data)
                
                # 如果配置了保存文件
                if save_files:
                    base_name = Path(filename).stem
                    dir_name, file_base_name = generate_timestamped_name(base_name, is_pdf=False)
                    output_dir = Path("output") / dir_name
                    with log_performance("生成输出文件", logger, {"base_name": file_base_name}):
                        files_generated = generate_output_files(
                            result["structured_result"],
                            output_dir,
                            base_name=file_base_name,
                        )
                    result["output_files"] = {
                        str(k): str(v) for k, v in files_generated.items()
                    }
                    logger.info(f"输出文件已保存 - 目录: {output_dir}", extra={"context": {"output_dir": str(output_dir)}})
                
                return {
                    "file_type": "image",
                    "result": result,
                }
        except Exception as e:
            log_exception(logger, f"图片处理失败: {filename}", extra_context={"filename": filename, "file_size": file_size})
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
    total_files = len(files)
    logger.info(
        f"收到批量处理请求 - 文件数量: {total_files}, 保存文件: {save_files}",
        extra={"context": {"total_files": total_files, "save_files": save_files}}
    )
    
    results = []
    successful = 0
    failed = 0
    
    with log_performance("批量处理", logger, {"total_files": total_files}):
        for idx, file in enumerate(files):
            filename = file.filename or f"file_{idx}"
            try:
                logger.info(f"处理文件 [{idx+1}/{total_files}]: {filename}")
                
                file_data = await file.read()
                file_ext = Path(filename).suffix.lower()
                file_size = len(file_data)
                
                if is_pdf(file_data) or file_ext == ".pdf":
                    # PDF 处理（使用300 DPI以提高识别质量）
                    with log_performance(f"批量PDF处理: {filename}", logger):
                        pdf_pages = process_pdf(file_data, dpi=300)
                        logger.info(f"PDF解析完成 - {filename}, 页数: {len(pdf_pages)}")
                        
                        for page_info in pdf_pages:
                            page_result = await process_single_image(
                                page_info["image_bytes"],
                                is_pdf_file=True,
                                page_number=page_info["page_number"],
                            )
                            results.append({
                                "filename": filename,
                                "page": page_info["page_number"],
                                "status": "success",
                                "result": page_result,
                            })
                            successful += 1
                            
                            if save_files:
                                base_name = Path(filename).stem
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
                    with log_performance(f"批量图片处理: {filename}", logger):
                        result = await process_single_image(file_data)
                        results.append({
                            "filename": filename,
                            "status": "success",
                            "result": result,
                        })
                        successful += 1
                        
                        if save_files:
                            base_name = Path(filename).stem
                            dir_name, file_base_name = generate_timestamped_name(base_name, is_pdf=False)
                            output_dir = Path("output") / dir_name
                            generate_output_files(
                                result["structured_result"],
                                output_dir,
                                base_name=file_base_name,
                            )
                
                logger.info(f"文件处理成功 [{idx+1}/{total_files}]: {filename}")
            except Exception as e:
                failed += 1
                log_exception(
                    logger,
                    f"文件处理失败 [{idx+1}/{total_files}]: {filename}",
                    extra_context={"filename": filename, "file_index": idx, "error": str(e)}
                )
                results.append({
                    "filename": filename,
                    "status": "failed",
                    "error": str(e),
                })
    
    logger.info(
        f"批量处理完成 - 总计: {total_files}, 成功: {successful}, 失败: {failed}",
        extra={"context": {"total_files": total_files, "successful": successful, "failed": failed}}
    )
    
    return {
        "total_files": total_files,
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
        log_exception(
            logger,
            "重新生成输出文件失败",
            extra_context={"base_name": base_name, "output_dir": str(output_path)}
        )
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
