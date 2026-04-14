"""
CLIP Encoder — wraps HuggingFace CLIP model for both image and text encoding.

Model: openai/clip-vit-base-patch32
Embedding dimension: 512
Shared vector space: text and images are encoded into the SAME 512-dim space,
                     enabling cross-modal retrieval (text query -> image results).

Key concept:
    CLIP was trained to align text and image representations.
    So "red velvet cake" as text and an image of a red velvet cake
    will have HIGH cosine similarity in this 512-dim space.

Usage:
    encoder = CLIPEncoder()

    # Encode a text query
    text_vec = encoder.encode_text("birthday cake with candles")

    # Encode an image
    image_vec = encoder.encode_image(Path("data/images/prod_001.jpg"))

    # Similarity
    from numpy import dot
    score = dot(text_vec, image_vec)  # Higher = more similar
"""

import numpy as np
from pathlib import Path
from PIL import Image
from loguru import logger
from transformers import CLIPProcessor, CLIPModel
import torch
from config.settings import Settings

settings = Settings()


class CLIPEncoder:
    """
    Singleton-style CLIP encoder.
    Loads model once, reuses for all encoding operations.
    Runs on CPU — no GPU required.
    """

    _instance = None  # Singleton pattern — only load model once

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        logger.info(f"Loading CLIP model: {settings.CLIP_MODEL_NAME}")
        self.model = CLIPModel.from_pretrained(settings.CLIP_MODEL_NAME)
        self.processor = CLIPProcessor.from_pretrained(settings.CLIP_MODEL_NAME)
        self.model.eval()  # Inference mode
        self.device = "cpu"
        self.embedding_dim = settings.CLIP_EMBEDDING_DIM
        self._initialized = True
        logger.info("CLIP model loaded")

    def encode_text(self, text: str) -> list[float]:
        """
        Encode a text string into a 512-dim CLIP embedding.

        This embedding lives in the SAME space as image embeddings,
        so you can search image collections with text queries.

        Args:
            text: Natural language string (e.g. "chocolate birthday cake")

        Returns:
            Normalized 512-dim embedding as list[float]
        """
        inputs = self.processor(text=[text], return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            out = self.model.get_text_features(**inputs)
        # transformers >=5.x returns BaseModelOutputWithPooling; <5.x returns tensor
        features = out.pooler_output if hasattr(out, "pooler_output") else out
        # L2 normalize (CLIP embeddings should be normalized for cosine sim)
        features = features / features.norm(dim=-1, keepdim=True)
        return features[0].tolist()

    def encode_image(self, image_path: Path) -> list[float] | None:
        """
        Encode a product image into a 512-dim CLIP embedding.

        Args:
            image_path: Path to local image file (.jpg, .png)

        Returns:
            Normalized 512-dim embedding as list[float], or None if image fails to load
        """
        try:
            image = Image.open(image_path).convert("RGB")
            inputs = self.processor(images=image, return_tensors="pt")
            with torch.no_grad():
                out = self.model.get_image_features(pixel_values=inputs["pixel_values"])
            features = out.pooler_output if hasattr(out, "pooler_output") else out
            features = features / features.norm(dim=-1, keepdim=True)
            return features[0].tolist()
        except Exception as e:
            logger.warning(f"  Failed to encode image {image_path}: {e}")
            return None

    def encode_images_batch(self, image_paths: list[Path], batch_size: int = 32) -> list[tuple[Path, list[float]]]:
        """
        Encode multiple images in batches (more efficient than one-by-one).

        Args:
            image_paths: List of image file paths
            batch_size: Number of images to process at once

        Returns:
            List of (path, embedding) tuples — failed images are skipped
        """
        results = []
        total = len(image_paths)

        for i in range(0, total, batch_size):
            batch_paths = image_paths[i:i + batch_size]
            logger.info(f"  Encoding batch {i // batch_size + 1} / {(total + batch_size - 1) // batch_size}")

            images, valid_paths = [], []
            for p in batch_paths:
                try:
                    images.append(Image.open(p).convert("RGB"))
                    valid_paths.append(p)
                except Exception:
                    logger.warning(f"  Skipping unreadable: {p}")

            if not images:
                continue

            inputs = self.processor(images=images, return_tensors="pt")
            with torch.no_grad():
                out = self.model.get_image_features(pixel_values=inputs["pixel_values"])
            # transformers >=5.x returns BaseModelOutputWithPooling; <5.x returns tensor
            features = out.pooler_output if hasattr(out, "pooler_output") else out
            features = features / features.norm(dim=-1, keepdim=True)

            for path, embedding in zip(valid_paths, features.tolist()):
                results.append((path, embedding))

        logger.info(f"  Encoded {len(results)} / {total} images")
        return results
