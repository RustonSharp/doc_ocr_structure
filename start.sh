#!/bin/bash

echo "正在启动 OCR 服务..."
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到 Python3，请先安装 Python"
    exit 1
fi

# 启动后端服务（在后台）
echo "启动后端服务 (端口 8000)..."
python3 main.py &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 启动前端服务器
echo "启动前端服务器 (端口 8080)..."
echo ""
echo "前端地址：http://localhost:8080"
echo "后端 API 文档：http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

cd frontend
python3 -m http.server 8080

# 清理：停止后端服务
kill $BACKEND_PID 2>/dev/null

