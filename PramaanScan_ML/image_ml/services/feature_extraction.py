"""
Praman Scan - Handcrafted Feature Extraction.

This module converts a raw RGB image into a single fixed-length feature
vector built entirely from classical computer-vision descriptors. No deep
learning / CNN feature maps are used anywhere in this pipeline, in line
with the project requirement to rely only on classical machine learning.

Feature groups (in the order they are concatenated into the final vector):
    1. Local Binary Pattern (LBP) histogram              - texture
    2. Histogram of Oriented Gradients (HOG), pooled      - shape/edges
    3. Color histogram (HSV, 3 channels)                  - color
    4. GLCM texture statistics                            - texture
    5. FFT / frequency-domain statistics                  - spectral
    6. Edge density (Canny)                                - edges
    7. Sharpness (variance of Laplacian)                   - focus/blur
    8. Noise statistics (high-pass residual)               - sensor noise
    9. JPEG compression / blockiness statistics            - compression

Every function below is independent and returns a 1-D numpy array plus a
matching list of human-readable feature names, so the combined vector and
its names always stay in sync (used later for feature-importance display).
"""
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
import cv2
from scipy import ndimage
from scipy.fft import fft2, fftshift
from skimage.feature import local_binary_pattern, hog, graycomatrix, graycoprops

from image_ml.config import get_settings

settings = get_settings()


@dataclass
class FeatureVector:
    values: np.ndarray
    names: List[str]


def _to_gray(img_rgb: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)


def _resize(img_rgb: np.ndarray, dim: int) -> np.ndarray:
    return cv2.resize(img_rgb, (dim, dim), interpolation=cv2.INTER_AREA)


# --------------------------------------------------------------------------- #
# 1. Local Binary Pattern
# --------------------------------------------------------------------------- #
def extract_lbp_features(gray: np.ndarray) -> Tuple[np.ndarray, List[str]]:
    radius = settings.LBP_RADIUS
    n_points = settings.LBP_POINTS
    lbp = local_binary_pattern(gray, n_points, radius, method="uniform")
    n_bins = n_points + 2
    hist, _ = np.histogram(lbp.ravel(), bins=n_bins, range=(0, n_bins), density=True)
    names = [f"lbp_bin_{i}" for i in range(n_bins)]
    return hist.astype(np.float64), names


# --------------------------------------------------------------------------- #
# 2. Histogram of Oriented Gradients (pooled into summary stats to keep the
#    vector a manageable, fixed size regardless of resize dimension)
# --------------------------------------------------------------------------- #
def extract_hog_features(gray: np.ndarray) -> Tuple[np.ndarray, List[str]]:
    hog_vec = hog(
        gray,
        orientations=9,
        pixels_per_cell=(settings.HOG_PIXELS_PER_CELL, settings.HOG_PIXELS_PER_CELL),
        cells_per_block=(settings.HOG_CELLS_PER_BLOCK, settings.HOG_CELLS_PER_BLOCK),
        block_norm="L2-Hys",
        feature_vector=True,
    )
    stats = np.array(
        [
            hog_vec.mean(),
            hog_vec.std(),
            np.percentile(hog_vec, 25),
            np.percentile(hog_vec, 50),
            np.percentile(hog_vec, 75),
            hog_vec.max(),
            (hog_vec > hog_vec.mean()).mean(),  # fraction of "active" cells
        ]
    )
    names = [
        "hog_mean", "hog_std", "hog_p25", "hog_p50", "hog_p75", "hog_max", "hog_active_frac",
    ]
    return stats, names


# --------------------------------------------------------------------------- #
# 3. Color histogram (HSV space, more perceptually relevant than RGB for
#    detecting unnatural color distributions common in generated images)
# --------------------------------------------------------------------------- #
def extract_color_histogram(img_rgb: np.ndarray) -> Tuple[np.ndarray, List[str]]:
    hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
    bins = settings.COLOR_HIST_BINS
    feats = []
    names = []
    for i, channel in enumerate(["h", "s", "v"]):
        hist = cv2.calcHist([hsv], [i], None, [bins], [0, 256]).flatten()
        hist = hist / (hist.sum() + 1e-8)
        feats.append(hist)
        names.extend([f"color_{channel}_bin_{b}" for b in range(bins)])
    return np.concatenate(feats), names


