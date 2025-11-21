#!/usr/bin/env python
"""
启动脚本：同时启动后端服务和前端 HTTP 服务器
"""
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
import threading

def start_backend():
    """启动后端 FastAPI 服务"""
    print("正在启动后端服务 (FastAPI)...")
    subprocess.run([sys.executable, "main.py"])

def start_frontend():
    """启动前端 HTTP 服务器"""
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("错误：frontend 目录不存在")
        return
    
    print("正在启动前端 HTTP 服务器...")
    print("前端地址：http://localhost:8080")
    subprocess.run([
        sys.executable, "-m", "http.server", "8080"
    ], cwd=frontend_dir)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="启动 OCR 服务")
    parser.add_argument("--backend-only", action="store_true", help="仅启动后端服务")
    parser.add_argument("--frontend-only", action="store_true", help="仅启动前端服务器")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
    
    args = parser.parse_args()
    
    if args.backend_only:
        start_backend()
    elif args.frontend_only:
        start_frontend()
    else:
        # 启动后端（在后台线程）
        backend_thread = threading.Thread(target=start_backend, daemon=True)
        backend_thread.start()
        
        # 等待后端启动
        print("等待后端服务启动...")
        time.sleep(3)
        
        # 启动前端
        if not args.no_browser:
            print("3 秒后自动打开浏览器...")
            time.sleep(3)
            webbrowser.open("http://localhost:8080")
        
        start_frontend()

