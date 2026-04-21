@echo off
echo ========================================
echo    STARTING DHUN SERVER
echo ========================================
echo.

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Check if .env exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Run setup.bat first
    pause
    exit /b 1
)

echo Server starting...
echo.
echo API URL:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop server
echo.

:: Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause