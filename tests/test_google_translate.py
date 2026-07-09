from dioptra.translation.google_translate import GoogleTranslateTranslator


def test_init() -> None:
    t = GoogleTranslateTranslator(source="en", target="ru")
    assert t._source == "en"
    assert t._target == "ru"


def test_set_target_language() -> None:
    t = GoogleTranslateTranslator(source="en", target="ru")
    t.set_target_language("de")
    assert t._target == "de"


def test_set_target_language_same() -> None:
    t = GoogleTranslateTranslator(source="en", target="ru")
    t.set_target_language("ru")
    assert t._target == "ru"
