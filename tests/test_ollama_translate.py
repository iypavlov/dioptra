import json
from unittest.mock import MagicMock, patch

from dioptra.translation.ollama_translate import OllamaTranslateTranslator


def test_init() -> None:
    t = OllamaTranslateTranslator(model="llama3", target_language="ru", timeout=15, url="http://localhost:11434")
    assert t._model == "llama3"
    assert t.target_language == "ru"
    assert t._timeout == 15
    assert t._url == "http://localhost:11434"


def test_set_target_language() -> None:
    t = OllamaTranslateTranslator()
    t.set_target_language("de")
    assert t.target_language == "de"


def test_translate_success() -> None:
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({
        "message": {"content": "привет"},
    }).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        t = OllamaTranslateTranslator(model="llama3", target_language="ru")
        result = t.translate("hello")
        assert result == "привет"
        mock_urlopen.assert_called_once()


def test_translate_network_error() -> None:
    with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
        t = OllamaTranslateTranslator()
        result = t.translate("hello")
        assert result.startswith("[Ollama error:")


def test_list_models_success() -> None:
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({
        "models": [{"name": "llama3.2"}, {"name": "mistral"}],
    }).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        models = OllamaTranslateTranslator.list_models("http://localhost:11434")
        assert models == ["llama3.2", "mistral"]


def test_list_models_error() -> None:
    with patch("urllib.request.urlopen", side_effect=Exception("Timeout")):
        models = OllamaTranslateTranslator.list_models("http://localhost:11434")
        assert models == []
