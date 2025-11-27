"""
统一的日志配置模块

提供统一的日志管理，支持：
- 统一日志格式
- 性能分析（执行时间记录）
- 问题追踪（上下文信息）
- 日志文件管理（按日期轮转）
"""

import logging
import logging.handlers
import os
import sys
import time
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional

# 日志目录
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# 日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DETAILED_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s - %(message)s"

# 日志文件路径
APP_LOG_FILE = LOG_DIR / "app.log"
ERROR_LOG_FILE = LOG_DIR / "error.log"
PERFORMANCE_LOG_FILE = LOG_DIR / "performance.log"


def setup_logging(
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
    detailed_format: bool = False,
) -> None:
    """
    配置全局日志系统
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: 是否记录到文件
        log_to_console: 是否输出到控制台
        detailed_format: 是否使用详细格式（包含文件名、行号等）
    """
    # 获取日志级别
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # 选择日志格式
    formatter = logging.Formatter(
        DETAILED_LOG_FORMAT if detailed_format else LOG_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 根日志记录器配置
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # 清除已有的处理器
    root_logger.handlers.clear()
    
    # 控制台处理器
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # 文件处理器（应用日志）
    if log_to_file:
        # 使用TimedRotatingFileHandler，每天轮转一次
        file_handler = logging.handlers.TimedRotatingFileHandler(
            APP_LOG_FILE,
            when="midnight",
            interval=1,
            backupCount=30,  # 保留30天
            encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # 错误日志文件（只记录ERROR及以上级别）
        error_handler = logging.handlers.TimedRotatingFileHandler(
            ERROR_LOG_FILE,
            when="midnight",
            interval=1,
            backupCount=90,  # 保留90天
            encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)
        
        # 性能日志文件（单独的日志器）
        performance_handler = logging.handlers.TimedRotatingFileHandler(
            PERFORMANCE_LOG_FILE,
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8"
        )
        performance_handler.setLevel(logging.INFO)
        performance_handler.setFormatter(formatter)
        
        performance_logger = logging.getLogger("performance")
        performance_logger.setLevel(logging.INFO)
        performance_logger.addHandler(performance_handler)
        performance_logger.propagate = False  # 不传播到根日志器，避免重复记录
    
    # 设置第三方库的日志级别（避免过多输出）
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志记录器
    
    Args:
        name: 日志记录器名称（通常是模块名）
    
    Returns:
        日志记录器实例
    """
    return logging.getLogger(name)


@contextmanager
def log_performance(operation_name: str, logger: Optional[logging.Logger] = None, extra_context: Optional[Dict[str, Any]] = None):
    """
    性能日志上下文管理器
    
    Usage:
        with log_performance("OCR处理", logger, {"engine": "pytesseract"}):
            # 执行操作
            result = ocr_process()
    
    Args:
        operation_name: 操作名称
        logger: 日志记录器（如果为None，使用performance日志器）
        extra_context: 额外的上下文信息
    """
    if logger is None:
        logger = logging.getLogger("performance")
    
    start_time = time.perf_counter()
    context_info = extra_context or {}
    
    try:
        logger.info(f"开始执行: {operation_name}", extra={"context": context_info})
        yield
        elapsed_time = time.perf_counter() - start_time
        logger.info(
            f"完成执行: {operation_name} - 耗时: {elapsed_time:.3f}秒",
            extra={"context": {**context_info, "elapsed_time": elapsed_time}}
        )
    except Exception as e:
        elapsed_time = time.perf_counter() - start_time
        logger.error(
            f"执行失败: {operation_name} - 耗时: {elapsed_time:.3f}秒 - 错误: {str(e)}",
            extra={"context": {**context_info, "elapsed_time": elapsed_time, "error": str(e)}},
            exc_info=True
        )
        raise


def log_function_performance(operation_name: Optional[str] = None, log_args: bool = False, log_result: bool = False):
    """
    函数性能日志装饰器
    
    Usage:
        @log_function_performance("OCR识别", log_args=True)
        def process_image(image_data):
            # 函数实现
            return result
    
    Args:
        operation_name: 操作名称（如果为None，使用函数名）
        log_args: 是否记录函数参数
        log_result: 是否记录函数返回值
    """
    def decorator(func: Callable) -> Callable:
        op_name = operation_name or func.__name__
        logger = get_logger(func.__module__)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            context = {}
            
            if log_args:
                context["args"] = str(args)[:200]  # 限制长度
                context["kwargs"] = str(kwargs)[:200]
            
            try:
                result = func(*args, **kwargs)
                elapsed_time = time.perf_counter() - start_time
                
                log_msg = f"{op_name} 完成 - 耗时: {elapsed_time:.3f}秒"
                if log_result and result is not None:
                    result_str = str(result)[:200]
                    log_msg += f" - 结果: {result_str}"
                
                logger.info(log_msg, extra={"context": context, "elapsed_time": elapsed_time})
                return result
            except Exception as e:
                elapsed_time = time.perf_counter() - start_time
                logger.error(
                    f"{op_name} 失败 - 耗时: {elapsed_time:.3f}秒 - 错误: {str(e)}",
                    extra={"context": context, "elapsed_time": elapsed_time},
                    exc_info=True
                )
                raise
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            context = {}
            
            if log_args:
                context["args"] = str(args)[:200]
                context["kwargs"] = str(kwargs)[:200]
            
            try:
                result = await func(*args, **kwargs)
                elapsed_time = time.perf_counter() - start_time
                
                log_msg = f"{op_name} 完成 - 耗时: {elapsed_time:.3f}秒"
                if log_result and result is not None:
                    result_str = str(result)[:200]
                    log_msg += f" - 结果: {result_str}"
                
                logger.info(log_msg, extra={"context": context, "elapsed_time": elapsed_time})
                return result
            except Exception as e:
                elapsed_time = time.perf_counter() - start_time
                logger.error(
                    f"{op_name} 失败 - 耗时: {elapsed_time:.3f}秒 - 错误: {str(e)}",
                    extra={"context": context, "elapsed_time": elapsed_time},
                    exc_info=True
                )
                raise
        
        # 检查是否为协程函数
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_exception(logger: logging.Logger, message: str, exc_info: bool = True, extra_context: Optional[Dict[str, Any]] = None):
    """
    记录异常的辅助函数
    
    Args:
        logger: 日志记录器
        message: 错误消息
        exc_info: 是否包含异常堆栈信息
        extra_context: 额外的上下文信息
    """
    context = extra_context or {}
    logger.error(
        message,
        extra={"context": context},
        exc_info=exc_info
    )


# 初始化日志系统（在模块导入时执行）
# 可以通过环境变量配置
_log_level = os.getenv("LOG_LEVEL", "INFO")
_log_to_file = os.getenv("LOG_TO_FILE", "true").lower() == "true"
_log_to_console = os.getenv("LOG_TO_CONSOLE", "true").lower() == "true"
_detailed_format = os.getenv("LOG_DETAILED_FORMAT", "false").lower() == "true"

setup_logging(
    log_level=_log_level,
    log_to_file=_log_to_file,
    log_to_console=_log_to_console,
    detailed_format=_detailed_format
)

