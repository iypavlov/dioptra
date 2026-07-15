import json
import urllib.error
import urllib.request

from .base import AbstractTranslator

SYSTEM_PROMPT_TEMPLATE = (
    "You are a professional translator. Translate the following text to {target}.\n"
    "Rules:\n"
    "- Return ONLY the translated text, no explanations, no notes\n"
    "- Preserve the original meaning, tone, and style\n"
    "- Use natural, idiomatic {target}\n"
    "- Keep formatting (line breaks, punctuation) as close to the original as possible"
)


class OllamaTranslateTranslator(AbstractTranslator):
    def __init__(self, model: str = "llama3.2", target_language: str = "ru",
                 timeout: int = 10, url: str = "http://localhost:11434"):
        self._model = model
        self._target_language_value = target_language
        self._timeout = timeout
        self._url = url.rstrip("/")

    @property
    def target_language(self) -> str:
        return self._target_language_value

    def set_target_language(self, lang: str):
        self._target_language_value = lang

    def translate(self, text: str, **kwargs) -> str:
        lang = self._target_language_value
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT_TEMPLATE.format(target=lang)},
                {"role": "user", "content": text},
            ],
            "stream": False,
            "options": {"temperature": 0},
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self._url}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("message", {}).get("content", "").strip()
        except urllib.error.URLError as e:
            return f"[Ollama error: {e.reason}]"
        except Exception as e:
            return f"[Ollama error: {e}]"

    @staticmethod
    def list_models(url: str = "http://localhost:11434") -> list[str]:
        try:
            req = urllib.request.Request(f"{url.rstrip('/')}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []
