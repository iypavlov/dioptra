from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QLineEdit, QPushButton,
    QGroupBox, QSpinBox,
)
from PyQt6.QtCore import Qt
from settings import SettingsManager
from translation.ollama_translate import OllamaTranslateTranslator


LANGUAGES = {
    "ru": "Russian",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "zh": "Chinese",
    "ja": "Japanese",
    "ar": "Arabic",
    "ko": "Korean",
    "pl": "Polish",
    "nl": "Dutch",
    "tr": "Turkish",
    "cs": "Czech",
    "sv": "Swedish",
}


class SettingsWindow(QDialog):
    def __init__(self, settings: SettingsManager, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._setup_ui()
        self._load_current()

    def _setup_ui(self):
        self.setWindowTitle("Settings")
        self.setFixedSize(420, 400)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout()
        layout.setSpacing(12)

        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Target language:"))
        self._lang_combo = QComboBox()
        for code, name in LANGUAGES.items():
            self._lang_combo.addItem(f"{name} ({code})", code)
        lang_layout.addWidget(self._lang_combo)
        layout.addLayout(lang_layout)

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
        mod_layout.addWidget(QLabel("Selection modifier:"))
        self._modifier_combo = QComboBox()
        self._modifier_combo.addItem("Ctrl", "ctrl")
        self._modifier_combo.addItem("Alt", "alt")
        self._modifier_combo.addItem("Win", "win")
        mod_layout.addWidget(self._modifier_combo)
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

    def showEvent(self, event):
        super().showEvent(event)
        self._center_on_screen()

    def _center_on_screen(self):
        screen = self.screen()
        if screen:
            sg = screen.availableGeometry()
            x = sg.x() + (sg.width() - self.width()) // 2
            y = sg.y() + (sg.height() - self.height()) // 2
            self.move(x, y)

    def _on_provider_changed(self, index: int):
        is_ollama = self._provider_combo.itemData(index) == "ollama"
        self._ollama_group.setVisible(is_ollama)
        if is_ollama:
            self._refresh_ollama_models()

    def _refresh_ollama_models(self):
        url = self._ollama_url_input.text().strip() or "http://localhost:11434"
        models = OllamaTranslateTranslator.list_models(url)
        current = self._ollama_model_combo.currentText()
        self._ollama_model_combo.clear()
        if models:
            self._ollama_model_combo.addItems(models)
        else:
            self._ollama_model_combo.setPlaceholderText("No models found (check URL)")
        if current:
            idx = self._ollama_model_combo.findText(current)
            if idx >= 0:
                self._ollama_model_combo.setCurrentIndex(idx)
            else:
                self._ollama_model_combo.setEditText(current)

    def _load_current(self):
        idx = self._lang_combo.findData(self._settings.target_language)
        if idx >= 0:
            self._lang_combo.setCurrentIndex(idx)
        pidx = self._provider_combo.findData(self._settings.translator)
        if pidx >= 0:
            self._provider_combo.setCurrentIndex(pidx)
        self._ollama_url_input.setText(self._settings.ollama_url)
        self._ollama_model_combo.setEditText(self._settings.ollama_model)
        self._ollama_timeout_spin.setValue(self._settings.ollama_timeout)
        self._on_provider_changed(self._provider_combo.currentIndex())
        midx = self._modifier_combo.findData(self._settings.selection_modifier)
        if midx >= 0:
            self._modifier_combo.setCurrentIndex(midx)

    def _save(self):
        self._settings.target_language = self._lang_combo.currentData()
        self._settings.translator = self._provider_combo.currentData()
        self._settings.ollama_url = self._ollama_url_input.text().strip()
        self._settings.ollama_model = self._ollama_model_combo.currentText().strip()
        self._settings.ollama_timeout = self._ollama_timeout_spin.value()
        self._settings.selection_modifier = self._modifier_combo.currentData()
        self.accept()
