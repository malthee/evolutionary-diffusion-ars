from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QMainWindow, QLabel, QWidget, QHBoxLayout, QVBoxLayout, QPushButton

from image_manager import ImageInfo, ImageManager

CUSTOM_TITLE_BAR_HEIGHT = 30
DRAG_THRESHOLD = 10
IMAGE_SIZE = 275
LABEL_HEIGHT = 70
DRAGGABLE_WINDOW_HEIGHT = IMAGE_SIZE + LABEL_HEIGHT + CUSTOM_TITLE_BAR_HEIGHT
DRAGGABLE_WINDOW_WIDTH = IMAGE_SIZE


def format_image_name(name: str) -> str:
    """
    Format as #000001, #000002, etc. when parsable as number or fallback to string
    """
    try:
        number = int(name)
        return "#{:06d}".format(number)
    except ValueError:
        return f"{name}"


class ImageWindowTitleBar(QWidget):
    def __init__(self, parent=None, name=""):
        super().__init__(parent)
        self.parent = parent
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.title = QLabel(self)
        self.title.setText("IMAGE " + format_image_name(name))
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
    def __init__(self, image_info: ImageInfo, image_manager: ImageManager):
        super().__init__()
        self._image_info = image_info
        self._image_manager = image_manager
        self._image_manager.selectionChanged.connect(self.on_selection_changed)
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
        self.score_label.setStyleSheet("font-size: 24px; font-weight: bold; padding-top: 8px;")

        parents_text = "Parent: "
        if image_info.parent1 is not None:
            parents_text += format_image_name(image_info.parent1.name)
            if image_info.parent2 is not None:
                parents_text += " + " + format_image_name(image_info.parent2.name)
        else:
            parents_text += "None"

        self.parents_label = QLabel(parents_text, self.central_widget)
        self.parents_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.parents_label.setStyleSheet("font-size: 12px; color: gray; margin-top: -12px;")

        self.layout.addWidget(self.title_bar)
        self.layout.addWidget(self.image)
        self.layout.addWidget(self.score_label)
        self.layout.addWidget(self.parents_label)

        self.setProperty('selected', False)
        self.offset = None
        self.start_pos = None  # For drag threshold

    def closeEvent(self, event):
        self._image_manager.remove_image(self._image_info)
        self._image_manager.selectionChanged.disconnect(self.on_selection_changed)
        event.accept()

    @property
    def image_info(self):
        return self._image_info

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
            if distance < DRAG_THRESHOLD and self._image_info.selectable:  # Do not select if user is dragging
                if self.property('selected'):
                    self._image_manager.unselect_image(self._image_info)
                else:
                    self._image_manager.select_image(self._image_info)
            self.start_pos = None
        self.offset = None
