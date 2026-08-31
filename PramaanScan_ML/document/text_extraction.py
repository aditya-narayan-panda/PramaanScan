from io import BytesIO
from pathlib import Path
from pypdf import PdfReader

SUPPORTED_EXTENSIONS={".pdf",".txt"}

def extract_content(data: bytes, filename: str, content_type: str) -> dict:
    ext=Path(filename).suffix.lower()
    if ext == ".pdf" or content_type == "application/pdf":
        try:
            reader=PdfReader(BytesIO(data))
            pages=[]
            for page in reader.pages:
                pages.append((page.extract_text() or "").strip())
            text="\n\n".join(p for p in pages if p)
            if not text.strip():
                raise ValueError("PDF was read successfully but no selectable text was found. Use a text-based PDF for this demo.")
            return _result(text,"PDF",len(reader.pages))
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(f"Could not read PDF: {exc}") from exc
    if ext == ".txt" or content_type.startswith("text/"):
        text=data.decode("utf-8", errors="replace")
        if not text.strip():
            raise ValueError("Text file contains no readable text.")
        return _result(text,"TEXT",1)
    raise ValueError("This demo currently verifies text-based PDF and TXT files. PDF/image/audio/video model adapters can be added later without changing the API contract.")

def _result(text: str, file_type: str, pages: int) -> dict:
    words=len(text.split())
    return {"text":text, "file_type":file_type, "characters_extracted":len(text), "words_extracted":words, "pages":pages}
