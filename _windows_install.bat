@echo off
setlocal
set "VENV_DIR=.venv"
set "TORCH_VERSION=2.7.1"
set "TORCHVISION_VERSION=0.22.1"
set "TORCHAUDIO_VERSION=2.7.1"
set "TORCH_INDEX_URL=https://download.pytorch.org/whl/cu126"

REM requirements.txt uses a GitHub VCS dependency.
where git >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is required to install dependencies from requirements.txt.
    echo Install Git for Windows first: https://git-scm.com/download/win
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "%VENV_DIR%" (
    echo Creating virtual environment...
    py -3.12 -m venv "%VENV_DIR%" 2>nul
    if errorlevel 1 (
        python -m venv "%VENV_DIR%"
    )
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment. Ensure Python 3.12+ is installed.
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call "%VENV_DIR%\Scripts\activate"
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment.
    pause
    exit /b 1
)

echo Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo ERROR: Failed to upgrade pip.
    deactivate
    pause
    exit /b 1
)

REM Install specific versions of torch, torchvision, and torchaudio
echo Installing CUDA PyTorch stack...
python -m pip install torch==%TORCH_VERSION% torchvision==%TORCHVISION_VERSION% torchaudio==%TORCHAUDIO_VERSION% --index-url %TORCH_INDEX_URL%
if errorlevel 1 (
    echo ERROR: Failed to install CUDA PyTorch packages from %TORCH_INDEX_URL%.
    echo If you do not use CUDA, install CPU wheels manually and rerun this script.
    deactivate
    pause
    exit /b 1
)

REM Check and install required packages from requirements.txt
if exist requirements.txt (
    echo Installing required packages from requirements.txt...
    python -m pip install --extra-index-url %TORCH_INDEX_URL% -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install requirements.txt
        deactivate
        pause
        exit /b 1
    )
) 

REM Deactivate virtual environment
deactivate

echo Environment setup complete.
pause
