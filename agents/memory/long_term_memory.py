"""
Long-Term Memory — ULTIMATE CRONUS
Memória semântica persistente para agentes.
Armazena conhecimento, decisões, aprendizados e recupera por similaridade.
"""

import json
import time
from pathlib import Path
from typing import Any

from .vector_store import create_vector_store


class LongTermMemory:
    """
    Memória de longo prazo com busca semântica.
    Agentes podem SALVAR fatos/decisões e BUSCAR por contexto.

    Exemplo:
        mem = LongTermMemory("HUNTER")
        mem.remember("Lead XYZ tem budget de R$50k e decide em março", tags=["lead", "XYZ"])
        results = mem.recall("leads com budget alto")
    """

    def __init__(self, agent_name: str, persist_dir: str = "agents/memory/db"):
        self.agent_name = agent_name
        self._store = create_vector_store(
            name=f"ltm_{agent_name.lower()}",
            persist_dir=persist_dir,
        )

    def remember(
        self,
        text: str,
        category: str = "fact",
        tags: list[str] | None = None,
        importance: int = 5,
        source: str = "",
    ) -> str:
        """
        Salva um fato/memória.

        Args:
            text:       Conteúdo a lembrar
            category:   Tipo: 'fact', 'decision', 'insight', 'lead', 'metric', 'error'
            tags:       Tags para filtragem
            importance: 1-10, importância relativa
            source:     Origem da informação

        Returns:
            ID da memória criada
        """
        metadata = {
            "agent":      self.agent_name,
            "category":   category,
            "tags":       json.dumps(tags or []),
            "importance": importance,
            "source":     source,
            "timestamp":  time.time(),
        }
        doc_id = self._store.add(text=text, metadata=metadata)
        return doc_id

    def recall(
        self,
        query: str,
        n: int = 5,
        category: str = "",
        min_importance: int = 0,
    ) -> list[dict]:
        """
        Busca memórias relevantes por similaridade semântica.

        Args:
            query:          O que buscar
            n:              Máximo de resultados
            category:       Filtrar por categoria
            min_importance: Importância mínima (0 = sem filtro)

        Returns:
            Lista de memórias ordenadas por relevância
        """
        filter_meta = {}
        if category:
            filter_meta["category"] = category

        results = self._store.search(query=query, n=n * 2, filter_meta=filter_meta or None)

        # Filtrar por importância mínima
        if min_importance > 0:
            results = [
                r for r in results
                if r.get("metadata", {}).get("importance", 0) >= min_importance
            ]

        return results[:n]

    def recall_as_context(self, query: str, n: int = 5) -> str:
        """
        Retorna memórias relevantes formatadas para incluir no prompt.
        """
        memories = self.recall(query, n=n)
        if not memories:
            return ""

        lines = [f"[Memória de longo prazo — {self.agent_name}]"]
        for i, mem in enumerate(memories, 1):
            cat = mem.get("metadata", {}).get("category", "fact")
            score = mem.get("score", 0)
            lines.append(f"{i}. [{cat}] (relevância: {score:.2f}) {mem['text']}")

        return "\n".join(lines)

    def forget(self, doc_id: str) -> bool:
        """Remove uma memória específica."""
        return self._store.delete(doc_id)

    def stats(self) -> dict:
        return {
            "agent":  self.agent_name,
            "total":  self._store.count(),
        }

    def dump(self, n: int = 20) -> list[dict]:
        """Retorna as memórias mais recentes (debug)."""
        return self._store.search("", n=n)
