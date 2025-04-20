import os
import sys

import torch
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication
from dotenv import load_dotenv
load_dotenv() # Load environment variables from .env file, needed in other modules

from main_window import MainWindow
from sklera_inactivity_manager import SkleraInactivityManager

APP_NAME = "evolutionary-diffusion Interactive Ars Demo"
APP_ICON = "./assets/icon.png"
APP_VERSION = "0.2.0"

"""
Quick method to check if the device has CUDA or MPS available.
"""
def check_device():
    if torch.cuda.is_available():
        print("CUDA is available.")
    elif torch.backends.mps.is_available():
        print("MPS is available.")
    else:
        print("CUDA and MPS are not available. Using CPU. (NOT RECOMMENDED)")


if __name__ == '__main__':
    os.environ["QT_QPA_PLATFORMTHEME"] = "light"  # Force light theme
    check_device()

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(APP_ICON))
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    sklera_inactivity_manager = None
    if os.environ.get("SKLERA_ENABLED"):
        sklera_inactivity_manager = SkleraInactivityManager()
        app.installEventFilter(sklera_inactivity_manager)
    mainWindow = MainWindow(APP_NAME, inactivity_manager=sklera_inactivity_manager)
    mainWindow.show()
    sys.exit(app.exec())
