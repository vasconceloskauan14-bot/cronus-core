"""
Tree of Thought — ULTIMATE CRONUS
Explora múltiplos caminhos de raciocínio e escolhe o melhor.
Ideal para decisões estratégicas com múltiplas alternativas.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ThoughtNode:
    id: str
    depth: int
    thought: str
    value: float = 0.0
    children: list["ThoughtNode"] = field(default_factory=list)
    pruned: bool = False


@dataclass
class ToTResult:
    problem: str
    best_path: list[str]
    best_value: float
    final_answer: str
    all_thoughts: list[dict] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)


GENERATE_SYSTEM = """Você é um gerador de pensamentos estratégicos do ULTIMATE CRONUS.
Dado um problema, gere {n} abordagens/perspectivas DISTINTAS e criativas.
Cada abordagem deve ser uma direção diferente de resolução.
Seja conciso (1-2 frases por abordagem) e específico ao contexto.
Numere cada abordagem claramente (1. ... 2. ... 3. ...)."""

EVALUATE_SYSTEM = """Você é um avaliador estratégico do ULTIMATE CRONUS.
Avalie cada abordagem de resolução de problema com um score de 0-10.
Critérios: viabilidade, impacto, custo, prazo, risco.
Responda com JSON: {"scores": [{"id": 1, "score": 8.5, "rationale": "..."}, ...]}"""

EXPAND_SYSTEM = """Você é um agente de expansão estratégica do ULTIMATE CRONUS.
Dado um caminho de raciocínio, desenvolva o PRÓXIMO passo lógico.
Seja específico, acionável e concreto. 2-3 frases."""


class TreeOfThought:
    """
    Tree-of-Thought: busca BFS/DFS em espaço de raciocínio.
    Gera N pensamentos por nível, avalia, poda os ruins, expande os melhores.
    """

    def __init__(
        self,
        breadth: int = 3,       # pensamentos por nível
        depth: int = 2,          # profundidade da árvore
        top_k: int = 2,          # melhores a expandir
        score_threshold: float = 5.0,  # mínimo para não podar
    ):
        self.breadth = breadth
        self.depth = depth
        self.top_k = top_k
        self.score_threshold = score_threshold

    def build_generate_prompt(self, problem: str, context: str = "", n: int = 0) -> str:
        n = n or self.breadth
        ctx = f"Contexto:\n{context}\n\n" if context else ""
        return (
            f"{ctx}Problema: {problem}\n\n"
            f"Gere {n} abordagens distintas para resolver este problema."
        )

    def build_evaluate_prompt(self, problem: str, thoughts: list[str]) -> str:
        thoughts_text = "\n".join(f"{i+1}. {t}" for i, t in enumerate(thoughts))
        return (
            f"Problema: {problem}\n\n"
            f"Abordagens a avaliar:\n{thoughts_text}\n\n"
            "Avalie cada abordagem (score 0-10) e explique brevemente."
        )

    def build_expand_prompt(self, problem: str, path: list[str]) -> str:
        path_text = "\n→ ".join(path)
        return (
            f"Problema original: {problem}\n\n"
            f"Caminho de raciocínio até agora:\n→ {path_text}\n\n"
            "Desenvolva o próximo passo lógico deste caminho."
        )

    def build_final_prompt(self, problem: str, best_paths: list[list[str]]) -> str:
        paths_text = ""
        for i, path in enumerate(best_paths, 1):
            paths_text += f"\nCaminho {i}:\n" + "\n→ ".join(path) + "\n"
        return (
            f"Problema: {problem}\n\n"
            f"Melhores caminhos de raciocínio explorados:{paths_text}\n"
            "Com base nestes caminhos, produza a MELHOR resposta final, "
            "sintetizando os insights de todos os caminhos promissores."
        )

    def parse_thoughts(self, text: str) -> list[str]:
        """Extrai lista de pensamentos numerados de um texto."""
        import re
        thoughts = []
        # Tenta padrão numerado
        matches = re.findall(r"^\d+\.\s+(.+?)(?=^\d+\.|\Z)", text, re.MULTILINE | re.DOTALL)
        if matches:
            return [m.strip() for m in matches if m.strip()]
        # Fallback: split por linhas não vazias
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        return lines[:self.breadth]

    def parse_scores(self, text: str, n: int) -> list[float]:
        """Extrai scores de uma resposta de avaliação."""
        import re
        import json
        # Tenta JSON
        try:
            data = json.loads(text)
            if "scores" in data:
                return [float(s.get("score", 5)) for s in data["scores"]]
        except Exception:
            pass
        # Regex fallback
        scores = re.findall(r"(?:score|nota|avaliação)[:\s]+(\d+\.?\d*)", text, re.IGNORECASE)
        if scores:
            return [float(s) for s in scores[:n]]
        # Números soltos
        nums = re.findall(r"\b(\d+\.?\d*)\b", text)
        valid = [float(n) for n in nums if 0 <= float(n) <= 10]
        return (valid + [5.0] * n)[:n]


class MCTS:
    """
    Monte Carlo Tree Search simplificado para decisões estratégicas.
    Usa simulação aleatória para estimar valor de nós.
    """

    def __init__(self, simulations: int = 5, exploration: float = 1.41):
        self.simulations = simulations
        self.exploration = exploration  # UCB1 constant

    def build_simulation_prompt(self, problem: str, path: list[str]) -> str:
        path_text = " → ".join(path)
        return (
            f"Problema: {problem}\n"
            f"Estratégia: {path_text}\n\n"
            "Se implementarmos esta estratégia, qual seria o resultado esperado? "
            "Dê um score de sucesso (0-10) e explique em 2 frases."
        )

    def ucb1(self, value: float, visits: int, parent_visits: int) -> float:
        import math
        if visits == 0:
            return float("inf")
        return value / visits + self.exploration * math.sqrt(math.log(parent_visits) / visits)
