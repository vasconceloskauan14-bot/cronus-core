"""
Episodic Memory — ULTIMATE CRONUS
Memória episódica: registra execuções passadas, resultados e aprendizados.
Permite que agentes aprendam com o histórico de tarefas.
"""

import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Any


@dataclass
class Episode:
    """Uma execução/tarefa completa registrada na memória episódica."""
    id: str
    agent: str
    task: str
    input_summary: str
    output_summary: str
    success: bool
    duration_s: float
    timestamp: float = field(default_factory=time.time)
    tags: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    learnings: list[str] = field(default_factory=list)
    cost_usd: float = 0.0


class EpisodicMemory:
    """
    Registra e recupera episódios de execução dos agentes.
    Persiste em JSON estruturado por agente.

    Uso:
        em = EpisodicMemory("HUNTER")
        ep_id = em.start_episode("Prospectar leads B2B", input_summary="ICP: SaaS BR 50-500 func")
        # ... execução ...
        em.end_episode(ep_id, output_summary="32 leads qualificados", success=True,
                       learnings=["SaaS no RS responde mais rápido", "Evitar segunda-feira"])
    """

    def __init__(self, agent_name: str, persist_dir: str = "agents/memory/episodes"):
        self.agent_name = agent_name
        self._dir = Path(persist_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path = self._dir / f"{agent_name.lower()}_episodes.json"
        self._episodes: list[dict] = self._load()
        self._active: dict[str, dict] = {}

    def _load(self) -> list[dict]:
        if self._path.exists():
            try:
                return json.loads(self._path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return []

    def _save(self):
        self._path.write_text(
            json.dumps(self._episodes, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def start_episode(self, task: str, input_summary: str = "", tags: list[str] | None = None) -> str:
        """Inicia registro de um episódio. Retorna ID."""
        ep_id = f"{self.agent_name}_{int(time.time() * 1000)}"
        self._active[ep_id] = {
            "id": ep_id,
            "agent": self.agent_name,
            "task": task,
            "input_summary": input_summary,
            "output_summary": "",
            "success": False,
            "duration_s": 0.0,
            "timestamp": time.time(),
            "tags": tags or [],
            "metrics": {},
            "learnings": [],
            "cost_usd": 0.0,
            "_start": time.time(),
        }
        return ep_id

    def end_episode(
        self,
        ep_id: str,
        output_summary: str = "",
        success: bool = True,
        learnings: list[str] | None = None,
        metrics: dict | None = None,
        cost_usd: float = 0.0,
    ):
        """Finaliza um episódio e persiste."""
        if ep_id not in self._active:
            return
        ep = self._active.pop(ep_id)
        ep["output_summary"] = output_summary
        ep["success"] = success
        ep["duration_s"] = round(time.time() - ep.pop("_start"), 2)
        ep["learnings"] = learnings or []
        ep["metrics"] = metrics or {}
        ep["cost_usd"] = cost_usd
        self._episodes.append(ep)
        self._save()

    def get_recent(self, n: int = 10, only_successful: bool = False) -> list[dict]:
        """Retorna episódios mais recentes."""
        eps = self._episodes
        if only_successful:
            eps = [e for e in eps if e.get("success")]
        return sorted(eps, key=lambda e: e.get("timestamp", 0), reverse=True)[:n]

    def get_learnings(self, n: int = 20) -> list[str]:
        """Extrai todos os aprendizados registrados."""
        learnings = []
        for ep in sorted(self._episodes, key=lambda e: e.get("timestamp", 0), reverse=True):
            learnings.extend(ep.get("learnings", []))
        # Deduplica mantendo ordem
        seen = set()
        unique = []
        for l in learnings:
            if l not in seen:
                seen.add(l)
                unique.append(l)
        return unique[:n]

    def format_for_prompt(self, n: int = 5) -> str:
        """Formata episódios recentes para incluir no system prompt."""
        recent = self.get_recent(n=n, only_successful=True)
        if not recent:
            return ""

        lines = [f"[Histórico recente — {self.agent_name}]"]
        for ep in recent:
            status = "✓" if ep.get("success") else "✗"
            lines.append(f"{status} {ep['task']}: {ep.get('output_summary', '')[:120]}")

        learnings = self.get_learnings(n=5)
        if learnings:
            lines.append("\n[Aprendizados acumulados]")
            for l in learnings:
                lines.append(f"  • {l}")

        return "\n".join(lines)

    def stats(self) -> dict:
        total = len(self._episodes)
        success = sum(1 for e in self._episodes if e.get("success"))
        total_cost = sum(e.get("cost_usd", 0) for e in self._episodes)
        return {
            "agent":        self.agent_name,
            "total":        total,
            "success_rate": f"{success/total:.1%}" if total else "N/A",
            "total_cost":   f"${total_cost:.4f}",
            "learnings":    len(self.get_learnings(n=1000)),
        }
