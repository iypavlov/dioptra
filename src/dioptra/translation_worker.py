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
            target_lang = self._get_target_language()

            if self._cache and img_bytes:
                cached = self._cache.get(img_bytes, target_lang)
                if cached:
                    word, translation = cached
                    log.debug("Cache hit for seq=%d", request_seq)
                    self.ocr_result.emit(word, request_seq)
                    self.translation_result.emit(word, translation, request_seq)
                    return

            log.debug("Starting OCR for seq=%d", request_seq)
            words = self._ocr.recognize(image)
            if self._cancelled:
                log.debug("Cancelled after OCR (seq=%d)", request_seq)
                return

            if not words:
                log.debug("No OCR words found (seq=%d)", request_seq)
                self.no_text_found.emit(request_seq)
                return

            text = " ".join(w["text"] for w in words if w["confidence"] > 0.3)
            if not text or not text.strip():
                log.debug("Empty text after filtering (seq=%d)", request_seq)
                self.no_text_found.emit(request_seq)
                return

            log.debug("OCR text: '%s' (seq=%d)", text[:60], request_seq)
            self.ocr_result.emit(text, request_seq)

            log.debug("Translating seq=%d via %s", request_seq, type(self._translator).__name__)
            translation = self._translator.translate(text)
            if self._cancelled:
                log.debug("Cancelled after translation (seq=%d)", request_seq)
                return

            if self._cache and img_bytes:
                self._cache.set(img_bytes, text, translation, target_lang)
                log.debug("Cached result for seq=%d", request_seq)

            self.translation_result.emit(text, translation, request_seq)

        except Exception as e:
            log.error("Worker error (seq=%d): %s", request_seq, e, exc_info=True)
            self.error_occurred.emit(str(e), request_seq)

    def _get_target_language(self) -> str:
        if hasattr(self._translator, '_target_language'):
            return self._translator._target_language
        if hasattr(self._translator, '_target'):
            return self._translator._target
        return "ru"

    @staticmethod
    def _image_to_bytes(image: Image.Image) -> bytes:
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()
