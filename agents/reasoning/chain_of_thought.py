"""
Chain of Thought — ULTIMATE CRONUS
Raciocínio passo-a-passo para decisões complexas.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ThoughtStep:
    step: int
    thought: str
    conclusion: str = ""


@dataclass
class CoTResult:
    question: str
    steps: list[ThoughtStep]
    final_answer: str
    confidence: float = 0.0
    reasoning_summary: str = ""


COT_SYSTEM = """Você é um agente de raciocínio analítico do ULTIMATE CRONUS.
Ao receber uma pergunta ou problema, raciocine EXPLICITAMENTE passo a passo.
Estruture seu pensamento assim:
  Passo 1: [Observação/análise inicial]
  Passo 2: [Decomposição do problema]
  Passo 3: [Análise de evidências/dados]
  Passo 4: [Consideração de alternativas]
  Passo 5: [Conclusão fundamentada]
Seja preciso, cite dados quando disponíveis, e indique sua confiança (0-100%)."""


COT_JSON_SYSTEM = """Você é um agente de raciocínio do ULTIMATE CRONUS.
Responda APENAS com JSON válido no formato:
{
  "steps": [
    {"step": 1, "thought": "...", "conclusion": "..."},
    {"step": 2, "thought": "...", "conclusion": "..."}
  ],
  "final_answer": "...",
  "confidence": 85,
  "reasoning_summary": "..."
}"""


class ChainOfThought:
    """
    Implementa Chain-of-Thought prompting.
    Pode ser usado standalone ou via base_agent.think().
    """

    @staticmethod
    def build_prompt(question: str, context: str = "", examples: list[str] | None = None) -> str:
        parts = []
        if context:
            parts.append(f"Contexto:\n{context}\n")
        if examples:
            parts.append("Exemplos de raciocínio:\n" + "\n".join(examples) + "\n")
        parts.append(
            f"Pergunta/Problema: {question}\n\n"
            "Pense passo a passo antes de dar a resposta final."
        )
        return "\n".join(parts)

    @staticmethod
    def build_json_prompt(question: str, context: str = "") -> str:
        ctx = f"Contexto:\n{context}\n\n" if context else ""
        return (
            f"{ctx}Problema: {question}\n\n"
            "Raciocine passo a passo e responda com JSON estruturado."
        )

    @staticmethod
    def parse_steps(text: str) -> list[ThoughtStep]:
        """Extrai passos de um texto de raciocínio livre."""
        import re
        steps = []
        pattern = r"(?:Passo|Step)\s*(\d+)[:\.\)]\s*(.+?)(?=(?:Passo|Step)\s*\d+|$)"
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        for num, content in matches:
            lines = content.strip().split("\n")
            thought = lines[0].strip()
            conclusion = " ".join(l.strip() for l in lines[1:] if l.strip())
            steps.append(ThoughtStep(step=int(num), thought=thought, conclusion=conclusion))
        return steps

    @staticmethod
    def few_shot_examples() -> list[str]:
        """Exemplos de CoT para few-shot prompting."""
        return [
            (
                "Pergunta: Devemos expandir para o mercado europeu agora?\n"
                "Passo 1: Analisar prontidão interna — MRR R$500k, time de 8 pessoas, produto maduro\n"
                "Passo 2: Analisar mercado — Europa tem 3x o TAM do Brasil, mas CAC 2x maior\n"
                "Passo 3: Avaliar riscos — GDPR, moeda, suporte timezone\n"
                "Passo 4: Calcular runway — 18 meses, expansão consumiria 6 meses\n"
                "Conclusão: NÃO agora. Esperar atingir R$1M MRR primeiro. Confiança: 80%"
            )
        ]


class ZeroShotCoT:
    """Zero-shot CoT: adiciona 'Pense passo a passo' ao prompt."""

    TRIGGER = "\n\nPense passo a passo antes de responder."

    @staticmethod
    def augment(prompt: str) -> str:
        return prompt + ZeroShotCoT.TRIGGER


class SelfConsistency:
    """
    Self-Consistency: gera N respostas CoT e escolhe a mais frequente.
    Melhora precisão em problemas com resposta definitiva.
    """

    @staticmethod
    def build_prompts(question: str, n: int = 3) -> list[str]:
        base = ChainOfThought.build_prompt(question)
        return [base] * n

    @staticmethod
    def aggregate(answers: list[str]) -> str:
        """Escolhe a resposta mais comum entre N tentativas."""
        from collections import Counter
        # Extrai última linha de cada resposta como conclusão
        conclusions = []
        for ans in answers:
            lines = [l.strip() for l in ans.strip().split("\n") if l.strip()]
            conclusions.append(lines[-1] if lines else ans[:100])

        counter = Counter(conclusions)
        return counter.most_common(1)[0][0]
