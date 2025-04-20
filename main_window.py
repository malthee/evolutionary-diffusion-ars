import os
import random
from typing import Optional

from PyQt6.QtCore import Qt, QRect, pyqtSlot
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton

from image_manager import ImageInfo, ImageManager
from image_menu import ImageMenu
from image_window import DRAGGABLE_WINDOW_WIDTH, DRAGGABLE_WINDOW_HEIGHT, DraggableImageWindow
from info_window import InfoWindow
from qr_blob_manager import QRBlobManager
from sklera_inactivity_manager import SkleraInactivityManager

START_IMAGES = 3
MAX_FIND_POSITION_TRIES = 10
BACKGROUND_COLOR = os.getenv("BACKGROUND_COLOR", "#e0e0e0")

class MainWindow(QMainWindow):
    def __init__(self, app_name, inactivity_manager: Optional[SkleraInactivityManager] = None):
        super().__init__()
        self._inactivity_manager = inactivity_manager
        self._image_manager = ImageManager()
        self._qr_blob_manager = QRBlobManager()
        self._image_manager.imageAdded.connect(self.on_image_added)
        self._image_manager.imageRemoved.connect(self.on_image_removed)
        # Finished qr codes are added to the image manager
        self._qr_blob_manager.qr_image_finished.connect(self._image_manager.manual_add_image)

        self.setWindowTitle(app_name)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.CustomizeWindowHint)
        self.showFullScreen()

        # Set the background color to light gray
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(BACKGROUND_COLOR))
        self.setPalette(palette)
        button_style = """
                    QPushButton {
                        background-color: transparent;
                        font-size: 56px;
                        border: none;
                        border-radius: 12px;
                        margin: 10px;
                    }
                    QPushButton:hover {
                        background-color: lightgray;
                    }
                """

        # Create a helper method to create buttons with consistent styling and properties
        def create_button(parent, text, tooltip, slot):
            button = QPushButton(parent=parent, text=text)
            button.setToolTip(tooltip)
            button.setStyleSheet(button_style)
            button.clicked.connect(slot)
            return button

        corner_layout = QHBoxLayout()
        corner_layout.setSpacing(0)
        corner_layout.addStretch()
        # self.uk_button = create_button(self, "🇬🇧", "English (UK)", lambda: self.change_language("en"))
        # corner_layout.addWidget(self.uk_button)
        # self.austria_button = create_button(self, "🇦🇹", "German (Austria)", lambda: self.change_language("de"))
        # corner_layout.addWidget(self.austria_button)
        self.info_button = create_button(self, "ℹ️", "Information", self.show_info)
        corner_layout.addWidget(self.info_button)
        self.trash_button = create_button(self, "🗑️", "Clear all Images", self.clear_all_images)
        corner_layout.addWidget(self.trash_button)

        self.image_menu = ImageMenu(self._image_manager, self._qr_blob_manager, self)
        main_layout = QVBoxLayout()
        main_layout.addLayout(corner_layout)
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        main_layout.addStretch()
        main_layout.addWidget(self.image_menu, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
        self.setCentralWidget(central_widget)

        self.frames = []
        self.info_window = None
        self._initImages()

    # If needed to prevent closing
    # def closeEvent(self, event):
    #   event.ignore()

    def _initImages(self):
        for _ in range(START_IMAGES):
            self._image_manager.generate_image()

    def _getRandomRect(self):
        """Tries to find a random rectangle that does not intersect with any of the existing frames in MAX_FIND_POSITION_TRIES
        attempts. Otherwise, just uses the random position."""
        for _ in range(MAX_FIND_POSITION_TRIES):
            x = random.randint(0, self.width() - DRAGGABLE_WINDOW_WIDTH)
            y = random.randint(0, self.height() - DRAGGABLE_WINDOW_HEIGHT)
            rect = QRect(x, y, DRAGGABLE_WINDOW_WIDTH, DRAGGABLE_WINDOW_HEIGHT)

            if not any(frame.geometry().intersects(rect) for frame in self.frames):
                return rect
        return QRect(random.randint(0, self.width() - DRAGGABLE_WINDOW_WIDTH), random.randint(0, self.height() - DRAGGABLE_WINDOW_HEIGHT),
                     DRAGGABLE_WINDOW_WIDTH, DRAGGABLE_WINDOW_HEIGHT)

    def _getCenterFromRects(self, rect1, rect2):
        """Returns a QRect that is centered between two QRects but bounded in the main window."""
        x = int((rect1.x() + rect2.x()) / 2)
        y = int((rect1.y() + rect2.y()) / 2)
        # Check bounds
        if x + DRAGGABLE_WINDOW_WIDTH > self.width():
            x = self.width() - DRAGGABLE_WINDOW_WIDTH
        if y + DRAGGABLE_WINDOW_HEIGHT > self.height():
            y = self.height() - DRAGGABLE_WINDOW_HEIGHT
        return QRect(x, y, DRAGGABLE_WINDOW_WIDTH, DRAGGABLE_WINDOW_HEIGHT)

    def _getCloseRect(self, rect):
        """Returns a QRect that is close to the given QRect."""
        x = rect.x() + DRAGGABLE_WINDOW_WIDTH + 10  # 10 pixels to the right
        y = rect.y()
        if x + DRAGGABLE_WINDOW_WIDTH > self.width():
            x = self.width() - DRAGGABLE_WINDOW_WIDTH
        if y + DRAGGABLE_WINDOW_HEIGHT > self.height():
            y = self.height() - DRAGGABLE_WINDOW_HEIGHT
        return QRect(x, y, DRAGGABLE_WINDOW_HEIGHT, DRAGGABLE_WINDOW_HEIGHT)

    def _frameForImage(self, image_info: ImageInfo) -> DraggableImageWindow:
        return next((f for f in self.frames if f.image_info == image_info), None)

    @pyqtSlot(ImageInfo)
    def on_image_added(self, image_info: ImageInfo):
        print(f"Image added: {image_info.name}")
        # Prevent showing a new image on top when the app is hidden
        if self._inactivity_manager is not None and self._inactivity_manager.currently_hidden:
            print("Not showing image, app currently hidden.")
            return

        frame = DraggableImageWindow(image_info, self._image_manager)
        if image_info.parent1 is not None:
            parent1_frame = self._frameForImage(image_info.parent1)
            if image_info.parent2 is not None:  # Child created
                parent2_frame = self._frameForImage(image_info.parent2)
                if parent1_frame is not None and parent2_frame is not None:
                    frame.setGeometry(self._getCenterFromRects(parent1_frame.geometry(), parent2_frame.geometry()))
            elif parent1_frame is not None:  # Mutated
                frame.setGeometry(self._getCloseRect(parent1_frame.geometry()))
        else:  # New image
            frame.setGeometry(self._getRandomRect())
        frame.show()
        frame.raise_()
        self.frames.append(frame)

    @pyqtSlot(ImageInfo)
    def on_image_removed(self, image_info: ImageInfo):
        frame = self._frameForImage(image_info)
        if frame is not None:
            frame.close()
            self.frames.remove(frame)

    @pyqtSlot()
    def clear_all_images(self):
        self._image_manager.clear_all_images()
        for frame in self.frames:
            frame.close()

    @pyqtSlot()
    def show_info(self):
        if self.info_window is None:
            self.info_window = InfoWindow()
        self.info_window.show()
        self.info_window.raise_()

    @pyqtSlot(str)
    def change_language(self, language):
        print(f"Change language to {language}")  # TODO maybe language selection

    def mousePressEvent(self, event):
        print('Mouse pressed, unselecting all images.')
        if event.button() == Qt.MouseButton.LeftButton:
            self._image_manager.unselect_all()