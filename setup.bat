@echo off
echo ========================================
echo    DHUN SERVER SETUP - WINDOWS
echo ========================================
echo.

:: Check Python installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not installed!
    echo Download from https://python.org
    pause
    exit /b 1
)

echo [1/6] Python found!
python --version

:: Create project folder
echo.
echo [2/6] Creating folder structure...

mkdir dhun-server
cd dhun-server

mkdir app
mkdir app\models
mkdir app\schemas
mkdir app\routers
mkdir app\services
mkdir app\middleware
mkdir app\utils
mkdir uploads
mkdir uploads\audio
mkdir uploads\covers

echo Folders created!

:: Create virtual environment
echo.
echo [3/6] Creating virtual environment...
python -m venv venv

:: Activate virtual environment
echo.
echo [4/6] Activating virtual environment...
call venv\Scripts\activate.bat

:: Install dependencies
echo.
echo [5/6] Installing dependencies...

pip install fastapi==0.115.0
pip install uvicorn[standard]==0.32.0
pip install sqlalchemy==2.0.36
pip install alembic==1.14.0
pip install python-jose[cryptography]==3.3.0
pip install passlib[bcrypt]==1.7.4
pip install python-multipart==0.0.12
pip install aiofiles==24.1.0
pip install python-dotenv==1.0.1
pip install pydantic[email]==2.10.0
pip install mutagen==1.47.0
pip install slowapi==0.1.9

:: Save requirements
pip freeze > requirements.txt

echo.
echo [6/6] Creating __init__.py files...

type nul > app\__init__.py
type nul > app\models\__init__.py
type nul > app\schemas\__init__.py
type nul > app\routers\__init__.py
type nul > app\services\__init__.py
type nul > app\middleware\__init__.py
type nul > app\utils\__init__.py

:: Create .env file
echo.
echo Creating .env file...

(
echo # Dhun Server Environment Variables
echo.
echo # Database
echo DATABASE_URL=sqlite:///./dhun.db
echo.
echo # JWT Secret - CHANGE THIS IN PRODUCTION
echo SECRET_KEY=dhun_secret_key_change_this_in_production_2024
echo ALGORITHM=HS256
echo ACCESS_TOKEN_EXPIRE_MINUTES=1440
echo REFRESH_TOKEN_EXPIRE_DAYS=30
echo.
echo # Server
echo HOST=0.0.0.0
echo PORT=8000
echo DEBUG=True
echo.
echo # File Upload
echo MAX_FILE_SIZE_MB=50
echo UPLOAD_DIR=uploads
echo ALLOWED_AUDIO_TYPES=audio/mpeg,audio/mp3,audio/wav,audio/flac,audio/ogg
echo.
echo # CORS - Add your app's origin
echo CORS_ORIGINS=*
) > .env

:: Create .env.example
copy .env .env.example

echo.
echo ========================================
echo    SETUP COMPLETE!
echo ========================================
echo.
echo Folder: dhun-server/
echo.
echo Next steps:
echo   1. cd dhun-server
echo   2. Run: setup_code.bat  (to create all code files)
echo   3. Run: run.bat         (to start server)
echo.
echo Server will run at: http://localhost:8000
echo API Docs at:        http://localhost:8000/docs
echo.
pause