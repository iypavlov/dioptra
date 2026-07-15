from dioptra.translation.base import AbstractTranslator, TranslatorFactory


class FakeTranslator(AbstractTranslator):
    def __init__(self, **kwargs) -> None:
        self._target = kwargs.get("target", "ru")
        self._kwargs = kwargs

    @property
    def target_language(self) -> str:
        return self._target

    def set_target_language(self, lang: str) -> None:
        self._target = lang

    def translate(self, text: str, source: str = "en", target: str = "ru") -> str:
        return f"[{source}->{target}] {text}"


def test_register_and_create() -> None:
    TranslatorFactory.register("fake", FakeTranslator)
    instance = TranslatorFactory.create("fake")
    assert isinstance(instance, FakeTranslator)


def test_create_with_kwargs() -> None:
    TranslatorFactory.register("fake_kwargs", FakeTranslator)
    instance = TranslatorFactory.create("fake_kwargs", extra="value")
    assert isinstance(instance, FakeTranslator)


def test_unknown_translator() -> None:
    try:
        TranslatorFactory.create("nonexistent")
        raise AssertionError("Expected ValueError")
    except ValueError:
        pass


def test_translate_implementation() -> None:
    t = FakeTranslator()
    result = t.translate("hello", source="en", target="ru")
    assert result == "[en->ru] hello"
