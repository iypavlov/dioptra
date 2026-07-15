from deep_translator import GoogleTranslator

from .base import AbstractTranslator


class GoogleTranslateTranslator(AbstractTranslator):
    def __init__(self, source: str = "en", target: str = "ru"):
        self._source = source
        self._target = target
        self._translator = GoogleTranslator(source=source, target=target)

    @property
    def target_language(self) -> str:
        return self._target

    def set_target_language(self, lang: str):
        if lang != self._target:
            self._target = lang
            self._translator = GoogleTranslator(source=self._source, target=lang)

    def translate(self, text: str, source: str = "en", target: str = "ru") -> str:
        if source != self._source or target != self._target:
            self._translator = GoogleTranslator(source=source, target=target)
            self._source = source
            self._target = target
        return self._translator.translate(text)
