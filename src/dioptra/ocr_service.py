import threading
from typing import Any

import numpy as np
from paddleocr import PaddleOCR
from PIL import Image, ImageEnhance, ImageFilter

from dioptra.log import get_logger

log = get_logger("dioptra.ocr")


class OcrService:
    def __init__(self, lang: str = "en") -> None:
        self._lang = lang
        self._ocr: PaddleOCR | None = None
        self._lock = threading.Lock()

    def set_lang(self, lang: str) -> None:
        if lang != self._lang:
            log.debug("OCR language changed: %s -> %s", self._lang, lang)
            with self._lock:
                self._lang = lang
                self._ocr = None

    def _ensure_ocr(self) -> PaddleOCR:
        if self._ocr is None:
            with self._lock:
                if self._ocr is None:
                    log.info("Initializing PaddleOCR (lang=%s)", self._lang)
                    self._ocr = PaddleOCR(use_angle_cls=False, lang=self._lang)
                    log.info("PaddleOCR initialized")
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
        result = ocr.ocr(img_array, cls=False)
        words = []
        if result and result[0]:
            for line in result[0]:
                box, (text, confidence) = line
                words.append({
                    "text": text,
                    "box": [[int(coord[0] / 2), int(coord[1] / 2)] for coord in box],
                    "confidence": confidence,
                })
        log.debug("OCR recognized %d words in %dx%d image", len(words), w, h)
        return words
