from abc import ABC, abstractmethod


class ModelUnavailableError(RuntimeError):
    """Raised when an optional local model cannot be reached."""


class SummaryModel(ABC):
    @abstractmethod
    def summarize(self, prompt: str, max_tokens: int = 512) -> str:
        raise NotImplementedError
