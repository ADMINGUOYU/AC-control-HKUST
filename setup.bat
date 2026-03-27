@REM This script sets up a Python virtual environment for the project, 
@REM installs dependencies, and preinstalls chromedriver for Selenium tests.
@REM Made for Windows users. For Unix-like systems, please use setup.sh.

:: echo off to prevent command echoing
:: enable delayed expansion for variable handling
@echo off
setlocal enabledelayedexpansion

:: Define paths and variables
set "VENV_PATH=%~dp0.venv"
set "VENV_BIN=%VENV_PATH%\Scripts"
set "CHROMEDRIVER_NAME=chromedriver.exe"

:: Color codes
:: Using ANSI escape codes for colored output in Windows 10+ terminals
:: [TRICK] Get the ESC character from the prompt command
for /F "tokens=1,2 delims=#" %%a in ('"prompt #$H#$E# & echo on & for %%b in (1) do rem"') do set "ESC=%%b"
set "GREEN=%ESC%[92m[INFO]%ESC%[0m"
set "YELLOW=%ESC%[93m[WARN]%ESC%[0m"
set "RED=%ESC%[91m[ERROR]%ESC%[0m"
set "NC=%ESC%[0m"

:: Create virtual environment
echo %GREEN% Creating Python virtual environment at %VENV_PATH%...
python -m venv "%VENV_PATH%"

:: Verify virtual environment creation
if not exist "%VENV_BIN%\activate.bat" (
    echo %RED% Virtual environment activation script not found.
    exit /b 1
)

:: Activate virtual environment
call "%VENV_BIN%\activate.bat"

:: Upgrade pip and install dependencies
echo %GREEN% Upgrading pip...
python -m pip install --upgrade pip

echo %GREEN% Installing dependencies from requirements.txt...
if exist "%~dp0requirements.txt" (
    pip install -r "%~dp0requirements.txt"
) else (
    echo %YELLOW% requirements.txt not found, skipping.
)

:: Chromedriver Installation via Selenium/Webdriver-Manager
echo %GREEN% Installing chromedriver via webdriver-manager...

:: Install helper
pip install webdriver-manager

:: Use Python to fetch the driver path and copy it
set "SE_CACHE_PATH=%VENV_PATH%\.cache"
set "PY_CMD=import os; from webdriver_manager.core.driver_cache import DriverCacheManager; from webdriver_manager.chrome import ChromeDriverManager; custom_path = r'%SE_CACHE_PATH%'; manager = DriverCacheManager(root_dir=custom_path); path = ChromeDriverManager(cache_manager=manager).install(); print(os.path.normpath(path))"
for /f "delims=" %%i in ('python -c "%PY_CMD%" 2^>nul') do set "DRIVER_PATH=%%i"

if "%DRIVER_PATH%"=="" (
    echo %RED% Failed to locate chromedriver using selenium.
    exit /b 1
)

echo %GREEN% Found chromedriver at: %DRIVER_PATH%

:: Copy chromedriver to virtual environment Scripts folder
copy /Y "%DRIVER_PATH%" "%VENV_BIN%\%CHROMEDRIVER_NAME%" >nul

:: Cleanup
if exist "%SE_CACHE_PATH%" (
    rmdir /s /q "%SE_CACHE_PATH%"
    echo %GREEN% Cache directory deleted.
)
pip uninstall -y webdriver-manager

:: Verify chromedriver installation
if not exist "%VENV_BIN%\%CHROMEDRIVER_NAME%" (
    echo %RED% Chromedriver installation failed.
    exit /b 1
)

:: Final success message
echo.
echo %GREEN% ^>^>^> Setup completed successfully ^>^>^>
echo Virtual environment ready. Activate with: call %VENV_BIN%\activate.bat
echo To remove .venv, simply run: rmdir /s /q "%VENV_PATH%"

:: Prints "press any key to continue"
pause