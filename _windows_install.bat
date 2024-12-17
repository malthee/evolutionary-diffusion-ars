@echo off
set VENV_DIR=.venv

REM Check if virtual environment exists
if not exist %VENV_DIR% (
    echo Creating virtual environment...
    python -m venv %VENV_DIR%
)

REM Activate virtual environment
call %VENV_DIR%\Scripts\activate

REM Install specific versions of torch, torchvision, and torchaudio
echo Installing specific versions of torch, torchvision, and torchaudio...
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121

REM Check and install required packages from requirements.txt
if exist requirements.txt (
    echo Installing required packages from requirements.txt...
    pip install -r requirements.txt
) 

REM Deactivate virtual environment
deactivate

echo Environment setup complete.
pause
