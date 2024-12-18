import os

import requests
from PyQt6.QtCore import QObject, QEvent, QTimer

SKLERA_TIMEOUT_MS = os.environ.get("SKLERA_TIMEOUT_MS", 30000)
SKLERA_API_TOKEN = os.environ.get("SKLERA_API_TOKEN")
SKLERA_SCREEN_ID = os.environ.get("SKLERA_SCREEN_ID")
SKLERA_MAX_RETRIES = os.environ.get("SKLERA_MAX_RETRIES", 3)
SKLERA_API_URL = os.environ.get("SKLERA_API_URL", "https://my.sklera.tv/data/api/screens/sendCmd")
BACKOFF_FACTOR = 2

class SkleraInactivityManager(QObject):
    def __init__(self):
        super().__init__()
        if any(var is None or var.strip() == "" for var in [SKLERA_TIMEOUT_MS, SKLERA_API_TOKEN, SKLERA_SCREEN_ID, SKLERA_MAX_RETRIES, SKLERA_API_URL]):
            raise ValueError("SKLERA_API_TOKEN and SKLERA_SCREEN_ID is required and may not be empty. Other SKLERA environment variables are optional but may also not be empty when defined.")

        self.timeout = SKLERA_TIMEOUT_MS
        self.timer = QTimer()
        self.timer.setInterval(self.timeout)
        self.timer.timeout.connect(self._handle_inactivity)
        self.timer.start()

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Type.MouseMove, QEvent.Type.MouseButtonPress, QEvent.Type.KeyPress):
            self._reset_timer()
        return super().eventFilter(obj, event)

    def _reset_timer(self):
        if self.timer.isActive():
            self.timer.stop()
        self.timer.start()

    def _send_sklera_hide_command(self, attempt=1):
        headers = {
            "apiToken": SKLERA_API_TOKEN,
            "Content-Type": "application/json"
        }
        payload = {
            "id": SKLERA_SCREEN_ID,
            "cmd": "app_hide"
        }

        try:
            response = requests.post(SKLERA_API_URL, json=payload, headers=headers)
            response.raise_for_status()  # Raise an exception for HTTP errors
            print(f"App hide attempt {attempt}: Command successful.")
        except requests.exceptions.RequestException as e:
            print(f"App hide attempt {attempt}: Error occurred: {e}")
            if attempt < SKLERA_MAX_RETRIES:
                sleep_time = (BACKOFF_FACTOR ** (attempt - 1)) * 5000
                QTimer.singleShot(sleep_time, self._send_sklera_hide_command, attempt + 1)
            else:
                print(f"App hide attempt {attempt}: Max retries reached. Command failed.")

    def _handle_inactivity(self):
        print("User inactive for", self.timeout / 1000, "seconds.")
        self._send_sklera_hide_command()
