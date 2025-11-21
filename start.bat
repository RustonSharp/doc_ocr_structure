@echo off
chcp 65001 >nul 2>&1
echo Starting OCR Service...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python first.
    pause
    exit /b 1
)

REM Start backend service (in background)
echo Starting backend service (port 8000)...
start "OCR Backend" cmd /k "python main.py"

REM Wait for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend server
echo Starting frontend server (port 8080)...
echo.
echo Frontend URL: http://localhost:8080
echo Backend API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop services
echo.

cd frontend
python -m http.server 8080