# --------------------------------------------------------------------------- #
# 4. GLCM texture statistics
# --------------------------------------------------------------------------- #
def extract_texture_statistics(gray: np.ndarray) -> Tuple[np.ndarray, List[str]]:
    gray_q = (gray / 32).astype(np.uint8)  # quantize to 8 levels for a tractable GLCM
    glcm = graycomatrix(
        gray_q, distances=[1, 3], angles=[0, np.pi / 4, np.pi / 2, 3 * np.pi / 4],
        levels=8, symmetric=True, normed=True,
    )
    props = ["contrast", "dissimilarity", "homogeneity", "energy", "correlation", "ASM"]
    feats = []
    names = []
    for prop in props:
        vals = graycoprops(glcm, prop)
        feats.append(vals.mean())
        feats.append(vals.std())
        names.append(f"glcm_{prop}_mean")
        names.append(f"glcm_{prop}_std")
    return np.array(feats), names


# --------------------------------------------------------------------------- #
# 5. Frequency domain (FFT) statistics
#    AI-generated images frequently show characteristic periodic artifacts
#    (upsampling / GAN checkerboarding) that show up as anomalies in the
#    radially-averaged power spectrum.
# --------------------------------------------------------------------------- #
def extract_fft_statistics(gray: np.ndarray) -> Tuple[np.ndarray, List[str]]:
    f = fft2(gray.astype(np.float64))
    fshift = fftshift(f)
    magnitude = np.abs(fshift)
    magnitude_log = np.log1p(magnitude)

    h, w = gray.shape
    cy, cx = h // 2, w // 2
    y, x = np.ogrid[:h, :w]
    radius = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    max_r = radius.max()

    low_mask = radius <= max_r * 0.15
    mid_mask = (radius > max_r * 0.15) & (radius <= max_r * 0.5)
    high_mask = radius > max_r * 0.5

    low_energy = magnitude[low_mask].mean()
    mid_energy = magnitude[mid_mask].mean()
    high_energy = magnitude[high_mask].mean()
    total_energy = magnitude.mean() + 1e-8

    feats = np.array(
        [
            magnitude_log.mean(),
            magnitude_log.std(),
            low_energy / total_energy,
            mid_energy / total_energy,
            high_energy / total_energy,
            high_energy / (low_energy + 1e-8),
        ]
    )
    names = [
        "fft_logmag_mean", "fft_logmag_std", "fft_low_energy_ratio",
        "fft_mid_energy_ratio", "fft_high_energy_ratio", "fft_high_to_low_ratio",
    ]
    return feats, names


# --------------------------------------------------------------------------- #
# 6. Edge density (Canny)
# --------------------------------------------------------------------------- #
def extract_edge_density(gray: np.ndarray) -> Tuple[np.ndarray, List[str]]:
    edges = cv2.Canny(gray, 100, 200)
    density = edges.mean() / 255.0
    # edge orientation spread, using Sobel gradients
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    orientation = np.arctan2(gy, gx)
    orientation_std = orientation[edges > 0].std() if np.any(edges > 0) else 0.0
    feats = np.array([density, orientation_std])
    names = ["edge_density", "edge_orientation_std"]
    return feats, names


# --------------------------------------------------------------------------- #
# 7. Sharpness (variance of Laplacian) - AI upscaling/smoothing often
#    produces unnaturally uniform sharpness across the frame.
# --------------------------------------------------------------------------- #
def extract_sharpness_statistics(gray: np.ndarray) -> Tuple[np.ndarray, List[str]]:
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    global_var = lap.var()

    # split into a 4x4 grid and look at variance-of-variance to capture
    # spatial (in)consistency of sharpness across the image
    h, w = gray.shape
    gh, gw = h // 4, w // 4
    local_vars = []
    for i in range(4):
        for j in range(4):
            block = lap[i * gh:(i + 1) * gh, j * gw:(j + 1) * gw]
            if block.size > 0:
                local_vars.append(block.var())
    local_vars = np.array(local_vars) if local_vars else np.array([0.0])

    feats = np.array([global_var, local_vars.mean(), local_vars.std()])
    names = ["sharpness_laplacian_var", "sharpness_block_mean", "sharpness_block_std"]
    return feats, names


