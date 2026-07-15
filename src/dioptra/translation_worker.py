import io

from PIL import Image
from PyQt6.QtCore import QObject, pyqtSignal

from dioptra.log import get_logger

log = get_logger("dioptra.worker")


class TranslationWorker(QObject):
    ocr_result = pyqtSignal(str, int)
    translation_result = pyqtSignal(str, str, int)
    error_occurred = pyqtSignal(str, int)
    no_text_found = pyqtSignal(int)
    request_process = pyqtSignal(object, int, int, int)

    def __init__(self, ocr_service, translator, cache=None) -> None:
        super().__init__()
        self._ocr = ocr_service
        self._translator = translator
        self._cache = cache
        self._cancelled: bool = False
        self.request_process.connect(self._on_process)

    def cancel(self) -> None:
        self._cancelled = True

    def _on_process(self, image: Image.Image, cx: int, cy: int, request_seq: int) -> None:
        self._cancelled = False
        try:
            img_bytes = self._image_to_bytes(image) if self._cache else None
            target_lang = self._translator.target_language

            if self._cache and img_bytes:
                cached = self._cache.get(img_bytes, target_lang)
                if cached:
                    word, translation = cached
                    self.ocr_result.emit(word, request_seq)
                    self.translation_result.emit(word, translation, request_seq)
                    return

            words = self._ocr.recognize(image)
            if self._cancelled:
                return

            if not words:
                self.no_text_found.emit(request_seq)
                return

            text = " ".join(w["text"] for w in words if w["confidence"] > 0.3)
            if not text or not text.strip():
                self.no_text_found.emit(request_seq)
                return

            self.ocr_result.emit(text, request_seq)

            translation = self._translator.translate(text)
            if self._cancelled:
                return

            if self._cache and img_bytes:
                self._cache.set(img_bytes, text, translation, target_lang)

            self.translation_result.emit(text, translation, request_seq)

        except Exception as e:
            log.error("Worker error (seq=%d): %s", request_seq, e, exc_info=True)
            self.error_occurred.emit(str(e), request_seq)

    @staticmethod
    def _image_to_bytes(image: Image.Image) -> bytes:
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()
