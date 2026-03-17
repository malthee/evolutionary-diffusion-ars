# Evolutionary Diffusion Ars Interactive Edition
Interactive Installation, 2024. Creating images with Diffusion Models and Evolutionary Computing. 

Complementary to the https://github.com/malthee/evolutionary-diffusion repository.

<img alt="ui_overview" src="https://github.com/user-attachments/assets/57bd2aea-fb3b-4fc4-9114-4205bd06c7df">

## Installation
1. Install Python from https://www.python.org/downloads/ (Python `3.12` recommended).
2. Install Git (required because `requirements.txt` includes a GitHub dependency).
3. Windows (CUDA): execute `_windows_install.bat`.
4. Others: navigate to `evolutionary-diffusion-ars` and install dependencies:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

5. Define the `.env` variables.

Pinned upstream dependency:
* `evolutionary-diffusion` is pinned in `requirements.txt` to commit `d4906d8b2eb12aa56b12beca36d791697969279d` for reproducibility.

Windows CUDA notes:
* `_windows_install.bat` installs `torch==2.7.1`, `torchvision==0.22.1`, `torchaudio==2.7.1` from `https://download.pytorch.org/whl/cu126`.
* It then installs the remaining dependencies from `requirements.txt` with the same PyTorch index as extra index.

Environment Variables. Can be provided in a `.env` file in the root of the project:
* `ED_BLOB_CONTAINER_NAME`, `ED_BLOB_KEY`, `ED_BLOB_URL` (optional): Enables QR upload/download feature.
* `SKLERA_ENABLED` (optional): Set to `true/1/yes/on` to enable Sklera inactivity integration.
* `SKLERA_API_TOKEN`, `SKLERA_SCREEN_ID` (required only when `SKLERA_ENABLED=true`).

## Running
Run the `main.py` file.

For Windows there is a convenience script `_windows_run.bat` that can be used.

## Resetting and Saving Space
The `results` folder contains all the generated images. The `results` folder can be deleted to free up space.  
To reset the counter, delete the `_shelve` files. Warning, this will cause the counter to reset to 0 and overwrite existing images.
