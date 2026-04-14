"""
Code Executor Tool — ULTIMATE CRONUS
Executa código Python em subprocesso isolado com timeout e sandbox básico.
"""

import subprocess
import sys
import tempfile
import textwrap
import os
from pathlib import Path
from .base_tool import BaseTool, ToolResult


# Imports proibidos por segurança
BLOCKED_IMPORTS = {
    "os.system", "subprocess", "shutil.rmtree", "ctypes",
    "__import__", "eval(", "exec(", "open('/etc", "open('C:\\Windows",
}


class CodeExecutorTool(BaseTool):
    """
    Executa código Python gerado pelo agente.
    Roda em subprocesso isolado com timeout.
    """

    name = "code_executor"
    description = "Executa código Python e retorna o output. Útil para análises, cálculos e processamento de dados."

    def __init__(self, timeout: int = 30, max_output: int = 10_000):
        self.timeout = timeout
        self.max_output = max_output

    def _is_safe(self, code: str) -> tuple[bool, str]:
        """Verificação básica de segurança."""
        code_lower = code.lower()
        danger_patterns = [
            "rmdir", "shutil.rmtree", "os.remove", "os.unlink",
            "format(", "subprocess.call", "subprocess.run",
            "__import__('os').system", "open('/etc/passwd",
        ]
        for pattern in danger_patterns:
            if pattern in code_lower:
                return False, f"Padrão perigoso detectado: '{pattern}'"
        return True, ""

    def run(self, code: str, timeout: int = 0) -> ToolResult:
        """
        Executa código Python.
        Args:
            code: Código Python a executar
            timeout: Timeout em segundos (default: self.timeout)
        """
        t = timeout or self.timeout

        # Verificação de segurança
        safe, reason = self._is_safe(code)
        if not safe:
            return ToolResult(success=False, output="", error=f"Código bloqueado: {reason}")

        # Escrever código em arquivo temporário
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(textwrap.dedent(code))
            tmp_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True,
                text=True,
                timeout=t,
                cwd=tempfile.gettempdir(),
            )
            stdout = result.stdout[:self.max_output]
            stderr = result.stderr[:2000]

            if result.returncode == 0:
                return ToolResult(
                    success=True,
                    output=stdout or "(sem output)",
                    metadata={"returncode": 0, "stderr": stderr},
                )
            else:
                return ToolResult(
                    success=False,
                    output=stdout,
                    error=stderr or f"Exit code: {result.returncode}",
                    metadata={"returncode": result.returncode},
                )
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, output="", error=f"Timeout após {t}s")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    def schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Código Python a executar"},
                    "timeout": {"type": "integer", "description": "Timeout em segundos", "default": 30},
                },
                "required": ["code"],
            },
        }
