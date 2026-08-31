from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from config import TRAIN_REAL,TRAIN_FAKE,TEST_REAL,TEST_FAKE
from src.video import list_frames
for name,p in [("TRAIN REAL",TRAIN_REAL),("TRAIN FAKE",TRAIN_FAKE),("TEST REAL",TEST_REAL),("TEST FAKE",TEST_FAKE)]:
    folders=[x for x in Path(p).iterdir() if x.is_dir()]
    counts=[len(list_frames(x)) for x in folders]
    print(f"{name:<12} videos={len(folders):4d} frames={sum(counts):6d} empty={sum(c==0 for c in counts):4d}")
