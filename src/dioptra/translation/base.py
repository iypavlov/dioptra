from abc import ABC, abstractmethod


class AbstractTranslator(ABC):
    @abstractmethod
    def translate(self, text: str, source: str = "en", target: str = "ru") -> str:
        ...

    @abstractmethod
    def set_target_language(self, lang: str) -> None:
        ...

    @property
    @abstractmethod
    def target_language(self) -> str:
        ...


class TranslatorFactory:
    _registry: dict[str, type[AbstractTranslator]] = {}

    @classmethod
    def register(cls, name: str, translator_cls: type[AbstractTranslator]) -> None:
        cls._registry[name] = translator_cls

    @classmethod
    def create(cls, name: str, **kwargs: object) -> AbstractTranslator:
        if name not in cls._registry:
            raise ValueError(f"Unknown translator: {name}. Available: {list(cls._registry.keys())}")
        return cls._registry[name](**kwargs)


