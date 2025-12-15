from typing import List
from PIL import Image
import pytesseract
from io import BytesIO

def ocr_images_to_text(images_bytes: List[bytes]) -> str:
    texts: List[str] = []
    for b in images_bytes:
        try:
            img = Image.open(BytesIO(b)).convert("RGB")
            txt = pytesseract.image_to_string(img, lang="eng+vie")
            if txt:
                texts.append(txt.strip())
        except Exception:
            # skip bad image
            continue
    return "\n\n".join([t for t in texts if t])

def health_check_ocr() -> bool:
    try:
        _ = pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False