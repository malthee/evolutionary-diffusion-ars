import os
import qrcode
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from azure.storage.blob import BlobServiceClient
from qrcode.image.styledpil import StyledPilImage

from image_manager import ImageInfo, IMAGE_LOCATION

BLOB_CONTAINER_NAME = os.environ.get("ED_BLOB_CONTAINER_NAME")
BLOB_KEY = os.environ.get("ED_BLOB_KEY")
BLOB_URL = os.environ.get("ED_BLOB_URL")

class QRBlobManager(QObject):
    """
    Class to manage the uploading of images to the cloud and generating QR codes for downloading.
    """
    qr_image_finished = pyqtSignal(ImageInfo)

    def __init__(self):
        if any(var is None or (isinstance(var, str) and var.strip() == "") for var in [BLOB_CONTAINER_NAME, BLOB_KEY, BLOB_URL]):
            raise ValueError("ED_BLOB_CONTAINER_NAME, ED_BLOB_KEY, ED_BLOB_URL must be set in environment variables.")

        super().__init__()

        # Thread management
        self._current_threads = {}

    def start_upload(self, input_image: ImageInfo):
        """
        Starts the upload of the current image to the cloud.
        Executes the upload in a separate QThread.
        """
        if self._current_threads.get(input_image) is not None:
            print("Thread already running. Do not start_upload twice.")
            return

        image_qr_path = os.path.join(IMAGE_LOCATION, f"{input_image.name}_qr.png")
        # Return the existing QR code
        goal_image_qr_info = ImageInfo(path=image_qr_path,
                                       arguments=input_image.arguments, score=input_image.score,
                                       selectable=False, parent1=input_image)

        if os.path.exists(image_qr_path):
            print("QR code already generated, returning existing QR code.")
            self.qr_image_finished.emit(goal_image_qr_info)
            return

        current_thread = QThread()
        self._current_threads[input_image] = current_thread
        client = BlobServiceClient(account_url=BLOB_URL, credential=BLOB_KEY)

        def task():
            try:
                container_client = client.get_container_client(container=BLOB_CONTAINER_NAME)
                with open(file=input_image.path, mode="rb") as data:
                    container_client = container_client.upload_blob(input_image.filename, data, overwrite=True)
                image_url = container_client.url
                qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_Q)
                # High error correct for embedded image
                qr.add_data(image_url)
                image_qr = qr.make_image(image_factory=StyledPilImage, embeded_image_path=input_image.path)
                # Copy of image info with qr code embedded
                image_qr.save(image_qr_path)
                print("Upload finished for", image_url)
                self.qr_image_finished.emit(goal_image_qr_info)
            except Exception as e:
                print("Exception in upload task:", e)
            finally:
                self._current_threads.pop(input_image)
                current_thread.quit()

        current_thread.run = task
        current_thread.finished.connect(current_thread.deleteLater)
        current_thread.start()
