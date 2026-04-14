"""
Base Provider — ULTIMATE CRONUS
Interface abstrata que todo provider de IA deve implementar.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    role: str  # "user" | "assistant" | "system"
    content: str


@dataclass
class CompletionRequest:
    messages: list[Message]
    system: str = ""
    max_tokens: int = 8096
    temperature: float = 0.7
    model: str = ""           # Overrides provider default if set
    json_mode: bool = False
    extra: dict = field(default_factory=dict)


@dataclass
class CompletionResponse:
    text: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0


class BaseProvider(ABC):
    """
    Interface que todos os providers de IA devem implementar.
    Qualquer provider que implemente complete() funciona com o sistema inteiro.
    """

    name: str = "base"
    default_model: str = ""

    @abstractmethod
    def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Envia requisição e retorna resposta normalizada."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Verifica se o provider está configurado e acessível."""
        ...

    @abstractmethod
    def list_models(self) -> list[str]:
        """Lista modelos disponíveis neste provider."""
        ...

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str = "") -> float:
        """Estimativa de custo em USD. Override no provider específico."""
        return 0.0

    def __repr__(self):
        return f"<{self.__class__.__name__} model={self.default_model}>"
