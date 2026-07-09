from abc import ABC, abstractmethod


class AbstractTranslator(ABC):
    @abstractmethod
    def translate(self, text: str, source: str = "en", target: str = "ru") -> str:
        ...


class TranslatorFactory:
    _registry: dict[str, type[AbstractTranslator]] = {}

    @classmethod
    def register(cls, name: str, translator_cls: type[AbstractTranslator]):
        cls._registry[name] = translator_cls

    @classmethod
    def create(cls, name: str, **kwargs) -> AbstractTranslator:
        if name not in cls._registry:
            raise ValueError(f"Unknown translator: {name}. Available: {list(cls._registry.keys())}")
        return cls._registry[name](**kwargs)
