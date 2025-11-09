@echo off
setlocal

echo ========================================
echo Logarithmic Build Script
echo ========================================
echo.

REM Check if .venv exists
if not exist ".venv\" (
    echo [1/5] Creating virtual environment...
    python3.13 -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
    echo.
) else (
    echo [1/5] Virtual environment already exists.
    echo.
)

REM Install/update dependencies
echo [2/5] Installing/updating dependencies...
.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
.venv\Scripts\pip.exe install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully.
echo.

REM Install PyInstaller
echo [3/5] Installing PyInstaller...
.venv\Scripts\pip.exe install pyinstaller --quiet
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller
    pause
    exit /b 1
)
echo PyInstaller installed.
echo.

REM Set PYTHONPATH
set PYTHONPATH=%CD%\src

REM Kill any running instances
echo [4/5] Checking for running instances...
taskkill /F /IM Logarithmic.exe >nul 2>&1
if errorlevel 1 (
    echo No running instances found.
) else (
    echo Killed running instance.
    timeout /t 1 /nobreak >nul
)
echo.

REM Build the exe
echo [5/6] Building executable...
.venv\Scripts\pyinstaller.exe --name=Logarithmic --onefile --windowed ^
    --hidden-import=PySide6.QtCore ^
    --hidden-import=PySide6.QtWidgets ^
    --hidden-import=PySide6.QtGui ^
    --hidden-import=watchdog.observers ^
    --hidden-import=watchdog.events ^
    src/logarithmic/__main__.py

if errorlevel 1 (
    echo ERROR: Failed to build executable
    pause
    exit /b 1
)
echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.

REM Run the exe
echo [6/6] Launching Logarithmic...
echo.
echo Executable location: %CD%\dist\Logarithmic.exe
echo.
echo To run from CLI:
echo   .\dist\Logarithmic.exe
echo.
echo Starting application...
echo.

dist\Logarithmic.exe

endlocal
