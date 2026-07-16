import threading
from typing import Any

import numpy as np
from rapidocr import RapidOCR
from PIL import Image, ImageEnhance, ImageFilter

from dioptra.log import get_logger

log = get_logger("dioptra.ocr")


class OcrService:
    def __init__(self, lang: str = "en") -> None:
        self._lang = lang
        self._ocr: RapidOCR | None = None
        self._lock = threading.Lock()

    def set_lang(self, lang: str) -> None:
        if lang != self._lang:
            log.debug("OCR language changed: %s -> %s", self._lang, lang)
            with self._lock:
                self._lang = lang
                self._ocr = None

    def _ensure_ocr(self) -> RapidOCR:
        if self._ocr is None:
            with self._lock:
                if self._ocr is None:
                    log.info("Initializing RapidOCR (lang=%s)", self._lang)
                    self._ocr = RapidOCR(params={"Global.use_cls": False})
                    log.info("RapidOCR initialized")
        return self._ocr

    def recognize(self, image: Image.Image) -> list[dict[str, Any]]:
        img = image.convert("RGB")

        w, h = img.size
        img = img.resize((w * 2, h * 2), Image.Resampling.LANCZOS)

        img = img.filter(ImageFilter.SHARPEN)

        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)

        img_array = np.array(img)
        ocr = self._ensure_ocr()
        result = ocr(img_array)
        words = []
        if result.txts:
            for i in range(len(result.txts)):
                box = result.boxes[i]
                words.append({
                    "text": result.txts[i],
                    "box": [[int(coord[0] / 2), int(coord[1] / 2)] for coord in box],
                    "confidence": float(result.scores[i]),
                })
        log.debug("OCR recognized %d words in %dx%d image", len(words), w, h)
        return words
