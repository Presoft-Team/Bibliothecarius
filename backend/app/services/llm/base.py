from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ChatMessage:
    role: str  # "user" | "assistant"
    content: str


class LLMProviderError(Exception):
    """Raised for any provider-side failure (auth, rate limit, network, etc.)."""


class LLMProvider(ABC):
    def __init__(self, model: str):
        self.model = model

    @abstractmethod
    def generate(self, messages: list[ChatMessage], system_prompt: str, params: dict) -> str:
        """Return the assistant's reply text for the given conversation turn."""
