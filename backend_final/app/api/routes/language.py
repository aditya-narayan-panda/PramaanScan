from functools import lru_cache
from urllib.parse import quote
from urllib.request import Request, urlopen
from concurrent.futures import ThreadPoolExecutor
import json

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/language", tags=["language"])

# Google Translate language codes for the Indian-language selector.
GOOGLE_CODES = {
    "hi", "or", "bn", "te", "ta", "mr", "gu", "kn", "ml", "pa", "as",
    "ur", "sa", "gom", "ne", "doi", "mai", "ks", "mni", "sat", "brx",
}

class TranslateRequest(BaseModel):
    texts: list[str] = Field(default_factory=list, max_length=100)
    target_language: str = Field(min_length=2, max_length=8)

class TranslateResponse(BaseModel):
    translations: list[str]

@lru_cache(maxsize=4096)
def _translate_one(text: str, target: str) -> str:
    if not text or target == "en":
        return text
    if target not in GOOGLE_CODES:
        return text

    # Public Google Translate web endpoint; no API key is required.
    url = (
        "https://translate.googleapis.com/translate_a/single"
        f"?client=gtx&sl=en&tl={quote(target)}&dt=t&q={quote(text)}"
    )
    try:
        request = Request(url, headers={"User-Agent": "PramaanScan/1.0"})
        with urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return "".join(part[0] for part in payload[0] if part and part[0]) or text
    except Exception:
        # Translation is an enhancement; never let it break verification.
        return text

@router.post("/translate", response_model=TranslateResponse)
def translate(request: TranslateRequest):
    target = request.target_language.lower()
    if target == "en" or not request.texts:
        return TranslateResponse(translations=request.texts)

    # Translate concurrently so a page with many labels remains responsive.
    with ThreadPoolExecutor(max_workers=min(8, len(request.texts))) as pool:
        translations = list(pool.map(lambda text: _translate_one(text, target), request.texts))
    return TranslateResponse(translations=translations)
