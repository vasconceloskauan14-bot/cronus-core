"""
Base Tool — ULTIMATE CRONUS
Interface abstrata para todas as ferramentas dos agentes.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    success: bool
    output: Any
    error: str = ""
    metadata: dict = field(default_factory=dict)

    def __str__(self):
        if self.success:
            return str(self.output)
        return f"[ERRO] {self.error}"


class BaseTool(ABC):
    """Interface base para ferramentas que agentes podem usar."""

    name: str = "base"
    description: str = ""
    requires_key: bool = False

    @abstractmethod
    def run(self, **kwargs) -> ToolResult:
        """Executa a ferramenta e retorna resultado."""
        ...

    def is_available(self) -> bool:
        """Verifica se a ferramenta está disponível/configurada."""
        return True

    def schema(self) -> dict:
        """Retorna schema OpenAI function-calling da ferramenta."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {"type": "object", "properties": {}, "required": []},
        }

    def __repr__(self):
        return f"<Tool:{self.name}>"
