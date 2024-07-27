import os
import random
import shelve
import sys
from typing import List

from PyQt6.QtCore import Qt, QRect, pyqtSlot, QObject, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QHBoxLayout, QFrame, QVBoxLayout, QPushButton, \
    QSlider

from diffusers.utils import logging
from evolutionary_prompt_embedding.argument_types import PooledPromptEmbedData
from evolutionary_prompt_embedding.image_creation import SDXLPromptEmbeddingImageCreator
from evolutionary_prompt_embedding.variation import \
    UniformGaussianMutatorArguments, PooledUniformGaussianMutator, PooledArithmeticCrossover
from evolutionary_prompt_embedding.value_ranges import SDXLTurboEmbeddingRange, SDXLTurboPooledEmbeddingRange
from evolutionary_imaging.evaluators import AestheticsImageEvaluator
from evolutionary_imaging.image_base import ImageSolutionData

APP_NAME = "evolutionary-diffusion Interactive Ars Demo"
APP_ICON = "./assets/icon.png"
APP_VERSION = "0.1.0"
TEST_IMAGES = ["./assets/test1.png", "./assets/test2.png", "./assets/test3.png"]
SHELVE = "evolutionary_diffusion_shelve"
IMAGE_COUNTER = "image_counter"
IMAGE_LOCATION = "results"
IMAGE_SIZE = 250
LABEL_HEIGHT = 50
CUSTOM_TITLE_BAR_HEIGHT = 30
DRAGGABLE_WINDOW_HEIGHT = IMAGE_SIZE + LABEL_HEIGHT + CUSTOM_TITLE_BAR_HEIGHT
DRAGGABLE_WINDOW_WIDTH = IMAGE_SIZE
MAX_FIND_POSITION_TRIES = 10
DRAG_THRESHOLD = 10
MAX_IMAGES = 10

os.environ["QT_QPA_PLATFORMTHEME"] = "light"
os.environ["TOKENIZERS_PARALLELISM"] = "false"  # Avoids warning from transformers
logging.disable_progress_bar()  # Or else your output will be full of progress bars
logging.set_verbosity_error()
os.mkdir(IMAGE_LOCATION) if not os.path.exists(IMAGE_LOCATION) else None


