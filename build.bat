@echo off
setlocal

echo ============================================
echo  Music-Algorithm -- Windows .exe builder
echo ============================================
echo.

:: Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo [1/3] Installing dependencies...
pip install -r requirements.txt pyinstaller>=6.0 --quiet
if errorlevel 1 (
    echo ERROR: pip install failed.
    pause
    exit /b 1
)

echo [2/3] Building executable...
pyinstaller music_algorithm.spec --clean --noconfirm
if errorlevel 1 (
    echo ERROR: PyInstaller build failed.
    pause
    exit /b 1
)

echo [3/3] Copying credential template...
if not exist dist\.env (
    copy .env.example dist\.env >nul
    echo.
    echo  ACTION REQUIRED: Open dist\.env and fill in your Spotify credentials.
    echo  Get your credentials at: https://developer.spotify.com/dashboard
)

echo.
echo ============================================
echo  Build complete!  dist\music-algorithm.exe
echo ============================================
echo.
echo Usage:
echo   dist\music-algorithm.exe ^<playlist_url^> [--arc] [--fast] [--json out.json]
echo.
pause
endlocal
