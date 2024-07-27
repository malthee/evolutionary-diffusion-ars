import os
import random
import sys
from typing import List

from PyQt6.QtCore import Qt, QRect, pyqtSlot, QObject, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QHBoxLayout, QFrame, QVBoxLayout, QPushButton, \
    QSlider

APP_NAME = "evolutionary-diffusion Interactive Ars Demo"
APP_ICON = "./assets/icon.png"
APP_VERSION = "0.1.0"
TEST_IMAGES = ["./assets/test1.png", "./assets/test2.png", "./assets/test3.png"]
IMAGE_SIZE = 250
LABEL_HEIGHT = 50
CUSTOM_TITLE_BAR_HEIGHT = 30
DRAGGABLE_WINDOW_HEIGHT = IMAGE_SIZE + LABEL_HEIGHT + CUSTOM_TITLE_BAR_HEIGHT
DRAGGABLE_WINDOW_WIDTH = IMAGE_SIZE
MAX_FIND_POSITION_TRIES = 10
DRAG_THRESHOLD = 10
MAX_IMAGES = 25

os.environ["QT_QPA_PLATFORMTHEME"] = "light"

class ImageInfo:
    def __init__(self, path: str, score: float):
        self._path = path
        self._score = score
        self._name = os.path.splitext(os.path.basename(path))[0]  # Filename without extension for display

    @property
    def path(self):
        return self._path

    @property
    def score(self):
        return self._score

    @property
    def name(self):
        return self._name

    def __eq__(self, other):
        return self.path == other.path


class ImageManager(QObject):
    """
    Manages the display and selection of images.
    Only two images can be selected at a time.
    Only MAX_IMAGES images can be displayed at a time.
    Otherwise, the oldest image is removed.
    """

    selectionChanged = pyqtSignal((ImageInfo, bool))
    selectionCountChanged = pyqtSignal(int)
    imageAdded = pyqtSignal(ImageInfo)
    imageRemoved = pyqtSignal(ImageInfo)

    def __init__(self):
        super().__init__()
        self._selected_images: List[ImageInfo] = []
        self._images: List[ImageInfo] = []
        self.selectionChanged.connect(self.on_selection_changed)  # Update count on selection changes
        self.imageRemoved.connect(self.on_selection_changed)  # Update count on image removal

    @property
    def selected_images(self): 
        return self._selected_images

    @property
    def images(self):
        return self._images

    @pyqtSlot()
    def on_selection_changed(self):
        self.selectionCountChanged.emit(len(self._selected_images))

    def select_image(self, image_info: ImageInfo):
        if len(self._selected_images) >= 2:
            self.unselect_image(self._selected_images[0])
        self._selected_images.append(image_info)
        self.selectionChanged.emit(image_info, True)

    def unselect_image(self, image_info: ImageInfo):
        if image_info in self._selected_images:
            self._selected_images.remove(image_info)
            self.selectionChanged.emit(image_info, False)

    def unselect_all(self):
        for image in list(self._selected_images):  # Copy to avoid modifying while iterating
            self.unselect_image(image)
        self._selected_images.clear()

    def add_image(self, image_info: ImageInfo):
        if len(self._images) >= MAX_IMAGES:
            self.remove_image(self._images[0])
        self._images.append(image_info)
        self.imageAdded.emit(image_info)

    def remove_image(self, image_info: ImageInfo):
        if image_info in self._images:
            self._images.remove(image_info)
            self.imageRemoved.emit(image_info)

    def clear_all_images(self):
        self.unselect_all()
        for image in list(self._images):  # Copy to avoid modifying while iterating
            self.remove_image(image)
        self._images.clear()


