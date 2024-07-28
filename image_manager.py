import os
import shelve
from queue import Queue
from typing import List

from PyQt6.QtCore import pyqtSlot, QObject, pyqtSignal, QThread, QMutex
from diffusers.utils import logging
from evolutionary_imaging.evaluators import AestheticsImageEvaluator
from evolutionary_prompt_embedding.argument_types import PooledPromptEmbedData
from evolutionary_prompt_embedding.image_creation import SDXLPromptEmbeddingImageCreator
from evolutionary_prompt_embedding.value_ranges import SDXLTurboEmbeddingRange, SDXLTurboPooledEmbeddingRange
from evolutionary_prompt_embedding.variation import \
    UniformGaussianMutatorArguments, PooledUniformGaussianMutator, PooledArithmeticCrossover

SHELVE = "evolutionary_diffusion_shelve"
IMAGE_COUNTER = "image_counter"
IMAGE_LOCATION = "results"
MAX_IMAGES = 10


def get_current_image_counter():
    with shelve.open(SHELVE) as db:
        return db.get(IMAGE_COUNTER, 0)


class ImageInfo:
    def __init__(self, arguments, path: str, score: float, selectable=True,
                 parent1: 'ImageInfo' = None, parent2: 'ImageInfo' = None):
        self._arguments = arguments
        self._path = path
        self._score = score
        self._selectable = selectable
        self._parent1 = parent1
        self._parent2 = parent2
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
    def selectable(self):
        return self._selectable

    @property
    def parent1(self):
        return self._parent1

    @property
    def parent2(self):
        return self._parent2

    @property
    def name(self):
        return self._name

    @property
    def filename(self):
        return os.path.basename(self._path)

    def __eq__(self, other):
        return self.path == other.path

    def __hash__(self):
        return hash(self.path)


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
    isLoadingChanged = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self._selected_images: List[ImageInfo] = []
        self._images: List[ImageInfo] = []
        self.selectionChanged.connect(self.on_selection_changed)  # Update count on selection changes
        self.imageRemoved.connect(self.on_selection_changed)  # Update count on image removal
        self.imageAdded.connect(self.on_new_image)  # Update persisted counter of images and loading state

        # Image generation thread management
        self._thread_running = False
        self._task_queue = Queue()
        self._mutex = QMutex()
        self._current_thread = None

        # Setup for image generation, part of the evolutionary_diffusion library
        os.environ["TOKENIZERS_PARALLELISM"] = "false"  # Avoids warning from transformers
        logging.disable_progress_bar()  # Or else your output will be full of progress bars
        logging.set_verbosity_error()
        os.mkdir(IMAGE_LOCATION) if not os.path.exists(IMAGE_LOCATION) else None
        self.imageCreator = SDXLPromptEmbeddingImageCreator(inference_steps=4, batch_size=1, deterministic=True)
        self.evaluator = AestheticsImageEvaluator()
        self.embedding_range = SDXLTurboEmbeddingRange()
        self.pooled_embedding_range = SDXLTurboPooledEmbeddingRange()
        self.mutation_arguments = UniformGaussianMutatorArguments(mutation_rate=0.005, mutation_strength=0.01,
                                                                  clamp_range=(self.embedding_range.minimum,
                                                                               self.embedding_range.maximum))
        self.mutation_arguments_pooled = UniformGaussianMutatorArguments(mutation_rate=0.005, mutation_strength=0.05,
                                                                         clamp_range=(
                                                                             self.pooled_embedding_range.minimum,
                                                                             self.pooled_embedding_range.maximum))
        self.mutator = PooledUniformGaussianMutator(self.mutation_arguments, self.mutation_arguments_pooled)

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
        self.isLoadingChanged.emit(False)
        with shelve.open(SHELVE) as db:
            counter = db.get(IMAGE_COUNTER, 0)
            counter += 1
            db[IMAGE_COUNTER] = counter

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

    def _schedule_create_image(self, embeds, parent1=None, parent2=None):
        """
        Schedules the creation of an image with the given embeddings.
        Executed in a QThread to avoid blocking the main thread.
        """
        self._mutex.lock()
        if self._thread_running:
            self._mutex.unlock()
            self._task_queue.put((embeds, parent1, parent2))
        else:
            self._thread_running = True
            self._mutex.unlock()
            self._current_thread = QThread()

            def task():
                self.isLoadingChanged.emit(True)
                image_data = self.imageCreator.create_solution(embeds)
                image_data.fitness = self.evaluator.evaluate(image_data.result)
                image_filename = f"{get_current_image_counter()}.png"
                image_path = os.path.join(IMAGE_LOCATION, image_filename)
                image_data.result.images[0].save(image_path)
                image_info = ImageInfo(arguments=embeds, path=image_path, score=image_data.fitness,
                                       parent1=parent1, parent2=parent2)
                self._add_or_replace_image(image_info)
                self.isLoadingChanged.emit(False)
                self._thread_finished()

            self._current_thread.run = task
            self._current_thread.finished.connect(self._current_thread.deleteLater)
            self._current_thread.start()

    def _thread_finished(self):
        self._mutex.lock()
        self._thread_running = False
        if not self._task_queue.empty():
            embeds, parent1, parent2 = self._task_queue.get()
            self._mutex.unlock()
            self._schedule_create_image(embeds, parent1, parent2)
        else:
            self._mutex.unlock()

    def _add_or_replace_image(self, image_info: ImageInfo):
        if len(self._images) >= MAX_IMAGES:
            # Remove oldest non-selected image
            self.remove_image(
                next((image for image in self._images if image not in self._selected_images), self._images[0]))
        self._images.append(image_info)
        self.imageAdded.emit(image_info)

    def manual_add_image(self, image_info: ImageInfo):
        """
        Manually adds an image to the manager if it does not already exist.
        """
        if image_info not in self._images:
            self._add_or_replace_image(image_info)

    def generate_image(self):
        print("Generating new image")
        random_embeds = PooledPromptEmbedData(self.embedding_range.random_tensor_in_range(),
                                              self.pooled_embedding_range.random_tensor_in_range())
        self._schedule_create_image(random_embeds)

    def mutate_image(self, image_info: ImageInfo):
        print(f"Mutating image {image_info.name}")
        mutated_embeds = self.mutator.mutate(image_info.arguments)
        self._schedule_create_image(mutated_embeds, parent1=image_info)

    def create_child(self, parent1: ImageInfo, parent2: ImageInfo, parent_contribution: int):
        weight = float(parent_contribution) / 100
        print(f"Parent contribution: {weight} for {parent1.name} and {parent2.name}")
        child_embeds = (PooledArithmeticCrossover(interpolation_weight=weight, interpolation_weight_pooled=weight)
                        .crossover(parent1.arguments, parent2.arguments))
        self._schedule_create_image(child_embeds, parent1, parent2)

    def remove_image(self, image_info: ImageInfo):  # May also remove image from disk in the future?
        print(f"Removing image {image_info.name}")
        if image_info in self._images:
            self.unselect_image(image_info)
            self._images.remove(image_info)
            self.imageRemoved.emit(image_info)

    def clear_all_images(self):
        self.unselect_all()
        for image in list(self._images):  # Copy to avoid modifying while iterating
            self.remove_image(image)
        self._images.clear()
