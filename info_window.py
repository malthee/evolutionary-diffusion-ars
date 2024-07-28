from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QScrollArea, QLabel, QSizePolicy


class InfoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Information")
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint |
                            Qt.WindowType.WindowCloseButtonHint)
        # Move the window to the top left corner
        self.move(QPoint(20, 50))

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_area.setWidget(scroll_content)

        info_label = QLabel(self)
        info_label.setTextFormat(Qt.TextFormat.RichText)
        info_label.setWordWrap(True)
        info_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        info_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        info_label.setText("""
            <h1>Evolutionary Diffusion Ars</h1>
            <p>
                This interactive installation showcases how evolutionary algorithms can be used to optimize and automatically generate images based on a score. 
                In this case, you the human play the role of the selector, deciding which images to combine, mutate and create.
            </p>
            
            <h1>Usage</h1>
            <p>
                According to Stability AI guidelines, parental approval is required for users under 18 years old.
            </p>
            <p>
                Click on one or more images to perform evolutionary actions:
            </p>
            <ul>
                <li><b>No Image Selected</b>: Create a new random image.</li>
                <li><b>Single Image Selected</b>: Mutate the image to create a slightly different version. Or you also download the image
                by creating a download QR code.</li>
                <li><b>Two Images Selected</b>: Create a new image that combines aspects of both selected images.</li>
                <li><b>Delete All Images</b>: Click the trash can icon in the top right corner.</li>
            </ul>
            
            <p class="note">
                Note: The results of the combinations or mutations may not always be perfect or immediately understandable. The process involves a complex algorithm with elements of randomness, making each outcome unique.
            </p>
            <h1>Details</h1>
            <p>
                The underlying score function here is the Aesthetics Predictor V2 made by Christoph Schuhmann at LAION. They used this predictor to segment a dataset into aesthetics categories. While the name "aesthetics" might cause some discussion, the real use case was to separate "usable or okay looking images" from bad images, which it does pretty well. Only in the extremes (high and low scores) does the predictor get biased.
            </p>
            <p>
                The image generator used here is SDXL Turbo, which uses a novel training technique to make generation much quicker (as you can see, images are generated in mere seconds). 
            </p>
            <p>
                To generate random images, the value range of a benchmark framework called Google Parti Prompts P2 was used to get a min/max value range. Then a random embedding inside this range is created and used in the image generation process.
            </p>
            <p>
                Lastly, the interactive part was made in Python with PyQt6 as the GUI, and the source code is publicly available at https://github.com/malthee/evolutionary-diffusion-ars.
            </p>
            <h1>Evolutionary Diffusion</h1>
            <p>
                Evolutionary Diffusion is a project I started for my master's thesis. In collaboration with my advisor Prof. (FH) Priv.-Doz. Dipl.-Ing. Dr. Michael Affenzeller, the goal was to create novel images and optimize them on different criteria. The gist behind it is using the vector embeddings, which semantically encapsulate the meaning of a prompt (or image description) in numerical values to steer the image generation. These embeddings, or sets of numerical values, are optimized through evolutionary processes like mutation (changing values) and crossover (mixing values, creating children) steered by a fitness function, like in natural selection. You can think of it like the best images survive.
            </p>
            <p>
                Through this process, it was possible to:
            </p>
            <ul>
                <li>Optimize for aesthetics (as defined by the predictor).</li>
                <li>Find an image matching a prompt.</li>
                <li>Maximize visual criteria like “happiness, sadness, brightness, etc.”</li>
                <li>Work against/with AI-Detection.</li>
                <li>Explore artistic creations by concurrently performing evolution with different styles (like Artists or Epochs, which influence each other over time).</li>
            </ul>
            <h1>Author</h1>
            <p>
            My Name is Marcel Salvenmoser. I studied Software Engineering at the University of Applied Sciences Upper Austria in Hagenberg. 
            For my Master's Thesis I wrote a framework for applying evolutionary computing to image generation. Nowadays I work at winkk GmbH as a Software Engineer. 
            I am really stoked about creating my first interactive installation and I hope you enjoy it as much as I did creating it. It was a tough weekend though. :D
            </p>
            <h1>References</h1>
            <ul>
                <li>Axel Sauer et al. “Adversarial Diffusion Distillation”. arXiv.org (2023). doi: https://doi.org/10.48550/arxiv.2311.17042</li>
                <li>Google-Research/Parti. Google Research, Mar. 12, 2024. url: https://github.com/google-research/parti (visited on 03/18/2024)</li>
                <li>Christoph Schuhmann. LAION-Aesthetics | LAION. url: https://laion.ai/blog/laion-aesthetics (visited on 03/18/2024)</li>
                <li>Christoph Schuhmann. Christophschuhmann/Improved-Aesthetic-Predictor. Apr. 5, 2024. url: https://github.com/christophschuhmann/improved-aesthetic-predictor (visited on 04/05/2024)</li>
                <li>Stabilityai/Sdxl-Turbo · Hugging Face. url: https://huggingface.co/stabilityai/sdxl-turbo (visited on 03/18/2024)</li>
            </ul>
        """)
        scroll_layout.addWidget(info_label)
