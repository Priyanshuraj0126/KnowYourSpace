@echo off
echo ========================================
echo    KnowYourSpace - Space Exploration
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo Python found: 
python --version
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Check if requirements are installed
echo Checking dependencies...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
    echo Dependencies installed successfully!
    echo.
)

REM Check if .env file exists
if not exist ".env" (
    echo WARNING: .env file not found
    echo Please copy env.example to .env and configure your API keys
    echo.
    echo Required API keys:
    echo - GEMINI_API_KEY (from https://makersuite.google.com/app/apikey)
    echo - SUPABASE_URL and SUPABASE_ANON_KEY (from https://supabase.com)
    echo.
    echo You can still run the app, but some features may not work
    echo.
)

REM Run the application
echo Starting KnowYourSpace...
echo.
echo The application will be available at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.
python app.py

pause
