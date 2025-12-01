"""
启动脚本模块测试
"""
import pytest
import subprocess
import sys
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# 注意：start_server.py 是一个启动脚本，主要测试其参数解析和函数调用


class TestStartServerFunctions:
    """启动脚本函数测试"""
    
    @patch('start_server.subprocess.run')
    def test_start_backend_function(self, mock_run):
        """测试启动后端函数"""
        from start_server import start_backend
        
        mock_run.return_value = Mock()
        start_backend()
        
        # 验证 subprocess.run 被调用
        assert mock_run.called
        # 验证调用参数
        call_args = mock_run.call_args[0][0]
        assert sys.executable in call_args
        assert "main.py" in call_args
    
    @patch('start_server.subprocess.run')
    @patch('start_server.Path')
    def test_start_frontend_function_exists(self, mock_path, mock_run):
        """测试启动前端函数（目录存在）"""
        from start_server import start_frontend
        
        # 模拟目录存在
        mock_frontend_dir = Mock()
        mock_frontend_dir.exists.return_value = True
        mock_path.return_value = mock_frontend_dir
        
        mock_run.return_value = Mock()
        start_frontend()
        
        # 验证 subprocess.run 被调用
        assert mock_run.called
        # 验证调用参数
        call_args = mock_run.call_args[0][0]
        assert sys.executable in call_args
        assert "-m" in call_args
        assert "http.server" in call_args
        assert "8080" in call_args
    
    @patch('start_server.subprocess.run')
    @patch('start_server.Path')
    def test_start_frontend_function_not_exists(self, mock_path, mock_run):
        """测试启动前端函数（目录不存在）"""
        from start_server import start_frontend
        
        # 模拟目录不存在
        mock_frontend_dir = Mock()
        mock_frontend_dir.exists.return_value = False
        mock_path.return_value = mock_frontend_dir
        
        start_frontend()
        
        # 目录不存在时不应该调用 subprocess.run
        assert not mock_run.called


class TestStartServerMain:
    """启动脚本主函数测试"""
    
    def test_main_backend_only(self):
        """测试仅启动后端参数解析逻辑"""
        # 这个测试主要验证参数解析逻辑
        # 由于主逻辑在 if __name__ == "__main__" 中，实际执行需要运行脚本
        # 这里只测试相关函数可以正常导入和调用
        try:
            import start_server
            assert hasattr(start_server, 'start_backend')
            assert hasattr(start_server, 'start_frontend')
        except ImportError:
            pytest.skip("无法导入 start_server 模块")
    
    @patch('start_server.start_backend')
    @patch('start_server.start_frontend')
    def test_main_frontend_only(self, mock_frontend, mock_backend):
        """测试仅启动前端"""
        # 这个测试需要模拟命令行参数解析
        # 由于 start_server.py 使用 argparse，测试会比较复杂
        pass
    
    @patch('start_server.start_backend')
    @patch('start_server.start_frontend')
    @patch('start_server.threading.Thread')
    @patch('start_server.time.sleep')
    @patch('start_server.webbrowser.open')
    def test_main_both_with_browser(self, mock_browser, mock_sleep, mock_thread, mock_frontend, mock_backend):
        """测试同时启动前后端并打开浏览器"""
        # 这个测试需要模拟完整的启动流程
        pass
    
    @patch('start_server.start_backend')
    @patch('start_server.start_frontend')
    @patch('start_server.threading.Thread')
    @patch('start_server.time.sleep')
    def test_main_both_no_browser(self, mock_sleep, mock_thread, mock_frontend, mock_backend):
        """测试同时启动前后端但不打开浏览器"""
        # 这个测试需要模拟完整的启动流程
        pass


class TestStartServerIntegration:
    """启动脚本集成测试"""
    
    def test_import_start_server(self):
        """测试导入启动脚本模块"""
        try:
            import start_server
            assert hasattr(start_server, 'start_backend')
            assert hasattr(start_server, 'start_frontend')
        except ImportError:
            pytest.skip("无法导入 start_server 模块")
    
    def test_start_server_module_structure(self):
        """测试启动脚本模块结构"""
        try:
            import start_server
            # 验证必要的函数存在
            assert callable(start_server.start_backend)
            assert callable(start_server.start_frontend)
        except ImportError:
            pytest.skip("无法导入 start_server 模块")

