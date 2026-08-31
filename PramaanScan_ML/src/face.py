import cv2
import numpy as np
import mediapipe as mp


class MediaPipeFaceDetector:

    def __init__(self, model_path, min_score=0.5):

        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision

        self.min_score = float(min_score)

        base = python.BaseOptions(
            model_asset_path=str(model_path)
        )

        options = vision.FaceDetectorOptions(
            base_options=base,
            min_detection_confidence=self.min_score
        )

        self.detector = (
            vision.FaceDetector.create_from_options(options)
        )

    # ============================================================
    # COMPATIBILITY METHOD
    # ============================================================

    def detect(self, rgb):
        """
        Compatibility wrapper used by the video/multimodal pipeline.

        The existing detector implementation uses detect_largest().
        Some parts of the project expect a detect() method, so this
        wrapper keeps both interfaces available.
        """

        return self.detect_largest(rgb)

    # ============================================================
    # DETECT LARGEST FACE
    # ============================================================

    def detect_largest(self, rgb):

        if rgb is None:
            return None, 0.0

        image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        result = self.detector.detect(image)

        if not result.detections:
            return None, 0.0

        best = None
        best_area = -1.0
        best_score = 0.0

        for det in result.detections:

            score = (
                float(det.categories[0].score)
                if det.categories
                else 0.0
            )

            if score < self.min_score:
                continue

            box = det.bounding_box

            width = max(
                0,
                int(box.width)
            )

            height = max(
                0,
                int(box.height)
            )

            area = width * height

            if area > best_area:

                best = det
                best_area = area
                best_score = score

        if best is None:
            return None, 0.0

        box = best.bounding_box

        return (
            int(box.origin_x),
            int(box.origin_y),
            int(box.width),
            int(box.height)
        ), best_score

    # ============================================================
    # CROP FACE
    # ============================================================

    def crop(self, rgb, margin=0.30):

        box, score = self.detect_largest(rgb)

        if box is None:
            return None, 0.0

        x, y, w, h = box

        if w <= 0 or h <= 0:
            return None, 0.0

        mx = int(w * margin)
        my = int(h * margin)

        x1 = max(
            0,
            x - mx
        )

        y1 = max(
            0,
            y - my
        )

        x2 = min(
            rgb.shape[1],
            x + w + mx
        )

        y2 = min(
            rgb.shape[0],
            y + h + my
        )

        if x2 <= x1 or y2 <= y1:
            return None, 0.0

        crop = rgb[
            y1:y2,
            x1:x2
        ]

        if crop.size == 0:
            return None, 0.0

        return crop, score