# --------------------------------------------------------------------------- #
# 8. Noise statistics - residual after a denoising filter approximates the
#    sensor / generative noise signature.
# --------------------------------------------------------------------------- #
def extract_noise_statistics(gray: np.ndarray) -> Tuple[np.ndarray, List[str]]:
    denoised = ndimage.median_filter(gray, size=3)
    residual = gray.astype(np.float64) - denoised.astype(np.float64)
    feats = np.array(
        [
            residual.std(),
            residual.mean(),
            np.mean(np.abs(residual)),
            float(np.percentile(np.abs(residual), 95)),
        ]
    )
    names = ["noise_residual_std", "noise_residual_mean", "noise_mean_abs", "noise_p95_abs"]
    return feats, names


# --------------------------------------------------------------------------- #
# 9. Compression / blockiness statistics - approximates JPEG block-grid
#    artifacts using the well-known blockiness measure over 8x8 boundaries.
# --------------------------------------------------------------------------- #
def extract_compression_statistics(gray: np.ndarray) -> Tuple[np.ndarray, List[str]]:
    g = gray.astype(np.float64)
    h, w = g.shape

    def boundary_diff(arr, axis):
        diffs = []
        step = 8
        limit = (arr.shape[axis] // step) * step
        if axis == 0:
            for i in range(step, limit, step):
                diffs.append(np.mean(np.abs(arr[i, :] - arr[i - 1, :])))
        else:
            for i in range(step, limit, step):
                diffs.append(np.mean(np.abs(arr[:, i] - arr[:, i - 1])))
        return np.array(diffs) if diffs else np.array([0.0])

    row_diffs = boundary_diff(g, axis=0)
    col_diffs = boundary_diff(g, axis=1)

    # overall pixel-to-pixel gradient for normalisation
    overall_grad = (np.mean(np.abs(np.diff(g, axis=0))) + np.mean(np.abs(np.diff(g, axis=1)))) / 2.0 + 1e-8

    blockiness = (row_diffs.mean() + col_diffs.mean()) / 2.0
    blockiness_ratio = blockiness / overall_grad

    feats = np.array([blockiness, blockiness_ratio, row_diffs.std(), col_diffs.std()])
    names = ["compression_blockiness", "compression_blockiness_ratio",
             "compression_row_std", "compression_col_std"]
    return feats, names


# --------------------------------------------------------------------------- #
# Combined pipeline
# --------------------------------------------------------------------------- #
_EXTRACTORS_GRAY = [
    extract_lbp_features,
    extract_hog_features,
    extract_texture_statistics,
    extract_fft_statistics,
    extract_edge_density,
    extract_sharpness_statistics,
    extract_noise_statistics,
    extract_compression_statistics,
]


def extract_feature_vector(img_rgb: np.ndarray) -> FeatureVector:
    """
    Run the full handcrafted feature-extraction pipeline on a single RGB
    image and return a FeatureVector (values + matching names).
    """
    img_rgb = _resize(img_rgb, settings.IMAGE_RESIZE_DIM)
    gray = _to_gray(img_rgb)

    all_values = []
    all_names = []

    for extractor in _EXTRACTORS_GRAY:
        values, names = extractor(gray)
        all_values.append(np.asarray(values, dtype=np.float64))
        all_names.extend(names)

    color_values, color_names = extract_color_histogram(img_rgb)
    all_values.append(color_values)
    all_names.extend(color_names)

    vector = np.concatenate(all_values)
    vector = np.nan_to_num(vector, nan=0.0, posinf=0.0, neginf=0.0)

    return FeatureVector(values=vector, names=all_names)


def get_feature_names() -> List[str]:
    """Return the feature name list without needing a real image, by
    running the pipeline once on a tiny synthetic image."""
    dummy = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
    return extract_feature_vector(dummy).names
