import json
from pathlib import Path

import numpy as np
import tensorflow as tf

from config import (
    IMG_SIZE,
    SEQ_LEN,
    FACE_MARGIN,
)

from .video import (
    list_frames,
    load_image,
    sample_indices,
)

from .quality import quality_score


# ============================================================
# VIDEO DATA GENERATOR
# ============================================================

class VideoSequence(tf.keras.utils.Sequence):

    def __init__(
        self,
        manifest,
        detector,
        batch_size=2,
        training=False,
        shuffle=True,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.manifest = manifest
        self.detector = detector
        self.batch_size = batch_size
        self.training = training
        self.shuffle = shuffle

        self.indices = np.arange(len(manifest))

        self.on_epoch_end()

    # ========================================================
    # NUMBER OF BATCHES
    # ========================================================

    def __len__(self):
        return int(
            np.ceil(
                len(self.indices) / self.batch_size
            )
        )

    # ========================================================
    # SHUFFLE
    # ========================================================

    def on_epoch_end(self):

        if self.shuffle:
            np.random.shuffle(self.indices)

    # ========================================================
    # TRAINING AUGMENTATION
    # ========================================================

    def _augment(self, face):

        if not self.training:
            return face

        # ----------------------------------------------------
        # Horizontal flip
        # ----------------------------------------------------

        if np.random.rand() < 0.35:

            face = tf.image.flip_left_right(face)

        # ----------------------------------------------------
        # Brightness
        # ----------------------------------------------------

        if np.random.rand() < 0.35:

            face = tf.image.random_brightness(
                face,
                max_delta=0.08
            )

        # ----------------------------------------------------
        # Contrast
        # ----------------------------------------------------

        if np.random.rand() < 0.35:

            face = tf.image.random_contrast(
                face,
                lower=0.85,
                upper=1.15
            )

        # ----------------------------------------------------
        # Saturation
        # ----------------------------------------------------

        if np.random.rand() < 0.25:

            face = tf.image.random_saturation(
                face,
                lower=0.90,
                upper=1.10
            )

        # ----------------------------------------------------
        # Small Gaussian noise
        # ----------------------------------------------------

        if np.random.rand() < 0.15:

            noise = tf.random.normal(
                tf.shape(face),
                mean=0.0,
                stddev=2.0
            )

            face = face + noise

        # ----------------------------------------------------
        # Mild blur
        # ----------------------------------------------------

        if np.random.rand() < 0.10:

            face = tf.expand_dims(
                face,
                axis=0
            )

            face = tf.nn.avg_pool2d(
                face,
                ksize=3,
                strides=1,
                padding="SAME"
            )

            face = tf.squeeze(
                face,
                axis=0
            )

        # ----------------------------------------------------
        # Keep valid image range
        # ----------------------------------------------------

        face = tf.clip_by_value(
            face,
            0.0,
            255.0
        )

        return face

    # ========================================================
    # TEMPORAL SAMPLING
    # ========================================================

    def _get_indices(self, frame_count):

        if frame_count <= SEQ_LEN:

            return sample_indices(
                frame_count,
                SEQ_LEN
            )

        # ----------------------------------------------------
        # Validation:
        # deterministic uniform sampling
        # ----------------------------------------------------

        if not self.training:

            return sample_indices(
                frame_count,
                SEQ_LEN
            )

        # ----------------------------------------------------
        # Training:
        # randomly shift the temporal window
        #
        # This allows different epochs to observe slightly
        # different temporal portions of the same video.
        # ----------------------------------------------------

        max_start = max(
            0,
            frame_count - SEQ_LEN
        )

        if max_start == 0:

            return sample_indices(
                frame_count,
                SEQ_LEN
            )

        start = np.random.randint(
            0,
            max_start + 1
        )

        end = min(
            frame_count,
            start + SEQ_LEN
        )

        indices = np.linspace(
            start,
            end - 1,
            SEQ_LEN
        ).astype(int)

        return indices

    # ========================================================
    # PROCESS ONE VIDEO
    # ========================================================

    def _one(self, item):

        frames = list_frames(
            item["path"]
        )

        # ----------------------------------------------------
        # Invalid / empty sequence
        # ----------------------------------------------------

        if len(frames) == 0:

            faces = np.zeros(
                (
                    SEQ_LEN,
                    IMG_SIZE,
                    IMG_SIZE,
                    3
                ),
                dtype=np.float32
            )

            qualities = np.zeros(
                (SEQ_LEN, 1),
                dtype=np.float32
            )

            return (
                faces,
                qualities,
                float(item["label"])
            )

        # ----------------------------------------------------
        # Temporal sampling
        # ----------------------------------------------------

        idx = self._get_indices(
            len(frames)
        )

        faces = []
        qualities = []

        last_face = None
        last_quality = 0.0

        # ====================================================
        # PROCESS SELECTED FRAMES
        # ====================================================

        for i in idx:

            rgb = load_image(
                frames[i]
            )

            face = None
            detection_score = 0.0

            # ------------------------------------------------
            # FACE DETECTION
            # ------------------------------------------------

            if rgb is not None:

                try:

                    face, detection_score = self.detector.crop(
                        rgb,
                        FACE_MARGIN
                    )

                except Exception:

                    face = None
                    detection_score = 0.0

            # ------------------------------------------------
            # VALID FACE
            # ------------------------------------------------

            if face is not None:

                face = tf.image.resize(
                    face,
                    (
                        IMG_SIZE,
                        IMG_SIZE
                    )
                )

                face = tf.cast(
                    face,
                    tf.float32
                )

                last_face = tf.identity(
                    face
                )

                last_quality = quality_score(
                    face.numpy().astype(np.uint8),
                    detection_score
                )

                current_quality = last_quality

            # ------------------------------------------------
            # TEMPORARY DETECTION FAILURE
            # ------------------------------------------------

            elif last_face is not None:

                face = tf.identity(
                    last_face
                )

                current_quality = (
                    last_quality * 0.65
                )

                last_quality = current_quality

            # ------------------------------------------------
            # NO FACE AVAILABLE
            # ------------------------------------------------

            else:

                face = tf.zeros(
                    (
                        IMG_SIZE,
                        IMG_SIZE,
                        3
                    ),
                    dtype=tf.float32
                )

                current_quality = 0.0

            # ------------------------------------------------
            # AUGMENTATION
            # ------------------------------------------------

            face = self._augment(
                face
            )

            # ------------------------------------------------
            # EFFICIENTNET V2 PREPROCESSING
            # ------------------------------------------------

            face = tf.keras.applications.efficientnet_v2.preprocess_input(
                face
            )

            faces.append(
                face.numpy()
            )

            qualities.append(
                [current_quality]
            )

        # ====================================================
        # FINAL ARRAYS
        # ====================================================

        faces = np.asarray(
            faces,
            dtype=np.float32
        )

        qualities = np.asarray(
            qualities,
            dtype=np.float32
        )

        return (
            faces,
            qualities,
            float(item["label"])
        )

    # ========================================================
    # BATCH
    # ========================================================

    def __getitem__(self, batch_index):

        start = (
            batch_index *
            self.batch_size
        )

        end = min(
            start + self.batch_size,
            len(self.indices)
        )

        ids = self.indices[
            start:end
        ]

        batch = [
            self._one(
                self.manifest[i]
            )
            for i in ids
        ]

        faces = np.asarray(
            [
                item[0]
                for item in batch
            ],
            dtype=np.float32
        )

        labels = np.asarray(
            [
                item[2]
                for item in batch
            ],
            dtype=np.float32
        )

        return {
            "video": faces
        }, labels


# ============================================================
# MANIFEST READER
# ============================================================

def read_manifest(path):

    with open(
        path,
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    if not isinstance(data, list):

        raise ValueError(
            f"Manifest must contain a list: {path}"
        )

    for item in data:

        if "path" not in item:

            raise ValueError(
                f"Missing 'path' in manifest: {path}"
            )

        if "label" not in item:

            raise ValueError(
                f"Missing 'label' in manifest: {path}"
            )

    return data