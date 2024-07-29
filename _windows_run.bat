@echo off
set VENV_DIR=.venv

REM Check if virtual environment exists
if not exist %VENV_DIR% (
    echo Virtual environment not found. Please run _windows_install.bat first.
    exit /b 1
)

REM Activate virtual environment
call %VENV_DIR%\Scripts\activate

REM Run the main application
echo Running the application...
python main.py

REM Deactivate virtual environment
deactivate

pause
