"""
Praman Scan - Image loading and validation helpers.
"""
from pathlib import Path
from typing import Union

import numpy as np
from PIL import Image, UnidentifiedImageError

from config import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class InvalidImageError(Exception):
    """Raised when an uploaded / referenced file is not a usable image."""


def load_image_as_array(source: Union[str, Path, bytes]) -> np.ndarray:
    """
    Load an image from a filesystem path or raw bytes and return it as an
    RGB numpy array (H, W, 3), resized so the longest edge does not exceed
    a sane bound while feature extraction itself resizes to a fixed square.
    """
    try:
        if isinstance(source, (str, Path)):
            img = Image.open(source)
        else:
            from io import BytesIO
            img = Image.open(BytesIO(source))
        img.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise InvalidImageError(f"File could not be read as an image: {exc}") from exc

    if img.mode != "RGB":
        img = img.convert("RGB")

    return np.array(img)


def validate_extension(filename: str) -> None:
    suffix = Path(filename).suffix.lower()
    if suffix not in settings.ALLOWED_EXTENSIONS:
        raise InvalidImageError(
            f"Unsupported file extension '{suffix}'. "
            f"Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )


def validate_size(num_bytes: int) -> None:
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if num_bytes > max_bytes:
        raise InvalidImageError(
            f"File is too large ({num_bytes / (1024 * 1024):.2f} MB). "
            f"Maximum allowed is {settings.MAX_UPLOAD_SIZE_MB} MB."
        )
