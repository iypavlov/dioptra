import os
import sys
from typing import Any

from PIL import Image

os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"

import keyboard
import mouse
from PyQt6.QtCore import QObject, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QWidget

from dioptra.app_paths import asset_path
from dioptra.log import get_logger, setup_logger
from dioptra.ocr_service import OcrService
from dioptra.settings import SettingsManager
from dioptra.translation.base import AbstractTranslator, TranslatorFactory
from dioptra.translation.google_translate import GoogleTranslateTranslator
from dioptra.translation.ollama_translate import OllamaTranslateTranslator
from dioptra.translation_worker import TranslationWorker
from dioptra.ui.modal_window import ModalOverlay
from dioptra.ui.region_selector import RegionSelector
from dioptra.ui.settings_window import SettingsWindow

log = get_logger("dioptra")


class ScreenTranslatorApp(QObject):
    region_start = pyqtSignal(int, int)
    region_move = pyqtSignal(int, int)
    region_end = pyqtSignal(int, int)

    def __init__(self) -> None:
        super().__init__()
        self._app = QApplication(sys.argv)
        self._app.setQuitOnLastWindowClosed(False)

        self._settings = SettingsManager()
        self._settings.language_changed.connect(self._on_language_changed)
        self._settings.translator_changed.connect(self._on_translator_changed)
        self._settings.ollama_settings_changed.connect(self._on_ollama_settings_changed)

        log.info("Starting Dioptra translator=%s lang=%s",
                  self._settings.translator, self._settings.target_language)

        self.region_start.connect(self._on_region_start)
        self.region_move.connect(self._on_region_move)
        self.region_end.connect(self._on_region_end)

        TranslatorFactory.register("google", GoogleTranslateTranslator)
        TranslatorFactory.register("ollama", OllamaTranslateTranslator)
        self._translator = self._create_translator()
        self._ocr_service = OcrService()
        self._modal = ModalOverlay()
        provider_name = {"ollama": "Ollama", "google": "Google Translate"}.get(
            self._settings.translator, self._settings.translator
        )
        self._modal.set_provider(provider_name)

        self._region_selector = RegionSelector()
        self._region_selector.region_captured.connect(self._on_region_captured)
        self._region_selector.selection_cancelled.connect(self._on_selection_cancelled)

        self._thread = QThread()
        self._worker = TranslationWorker(self._ocr_service, self._translator)
        self._worker.moveToThread(self._thread)
        self._worker.ocr_result.connect(self._on_worker_ocr)
        self._worker.translation_result.connect(self._on_worker_translation)
        self._worker.error_occurred.connect(self._on_worker_error)
        self._worker.no_text_found.connect(self._on_worker_no_text)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.start()

        self._modifier_pressed = False
        self._mouse_hook: Any = None
        self._request_seq = 0
        self._crosshair: QWidget | None = None

        self._combo_timer = QTimer()
        self._combo_timer.timeout.connect(self._poll_combo)
        self._combo_timer.start(50)

        self._settings_window = None
        self._setup_tray()

    def _show_crosshair(self) -> None:
        if self._crosshair is None:
            self._crosshair = QWidget()
            self._crosshair.setWindowFlags(
                Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.WindowStaysOnTopHint
            )
            self._crosshair.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self._crosshair.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            self._crosshair.setCursor(Qt.CursorShape.CrossCursor)
            screen = QApplication.primaryScreen()
            if screen:
                self._crosshair.setGeometry(screen.geometry())
        self._crosshair.showFullScreen()
        self._crosshair.raise_()

    def _hide_crosshair(self) -> None:
        if self._crosshair is not None:
            self._crosshair.hide()

    def _poll_combo(self) -> None:
        if self._modal.isVisible():
            if self._mouse_hook:
                self._unhook_mouse()
            self._hide_crosshair()
            return

        combo = self._settings.selection_modifier
        try:
            is_down = keyboard.is_pressed(combo)
        except Exception:
            is_down = False

        if is_down and not self._modifier_pressed:
            self._modifier_pressed = True
            self._mouse_hook = mouse.hook(self._on_mouse_event)
            self._show_crosshair()
        elif not is_down and self._modifier_pressed:
            self._modifier_pressed = False
            self._hide_crosshair()
            if self._region_selector.is_selecting:
                x, y = mouse.get_position()
                self._region_selector.end_selection(x, y)
            self._unhook_mouse()

    def _unhook_mouse(self) -> None:
        if self._mouse_hook:
            try:
                mouse.unhook(self._mouse_hook)
            except Exception:
                pass
        self._mouse_hook = None

    def _on_mouse_event(self, event: Any) -> None:
        if isinstance(event, mouse.ButtonEvent) and event.button == 'left':
            x, y = mouse.get_position()
            if event.event_type == 'down':
                self.region_start.emit(x, y)
            elif event.event_type == 'up' and self._region_selector.is_selecting:
                self.region_end.emit(x, y)
        elif isinstance(event, mouse.MoveEvent) and self._region_selector.is_selecting:
            self.region_move.emit(event.x, event.y)

    def _on_region_start(self, x: int, y: int) -> None:
        self._hide_crosshair()
        self._region_selector.start_selection(x, y)
        self._request_seq += 1
        self._worker.cancel()
        self._modal.hide()

    def _on_region_move(self, x: int, y: int) -> None:
        self._region_selector.update_selection(x, y)

    def _on_region_end(self, x: int, y: int) -> None:
        if self._region_selector.is_selecting:
            self._region_selector.end_selection(x, y)
        self._unhook_mouse()

    def _create_translator(self) -> AbstractTranslator:
        provider = self._settings.translator
        try:
            if provider == "ollama":
                return TranslatorFactory.create(
                    "ollama",
                    target_language=self._settings.target_language,
                    url=self._settings.ollama_url,
                    model=self._settings.ollama_model,
                    timeout=self._settings.ollama_timeout,
                )
            return TranslatorFactory.create("google")
        except Exception:
            return TranslatorFactory.create("google")

    def _on_language_changed(self, lang: str) -> None:
        self._translator.set_target_language(lang)

    def _on_translator_changed(self, provider: str) -> None:
        self._translator = self._create_translator()
        self._translator.set_target_language(self._settings.target_language)
        provider_name = {"ollama": "Ollama", "google": "Google Translate"}.get(provider, provider)
        self._modal.set_provider(provider_name)

    def _on_ollama_settings_changed(self, url: str, model: str, timeout: int) -> None:
        if self._settings.translator == "ollama":
            self._translator = self._create_translator()

    def _setup_tray(self) -> None:
        icon_path = asset_path("icon.png")
        icon = QIcon(str(icon_path)) if icon_path.is_file() else QIcon()
        self._app.setWindowIcon(icon)
        self._tray_icon = QSystemTrayIcon(icon)
        self._tray_icon.setToolTip("Dioptra")

        self._tray_menu = QMenu()

        self._settings_action = QAction("Settings")
        self._settings_action.triggered.connect(lambda: self._open_settings())
        self._tray_menu.addAction(self._settings_action)

        self._tray_menu.addSeparator()

        self._quit_action = QAction("Quit")
        self._quit_action.triggered.connect(self._quit)
        self._tray_menu.addAction(self._quit_action)

        self._tray_icon.setContextMenu(self._tray_menu)
        self._tray_icon.show()

    def _open_settings(self) -> None:
        try:
            w = SettingsWindow(self._settings)
            w.exec()
        except Exception as e:
            log.error("Settings error: %s", e, exc_info=True)

    def _on_region_captured(self, image: Image.Image, cx: int, cy: int) -> None:
        self._worker.cancel()
        self._last_cx = cx
        self._last_cy = cy
        self._modal.show_loading(cx, cy)
        self._worker.request_process.emit(image, cx, cy, self._request_seq)

    def _on_worker_ocr(self, text: str, request_seq: int) -> None:
        if request_seq != self._request_seq:
            return
        self._modal.show_ocr_progress(text, self._last_cx, self._last_cy)

    def _on_worker_translation(self, word: str, translation: str, request_seq: int) -> None:
        if request_seq != self._request_seq:
            return
        log.info("Translation: '%s' -> '%s' (seq=%d)", word[:40], translation[:80], request_seq)
        self._modal.show_translation(word, translation, self._last_cx, self._last_cy)

    def _on_selection_cancelled(self) -> None:
        self._modal.hide()

    def _on_worker_no_text(self, request_seq: int) -> None:
        if request_seq != self._request_seq:
            return
        self._modal.hide()

    def _on_worker_error(self, message: str, request_seq: int) -> None:
        if request_seq != self._request_seq:
            return
        log.warning("Worker error: %s (seq=%d)", message, request_seq)
        self._modal.show_message(message, self._last_cx, self._last_cy)

    def _quit(self) -> None:
        log.info("Shutting down Dioptra")
        self._worker.cancel()
        self._thread.quit()
        self._thread.wait(2000)
        self._unhook_mouse()
        self._app.quit()

    def run(self) -> None:
        sys.exit(self._app.exec())


def main() -> None:
    setup_logger()
    log.info("Dioptra v0.1.0 starting")
    app = ScreenTranslatorApp()
    app.run()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.critical("Fatal error: %s", e, exc_info=True)
        sys.exit(1)