class ImageMenu(QFrame):
    def __init__(self, image_manager, parent=None):
        super().__init__(parent)
        self._image_manager = image_manager
        self._image_manager.selectionCountChanged.connect(self.update_visibility)
        self.setFixedSize(300, 200)
        self.setStyleSheet("""
            QPushButton {
                background-color: #777;
                color: white;
                border: none;
                border-radius: 25px;
                font-size: 24px;
                padding: 14px;
                min-width: 150px;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #666;
            }
            QSlider::groove:horizontal {
                height: 14px;
                background: #DDD;
                border: 1px solid #999;
                border-radius: 8px;
            }
            QSlider::handle:horizontal {
                background: #888;
                border: 2px solid #666;
                width: 24px;
                height: 24px;
                margin: -5px 0;
                border-radius: 12px;
            }
            QLabel {
                color: #333;
                font-size: 24px;
                padding: 5px;
            }
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignBottom)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(10)

        self.new_image_button = QPushButton("+ New Image")
        self.new_image_button.clicked.connect(self.new_image)
        self.layout.addWidget(self.new_image_button)

        self.mutate_button = QPushButton("🧬 Mutate this Image")
        self.mutate_button.clicked.connect(self.mutate_image)
        self.layout.addWidget(self.mutate_button)

        self.slider_label = QLabel("🧑‍🧑‍🧒Parent Contribution")
        self.slider_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setValue(50)

        self.split_button = QPushButton("👶 Create Child")
        self.split_button.clicked.connect(self.create_child)

        self.slider_layout = QVBoxLayout()
        self.slider_layout.addWidget(self.slider_label)
        self.slider_layout.addWidget(self.slider)
        self.slider_layout.addWidget(self.split_button)
        self.layout.addLayout(self.slider_layout)

        self.update_visibility(len(self._image_manager.selected_images))

    def closeEvent(self, event):
        self._image_manager.selectionChanged.disconnect(self.update_visibility)
        event.accept()

    @pyqtSlot()
    def new_image(self):
        print("New Image")
        self._image_manager.unselect_all()

    @pyqtSlot()
    def mutate_image(self):
        print("Mutate Image")
        self._image_manager.unselect_all()

    @pyqtSlot()
    def create_child(self):
        print("Create Child")
        self._image_manager.unselect_all()

    @pyqtSlot(int)
    def update_visibility(self, selected_count):
        """
        When none selected, allow new child creation. Otherwise, either mutate an image or create a child from two images.
        """
        self.new_image_button.setVisible(selected_count == 0)
        self.mutate_button.setVisible(selected_count == 1)
        self.slider_label.setVisible(selected_count == 2)
        self.slider.setVisible(selected_count == 2)
        self.split_button.setVisible(selected_count == 2)


class ImageWindowTitleBar(QWidget):
    def __init__(self, parent=None, name=""):
        super().__init__(parent)
        self.parent = parent
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.title = QLabel(self)
        # Format as #000001, #000002, etc. when parsable as number or fallback to string
        try:
            number = int(name)
            self.title.setText("IMAGE #{:06d}".format(number))
        except ValueError:
            self.title.setText(f"IMAGE {name}")
        self.title.setStyleSheet("font-weight: bold; padding-left: 5px;")

        self.close_button = QPushButton("X", self)
        self.close_button.setFixedSize(CUSTOM_TITLE_BAR_HEIGHT, CUSTOM_TITLE_BAR_HEIGHT)
        self.close_button.setStyleSheet("background-color: red; color: white; border: none;")
        self.close_button.clicked.connect(self.close_window)

        self.layout.addWidget(self.title)
        self.layout.addStretch()
        self.layout.addWidget(self.close_button)

        self.setFixedHeight(CUSTOM_TITLE_BAR_HEIGHT)

    def close_window(self):
        self.parent.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.parent.offset = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.pos() - self.parent.offset
            self.parent.move(self.parent.pos() + delta)


class DraggableImageWindow(QMainWindow):
    def __init__(self, image_info: ImageInfo, selection_manager: ImageManager):
        super().__init__()
        self._image_info = image_info
        self._selection_manager = selection_manager
        self._selection_manager.selectionChanged.connect(self.on_selection_changed)
        self.setFixedSize(DRAGGABLE_WINDOW_WIDTH, DRAGGABLE_WINDOW_HEIGHT)
        # On top of the background, no frame as has custom title bar
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint |
                            Qt.WindowType.Tool)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QMainWindow[selected="true"] {
                background-color: lightblue;
            }
        """)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)  # Remove margins, otherwise image is not centered
        self.layout.setSpacing(0)

        self.title_bar = ImageWindowTitleBar(self, image_info.name)
        self.image = QLabel(self.central_widget)
        self.image.setScaledContents(True)
        pixmap = QPixmap(image_info.path)
        self.image.setPixmap(pixmap)
        self.image.setFixedSize(IMAGE_SIZE, IMAGE_SIZE)
        self.score_label = QLabel("Score: {:.2f}".format(image_info.score), self.central_widget)
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.score_label.setStyleSheet("font-size: 24px; font-weight: bold;")

        self.layout.addWidget(self.title_bar)
        self.layout.addWidget(self.image)
        self.layout.addWidget(self.score_label)

        self.setProperty('selected', False)
        self.offset = None
        self.start_pos = None  # For drag threshold

    def closeEvent(self, event):
        self._selection_manager.unselect_image(self._image_info)
        self._selection_manager.selectionChanged.disconnect(self.on_selection_changed)
        event.accept()

    @pyqtSlot(ImageInfo, bool)
    def on_selection_changed(self, image_info: ImageInfo, selected: bool):
        if image_info == self._image_info:
            self.setProperty('selected', selected)
            self.style().polish(self)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.globalPosition()
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.offset is not None and event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.pos() - self.offset
            self.move(self.pos() + delta)

    def mouseReleaseEvent(self, event):
        if self.start_pos is not None:
            distance = (event.globalPosition() - self.start_pos).manhattanLength()
            if distance < DRAG_THRESHOLD:  # Do not select if user is dragging
                if self.property('selected'):
                    self._selection_manager.unselect_image(self._image_info)
                else:
                    self._selection_manager.select_image(self._image_info)
            self.start_pos = None
        self.offset = None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._selection_manager = ImageManager()

        self.setWindowTitle(APP_NAME)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint |
                            Qt.WindowType.CustomizeWindowHint)
        self.showFullScreen()

        corner_layout = QHBoxLayout()
        corner_layout.addStretch()
        self.trash_button = QPushButton(parent=self, text="🗑️")
        self.trash_button.setToolTip("Clear all Images")
        self.trash_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                font-size: 48px;
                border: none;
                border-radius: 12px;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: lightgray;
            }
        """)
        self.trash_button.clicked.connect(self.clear_all_images)
        corner_layout.addWidget(self.trash_button)

        self.image_menu = ImageMenu(self._selection_manager, self)
        main_layout = QVBoxLayout()
        main_layout.addLayout(corner_layout)
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        main_layout.addStretch()
        main_layout.addWidget(self.image_menu, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
        self.setCentralWidget(central_widget)

        self.frames = []
        self.initUI()

    # If needed to prevent closing
    # def closeEvent(self, event):
    #   event.ignore()

    def initUI(self):
        for image_path in TEST_IMAGES:
            if os.path.exists(image_path):
                frame = DraggableImageWindow(ImageInfo(image_path, random.normalvariate()), self._selection_manager)
                frame.setGeometry(self.getRandomRect())
                frame.show()
                frame.raise_()
                self.frames.append(frame)

    def getRandomRect(self):
        """Tries to find a random rectangle that does not intersect with any of the existing frames in MAX_FIND_POSITION_TRIES
        attempts. Otherwise, just uses the random position."""
        for _ in range(MAX_FIND_POSITION_TRIES):
            x = random.randint(0, self.width() - IMAGE_SIZE)
            y = random.randint(0, self.height() - IMAGE_SIZE)
            rect = QRect(x, y, IMAGE_SIZE, IMAGE_SIZE)

            if not any(frame.geometry().intersects(rect) for frame in self.frames):
                return rect

    def getCenterFromRects(self, rect1, rect2):
        """Returns a QRect that is centered between two QRects but bounded in the main window."""
        x = (rect1.x() + rect2.x()) / 2
        y = (rect1.y() + rect2.y()) / 2
        # Check bounds
        if x + IMAGE_SIZE > self.width():
            x = self.width() - IMAGE_SIZE
        if y + IMAGE_SIZE > self.height():
            y = self.height() - IMAGE_SIZE
        return QRect(x, y, IMAGE_SIZE, IMAGE_SIZE)

    @pyqtSlot()
    def clear_all_images(self):
        self._selection_manager.clear_all_images()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._selection_manager.unselect_all()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(APP_ICON))
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec())
