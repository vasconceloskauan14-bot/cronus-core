"""
Calculator Tool — ULTIMATE CRONUS
Avalia expressões matemáticas e financeiras com segurança.
"""

import math
import re
from .base_tool import BaseTool, ToolResult


# Funções permitidas no contexto de avaliação
_SAFE_GLOBALS = {
    "__builtins__": {},
    "abs": abs, "round": round, "min": min, "max": max,
    "sum": sum, "pow": pow, "int": int, "float": float,
    # Math
    "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
    "exp": math.exp, "ceil": math.ceil, "floor": math.floor,
    "pi": math.pi, "e": math.e, "inf": math.inf,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
}


class CalculatorTool(BaseTool):
    """
    Avalia expressões matemáticas e financeiras.
    Seguro: usa contexto restrito sem acesso ao sistema.
    """

    name = "calculator"
    description = (
        "Calcula expressões matemáticas e financeiras. "
        "Ex: '1000 * 1.1 ** 5', 'sqrt(144)', 'log(1000, 10)'."
    )

    def run(self, expression: str, variables: dict | None = None) -> ToolResult:
        """
        Avalia expressão matemática.
        Args:
            expression: Expressão a avaliar (ex: '1000 * 1.1 ** 5')
            variables:  Variáveis extras (ex: {'mrr': 50000, 'growth': 0.1})
        """
        # Sanitizar: permitir apenas chars matemáticos
        clean = re.sub(r"[^0-9+\-*/().,%\s_a-zA-Z]", "", expression)
        if not clean.strip():
            return ToolResult(success=False, output=None, error="Expressão vazia ou inválida")

        ctx = dict(_SAFE_GLOBALS)
        if variables:
            ctx.update({k: v for k, v in variables.items() if isinstance(v, (int, float))})

        try:
            result = eval(clean, ctx)  # noqa: S307 — contexto restrito
            return ToolResult(
                success=True,
                output=result,
                metadata={"expression": clean, "result": result},
            )
        except ZeroDivisionError:
            return ToolResult(success=False, output=None, error="Divisão por zero")
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))

    def financial(self, principal: float, rate: float, periods: int,
                  pmt: float = 0) -> ToolResult:
        """
        Cálculos financeiros: VF, VP, CAGR.
        Args:
            principal: Capital inicial
            rate:      Taxa por período (decimal, ex: 0.10 = 10%)
            periods:   Número de períodos
            pmt:       Pagamento por período (0 para juros compostos simples)
        """
        try:
            fv = principal * (1 + rate) ** periods
            if pmt:
                fv += pmt * (((1 + rate) ** periods - 1) / rate)
            pv = fv / (1 + rate) ** periods
            cagr = (fv / principal) ** (1 / periods) - 1 if periods > 0 else 0

            return ToolResult(
                success=True,
                output={
                    "valor_futuro": round(fv, 2),
                    "valor_presente": round(pv, 2),
                    "cagr": f"{cagr:.2%}",
                    "retorno_total": f"{(fv/principal - 1):.2%}",
                },
                metadata={"principal": principal, "rate": rate, "periods": periods},
            )
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))

    def schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Expressão matemática a calcular"},
                    "variables":  {"type": "object", "description": "Variáveis opcionais (ex: {'mrr': 50000})"},
                },
                "required": ["expression"],
            },
        }
