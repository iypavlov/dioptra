from typing import Any

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from dioptra.log import get_logger
from dioptra.settings import SettingsManager
from dioptra.translation.ollama_translate import OllamaTranslateTranslator

log = get_logger("dioptra.ui.settings")


class SettingsWindow(QDialog):
    def __init__(self, settings: SettingsManager, parent: Any = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self._setup_ui()
        self._load_current()

    def _setup_ui(self) -> None:
        self.setWindowTitle("Settings")
        self.setFixedSize(420, 400)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout()
        layout.setSpacing(12)

        lang_label = QLabel("EN → RU")
        lang_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lang_label.setStyleSheet("color: #e8eaf0; background: #1a1b23; padding: 8px; border-radius: 6px;")
        layout.addWidget(lang_label)

        provider_layout = QHBoxLayout()
        provider_layout.addWidget(QLabel("Translator:"))
        self._provider_combo = QComboBox()
        self._provider_combo.addItem("Ollama (local)", "ollama")
        self._provider_combo.addItem("Google Translate", "google")
        self._provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        provider_layout.addWidget(self._provider_combo)
        layout.addLayout(provider_layout)

        self._ollama_group = QGroupBox("Ollama Configuration")
        ollama_layout = QVBoxLayout()

        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("Server URL:"))
        self._ollama_url_input = QLineEdit()
        url_layout.addWidget(self._ollama_url_input)
        ollama_layout.addLayout(url_layout)

        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self._ollama_model_combo = QComboBox()
        self._ollama_model_combo.setEditable(True)
        model_layout.addWidget(self._ollama_model_combo)
        self._refresh_models_btn = QPushButton("Refresh")
        self._refresh_models_btn.clicked.connect(self._refresh_ollama_models)
        model_layout.addWidget(self._refresh_models_btn)
        ollama_layout.addLayout(model_layout)

        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("Timeout (s):"))
        self._ollama_timeout_spin = QSpinBox()
        self._ollama_timeout_spin.setRange(1, 120)
        timeout_layout.addWidget(self._ollama_timeout_spin)
        ollama_layout.addLayout(timeout_layout)

        self._ollama_group.setLayout(ollama_layout)
        layout.addWidget(self._ollama_group)

        mod_layout = QHBoxLayout()
        mod_layout.addWidget(QLabel("Selection hotkey:"))
        self._modifier_input = QLineEdit()
        self._modifier_input.setPlaceholderText("e.g. ctrl+shift, alt+shift, ctrl")
        mod_layout.addWidget(self._modifier_input)
        layout.addLayout(mod_layout)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def showEvent(self, event: Any) -> None:
        super().showEvent(event)
        QTimer.singleShot(0, self._center_on_screen)

    def _center_on_screen(self) -> None:
        screen = self.screen()
        if screen:
            sg = screen.availableGeometry()
            x = sg.x() + (sg.width() - self.width()) // 2
            y = sg.y() + (sg.height() - self.height()) // 2
            self.move(x, y)

    def _on_provider_changed(self, index: int) -> None:
        is_ollama = self._provider_combo.itemData(index) == "ollama"
        self._ollama_group.setVisible(is_ollama)
        if is_ollama:
            self._refresh_ollama_models()

    def _refresh_ollama_models(self) -> None:
        url = self._ollama_url_input.text().strip() or "http://localhost:11434"
        log.debug("Refreshing Ollama models from %s", url)
        models = OllamaTranslateTranslator.list_models(url)
        current = self._ollama_model_combo.currentText()
        self._ollama_model_combo.clear()
        if models:
            log.debug("Found %d Ollama models: %s", len(models), ", ".join(models))
            self._ollama_model_combo.addItems(models)
        else:
            log.warning("No Ollama models found at %s", url)
            self._ollama_model_combo.setPlaceholderText("No models found (check URL)")
        if current:
            idx = self._ollama_model_combo.findText(current)
            if idx >= 0:
                self._ollama_model_combo.setCurrentIndex(idx)
            else:
                self._ollama_model_combo.setEditText(current)

    def _load_current(self) -> None:
        pidx = self._provider_combo.findData(self._settings.translator)
        if pidx >= 0:
            self._provider_combo.setCurrentIndex(pidx)
        self._ollama_url_input.setText(self._settings.ollama_url)
        self._ollama_model_combo.setEditText(self._settings.ollama_model)
        self._ollama_timeout_spin.setValue(self._settings.ollama_timeout)
        self._on_provider_changed(self._provider_combo.currentIndex())
        self._modifier_input.setText(self._settings.selection_modifier)

    def _save(self) -> None:
        log.info("Saving settings")
        self._settings.translator = self._provider_combo.currentData()
        self._settings.ollama_url = self._ollama_url_input.text().strip()
        self._settings.ollama_model = self._ollama_model_combo.currentText().strip()
        self._settings.ollama_timeout = self._ollama_timeout_spin.value()
        self._settings.selection_modifier = self._modifier_input.text().strip()
        self.accept()
