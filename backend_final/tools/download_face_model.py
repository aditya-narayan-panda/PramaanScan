from pathlib import Path
from urllib.request import urlretrieve
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from config import FACE_MODEL,FACE_MODEL_URL
if not FACE_MODEL.exists():
    FACE_MODEL.parent.mkdir(parents=True,exist_ok=True)
    print("Downloading MediaPipe face detector...")
    urlretrieve(FACE_MODEL_URL,FACE_MODEL)
print("Face model:",FACE_MODEL)
