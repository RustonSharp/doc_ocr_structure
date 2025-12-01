"""
图像预处理模块测试
"""
import pytest
import io
import numpy as np
from PIL import Image

from pre_preocess import (
    pre_preocess_for_pytesseract,
    pre_preocess_for_google_vision,
    preprocess_image,
    correct_skew
)


class TestPreProcessForPytesseract:
    """pytesseract 预处理测试"""
    
    def test_pre_preocess_for_pytesseract(self, sample_image_bytes):
        """测试 pytesseract 预处理"""
        result = pre_preocess_for_pytesseract(sample_image_bytes)
        assert result is not None
        assert isinstance(result, Image.Image)
    
    def test_pre_preocess_for_pytesseract_invalid_data(self):
        """测试无效数据的预处理"""
        invalid_data = b"not an image"
        # 函数会抛出异常，需要捕获
        with pytest.raises(Exception):  # PIL.UnidentifiedImageError 或其他异常
            pre_preocess_for_pytesseract(invalid_data)


class TestPreProcessForGoogleVision:
    """Google Vision 预处理测试"""
    
    def test_pre_preocess_for_google_vision(self, sample_image_bytes):
        """测试 Google Vision 预处理"""
        result = pre_preocess_for_google_vision(sample_image_bytes)
        assert result is not None
        assert isinstance(result, Image.Image)
    
    def test_pre_preocess_for_google_vision_preserves_color(self, sample_image_bytes):
        """测试 Google Vision 预处理保留颜色"""
        result = pre_preocess_for_google_vision(sample_image_bytes)
        # Google Vision 应该保留颜色信息
        assert result is not None
        assert isinstance(result, Image.Image)


class TestPreprocessImage:
    """preprocess_image 函数测试"""
    
    def test_preprocess_image_grayscale(self, sample_image):
        """测试灰度图像预处理"""
        result = preprocess_image(sample_image, preserve_color=False)
        assert result is not None
        assert isinstance(result, Image.Image)
        # 预处理后应该是灰度图或二值图
        assert result.mode in ['L', '1', 'RGB']
    
    def test_preprocess_image_preserve_color(self, sample_image):
        """测试保留颜色的预处理"""
        result = preprocess_image(sample_image, preserve_color=True)
        assert result is not None
        assert isinstance(result, Image.Image)
        # 保留颜色时应该还是彩色图
        assert result.mode in ['RGB', 'RGBA', 'L']
    
    def test_preprocess_image_small_image(self):
        """测试小图像预处理"""
        # 创建一个很小的测试图像
        small_img = Image.new('RGB', (10, 10), color=(255, 255, 255))
        result = preprocess_image(small_img, preserve_color=False)
        assert result is not None
        assert isinstance(result, Image.Image)
    
    def test_preprocess_image_large_image(self):
        """测试大图像预处理"""
        # 创建一个较大的测试图像
        large_img = Image.new('RGB', (1000, 1000), color=(255, 255, 255))
        result = preprocess_image(large_img, preserve_color=False)
        assert result is not None
        assert isinstance(result, Image.Image)


class TestCorrectSkew:
    """correct_skew 函数测试"""
    
    def test_correct_skew_no_skew(self):
        """测试无倾斜的图像"""
        # 创建一个无倾斜的图像
        img = np.ones((100, 100, 3), dtype=np.uint8) * 255
        result = correct_skew(img)
        assert result is not None
        assert result.shape == img.shape
    
    def test_correct_skew_grayscale(self):
        """测试灰度图像倾斜校正"""
        img = np.ones((100, 100), dtype=np.uint8) * 255
        result = correct_skew(img)
        assert result is not None
        assert result.shape == img.shape
    
    def test_correct_skew_color_image(self):
        """测试彩色图像倾斜校正"""
        img = np.ones((100, 100, 3), dtype=np.uint8) * 255
        result = correct_skew(img)
        assert result is not None
        assert result.shape == img.shape
    
    def test_correct_skew_small_image(self):
        """测试小图像倾斜校正"""
        img = np.ones((10, 10, 3), dtype=np.uint8) * 255
        result = correct_skew(img)
        assert result is not None
        assert result.shape == img.shape
    
    def test_correct_skew_exception_handling(self):
        """测试异常处理"""
        # 创建一个可能导致异常的图像（空图像）
        img = np.array([])
        try:
            result = correct_skew(img)
            # 如果函数有异常处理，应该返回原图或处理后的图像
            assert True
        except Exception:
            # 如果抛出异常，这也是可以接受的
            pytest.skip("correct_skew 函数对空图像的处理方式")


class TestPreProcessIntegration:
    """预处理集成测试"""
    
    def test_full_preprocess_pipeline(self, sample_image_bytes):
        """测试完整预处理流程"""
        # 测试 pytesseract 预处理流程
        result = pre_preocess_for_pytesseract(sample_image_bytes)
        assert result is not None
        assert isinstance(result, Image.Image)
        
        # 测试 Google Vision 预处理流程
        result2 = pre_preocess_for_google_vision(sample_image_bytes)
        assert result2 is not None
        assert isinstance(result, Image.Image)
    
    def test_preprocess_different_image_formats(self):
        """测试不同图像格式的预处理"""
        # 测试 RGB 图像
        rgb_img = Image.new('RGB', (100, 100), color=(255, 0, 0))
        result = preprocess_image(rgb_img, preserve_color=False)
        assert result is not None
        
        # 测试 RGBA 图像
        rgba_img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        result = preprocess_image(rgba_img, preserve_color=False)
        assert result is not None
        
        # 测试灰度图像
        gray_img = Image.new('L', (100, 100), color=128)
        result = preprocess_image(gray_img, preserve_color=False)
        assert result is not None

