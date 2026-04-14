"""
SWARM Agent — ULTIMATE CRONUS
Motor de Pesquisa Massiva com execução paralela.

Uso:
    python swarm_agent.py "tendências de IA em 2026" --depth 3 --parallel 10
    python swarm_agent.py "mercado de SaaS B2B no Brasil" --depth 4 --parallel 8
"""

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from base_agent import BaseAgent

SYSTEM_SWARM = """Você é o SWARM, Motor de Pesquisa Massiva do ULTIMATE CRONUS.
Você decompõe questões complexas em sub-queries focadas, pesquisa cada uma com profundidade
e sintetiza os achados em inteligência acionável.
Seja conciso, factual e sempre conecte achados a oportunidades de negócio."""


@dataclass
class SubQuery:
    id: int
    text: str
    result: str = ""
    score: float = 0.0
    elapsed_ms: int = 0
    error: str = ""


@dataclass
class SwarmResult:
    query: str
    depth: int
    parallel: int
    sub_queries: list = field(default_factory=list)
    synthesis: str = ""
    total_elapsed_ms: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class SwarmAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="SWARM", output_dir="agents/output")

    def research(self, query: str, depth: int = 3, parallel: int = 10) -> SwarmResult:
        """Executa pesquisa massiva paralela sobre um tópico."""
        depth = max(1, min(depth, 5))
        parallel = max(1, min(parallel, 20))

        self.logger.info(f"SWARM iniciado | query='{query[:60]}' | depth={depth} | parallel={parallel}")
        t0 = time.monotonic()

        result = SwarmResult(query=query, depth=depth, parallel=parallel)

        # 1. Decompõe em sub-queries
        sub_queries = self._decompose(query, depth)
        self.logger.info(f"Decomposto em {len(sub_queries)} sub-queries")

        # 2. Pesquisa em paralelo
        sub_queries = self._parallel_research(sub_queries, parallel)

        # 3. Pontua relevância
        sub_queries = self._score_relevance(sub_queries, query)

        # 4. Sintetiza
        result.sub_queries = sub_queries
        result.synthesis = self._synthesise(query, sub_queries)
        result.total_elapsed_ms = int((time.monotonic() - t0) * 1000)

        self.logger.info(f"SWARM completo em {result.total_elapsed_ms}ms")

        # Salva resultado
        path = self.save_result(
            {"query": query, "depth": depth, "parallel": parallel,
             "sub_queries": [asdict(sq) for sq in sub_queries],
             "synthesis": result.synthesis, "elapsed_ms": result.total_elapsed_ms},
            prefix="swarm"
        )
        return result

    def _decompose(self, query: str, depth: int) -> list[SubQuery]:
        count = depth * 3
        prompt = f"""Decomponha a seguinte query de pesquisa em exatamente {count} sub-queries distintas e não-sobrepostas que juntas cobrem o tópico completamente.

Query: {query}

Responda APENAS com um array JSON de strings. Exemplo: ["sub-query 1", "sub-query 2"]"""

        try:
            raw = self.ask(prompt, system=SYSTEM_SWARM, max_tokens=1024)
            start = raw.find("[")
            end = raw.rfind("]") + 1
            texts: list[str] = json.loads(raw[start:end])
        except Exception as e:
            self.logger.warning(f"Decomposição falhou ({e}), usando fallback")
            texts = [f"{query} — aspecto {i+1}" for i in range(max(count, 3))]

        return [SubQuery(id=i, text=t.strip()) for i, t in enumerate(texts[:count])]

    def _research_one(self, sq: SubQuery) -> SubQuery:
        t0 = time.monotonic()
        prompt = f"""Pesquise a seguinte questão com profundidade. Forneça uma resposta concisa mas completa (3-5 parágrafos) com dados, exemplos e insights acionáveis.

Questão: {sq.text}"""
        try:
            sq.result = self.ask(prompt, system=SYSTEM_SWARM, max_tokens=1024)
        except Exception as e:
            sq.error = str(e)
            self.logger.error(f"Sub-query {sq.id} falhou: {e}")
        sq.elapsed_ms = int((time.monotonic() - t0) * 1000)
        return sq

    def _parallel_research(self, sub_queries: list[SubQuery], parallel: int) -> list[SubQuery]:
        completed: list[SubQuery] = []
        with ThreadPoolExecutor(max_workers=parallel, thread_name_prefix="swarm") as ex:
            futures = {ex.submit(self._research_one, sq): sq for sq in sub_queries}
            done = 0
            for future in as_completed(futures):
                try:
                    sq = future.result()
                    completed.append(sq)
                    done += 1
                    self.logger.info(f"  [{done}/{len(sub_queries)}] Sub-query {sq.id} — {sq.elapsed_ms}ms")
                except Exception as e:
                    sq = futures[future]
                    sq.error = str(e)
                    completed.append(sq)
        completed.sort(key=lambda s: s.id)
        return completed

    def _score_relevance(self, sub_queries: list[SubQuery], original_query: str) -> list[SubQuery]:
        successful = [sq for sq in sub_queries if sq.result and not sq.error]
        if not successful:
            return sub_queries

        items = "\n\n".join(f"[{sq.id}] {sq.text}\n{sq.result[:300]}..." for sq in successful)
        prompt = f"""Query original: {original_query}

Avalie a relevância de cada resultado abaixo em uma escala de 0.0 a 1.0.
Responda com um objeto JSON mapeando cada ID (como string) ao seu score.
Exemplo: {{"0": 0.9, "1": 0.6}}

{items}"""

        try:
            raw = self.ask(prompt, system=SYSTEM_SWARM, max_tokens=512)
            start = raw.find("{")
            end = raw.rfind("}") + 1
            scores: dict[str, float] = json.loads(raw[start:end])
            id_map = {sq.id: sq for sq in successful}
            for k, v in scores.items():
                try:
                    id_map[int(k)].score = float(v)
                except (KeyError, ValueError):
                    pass
        except Exception as e:
            self.logger.warning(f"Scoring falhou ({e}), usando 0.5")
            for sq in successful:
                sq.score = 0.5
        return sub_queries

    def _synthesise(self, original_query: str, sub_queries: list[SubQuery]) -> str:
        successful = sorted(
            [sq for sq in sub_queries if sq.result and not sq.error],
            key=lambda s: s.score, reverse=True
        )
        if not successful:
            return "Nenhum resultado disponível para síntese."

        context = "\n\n---\n\n".join(
            f"**{sq.text}** (relevância={sq.score:.2f})\n{sq.result}"
            for sq in successful[:12]
        )
        prompt = f"""Você pesquisou a query: '{original_query}'

Abaixo estão os achados de {len(successful)} sub-queries ordenadas por relevância:

{context}

Sintetize em um relatório de inteligência completo e acionável em Markdown:

# 🔍 SWARM Intelligence Report
## Query: {original_query}

## 📊 Executive Summary
[3-4 linhas com os principais achados]

## 🎯 Key Findings
[bullet points dos achados mais importantes]

## 💡 Oportunidades Identificadas
[oportunidades de negócio concretas]

## ⚠️ Riscos e Ameaças
[riscos identificados]

## 🚀 Ações Recomendadas
[top 5 ações concretas baseadas na pesquisa]

## 📚 Fontes e Referências
[principais fontes mencionadas na pesquisa]"""

        try:
            return self.ask(prompt, system=SYSTEM_SWARM, max_tokens=3000)
        except Exception as e:
            self.logger.error(f"Síntese falhou: {e}")
            return f"Síntese falhou: {e}"


