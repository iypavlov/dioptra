import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from paddleocr import PaddleOCR


class OcrService:
    def __init__(self, lang: str = "en"):
        self._lang = lang
        self._ocr = None

    def _ensure_ocr(self):
        if self._ocr is None:
            from paddleocr import PaddleOCR
            self._ocr = PaddleOCR(use_angle_cls=False, lang=self._lang, show_log=False)
        return self._ocr

    def recognize(self, image: Image.Image) -> list[dict]:
        img = image.convert("RGB")

        # Upscale 2x for better small text recognition
        w, h = img.size
        img = img.resize((w * 2, h * 2), Image.LANCZOS)

        # Sharpen
        img = img.filter(ImageFilter.SHARPEN)

        # Increase contrast
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
        return words
