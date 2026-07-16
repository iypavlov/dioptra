from PIL import Image
from PyQt6.QtCore import QObject, pyqtSignal

from dioptra.log import get_logger
from dioptra.ocr_service import OcrService
from dioptra.translation.base import AbstractTranslator

log = get_logger("dioptra.worker")


class TranslationWorker(QObject):
    ocr_result = pyqtSignal(str, int)
    translation_result = pyqtSignal(str, str, str, int)
    error_occurred = pyqtSignal(str, int)
    no_text_found = pyqtSignal(int)
    request_process = pyqtSignal(object, int, int, int, str)

    def __init__(self, ocr_service: OcrService, translator: AbstractTranslator) -> None:
        super().__init__()
        self._ocr = ocr_service
        self._translator = translator
        self._cancelled: bool = False
        self.request_process.connect(self._on_process)

    def cancel(self) -> None:
        self._cancelled = True

    def _on_process(self, image: Image.Image, cx: int, cy: int, request_seq: int, source_lang: str = "en") -> None:
        self._cancelled = False
        try:
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

            translation = self._translator.translate(text, source=source_lang)
            if self._cancelled:
                return

            self.translation_result.emit(text, translation, source_lang, request_seq)

        except Exception as e:
            log.error("Worker error (seq=%d): %s", request_seq, e, exc_info=True)
            self.error_occurred.emit(str(e), request_seq)
