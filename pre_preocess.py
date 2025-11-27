from PIL import Image
import cv2
import numpy as np
import io

from logging_config import get_logger, log_performance

logger = get_logger(__name__)


def pre_preocess_for_pytesseract(image_data: bytes):
    image = Image.open(io.BytesIO(image_data))
    image = preprocess_image(image)
    return image

def pre_preocess_for_google_vision(image_data: bytes):
    image = Image.open(io.BytesIO(image_data))
    image = preprocess_image(image, preserve_color=True)
    return image

def preprocess_image(image: Image.Image, preserve_color: bool = False) -> Image.Image:
    """图像预处理：倾斜校正、去噪、二值化"""
    img_size = image.size
    logger.debug(f"开始图像预处理 - 尺寸: {img_size}, 保留颜色: {preserve_color}", 
                extra={"context": {"width": img_size[0], "height": img_size[1], "preserve_color": preserve_color}})
    
    with log_performance("图像预处理", logger, {"width": img_size[0], "height": img_size[1], "preserve_color": preserve_color}):
        # 转换为numpy数组
        img_array = np.array(image)

        # 1. 倾斜校正（检测并纠正≤30°倾斜）
        img_array = correct_skew(img_array)

        # 对于需要保留彩色信息的引擎（例如Google Vision），仅做倾斜校正
        if preserve_color:
            logger.debug("预处理完成（仅倾斜校正）")
            return Image.fromarray(img_array)

        # 2. 转换为灰度图
        if len(img_array.shape) == 3:
            img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            img_gray = img_array
        
        # 3. 去噪处理
        img_gray = cv2.fastNlMeansDenoising(img_gray, None, 10, 7, 21)
        
        # 4. 增强对比度（CLAHE）
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        img_gray = clahe.apply(img_gray)
        
        # 5. 二值化
        _, img_binary = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 6. 形态学操作去除小噪点
        kernel = np.ones((2, 2), np.uint8)
        img_binary = cv2.morphologyEx(img_binary, cv2.MORPH_OPEN, kernel)
        
        # 7. 水印抑制（弱化浅色水印/盖章）
        watermark_kernel = np.ones((5, 5), np.uint8)
        watermark_layer = cv2.morphologyEx(img_binary, cv2.MORPH_CLOSE, watermark_kernel, iterations=1)
        img_binary = cv2.bitwise_and(img_binary, watermark_layer)
        
        logger.debug("预处理完成（完整流程：倾斜校正、去噪、增强、二值化、水印抑制）")
        # 转换回PIL图像
        return Image.fromarray(img_binary)

def correct_skew(image: np.ndarray) -> np.ndarray:
    """自动检测并校正图片倾斜（支持±30°）"""
    try:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image

        # 边缘检测
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # 霍夫变换检测直线
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
        
        if lines is None:
            return image
        
        # 计算倾斜角度
        angles = []
        for rho, theta in lines[:, 0]:
            angle = (theta * 180 / np.pi) - 90
            if abs(angle) <= 30:  # 只处理≤30°的倾斜
                angles.append(angle)
        
        if not angles:
            return image
        
        # 取中位数作为倾斜角度
        median_angle = np.median(angles)
        
        # 如果倾斜角度很小，不需要校正
        if abs(median_angle) < 0.5:
            logger.debug(f"倾斜角度过小({median_angle:.2f}°)，无需校正")
            return image
        
        # 旋转校正
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, float(median_angle), 1.0)
        rotated = cv2.warpAffine(image, M, (w, h),
                                flags=cv2.INTER_CUBIC,
                                borderMode=cv2.BORDER_REPLICATE)
        
        logger.info(f"倾斜校正完成: 检测到{median_angle:.2f}°倾斜，已自动校正", 
                   extra={"context": {"angle": median_angle, "image_size": f"{w}x{h}"}})
        return rotated
        
    except Exception as e:
        logger.warning(f"倾斜校正失败: {str(e)}，使用原图", extra={"context": {"error": str(e)}})
        return image
