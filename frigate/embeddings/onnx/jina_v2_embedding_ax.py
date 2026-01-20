"""AX JinaV2 Embeddings."""

import io
import logging
import os
import threading
from typing import Any

import numpy as np
from PIL import Image
from transformers import AutoTokenizer
from transformers.utils.logging import disable_progress_bar, set_verbosity_error

from frigate.const import MODEL_CACHE_DIR
from frigate.embeddings.onnx.base_embedding import BaseEmbedding
from frigate.comms.inter_process import InterProcessRequestor
from frigate.util.downloader import ModelDownloader
from frigate.types import ModelStatusTypesEnum
from frigate.const import MODEL_CACHE_DIR, UPDATE_MODEL_STATE

import axengine as axe

# disables the progress bar and download logging for downloading tokenizers and image processors
disable_progress_bar()
set_verbosity_error()
logger = logging.getLogger(__name__)


class AXClipRunner:
    def __init__(self, image_encoder_path: str, text_encoder_path: str):
        self.image_encoder_path = image_encoder_path
        self.text_encoder_path = text_encoder_path
        self.image_encoder_runner = axe.InferenceSession(image_encoder_path)
        self.text_encoder_runner = axe.InferenceSession(text_encoder_path)

        for input in self.image_encoder_runner.get_inputs():
            logger.info(input.name, input.shape, input.dtype)

        for output in self.image_encoder_runner.get_outputs():
            logger.info(output.name, output.shape, output.dtype)

        for input in self.text_encoder_runner.get_inputs():
            logger.info(input.name, input.shape, input.dtype)

        for output in self.text_encoder_runner.get_outputs():
            logger.info(output.name, output.shape, output.dtype)

    def run(self, onnx_inputs):
        text_embeddings = []
        image_embeddings = []
        if "input_ids" in onnx_inputs:
            for input_ids in onnx_inputs["input_ids"]:
                input_ids = input_ids.reshape(1, -1)
                text_embeddings.append(
                    self.text_encoder_runner.run(None, {"inputs_id": input_ids})[0][0]
                )
        if "pixel_values" in onnx_inputs:
            for pixel_values in onnx_inputs["pixel_values"]:
                if len(pixel_values.shape) == 3:
                    pixel_values = pixel_values[None, ...]
                image_embeddings.append(
                    self.image_encoder_runner.run(None, {"pixel_values": pixel_values})[
                        0
                    ][0]
                )
        return np.array(text_embeddings), np.array(image_embeddings)