class ImageInfo:
    def __init__(self, arguments, path: str, score: float):
        self._arguments = arguments
        self._path = path
        self._score = score
        self._name = os.path.splitext(os.path.basename(path))[0]  # Filename without extension for display

    @property
    def arguments(self):
        return self._arguments

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

    # Setup for image generation, part of the evolutionary_diffusion library
    imageCreator = SDXLPromptEmbeddingImageCreator(inference_steps=4, batch_size=1, deterministic=True)
    evaluator = AestheticsImageEvaluator()
    embedding_range = SDXLTurboEmbeddingRange()
    pooled_embedding_range = SDXLTurboPooledEmbeddingRange()
    mutation_arguments = UniformGaussianMutatorArguments(mutation_rate=0.05, mutation_strength=2,
                                                         clamp_range=(embedding_range.minimum, embedding_range.maximum))
    mutation_arguments_pooled = UniformGaussianMutatorArguments(mutation_rate=0.05, mutation_strength=0.4,
                                                                clamp_range=(pooled_embedding_range.minimum,
                                                                             pooled_embedding_range.maximum))
    mutator = PooledUniformGaussianMutator(mutation_arguments, mutation_arguments_pooled)

    def __init__(self):
        super().__init__()
        self._selected_images: List[ImageInfo] = []
        self._images: List[ImageInfo] = []
        self.selectionChanged.connect(self.on_selection_changed)  # Update count on selection changes
        self.imageRemoved.connect(self.on_selection_changed)  # Update count on image removal
        self.imageAdded.connect(self.on_new_image)  # Update persisted counter of images

    @property
    def selected_images(self):
        return self._selected_images

    @property
    def images(self):
        return self._images

    @pyqtSlot()
    def on_selection_changed(self):
        self.selectionCountChanged.emit(len(self._selected_images))

    @pyqtSlot()
    def on_new_image(self):
        with shelve.open(SHELVE) as db:
            counter = db.get(IMAGE_COUNTER, 0)
            counter += 1
            db[IMAGE_COUNTER] = counter

    def get_current_image_counter(self):
        with shelve.open(SHELVE) as db:
            return db.get(IMAGE_COUNTER, 0)

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

    # TODO improve code dupe
    def generate_image(self):
        random_embeds = PooledPromptEmbedData(self.embedding_range.random_tensor_in_range(),
                                              self.pooled_embedding_range.random_tensor_in_range())
        image_data = self.imageCreator.create_solution(random_embeds)
        image_data.fitness = self.evaluator.evaluate(image_data.result)
        image_filename = f"{self.get_current_image_counter()}.png"
        image_path = os.path.join(IMAGE_LOCATION, image_filename)
        image_data.result.images[0].save(image_path)
        image_info = ImageInfo(random_embeds, image_path, image_data.fitness)

        if len(self._images) >= MAX_IMAGES:
            self.remove_image(self._images[0])
        self._images.append(image_info)
        self.imageAdded.emit(image_info)

    def mutate_image(self, image_info: ImageInfo):
        mutated_embeds = self.mutator.mutate(image_info.arguments)
        image_data = self.imageCreator.create_solution(mutated_embeds)
        image_data.fitness = self.evaluator.evaluate(image_data.result)
        image_filename = f"{self.get_current_image_counter()}.png"
        image_path = os.path.join(IMAGE_LOCATION, image_filename)
        image_data.result.images[0].save(image_path)
        mutated_info = ImageInfo(mutated_embeds, image_path, image_data.fitness)

        if len(self._images) >= MAX_IMAGES:
            self.remove_image(self._images[0])
        self._images.append(mutated_info)
        self.imageAdded.emit(mutated_info)

    def create_child(self, parent1: ImageInfo, parent2: ImageInfo, parent_contribution: int):
        weight = float(parent_contribution) / 100
        child_embeds = PooledArithmeticCrossover(weight, weight).crossover(parent1.arguments, parent2.arguments)
        image_data = self.imageCreator.create_solution(child_embeds)
        image_data.fitness = self.evaluator.evaluate(image_data.result)
        image_filename = f"{self.get_current_image_counter()}.png"
        image_path = os.path.join(IMAGE_LOCATION, image_filename)
        image_data.result.images[0].save(image_path)
        child_info = ImageInfo(child_embeds, image_path, image_data.fitness)

        if len(self._images) >= MAX_IMAGES:
            self.remove_image(self._images[0])
        self._images.append(child_info)
        self.imageAdded.emit(child_info)

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
        self._image_manager.generate_image()
        self._image_manager.unselect_all()

    @pyqtSlot()
    def mutate_image(self):
        self._image_manager.mutate_image(self._image_manager.selected_images[0])
        self._image_manager.unselect_all()

    @pyqtSlot()
    def create_child(self):
        parent1, parent2 = self._image_manager.selected_images
        parent_contribution = self.slider.value()
        self._image_manager.create_child(parent1, parent2, parent_contribution)
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
        self.score_label.setStyleSheet("font-size: 24px; font-weight: bold;")

        self.layout.addWidget(self.title_bar)
        self.layout.addWidget(self.image)
        self.layout.addWidget(self.score_label)

        self.setProperty('selected', False)
        self.offset = None
        self.start_pos = None  # For drag threshold

    def closeEvent(self, event):
        self._image_manager.unselect_image(self._image_info)
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
            if distance < DRAG_THRESHOLD:  # Do not select if user is dragging
                if self.property('selected'):
                    self._image_manager.unselect_image(self._image_info)
                else:
                    self._image_manager.select_image(self._image_info)
            self.start_pos = None
        self.offset = None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._image_manager = ImageManager()
        self._image_manager.imageAdded.connect(self.on_image_added)
        self._image_manager.imageRemoved.connect(self.on_image_removed)

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

        self.image_menu = ImageMenu(self._image_manager, self)
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
                frame = DraggableImageWindow(ImageInfo(None, image_path, random.normalvariate()), self._image_manager)
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
        return QRect(random.randint(0, self.width() - IMAGE_SIZE), random.randint(0, self.height() - IMAGE_SIZE),
                     IMAGE_SIZE, IMAGE_SIZE)

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
        self._image_manager.clear_all_images()
        for frame in self.frames:
            frame.close()

    @pyqtSlot(ImageInfo)
    def on_image_added(self, image_info: ImageInfo):
        frame = DraggableImageWindow(image_info, self._image_manager)
        frame.setGeometry(self.getRandomRect())
        frame.show()
        frame.raise_()
        self.frames.append(frame)

    @pyqtSlot(ImageInfo)
    def on_image_removed(self, image_info: ImageInfo):
        to_close = []
        for frame in list(self.frames):
            if frame.image_info == image_info:
                to_close.append(frame)

        for frame in to_close:
            frame.close()
            self.frames.remove(frame)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._image_manager.unselect_all()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(APP_ICON))
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec())
