"""AX650 Jina V2 语义搜索模型。"""

import io
import logging
import os
import threading

import numpy as np
from PIL import Image
from transformers import AutoTokenizer
from transformers.utils.logging import disable_progress_bar, set_verbosity_error

from frigate.comms.inter_process import InterProcessRequestor
from frigate.const import MODEL_CACHE_DIR, UPDATE_MODEL_STATE
from frigate.embeddings.onnx.base_embedding import BaseEmbedding
from frigate.types import ModelStatusTypesEnum
from frigate.util.downloader import ModelDownloader

disable_progress_bar()
set_verbosity_error()
logger = logging.getLogger(__name__)


class AXClipRunner:
    def __init__(self, image_encoder_path: str, text_encoder_path: str):
        try:
            import axengine as axe
        except ImportError as exc:
            raise RuntimeError(
                "ax_jinav2 需要 AXEngine Python 运行时，请确认当前镜像已安装 axengine/pyaxengine。"
            ) from exc

        self.image_encoder_runner = axe.InferenceSession(image_encoder_path)
        self.text_encoder_runner = axe.InferenceSession(text_encoder_path)

        for input_meta in self.image_encoder_runner.get_inputs():
            logger.info(
                "AX Jina image input %s %s %s",
                input_meta.name,
                input_meta.shape,
                input_meta.dtype,
            )

        for output_meta in self.image_encoder_runner.get_outputs():
            logger.info(
                "AX Jina image output %s %s %s",
                output_meta.name,
                output_meta.shape,
                output_meta.dtype,
            )

        for input_meta in self.text_encoder_runner.get_inputs():
            logger.info(
                "AX Jina text input %s %s %s",
                input_meta.name,
                input_meta.shape,
                input_meta.dtype,
            )

        for output_meta in self.text_encoder_runner.get_outputs():
            logger.info(
                "AX Jina text output %s %s %s",
                output_meta.name,
                output_meta.shape,
                output_meta.dtype,
            )

    def run(self, inputs: dict[str, np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
        text_embeddings = []
        image_embeddings = []

        if "input_ids" in inputs:
            for input_ids in inputs["input_ids"]:
                text_embeddings.append(
                    self.text_encoder_runner.run(
                        None, {"inputs_id": input_ids.reshape(1, -1)}
                    )[0][0]
                )

        if "pixel_values" in inputs:
            for pixel_values in inputs["pixel_values"]:
                if len(pixel_values.shape) == 3:
                    pixel_values = pixel_values[None, ...]
                image_embeddings.append(
                    self.image_encoder_runner.run(
                        None, {"pixel_values": pixel_values}
                    )[0][0]
                )

        return np.array(text_embeddings), np.array(image_embeddings)


class AXJinaV2Embedding(BaseEmbedding):
    def __init__(
        self,
        model_size: str,
        requestor: InterProcessRequestor,
        embedding_type: str | None = None,
    ):
        hf_endpoint = os.environ.get("HF_ENDPOINT", "https://huggingface.co")
        super().__init__(
            model_name="AXERA-TECH/jina-clip-v2",
            model_file="image_encoder.axmodel",
            download_urls={
                "image_encoder.axmodel": f"{hf_endpoint}/AXERA-TECH/jina-clip-v2/resolve/main/image_encoder.axmodel",
                "text_encoder.axmodel": f"{hf_endpoint}/AXERA-TECH/jina-clip-v2/resolve/main/text_encoder.axmodel",
            },
        )

        self.tokenizer_source = "jinaai/jina-clip-v2"
        self.tokenizer_file = "tokenizer"
        self.embedding_type = embedding_type
        self.requestor = requestor
        self.model_size = model_size
        self.download_path = os.path.join(MODEL_CACHE_DIR, self.model_name)
        self.tokenizer = None
        self.runner: AXClipRunner | None = None
        self.mean = np.array([0.48145466, 0.4578275, 0.40821073], dtype=np.float32)
        self.std = np.array([0.26862954, 0.26130258, 0.27577711], dtype=np.float32)
        self._call_lock = threading.Lock()

        file_names = list(self.download_urls.keys()) + [self.tokenizer_file]
        if not all(
            os.path.exists(os.path.join(self.download_path, name))
            for name in file_names
        ):
            logger.debug("starting model download for %s", self.model_name)
            self.downloader = ModelDownloader(
                model_name=self.model_name,
                download_path=self.download_path,
                file_names=file_names,
                download_func=self._download_model,
            )
            self.downloader.ensure_model_files()
            self._load_model_and_utils()
        else:
            self.downloader = None
            ModelDownloader.mark_files_state(
                self.requestor,
                self.model_name,
                file_names,
                ModelStatusTypesEnum.downloaded,
            )
            self._load_model_and_utils()
            logger.debug("models are already downloaded for %s", self.model_name)

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
                        MODEL_CACHE_DIR, self.model_name, self.tokenizer_file
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
                cache_dir=os.path.join(
                    MODEL_CACHE_DIR, self.model_name, self.tokenizer_file
                ),
                trust_remote_code=True,
                clean_up_tokenization_spaces=True,
            )
            self.runner = AXClipRunner(
                os.path.join(self.download_path, "image_encoder.axmodel"),
                os.path.join(self.download_path, "text_encoder.axmodel"),
            )

    def _preprocess_image(self, image_data: bytes | Image.Image) -> np.ndarray:
        if isinstance(image_data, bytes):
            image = Image.open(io.BytesIO(image_data))
        else:
            image = image_data

        if image.mode != "RGB":
            image = image.convert("RGB")

        image = image.resize((512, 512), Image.Resampling.LANCZOS)
        image_array = np.array(image, dtype=np.float32) / 255.0
        image_array = (image_array - self.mean) / self.std
        image_array = np.transpose(image_array, (2, 0, 1))

        return image_array

    def _preprocess_inputs(self, raw_inputs):
        if not isinstance(raw_inputs, list):
            raw_inputs = [raw_inputs]

        processed = []
        if self.embedding_type == "text":
            for text in raw_inputs:
                input_ids = self.tokenizer(
                    [text],
                    return_tensors="np",
                    padding="max_length",
                    max_length=50,
                )["input_ids"]
                processed.append(input_ids.astype(np.int32))
        elif self.embedding_type == "vision":
            for image in raw_inputs:
                processed.append(self._preprocess_image(image)[np.newaxis, ...])
        else:
            raise ValueError(
                f"Invalid embedding_type: {self.embedding_type}. "
                "Must be 'text' or 'vision'."
            )

        return processed

    def _postprocess_outputs(self, outputs):
        truncate_dim = 768

        if outputs.shape[-1] > truncate_dim:
            outputs = outputs[..., :truncate_dim]

        return outputs

    def __call__(self, inputs, embedding_type=None) -> list[np.ndarray]:
        with self._call_lock:
            self.embedding_type = embedding_type
            if not self.embedding_type:
                raise ValueError(
                    "embedding_type must be specified either in __init__ or __call__"
                )

            self._load_model_and_utils()
            processed = self._preprocess_inputs(inputs)

            runner_inputs = {}
            if self.embedding_type == "text":
                runner_inputs["input_ids"] = np.stack([item[0] for item in processed])
            elif self.embedding_type == "vision":
                runner_inputs["pixel_values"] = np.stack(
                    [item[0] for item in processed]
                )
            else:
                raise ValueError("Invalid embedding type")

            if self.runner is None:
                raise RuntimeError("AX Jina runner is not initialized")

            text_embeddings, image_embeddings = self.runner.run(runner_inputs)
            if self.embedding_type == "text":
                embeddings = text_embeddings
            elif self.embedding_type == "vision":
                embeddings = image_embeddings
            else:
                raise ValueError("Invalid embedding type")

            embeddings = self._postprocess_outputs(embeddings)
            return [embedding for embedding in embeddings]
