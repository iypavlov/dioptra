import json
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from dioptra.log import get_logger

log = get_logger("dioptra.settings")

DEFAULT_SETTINGS = {
    "target_language": "ru",
    "adaptivity_enabled": True,
    "translator": "ollama",
    "selection_modifier": "ctrl",
    "ollama_url": "http://localhost:11434",
    "ollama_model": "llama3.2",
    "ollama_timeout": 10,
}


class SettingsManager(QObject):
    language_changed = pyqtSignal(str)
    translator_changed = pyqtSignal(str)
    ollama_settings_changed = pyqtSignal(str, str, int)
    modifier_changed = pyqtSignal(str)

    def __init__(self, config_dir: Path | None = None):
        super().__init__()
        self._config_dir = config_dir or Path.home() / ".screen-translator"
        self._file = self._config_dir / "settings.json"
        self._data = dict(DEFAULT_SETTINGS)
        self._load()

    def _load(self):
        if self._file.exists():
            try:
                with open(self._file, encoding="utf-8") as f:
                    self._data = {**DEFAULT_SETTINGS, **json.load(f)}
            except Exception as e:
                log.warning("Failed to load settings: %s, using defaults", e)
                self._data = dict(DEFAULT_SETTINGS)

    def _save(self):
        self._config_dir.mkdir(parents=True, exist_ok=True)
        with open(self._file, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    @property
    def target_language(self) -> str:
        return self._data.get("target_language", "ru")

    @target_language.setter
    def target_language(self, value: str):
        if value != self._data.get("target_language"):
            log.info("Setting target language: %s", value)
            self._data["target_language"] = value
            self._save()
            self.language_changed.emit(value)

    @property
    def adaptivity_enabled(self) -> bool:
        return self._data.get("adaptivity_enabled", True)

    @adaptivity_enabled.setter
    def adaptivity_enabled(self, value: bool):
        self._data["adaptivity_enabled"] = value
        self._save()

    @property
    def translator(self) -> str:
        return self._data.get("translator", "ollama")

    @translator.setter
    def translator(self, value: str):
        if value != self._data.get("translator"):
            log.info("Switching translator: %s", value)
            self._data["translator"] = value
            self._save()
            self.translator_changed.emit(value)

    @property
    def selection_modifier(self) -> str:
        return self._data.get("selection_modifier", "ctrl")

    @selection_modifier.setter
    def selection_modifier(self, value: str):
        if value != self._data.get("selection_modifier"):
            self._data["selection_modifier"] = value
            self._save()
            self.modifier_changed.emit(value)

    @property
    def ollama_url(self) -> str:
        return self._data.get("ollama_url", "http://localhost:11434")

    @ollama_url.setter
    def ollama_url(self, value: str):
        value = value.rstrip("/")
        if value != self._data.get("ollama_url"):
            self._data["ollama_url"] = value
            self._save()
            self._emit_ollama_changed()

    @property
    def ollama_model(self) -> str:
        return self._data.get("ollama_model", "llama3.2")

    @ollama_model.setter
    def ollama_model(self, value: str):
        if value != self._data.get("ollama_model"):
            self._data["ollama_model"] = value
            self._save()
            self._emit_ollama_changed()

    @property
    def ollama_timeout(self) -> int:
        return self._data.get("ollama_timeout", 10)

    @ollama_timeout.setter
    def ollama_timeout(self, value: int):
        if value != self._data.get("ollama_timeout"):
            self._data["ollama_timeout"] = value
            self._save()
            self._emit_ollama_changed()

    def _emit_ollama_changed(self):
        self.ollama_settings_changed.emit(
            self.ollama_url, self.ollama_model, self.ollama_timeout
        )