class AXJinaV2Embedding(BaseEmbedding):
    def __init__(
        self,
        model_size: str,
        requestor: InterProcessRequestor,
        device: str = "AUTO",
        embedding_type: str = None,
    ):
        HF_ENDPOINT = os.environ.get("HF_ENDPOINT", "https://huggingface.co")
        super().__init__(
            model_name="AXERA-TECH/jina-clip-v2",
            model_file=None,
            download_urls={
                "image_encoder.axmodel": f"{HF_ENDPOINT}/AXERA-TECH/jina-clip-v2/resolve/main/image_encoder.axmodel",
                "text_encoder.axmodel": f"{HF_ENDPOINT}/AXERA-TECH/jina-clip-v2/resolve/main/text_encoder.axmodel",
            },
        )

        self.tokenizer_source = "jinaai/jina-clip-v2"
        self.tokenizer_file = "tokenizer"
        self.embedding_type = embedding_type
        self.requestor = requestor
        self.model_size = model_size
        self.device = device
        self.download_path = os.path.join(MODEL_CACHE_DIR, self.model_name)
        self.tokenizer = None
        self.image_processor = None
        self.runner = None
        self.mean = np.array([0.48145466, 0.4578275, 0.40821073], dtype=np.float32)
        self.std = np.array([0.26862954, 0.26130258, 0.27577711], dtype=np.float32)

        # Lock to prevent concurrent calls (text and vision share this instance)
        self._call_lock = threading.Lock()

        # download the model and tokenizer
        files_names = list(self.download_urls.keys()) + [self.tokenizer_file]
        if not all(
            os.path.exists(os.path.join(self.download_path, n)) for n in files_names
        ):
            logger.debug(f"starting model download for {self.model_name}")
            self.downloader = ModelDownloader(
                model_name=self.model_name,
                download_path=self.download_path,
                file_names=files_names,
                download_func=self._download_model,
            )
            self.downloader.ensure_model_files()
            # Avoid lazy loading in worker threads: block until downloads complete
            # and load the model on the main thread during initialization.
            self._load_model_and_utils()
        else:
            self.downloader = None
            ModelDownloader.mark_files_state(
                self.requestor,
                self.model_name,
                files_names,
                ModelStatusTypesEnum.downloaded,
            )
            self._load_model_and_utils()
            logger.debug(f"models are already downloaded for {self.model_name}")

    def _download_model(self, path: str):
        try:
            file_name = os.path.basename(path)

            if file_name in self.download_urls:
                ModelDownloader.download_from_url(self.download_urls[file_name], path)
            elif file_name == self.tokenizer_file:
                tokenizer = AutoTokenizer.from_pretrained(
                    self.tokenizer_source,
                    trust_remote_code=True,
                    cache_dir=os.path.join(
                        MODEL_CACHE_DIR, self.model_name, "tokenizer"
                    ),
                    clean_up_tokenization_spaces=True,
                )
                tokenizer.save_pretrained(path)
            self.requestor.send_data(
                UPDATE_MODEL_STATE,
                {
                    "model": f"{self.model_name}-{file_name}",
                    "state": ModelStatusTypesEnum.downloaded,
                },
            )
        except Exception:
            self.requestor.send_data(
                UPDATE_MODEL_STATE,
                {
                    "model": f"{self.model_name}-{file_name}",
                    "state": ModelStatusTypesEnum.error,
                },
            )

    def _load_model_and_utils(self):
        if self.runner is None:
            if self.downloader:
                self.downloader.wait_for_download()

            self.tokenizer = AutoTokenizer.from_pretrained(
                self.tokenizer_source,
                cache_dir=os.path.join(MODEL_CACHE_DIR, self.model_name, "tokenizer"),
                trust_remote_code=True,
                clean_up_tokenization_spaces=True,
            )

            self.runner = AXClipRunner(
                os.path.join(self.download_path, "image_encoder.axmodel"),
                os.path.join(self.download_path, "text_encoder.axmodel"),
            )

    def _preprocess_image(self, image_data: bytes | Image.Image):
        """
        Manually preprocess a single image from bytes or PIL.Image to (3, 512, 512).
        """
        if isinstance(image_data, bytes):
            image = Image.open(io.BytesIO(image_data))
        else:
            image = image_data

        if image.mode != "RGB":
            image = image.convert("RGB")

        image = image.resize((512, 512), Image.Resampling.LANCZOS)

        # Convert to numpy array, normalize to [0, 1], and transpose to (channels, height, width)
        image_array = np.array(image, dtype=np.float32) / 255.0
        # Normalize using mean and std
        image_array = (image_array - self.mean) / self.std

        image_array = np.transpose(image_array, (2, 0, 1))  # (H, W, C) -> (C, H, W)

        return image_array

    def _preprocess_inputs(self, raw_inputs):
        """
        Preprocess inputs into a list of real input tensors (no dummies).
        - For text: Returns list of input_ids.
        - For vision: Returns list of pixel_values.
        """
        if not isinstance(raw_inputs, list):
            raw_inputs = [raw_inputs]

        processed = []
        if self.embedding_type == "text":
            for text in raw_inputs:
                input_ids = self.tokenizer(
                    [text], return_tensors="np", padding="max_length", max_length=50
                )["input_ids"]
                input_ids = input_ids.astype(np.int32)
                processed.append(input_ids)
        elif self.embedding_type == "vision":
            for img in raw_inputs:
                pixel_values = self._preprocess_image(img)
                processed.append(
                    pixel_values[np.newaxis, ...]
                )  # Add batch dim: (1, 3, 512, 512)
        else:
            raise ValueError(
                f"Invalid embedding_type: {self.embedding_type}. Must be 'text' or 'vision'."
            )
        return processed

    def _postprocess_outputs(self, outputs):
        """
        Process ONNX model outputs, truncating each embedding in the array to truncate_dim.
        - outputs: NumPy array of embeddings.
        - Returns: List of truncated embeddings.
        """
        # size of vector in database
        truncate_dim = 768

        # jina v2 defaults to 1024 and uses Matryoshka representation, so
        # truncating only causes an extremely minor decrease in retrieval accuracy
        if outputs.shape[-1] > truncate_dim:
            outputs = outputs[..., :truncate_dim]

        return outputs

    def __call__(
        self, inputs: list[str] | list[Image.Image] | list[str], embedding_type=None
    ):
        # Lock the entire call to prevent race conditions when text and vision
        # embeddings are called concurrently from different threads
        with self._call_lock:
            self.embedding_type = embedding_type
            if not self.embedding_type:
                raise ValueError(
                    "embedding_type must be specified either in __init__ or __call__"
                )

            self._load_model_and_utils()
            processed = self._preprocess_inputs(inputs)

            # Prepare ONNX inputs with matching batch sizes
            onnx_inputs = {}
            if self.embedding_type == "text":
                onnx_inputs["input_ids"] = np.stack([x[0] for x in processed])
            elif self.embedding_type == "vision":
                onnx_inputs["pixel_values"] = np.stack([x[0] for x in processed])
            else:
                raise ValueError("Invalid embedding type")

            # Run inference
            text_embeddings, image_embeddings = self.runner.run(onnx_inputs)
            if self.embedding_type == "text":
                embeddings = text_embeddings  # text embeddings
            elif self.embedding_type == "vision":
                embeddings = image_embeddings  # image embeddings
            else:
                raise ValueError("Invalid embedding type")

            embeddings = self._postprocess_outputs(embeddings)
            return [embedding for embedding in embeddings]
