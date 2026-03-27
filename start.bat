@echo off
setlocal enabledelayedexpansion

:: ---------- Configuration Section ----------
:: Account credentials for AC Control server.
:: If your entries have "!" or "^", you must escape them with a
:: caret (^) in the value.
:: (i.e. password "p@ssw^rd!" should be set as "p@ssw^^rd^!")
if "%AC_USERNAME%"=="" set "AC_USERNAME=<USERNAME>"
if "%AC_PASSWORD%"=="" set "AC_PASSWORD=<PASSWORD>"
:: Optional: Set to 1 or true to run in headless mode (no GUI).
set "AC_HEADLESS=1"
:: Optional: Set the port for the server (default is 8000).
set "AC_PORT=8000"
:: -------------------------------------------

:: Get the directory of the script to determine the project root
set "PROJECT_ROOT=%~dp0"
set "VENV_PATH=%PROJECT_ROOT%.venv"

:: Environment checking
if not exist "%VENV_PATH%" (
    echo Virtual environment not found. Run setup.bat first.
    exit /b 1
)

:: Virtual environment binary path (Windows uses Scripts folder)
set "VENV_BIN=%VENV_PATH%\Scripts"

:: Handle Headless Flag
set "HEADLESS_FLAG="
if "%AC_HEADLESS%"=="1" set "HEADLESS_FLAG=--headless"
if "%AC_HEADLESS%"=="true" set "HEADLESS_FLAG=--headless"

:: [DEBUG] Print the configuration for verification
echo Starting AC Control server with the following configuration:
echo   Username: "%AC_USERNAME%"
echo   Password: "!AC_PASSWORD!"
echo   Headless Mode: "%AC_HEADLESS%"
echo   Port: "%AC_PORT%"

:: Activate the virtual environment and run the main application
call "%VENV_BIN%\activate.bat"
python -m ac_control.main --username "%AC_USERNAME%" --password "!AC_PASSWORD!" --port "%AC_PORT%" %HEADLESS_FLAG%

:: Prints "press any key to continue"
pause