def main():
    parser = argparse.ArgumentParser(description="SWARM — Motor de Pesquisa Massiva ULTIMATE CRONUS")
    parser.add_argument("query", help="Query de pesquisa")
    parser.add_argument("--depth", "-d", type=int, default=3, help="Profundidade (1-5)")
    parser.add_argument("--parallel", "-p", type=int, default=10, help="Workers paralelos (1-20)")
    args = parser.parse_args()

    agent = SwarmAgent()
    result = agent.research(args.query, depth=args.depth, parallel=args.parallel)

    print("\n" + "="*72)
    print(f"SWARM COMPLETO — {result.timestamp}")
    print("="*72)
    print(f"Query    : {result.query}")
    print(f"Depth    : {result.depth}  |  Parallel: {result.parallel}")
    print(f"Sub-queries: {len(result.sub_queries)}")
    print(f"Duração  : {result.total_elapsed_ms/1000:.1f}s")
    print("="*72)
    print("\n--- SÍNTESE ---\n")
    print(result.synthesis)
    print("\n--- SCORES DAS SUB-QUERIES ---")
    for sq in sorted(result.sub_queries, key=lambda s: s.score, reverse=True):
        status = "OK" if not sq.error else "ERR"
        print(f"  [{status}] score={sq.score:.2f} | {sq.text[:80]}")


if __name__ == "__main__":
    main()
