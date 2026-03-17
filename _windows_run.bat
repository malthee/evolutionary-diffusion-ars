@echo off
setlocal
set "VENV_DIR=.venv"

REM Check if virtual environment exists
if not exist "%VENV_DIR%" (
    echo Virtual environment not found. Please run _windows_install.bat first.
    pause
    exit /b 1
)

REM Activate virtual environment
call "%VENV_DIR%\Scripts\activate"
if errorlevel 1 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

REM Run the main application
echo Running the application...
python main.py
set "APP_EXIT_CODE=%ERRORLEVEL%"

REM Deactivate virtual environment
deactivate

if not "%APP_EXIT_CODE%"=="0" (
    echo Application exited with error code %APP_EXIT_CODE%.
)

pause
exit /b %APP_EXIT_CODE%
