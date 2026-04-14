"""
Tool Registry — ULTIMATE CRONUS
Registro central de todas as ferramentas disponíveis para os agentes.
"""

from .base_tool import BaseTool, ToolResult
from .web_search import WebSearchTool
from .code_executor import CodeExecutorTool
from .file_reader import FileReaderTool
from .calculator import CalculatorTool
from .scraper import ScraperTool


# Registry global
_REGISTRY: dict[str, BaseTool] = {}


def register(tool: BaseTool) -> None:
    _REGISTRY[tool.name] = tool


def get(name: str) -> BaseTool | None:
    return _REGISTRY.get(name)


def all_tools() -> dict[str, BaseTool]:
    return dict(_REGISTRY)


def available_tools() -> list[BaseTool]:
    return [t for t in _REGISTRY.values() if t.is_available()]


def schemas() -> list[dict]:
    """Retorna schemas OpenAI function-calling de todas as ferramentas disponíveis."""
    return [t.schema() for t in available_tools()]


def execute(name: str, **kwargs) -> ToolResult:
    """Executa uma ferramenta pelo nome."""
    tool = get(name)
    if not tool:
        return ToolResult(success=False, output="", error=f"Ferramenta '{name}' não encontrada")
    if not tool.is_available():
        return ToolResult(success=False, output="", error=f"Ferramenta '{name}' não disponível")
    return tool.run(**kwargs)


def build_default_registry(
    max_search_results: int = 5,
    code_timeout: int = 30,
) -> dict[str, BaseTool]:
    """Cria e registra todas as ferramentas padrão."""
    tools = [
        WebSearchTool(max_results=max_search_results),
        CodeExecutorTool(timeout=code_timeout),
        FileReaderTool(),
        CalculatorTool(),
        ScraperTool(),
    ]
    for t in tools:
        register(t)
    return _REGISTRY


class ToolKit:
    """
    Kit de ferramentas para um agente específico.
    Permite selecionar subconjunto de ferramentas e executar com histórico.
    """

    def __init__(self, tool_names: list[str] | None = None):
        """
        Args:
            tool_names: Lista de ferramentas a incluir. None = todas.
        """
        if not _REGISTRY:
            build_default_registry()

        if tool_names is None:
            self._tools = dict(_REGISTRY)
        else:
            self._tools = {n: _REGISTRY[n] for n in tool_names if n in _REGISTRY}

        self.history: list[dict] = []

    def run(self, name: str, **kwargs) -> ToolResult:
        """Executa ferramenta e registra no histórico."""
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(success=False, output="", error=f"Ferramenta '{name}' não disponível neste kit")

        result = tool.run(**kwargs)
        self.history.append({
            "tool": name,
            "kwargs": kwargs,
            "success": result.success,
            "output_preview": str(result.output)[:200],
        })
        return result

    def schemas(self) -> list[dict]:
        return [t.schema() for t in self._tools.values() if t.is_available()]

    def format_for_prompt(self) -> str:
        """Formata ferramentas disponíveis para incluir no system prompt."""
        lines = ["Ferramentas disponíveis:"]
        for name, tool in self._tools.items():
            lines.append(f"  - {name}: {tool.description}")
        return "\n".join(lines)

    def __repr__(self):
        return f"<ToolKit tools={list(self._tools.keys())}>"
