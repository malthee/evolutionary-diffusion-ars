# Evolutionary Diffusion Ars Interactive Edition
Interactive Installation, 2024. Creating images with Diffusion Models and Evolutionary Computing. 

Complementary to the https://github.com/malthee/evolutionary-diffusion repository.

<img alt="ui_overview" src="https://github.com/user-attachments/assets/57bd2aea-fb3b-4fc4-9114-4205bd06c7df">

## Installation
1. Install Python https://www.python.org/downloads/
2. (CUDA, Windows only) Windows needs additional special treatment for the `pytorch` package. For windows using CUDA, execute `_windows_install.bat`. 
2. (Others only) Navigate to the `evolutionary-diffusion-ars` folder and install the `requirements.txt` with `pip install -r requirements.txt`.
3. Define the `.env` variables

Required Environment Variables. Can be provided in a `.env` file in the root of the project:
* ED_BLOB_CONTAINER_NAME - Azure Blob Storage Container Name
* ED_BLOB_KEY - Azure Blob Storage Key
* ED_BLOB_URL - Azure Blob Storage URL

## Running
Run the `main.py` file.

For Windows there is a convenience script `_windows_run.bat` that can be used.

## Resetting and Saving Space
The `results` folder contains all the generated images. The `results` folder can be deleted to free up space.  
To reset the counter, delete the `_shelve` files. Warning, this will cause the counter to reset to 0 and overwrite existing images.
