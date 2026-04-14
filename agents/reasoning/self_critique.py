"""
Self-Critique — ULTIMATE CRONUS
O agente revisa e melhora sua própria resposta iterativamente.
"""

from dataclasses import dataclass, field


@dataclass
class CritiqueResult:
    original: str
    critique: str
    improved: str
    iterations: int
    score_before: float
    score_after: float
    improvements: list[str] = field(default_factory=list)


CRITIQUE_SYSTEM = """Você é um revisor crítico do ULTIMATE CRONUS.
Sua tarefa: avaliar uma resposta e identificar fraquezas, lacunas e imprecisões.
Seja específico — aponte EXATAMENTE o que está errado ou incompleto.
Formato:
  PONTOS FRACOS:
  - [problema específico]
  LACUNAS:
  - [informação faltante]
  SCORE: X/10
  SUGESTÕES DE MELHORIA:
  - [ação concreta]"""

IMPROVE_SYSTEM = """Você é um agente de melhoria do ULTIMATE CRONUS.
Receba uma resposta original e uma crítica, e produza uma versão MELHORADA.
A versão melhorada deve:
  1. Corrigir todos os problemas apontados
  2. Preencher as lacunas identificadas
  3. Manter o que estava correto
  4. Ser mais precisa, completa e útil"""

SCORE_SYSTEM = """Avalie a qualidade desta resposta em uma escala de 0 a 10.
Critérios: precisão, completude, relevância, clareza, utilidade prática.
Responda APENAS com um número decimal entre 0 e 10 (ex: 7.5)."""


class SelfCritique:
    """
    Loop de auto-crítica e melhoria.
    O agente gera uma resposta, critica, melhora — quantas vezes necessário.
    """

    def __init__(self, max_iterations: int = 2, score_threshold: float = 8.0):
        self.max_iterations = max_iterations
        self.score_threshold = score_threshold

    def build_critique_prompt(self, question: str, answer: str) -> str:
        return (
            f"Pergunta original: {question}\n\n"
            f"Resposta a avaliar:\n{answer}\n\n"
            "Critique esta resposta de forma construtiva e específica."
        )

    def build_improve_prompt(self, question: str, answer: str, critique: str) -> str:
        return (
            f"Pergunta original: {question}\n\n"
            f"Resposta original:\n{answer}\n\n"
            f"Crítica recebida:\n{critique}\n\n"
            "Produza uma versão melhorada que corrija todos os problemas apontados."
        )

    def build_score_prompt(self, question: str, answer: str) -> str:
        return (
            f"Pergunta: {question}\n\nResposta:\n{answer}\n\n"
            "Qual o score desta resposta (0-10)? Responda APENAS com o número."
        )

    def extract_score(self, score_text: str) -> float:
        """Extrai score numérico de uma resposta de avaliação."""
        import re
        matches = re.findall(r"\d+\.?\d*", score_text.strip())
        if matches:
            score = float(matches[0])
            return min(10.0, max(0.0, score))
        return 5.0

    def extract_improvements(self, critique: str) -> list[str]:
        """Extrai lista de melhorias de uma crítica."""
        import re
        items = re.findall(r"[-•]\s+(.+)", critique)
        return [i.strip() for i in items if i.strip()]


class ConstitutionalAI:
    """
    Variação: Constitutional AI — revisa com base em princípios definidos.
    Útil para garantir que respostas sigam padrões éticos/empresariais.
    """

    DEFAULT_PRINCIPLES = [
        "A resposta é factualmente correta e baseada em dados?",
        "A resposta é ética e não causa danos?",
        "A resposta é relevante para o negócio do usuário?",
        "A resposta é clara e acionável?",
        "A resposta considera riscos e alternativas?",
    ]

    def __init__(self, principles: list[str] | None = None):
        self.principles = principles or self.DEFAULT_PRINCIPLES

    def build_review_prompt(self, answer: str) -> str:
        principles_text = "\n".join(f"{i+1}. {p}" for i, p in enumerate(self.principles))
        return (
            f"Avalie esta resposta com base nos princípios abaixo:\n\n"
            f"RESPOSTA:\n{answer}\n\n"
            f"PRINCÍPIOS:\n{principles_text}\n\n"
            "Para cada princípio violado, sugira uma correção específica."
        )

    def build_revise_prompt(self, answer: str, violations: str) -> str:
        return (
            f"Resposta original:\n{answer}\n\n"
            f"Violações identificadas:\n{violations}\n\n"
            "Reescreva a resposta corrigindo todas as violações."
        )
