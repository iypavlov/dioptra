from typing import Any

import mss
from PIL import Image
from PyQt6.QtCore import QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen
from PyQt6.QtWidgets import QApplication, QWidget

from dioptra.log import get_logger

log = get_logger("dioptra.ui.selector")


class RegionSelector(QWidget):
    region_captured = pyqtSignal(object, int, int)
    selection_cancelled = pyqtSignal()

    def __init__(self) -> None:
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)

        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())
        else:
            self.setGeometry(0, 0, 1920, 1080)

        self._x1 = self._y1 = self._x2 = self._y2 = 0
        self._active = False

    def start_selection(self, x: int, y: int) -> None:
        self._x1 = self._x2 = x
        self._y1 = self._y2 = y
        self._active = True
        self.showFullScreen()
        self.raise_()

    def update_selection(self, x: int, y: int) -> None:
        if self._active:
            self._x2, self._y2 = x, y
            self.update()

    def end_selection(self, x: int, y: int) -> None:
        if not self._active:
            return
        self._active = False
        self._x2, self._y2 = x, y

        x1, y1 = min(self._x1, self._x2), min(self._y1, self._y2)
        x2, y2 = max(self._x1, self._x2), max(self._y1, self._y2)
        w, h = x2 - x1, y2 - y1

        if w > 10 and h > 10:
            monitor = {"left": x1, "top": y1, "width": w, "height": h}
            with mss.mss() as sct:
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", (sct_img.width, sct_img.height), sct_img.rgb)
            center_x = x1 + w // 2
            center_y = y1 + h // 2
            self.region_captured.emit(img, center_x, center_y)
        self._reset()
        self.hide()

    def cancel(self) -> None:
        self._active = False
        self._reset()
        self.hide()
        self.selection_cancelled.emit()

    def _reset(self) -> None:
        self._x1 = self._y1 = self._x2 = self._y2 = 0
        self.update()

    @property
    def is_selecting(self) -> bool:
        return self._active

    def keyPressEvent(self, event: Any) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.cancel()
        super().keyPressEvent(event)

    def paintEvent(self, event: Any) -> None:
        if self._x2 and self._y2 and (self._x1 != self._x2 or self._y1 != self._y2):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            rect = QRectF(self._x1, self._y1, self._x2 - self._x1, self._y2 - self._y1).normalized()
            painter.setPen(QPen(QColor(0, 120, 215), 2))
            painter.setBrush(QBrush(QColor(0, 120, 215, 30)))
            painter.drawRect(rect)
