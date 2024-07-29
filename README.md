# Evolutionary Diffusion Ars Interactive Edition
Interactive Installation, 2024. Creating images with Diffusion Models and Evolutionary Computing. 

Complementary to the https://github.com/malthee/evolutionary-diffusion repository.

<img alt="ui_overview" src="https://github.com/user-attachments/assets/57bd2aea-fb3b-4fc4-9114-4205bd06c7df">

## Installation
Install the `requirements.txt` with `pip install -r requirements.txt`.

Windows needs additional special treatment for the `pytorch` package. https://pytorch.org/get-started/locally/#start-locally  
Ex: `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124`

Required Environment Variables. Can be provided in a `.env` file in the root of the project:
* ED_BLOB_CONTAINER_NAME - Azure Blob Storage Container Name
* ED_BLOB_KEY - Azure Blob Storage Key
* ED_BLOB_URL - Azure Blob Storage URL
