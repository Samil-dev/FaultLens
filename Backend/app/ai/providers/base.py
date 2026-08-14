from abc import ABC, abstractmethod


class BaseAIProvider(ABC):
    """
    Base interface for AI providers.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Returns the provider name.
        """
        raise NotImplementedError

    @abstractmethod
    def generate(
        self,
        prompt: str
    ) -> str:
        """
        Generates a response from the provided prompt.
        """
        raise NotImplementedError