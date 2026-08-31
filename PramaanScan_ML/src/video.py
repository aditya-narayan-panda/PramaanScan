from pathlib import Path
import cv2
import numpy as np

def list_frames(folder):
    return sorted([p for p in Path(folder).iterdir() if p.is_file()], key=lambda p: p.name)

def load_image(path):
    img = cv2.imread(str(path))
    if img is None: return None
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

def sample_indices(n, seq_len):
    if n <= 0: return []
    if n == 1: return [0] * seq_len
    return np.linspace(0, n-1, seq_len).round().astype(int).tolist()
