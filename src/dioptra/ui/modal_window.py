from collections.abc import Callable
from typing import Any

import mouse
from PyQt6.QtCore import QObject, QPropertyAnimation, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from dioptra.log import get_logger

log = get_logger("dioptra.ui.modal")


class _MouseBridge(QObject):
    clicked = pyqtSignal()


class _BlockWidget(QWidget):
    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, w: int) -> int:
        ly = self.layout()
        if ly is not None:
            m = ly.contentsMargins()
            avail = w - m.left() - m.right()
            h = m.top() + m.bottom()
            for i in range(ly.count()):
                item = ly.itemAt(i)
                assert item is not None
                ih = -1
                widget = item.widget()
                if widget is not None and hasattr(widget, 'heightForWidth'):
                    ih = widget.heightForWidth(avail)
                elif hasattr(item, 'heightForWidth'):
                    ih = item.heightForWidth(avail)
                if ih < 0:
                    ih = item.sizeHint().height()
                if ih > 0:
                    w_item = item.widget()
                    if w_item is not None:
                        max_h = w_item.maximumHeight()
                        if 0 < max_h < ih:
                            ih = max_h
                    h += ih
                if i < ly.count() - 1:
                    h += ly.spacing()
            return h
        return super().heightForWidth(w)


class ModalOverlay(QWidget):
    def __init__(self) -> None:
        super().__init__(None)
        self._bridge = _MouseBridge()
        self._bridge.clicked.connect(self.hide)
        self._mouse_hook_ref = None
        self._auto_hide_timer = QTimer(self)
        self._auto_hide_timer.setSingleShot(True)
        self._auto_hide_timer.timeout.connect(self._fade_out)
        self._loading_timer = QTimer(self)
        self._loading_timer.timeout.connect(self._on_loading_timeout)
        self._loading_dots = 0
        self._loading_active = False
        self._fade_anim: QPropertyAnimation | None = None
        self._provider_name: str = ""
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(False)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setObjectName("modalScroll")
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._scroll.setStyleSheet("""
            #modalScroll { background: transparent; border: none; }
            #modalScroll > QScrollBar:vertical {
                background: transparent; width: 6px; margin: 0; border: none;
            }
            #modalScroll > QScrollBar::handle:vertical {
                background: #3a3d4e; border-radius: 3px; min-height: 30px;
            }
            #modalScroll > QScrollBar::handle:vertical:hover {
                background: #4a4d5e;
            }
            #modalScroll > QScrollBar::add-line:vertical,
            #modalScroll > QScrollBar::sub-line:vertical {
                height: 0; border: none;
            }
            #modalScroll > QScrollBar::add-page:vertical,
            #modalScroll > QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)
        vp = self._scroll.viewport()
        if vp is not None:
            vp.setStyleSheet("background: transparent;")

        self._bg = _BlockWidget()
        self._bg.setObjectName("modalBg")
        self._bg.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._bg.setStyleSheet("""
            #modalBg {
                background: rgba(26, 27, 35, 0.94);
                border: 1px solid rgba(46, 49, 64, 0.7);
                border-radius: 12px;
            }
        """)
        bg = QVBoxLayout(self._bg)
        bg.setContentsMargins(0, 0, 0, 0)
        bg.setSpacing(0)

        # --- Block 1: source word ---
        source_block = _BlockWidget()
        source_block.setStyleSheet("background: transparent;")
        sb = QVBoxLayout(source_block)
        sb.setContentsMargins(24, 20, 28, 12)
        label_src = QLabel("WORD")
        label_src.setFont(QFont("Segoe UI", 8))
        label_src.setStyleSheet("color: #585e72; background: transparent; letter-spacing: 1px;")
        sb.addWidget(label_src)
        self._source_label = QLabel()
        src_font = QFont("Segoe UI", 12)
        src_font.setWeight(QFont.Weight.Medium)
        self._source_label.setFont(src_font)
        self._source_label.setStyleSheet("color: #e8eaf0; background: transparent;")
        self._source_label.setWordWrap(True)
        self._source_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        sb.addWidget(self._source_label)
        bg.addWidget(source_block)

        # --- divider ---
        div = QWidget()
        div.setFixedHeight(1)
        div.setStyleSheet("background: #282a36;")
        bg.addWidget(div)

        # --- Block 2: translation ---
        trans_block = _BlockWidget()
        trans_block.setStyleSheet("background: transparent;")
        tb = QVBoxLayout(trans_block)
        tb.setContentsMargins(24, 14, 28, 18)
        label_tr = QLabel("TRANSLATION")
        label_tr.setFont(QFont("Segoe UI", 8))
        label_tr.setStyleSheet("color: #585e72; background: transparent; letter-spacing: 1px;")
        tb.addWidget(label_tr)
        self._translation_label = QLabel()
        self._translation_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self._translation_label.setStyleSheet("color: #ffffff; background: transparent;")
        self._translation_label.setWordWrap(True)
        self._translation_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        tb.addWidget(self._translation_label)
        bg.addWidget(trans_block)

        # --- footer ---
        footer = QHBoxLayout()
        footer.setContentsMargins(24, 6, 24, 12)
        self._provider_label = QLabel()
        self._provider_label.setFont(QFont("Segoe UI", 8))
        self._provider_label.setStyleSheet("color: #505568; background: transparent;")
        footer.addWidget(self._provider_label)
        footer.addStretch()
        bg.addLayout(footer)

        self._scroll.setWidget(self._bg)
        root.addWidget(self._scroll)
        self.setLayout(root)

    def clear_content(self) -> None:
        self._auto_hide_timer.stop()
        self._source_label.clear()
        self._start_loading_animation()

    def set_provider(self, name: str) -> None:
        self._provider_name = name

    def show_loading(self, cursor_x: int, cursor_y: int) -> None:
        self._auto_hide_timer.stop()
        self._source_label.setText("...")
        self._translation_label.clear()
        self._start_loading_animation()
        self._provider_label.setText(self._provider_name)
        self._position_and_show(cursor_x, cursor_y)

    def show_ocr_progress(self, word: str, cursor_x: int, cursor_y: int) -> None:
        self._auto_hide_timer.stop()
        self._source_label.setText(word)
        self._translation_label.clear()
        self._start_loading_animation()
        self._position_and_show(cursor_x, cursor_y)

    def show_translation(self, word: str, translation: str, cursor_x: int, cursor_y: int) -> None:
        self._stop_loading_animation()
        self._auto_hide_timer.stop()
        self._source_label.setText(word)
        self._translation_label.setText(translation)
        self._provider_label.setText(self._provider_name)
        self._position_and_show(cursor_x, cursor_y)

    def show_message(self, message: str, cursor_x: int, cursor_y: int) -> None:
        self._stop_loading_animation()
        self._auto_hide_timer.stop()
        self._source_label.setText("")
        self._translation_label.setText(message)
        self._provider_label.setText(self._provider_name)
        self._position_and_show(cursor_x, cursor_y)
        self._auto_hide_timer.start(2500)

    def _start_loading_animation(self) -> None:
        self._loading_dots = 0
        self._loading_active = True
        self._translation_label.setText("Translating")
        self._loading_timer.start(500)

    def _stop_loading_animation(self) -> None:
        self._loading_active = False
        self._loading_timer.stop()

    def _animate_opacity(
        self, target: float, duration: int,
        on_finish: Callable[[], None] | None = None,
    ) -> QPropertyAnimation:
        if self._fade_anim:
            try:
                self._fade_anim.finished.disconnect()
            except TypeError:
                pass
            self._fade_anim.stop()
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(duration)
        self._fade_anim.setStartValue(self.windowOpacity())
        self._fade_anim.setEndValue(target)
        if on_finish:
            self._fade_anim.finished.connect(on_finish)
        self._fade_anim.start()
        return self._fade_anim

    def _on_loading_timeout(self) -> None:
        if not self._loading_active:
            return
        self._loading_dots = (self._loading_dots + 1) % 4
        self._translation_label.setText(f"Translating{'.' * self._loading_dots}")

    def _position_and_show(self, cursor_x: int, cursor_y: int) -> None:
        MODAL_WIDTH = 440
        MARGIN = 15
        GAP = 15

        self._bg.setFixedWidth(MODAL_WIDTH)
        content_h = self._bg.heightForWidth(MODAL_WIDTH)
        if content_h <= 0:
            content_h = self._bg.minimumSizeHint().height()

        screen = self.screen()
        sg = screen.availableGeometry() if screen else None

        if sg:
            max_avail_h = sg.height() - 2 * MARGIN
            if content_h > max_avail_h:
                modal_h = max_avail_h
            else:
                modal_h = content_h
        else:
            modal_h = content_h

        self._bg.setFixedHeight(content_h)
        self.setFixedSize(MODAL_WIDTH, modal_h)
        w, h = MODAL_WIDTH, modal_h

        if sg:
            candidates = [
                (cursor_x + GAP, cursor_y - h // 2),
                (cursor_x - w - GAP, cursor_y - h // 2),
                (cursor_x - w // 2, cursor_y + GAP),
                (cursor_x - w // 2, cursor_y - h - GAP),
            ]
            best = None
            clamped = []
            for cx, cy in candidates:
                if (sg.left() + MARGIN <= cx <= sg.right() - w - MARGIN and
                    sg.top() + MARGIN <= cy <= sg.bottom() - h - MARGIN):
                    best = (cx, cy)
                    break
                clamped.append((
                    max(sg.left() + MARGIN, min(cx, sg.right() - w - MARGIN)),
                    max(sg.top() + MARGIN, min(cy, sg.bottom() - h - MARGIN)),
                ))
            if best is None and clamped:
                best = min(clamped, key=lambda p: abs(p[0] - cursor_x) + abs(p[1] - cursor_y))
            if best:
                x, y = best
        else:
            x = cursor_x + GAP
            y = cursor_y - h // 2

        self.move(x, y)
        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        self._animate_opacity(1.0, 150)
        self._start_mouse_hook()

    def _start_mouse_hook(self) -> None:
        self._stop_mouse_hook()

        def on_event(e: mouse.ButtonEvent | mouse.MoveEvent) -> None:
            if isinstance(e, mouse.ButtonEvent) and e.event_type == 'up' and e.button == 'left':
                x, y = mouse.get_position()
                rect = self.geometry()
                if not rect.contains(x, y):
                    self._bridge.clicked.emit()

        self._mouse_hook_ref = mouse.hook(on_event)

    def _stop_mouse_hook(self) -> None:
        if self._mouse_hook_ref is not None:
            try:
                mouse.unhook(self._mouse_hook_ref)
            except Exception:
                pass
            self._mouse_hook_ref = None

    def _fade_out(self) -> None:
        self._stop_mouse_hook()
        self._animate_opacity(0.0, 100, self.hide)

    def hideEvent(self, event: Any) -> None:
        self._stop_loading_animation()
        self._stop_mouse_hook()
        self._source_label.clear()
        self._translation_label.clear()
        self._provider_label.clear()
        super().hideEvent(event)

    def mousePressEvent(self, event: Any) -> None:
        event.accept()

    def keyPressEvent(self, event: Any) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self._fade_out()
        super().keyPressEvent(event)
