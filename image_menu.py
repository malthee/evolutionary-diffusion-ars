from PyQt6.QtCore import Qt, pyqtSlot, QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel, QWidget, QHBoxLayout, QFrame, QVBoxLayout, QPushButton, \
    QSlider, QComboBox

from image_manager import ImageManager
from qr_blob_manager import QRBlobManager

MENU_WIDTH = 400
MENU_HEIGHT = 300
IMAGE_EXAMPLE_SIZE = 80
STYLE_WEIGHT = 0.95
AVAILABLE_STYLES = [
    "Random",
    "Renaissance",
    "Baroque",
    "Impressionism",
    "Post-Impressionism",
    "Cubism",
    "Surrealism",
    "Pop Art",
    "Abstract Expressionism",
    "Modernism",
    "Fauvism",
    "Pointillism",
    "Minimalism",
    "Digital Art",
    "Street Art",
    # INDIVIDUAL ARTISTS
    "Leonardo da Vinci",
    "Vincent van Gogh",
    "Pablo Picasso",
    "Claude Monet",
    "Salvador Dalí",
    "Andy Warhol",
    "Jackson Pollock",
    "Henri Matisse",
    "Frida Kahlo",
    "Banksy",
    "Jean-Michel Basquiat",
]


class ImageMenu(QFrame):
    def __init__(self, image_manager: ImageManager, qr_blob_manager: QRBlobManager, parent=None):
        super().__init__(parent)
        self._image_manager = image_manager
        self._qr_blob_manager = qr_blob_manager
        self._image_manager.selectionCountChanged.connect(self.update_visibility)
        self._image_manager.isLoadingChanged.connect(self.update_loading)
        self.setFixedSize(MENU_WIDTH, MENU_HEIGHT)
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
            QComboBox {
                background-color: white;
                color: #333;
                border: none;
                border-radius: 25px;
                font-size: 24px;
                padding: 0 16px;               /* vertical padding removed */
                min-height: 56px;             /* exactly button height */
            }
            QComboBox:hover {
                background-color: #f2f2f2;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 40px;                /* comfortable tap area */
                border-left: none;
            }
            QComboBox::down-arrow {
              image: url("assets/down-arrow-gray.svg");
              width: 20px;
              height: 20px;
            }
            QComboBox QAbstractItemView {
                background: white;
                selection-background-color: #ddd;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
              min-height: 48px;            /* big items for touch */
              padding: 0 12px;
            }
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignBottom)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(10)

        # None selected, new image with optional style
        self.style_combo = QComboBox()
        self.style_combo.addItems(AVAILABLE_STYLES)
        # force full width pill
        self.style_combo.setMinimumWidth(MENU_WIDTH - 40)
        self.layout.addWidget(self.style_combo)

        self.new_image_button = QPushButton("+ New Image")
        self.new_image_button.clicked.connect(self.new_image)
        self.layout.addWidget(self.new_image_button)

        # One selected, mutation and qr code
        self.mutate_button = QPushButton("🧬 Mutate this Image")
        self.mutate_button.clicked.connect(self.mutate_image)

        self.qr_code_button = QPushButton("📷 Download QR Code")
        self.qr_code_button.clicked.connect(self.upload_and_get_qr_code)

        self.layout.addWidget(self.mutate_button)
        self.layout.addWidget(self.qr_code_button)

        # 2 Selected, Images and Slider for creating a child
        self.left_image_label = QLabel(self)
        self.left_image_label.setFixedSize(IMAGE_EXAMPLE_SIZE, IMAGE_EXAMPLE_SIZE)
        self.left_image_label.setScaledContents(True)
        self.right_image_label = QLabel(self)
        self.right_image_label.setFixedSize(IMAGE_EXAMPLE_SIZE, IMAGE_EXAMPLE_SIZE)
        self.right_image_label.setScaledContents(True)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setValue(50)

        self.split_button = QPushButton("🔗 Mix Traits")
        self.split_button.clicked.connect(self.create_child)

        # Inner layout for the two images and slider
        self.slider_images_widget = QWidget(self)  # Prevent layouting issues, wrap with widget
        self.slider_images_layout = QHBoxLayout(self.slider_images_widget)
        self.slider_images_layout.setSpacing(0)
        self.slider_images_layout.setContentsMargins(0, 0, 0, 0)
        self.slider_images_layout.addWidget(self.left_image_label)
        self.slider_images_layout.addWidget(self.slider)
        self.slider_images_layout.addWidget(self.right_image_label)
        self.slider_images_widget.setLayout(self.slider_images_layout)

        # Outer layout
        self.layout.addWidget(self.slider_images_widget)
        self.layout.addWidget(self.split_button)

        # Loading
        self.loading_label = QLabel("Being generated by AI", self)
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet("font-size: 24px; color: gray; padding-bottom:20px;")
        self.layout.addWidget(self.loading_label)
        self.loading_label.hide()  # Hide loading label initially

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate_loading)
        self.loading_dots = 0

        self.interactive_widgets = [
            self.style_combo,
            self.new_image_button,
            self.mutate_button,
            self.qr_code_button,
            self.split_button,
            self.slider_images_widget
        ]

        self.update_visibility(len(self._image_manager.selected_images))

    def closeEvent(self, event):
        self._qr_blob_manager.qr_image_finished.disconnect(self._image_manager.manual_add_image)
        self._image_manager.selectionChanged.disconnect(self.update_visibility)
        self._image_manager.isLoadingChanged.disconnect(self.update_loading)
        self.timer.stop()
        event.accept()

    @pyqtSlot()
    def new_image(self):
        style = self.style_combo.currentText()
        if style == "Random" or style == "":
            style = None
        self._image_manager.generate_image(style=style, weight=STYLE_WEIGHT)

    @pyqtSlot()
    def mutate_image(self):
        self._image_manager.mutate_image(self._image_manager.selected_images[0])

    @pyqtSlot()
    def create_child(self):
        parent1, parent2 = self._image_manager.selected_images
        parent_contribution = self.slider.value()
        self._image_manager.create_child(parent1, parent2, parent_contribution)
        # Reset slider
        self.slider.setValue(50)

    @pyqtSlot(int)
    def update_visibility(self, selected_count):
        """
        When none selected, allow new child creation. Otherwise, either mutate an image or create a child
        from two images.
        Do not show when loading.
        """
        is_loading = self.loading_label.isVisible()
        for widget in self.interactive_widgets:
            widget.setVisible(not is_loading)

        if not is_loading:
            none_selected = selected_count == 0
            one_selected = selected_count == 1
            two_selected = selected_count == 2
            self.style_combo.setVisible(none_selected)
            self.new_image_button.setVisible(none_selected)
            self.mutate_button.setVisible(one_selected)
            self.qr_code_button.setVisible(one_selected)
            self.split_button.setVisible(two_selected)
            self.slider_images_widget.setVisible(two_selected)

            # Update left and right image labels based on selection
            if two_selected:
                left_image = QPixmap(self._image_manager.selected_images[1].path)
                self.left_image_label.setPixmap(left_image)
                right_image = QPixmap(self._image_manager.selected_images[0].path)
                self.right_image_label.setPixmap(right_image)

    @pyqtSlot()
    def upload_and_get_qr_code(self):
        image_info = self._image_manager.selected_images[0]
        self._qr_blob_manager.start_upload(image_info)

    @pyqtSlot(bool)
    def update_loading(self, loading):
        self.loading_label.setVisible(loading)
        if loading:
            self.timer.start(300)
        else:
            self.timer.stop()
            self.loading_dots = 0
            self.loading_label.setText("Being generated by AI")
        self.update_visibility(len(self._image_manager.selected_images))

    @pyqtSlot()
    def animate_loading(self):
        dots = '.' * (self.loading_dots % 4)
        self.loading_label.setText(f"Being generated by AI{dots}")
        self.loading_dots += 1