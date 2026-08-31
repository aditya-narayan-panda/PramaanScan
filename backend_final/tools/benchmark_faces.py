import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from config import TEST_MANIFEST,FACE_MODEL
from src.face import MediaPipeFaceDetector
from src.video import list_frames,load_image,sample_indices
d=json.loads(TEST_MANIFEST.read_text(encoding="utf-8"))
det=MediaPipeFaceDetector(FACE_MODEL); total=found=0
for x in d:
    fr=list_frames(x["path"])
    for i in sample_indices(len(fr),16):
        box,_=det.detect_largest(load_image(fr[i])); total+=1; found+=box is not None
print("="*60); print("FRESH FACE BENCHMARK"); print("Frames:",total); print("Detected:",found); print("Rate:",f"{found/max(1,total):.2%}")
