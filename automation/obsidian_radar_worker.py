from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import sys
import textwrap
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock, Semaphore


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agents.providers.base_provider import CompletionRequest, Message
from agents.providers.factory import ProviderFactory
from agents.tools.web_search import WebSearchTool
from automation.obsidian_memory_store import ObsidianMemoryStore
from automation.rate_limiter import wait_for_slot


DEFAULT_CONFIG_PATH = ROOT / "config" / "obsidian_radar.json"
DEFAULT_STATE_PATH = ROOT / "state" / "obsidian_radar_state.json"


def _load_dotenv(env_path: Path) -> None:
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _resolve_vault_path(raw_value: str) -> Path:
    base_value = raw_value.strip() or "obsidian-ai-vault"
    path = Path(base_value)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def _slugify(value: str) -> str:
    normalized = value.casefold()
    allowed = [char if char.isalnum() else "-" for char in normalized]
    slug = "".join(allowed)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "tema"


def _read_json(path: Path, fallback: dict) -> dict:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


DEFAULT_CONFIG = {
    "enabled": True,
    "loop_minutes": 120,
    "max_topics_per_cycle": 2,
    "research_agents": 1,
    "max_parallel_searches": 12,
    "search_backend": "fallback",
    "search_min_interval_seconds": 8,
    "max_results_per_topic": 5,
    "queries_per_topic": 8,
    "query_agents_per_topic": 1,
    "query_pause_min_seconds": 20,
    "pause_between_topics_seconds": 60,
    "seen_urls_window": 120,
    "seen_queries_window": 48,
    "feed_summary_items": 6,
    "use_ai_provider": True,
    "ai_cooldown_after_rate_limit_minutes": 30,
    "topic_default_cadence_hours": 8,
    "topics": [
        {
            "name": "IA e automacao",
            "query": "novidades em IA agentes MCP automacao empresarial ferramentas",
            "folder": "Memoria/Radar/IA-e-automacao",
            "notes": "Priorize sinais praticos, ferramentas, integracoes, modelos locais, agent runners e automacao util.",
            "cadence_hours": 6,
            "priority": 10,
            "enabled": True,
        },
        {
            "name": "Mercado e oportunidades",
            "query": "novas oportunidades de negocio IA SaaS automacao pequenas empresas",
            "folder": "Memoria/Radar/Mercado-e-oportunidades",
            "notes": "Foque em oportunidades claras de produto, servico, nicho, dor urgente e demanda crescente.",
            "cadence_hours": 8,
            "priority": 7,
            "enabled": True,
        },
    ],
}


class ObsidianRadarWorker:
    def __init__(
        self,
        vault_path: Path,
        config_path: Path,
        state_path: Path,
        provider_alias: str = "",
        model: str = "",
        temperature: float = 0.3,
    ):
        self.vault_path = vault_path
        self.config_path = config_path
        self.state_path = state_path
        self.temperature = temperature

        self.store = ObsidianMemoryStore(vault_path=self.vault_path)
        self.store.bootstrap()
        self.search_tool = WebSearchTool(max_results=20)
        os.environ.setdefault("CRONUS_NO_PROVIDER_RETRY_ON_429", "1")
        self.provider_alias = provider_alias or os.environ.get("OBSIDIAN_AI_PROVIDER", "") or os.environ.get("CRONUS_PROVIDER", "") or "openai"
        self.model = model or os.environ.get("OBSIDIAN_AI_MODEL", "")
        self.provider = ProviderFactory.create(
            provider_alias=self.provider_alias,
            model=self.model,
            agent_name="OBSIDIAN_RADAR",
        )
        self._provider_lock = Lock()
        self._ai_cooldown_until = 0.0
        self._search_slot_lock = Lock()
        self._search_parallel_limit = 12
        self._search_slots = Semaphore(self._search_parallel_limit)

        self._ensure_config()

    def _ensure_config(self) -> None:
        if self.config_path.exists():
            return
        _write_json(self.config_path, DEFAULT_CONFIG)

    def _complete_with_provider(self, request: CompletionRequest):
        if self._is_ai_cooling_down():
            remaining = int(self._ai_cooldown_until - time.time())
            raise RuntimeError(f"provider em cooldown por rate limit ({remaining}s restantes)")
        with self._provider_lock:
            try:
                return self.provider.complete(request)
            except Exception as exc:
                lowered = str(exc).lower()
                if "429" in lowered or "rate limit" in lowered or "too many requests" in lowered:
                    self._start_ai_cooldown(str(exc))
                raise

    def _is_ai_cooling_down(self) -> bool:
        return time.time() < self._ai_cooldown_until

    def _start_ai_cooldown(self, reason: str) -> None:
        config = self.load_config()
        minutes = max(int(config.get("ai_cooldown_after_rate_limit_minutes", 30)), 1)
        self._ai_cooldown_until = time.time() + minutes * 60
        print(f"[radar] IA em cooldown por {minutes} min apos rate limit: {reason}")

    def load_config(self) -> dict:
        cfg = _read_json(self.config_path, DEFAULT_CONFIG)
        cfg.setdefault("enabled", True)
        cfg.setdefault("loop_minutes", 120)
        cfg.setdefault("max_topics_per_cycle", 2)
        cfg.setdefault("research_agents", 1)
        cfg.setdefault("max_parallel_searches", 12)
        cfg.setdefault("search_backend", "fallback")
        cfg.setdefault("search_min_interval_seconds", 8)
        cfg.setdefault("max_results_per_topic", 5)
        cfg.setdefault("queries_per_topic", 8)
        cfg.setdefault("query_agents_per_topic", 1)
        cfg.setdefault("query_pause_min_seconds", 20)
        cfg.setdefault("pause_between_topics_seconds", 60)
        cfg.setdefault("seen_urls_window", 120)
        cfg.setdefault("seen_queries_window", 48)
        cfg.setdefault("feed_summary_items", 6)
        cfg.setdefault("use_ai_provider", True)
        cfg.setdefault("ai_cooldown_after_rate_limit_minutes", 30)
        cfg.setdefault("topic_default_cadence_hours", 8)
        cfg.setdefault("topics", [])
        return cfg

    def load_state(self) -> dict:
        state = _read_json(self.state_path, {"topics": {}, "last_cycle_at": ""})
        state.setdefault("topics", {})
        state.setdefault("last_cycle_at", "")
        return state

    def save_state(self, state: dict) -> None:
        _write_json(self.state_path, state)

    def _set_search_parallel_limit(self, limit: int) -> None:
        normalized_limit = max(int(limit), 1)
        with self._search_slot_lock:
            if normalized_limit == self._search_parallel_limit:
                return
            self._search_parallel_limit = normalized_limit
            self._search_slots = Semaphore(normalized_limit)

    def run_forever(self) -> None:
        while True:
            config = self.load_config()
            if not config.get("enabled", True):
                print("Radar desativado no config. Aguardando proxima verificacao.")
            else:
                try:
                    self.run_cycle()
                except Exception as exc:
                    print(f"[radar] erro no ciclo: {exc}")

            loop_minutes = max(int(config.get("loop_minutes", 120)), 5)
            print(f"Aguardando {loop_minutes} minuto(s) para a proxima rodada.")
            time.sleep(loop_minutes * 60)

    def run_cycle(self) -> dict:
        config = self.load_config()
        state = self.load_state()

        selected_topics = self._pick_topics(config=config, state=state)
        results: list[dict] = []
        research_agents = max(int(config.get("research_agents", 1)), 1)
        pause_between_topics = max(int(config.get("pause_between_topics_seconds", 60)), 0)
        max_parallel_searches = max(int(config.get("max_parallel_searches", 12)), 1)
        self._set_search_parallel_limit(max_parallel_searches)
        if hasattr(self.search_tool, "configure"):
            self.search_tool.configure(
                duckduckgo_backend=str(config.get("search_backend", "fallback")).strip() or "fallback",
                min_interval_seconds=max(float(config.get("search_min_interval_seconds", 8)), 0.0),
            )

        if not selected_topics:
            state["last_cycle_at"] = datetime.now().isoformat(timespec="seconds")
            self.save_state(state)
            summary = {
                "ok": True,
                "processed_topics": 0,
                "results": [],
                "last_cycle_at": state["last_cycle_at"],
            }
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            return summary

        if research_agents > 1 and len(selected_topics) > 1:
            parallelism = min(research_agents, len(selected_topics))
            print(
                f"[radar] executando {len(selected_topics)} topico(s) com "
                f"{parallelism} agente(s) de pesquisa em paralelo "
                f"| teto global de buscas simultaneas: {max_parallel_searches}"
            )
            ordered_outcomes: list[dict | None] = [None] * len(selected_topics)
            with ThreadPoolExecutor(max_workers=parallelism) as executor:
                future_map = {}
                for idx, topic in enumerate(selected_topics):
                    topic_key = _slugify(topic.get("name", "tema"))
                    topic_state = copy.deepcopy(state["topics"].get(topic_key, {}))
                    future = executor.submit(self._process_topic, topic, config, topic_state)
                    future_map[future] = idx

                for future in as_completed(future_map):
                    idx = future_map[future]
                    topic = selected_topics[idx]
                    topic_key = _slugify(topic.get("name", "tema"))
                    try:
                        ordered_outcomes[idx] = future.result()
                    except Exception as exc:
                        ordered_outcomes[idx] = {
                            "topic": str(topic.get("name", "Tema sem nome")),
                            "topic_key": topic_key,
                            "ok": False,
                            "error": str(exc),
                            "topic_state": copy.deepcopy(state["topics"].get(topic_key, {})),
                        }

            for outcome in ordered_outcomes:
                if not outcome:
                    continue
                self._finalize_topic_outcome(outcome=outcome, state=state)
                self.save_state(state)
                results.append(self._public_outcome(outcome))

            state["last_cycle_at"] = datetime.now().isoformat(timespec="seconds")
            self.save_state(state)

            summary = {
                "ok": True,
                "processed_topics": len(selected_topics),
                "results": results,
                "last_cycle_at": state["last_cycle_at"],
            }
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            return summary

        if research_agents <= 1 or len(selected_topics) <= 1:
            for idx, topic in enumerate(selected_topics):
                topic_key = _slugify(topic.get("name", "tema"))
                topic_state = copy.deepcopy(state["topics"].get(topic_key, {}))
                outcome = self._process_topic(topic=topic, config=config, topic_state=topic_state)
                self._finalize_topic_outcome(outcome=outcome, state=state)
                self.save_state(state)
                results.append(self._public_outcome(outcome))
                if idx < len(selected_topics) - 1 and pause_between_topics:
                    print(f"[radar] pausa {pause_between_topics}s antes do proximo topico...")
                    time.sleep(pause_between_topics)
        state["last_cycle_at"] = datetime.now().isoformat(timespec="seconds")
        self.save_state(state)

        summary = {
            "ok": True,
            "processed_topics": len(selected_topics),
            "results": results,
            "last_cycle_at": state["last_cycle_at"],
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return summary

    def _public_outcome(self, outcome: dict) -> dict:
        return {
            key: value
            for key, value in outcome.items()
            if key not in {"topic_state", "topic_key", "feed_payload", "notification"}
        }

    def _finalize_topic_outcome(self, outcome: dict, state: dict) -> None:
        topic_key = str(outcome.get("topic_key", "")).strip()
        topic_state = outcome.get("topic_state")
        if topic_key and isinstance(topic_state, dict):
            state["topics"][topic_key] = topic_state

        feed_payload = outcome.get("feed_payload")
        if isinstance(feed_payload, dict) and feed_payload:
            self._append_to_feed(**feed_payload)

        notification = outcome.get("notification")
        if isinstance(notification, dict) and notification:
            self._notify(
                title=str(notification.get("title", "CRONUS")),
                message=str(notification.get("message", "")),
            )

    def _pick_topics(self, config: dict, state: dict) -> list[dict]:
        topics = [topic for topic in config.get("topics", []) if topic.get("enabled", True)]
        ranked: list[tuple[float, dict]] = []
        now = datetime.now()
        default_cadence = max(float(config.get("topic_default_cadence_hours", 8)), 0)

        for topic in topics:
            topic_key = _slugify(topic.get("name", "tema"))
            topic_state = state["topics"].get(topic_key, {})
            last_run_at = topic_state.get("last_run_at", "")
            cadence_hours = max(float(topic.get("cadence_hours", default_cadence)), 0)

            due_score = 9999.0
            if last_run_at:
                try:
                    last_run = datetime.fromisoformat(last_run_at)
                    due_in = last_run + timedelta(hours=cadence_hours) - now
                    due_score = due_in.total_seconds()
                except ValueError:
                    due_score = -1.0
            else:
                due_score = -1.0

            priority = int(topic.get("priority", 0))
            ranked.append((due_score - priority * 60.0, topic))

        ranked.sort(key=lambda item: item[0])
        limit = max(int(config.get("max_topics_per_cycle", 2)), 1)
        return [item[1] for item in ranked[:limit]]

    # Perspectivas rotacionadas a cada ciclo — garante ângulos diferentes
    _PERSPECTIVES = [
        "dados recentes: preços, estatísticas, tamanho de mercado, números concretos",
        "tendências e novidades: o que está crescendo, caindo ou mudando no setor",
        "comparações e rankings: quem lidera, diferenças entre opções, benchmarks",
        "casos reais e exemplos: histórias, posts, resultados, experiências concretas",
        "problemas e dores: reclamações, o que falta, o que é difícil, frustrações",
        "discussões reais: reddit, fóruns, comunidades, o que as pessoas estão dizendo",
        "modelos de negócio e monetização: como ganhar dinheiro, estratégias, pacotes",
        "notícias e lançamentos: o que mudou recentemente, novos players, ferramentas",
    ]

    def _read_vault_insights(self, topic: dict) -> str:
        """Lê as últimas notas do vault para este tópico e extrai achados-chave."""
        folder_raw = str(topic.get("folder", "")).strip()
        if not folder_raw:
            return ""
        folder = self.vault_path / folder_raw
        if not folder.exists():
            return ""
        notes = sorted(folder.rglob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
        if not notes:
            return ""
        excerpts = []
        for note in notes:
            try:
                text = note.read_text(encoding="utf-8", errors="ignore")
                # pega as 8 primeiras linhas não-vazias após o frontmatter
                lines = [l.strip() for l in text.split("---", 2)[-1].splitlines() if l.strip()]
                excerpts.append("\n".join(lines[:8]))
            except Exception:
                continue
        return "\n\n---\n".join(excerpts)

    def _generate_sub_queries(self, topic: dict, seen_queries: list[str], config: dict, cycle_index: int = 0) -> list[str]:
        """Gera 8 queries NOVAS aprendendo com o vault, evitando repetir o que já foi pesquisado."""
        topic_name = str(topic.get("name", ""))
        base_query = str(topic.get("query", topic_name)).strip()
        guidance = str(topic.get("notes", "")).strip()
        queries_per_topic = max(int(config.get("queries_per_topic", 8)), 4)
        use_ai_provider = bool(config.get("use_ai_provider", True))

        now = datetime.now()
        year = now.strftime("%Y")

        # Perspectiva desta rodada (rotaciona a cada ciclo)
        perspective = self._PERSPECTIVES[cycle_index % len(self._PERSPECTIVES)]

        # Últimas queries para evitar repetição
        recent_queries = seen_queries[-10:] if seen_queries else []
        recent_block = "\n".join(f"- {q}" for q in recent_queries) if recent_queries else "Nenhuma ainda."

        # Lê o cérebro do vault para gerar queries mais inteligentes
        vault_context = self._read_vault_insights(topic)
        vault_block = vault_context[:600] if vault_context else "Nenhuma nota anterior encontrada."

        if not use_ai_provider or not self.provider.is_available() or self._is_ai_cooling_down():
            fallback_queries = [
                f"{base_query} {year}",
                f"{base_query} brasil mercado {year}",
                f"{base_query} reddit forum discussion",
                f"{base_query} preços valores cobrados freelancer",
                f"{base_query} tendências crescimento percentual {year}",
                f"site:reddit.com {base_query}",
                f"{base_query} salario remuneracao media",
                f"{base_query} plataformas contratacao fiverr upwork",
            ]
            return fallback_queries[:queries_per_topic]

        try:
            wait_for_slot("radar:sub_queries")
            completion = self._complete_with_provider(CompletionRequest(
                system="Você é um pesquisador especialista. Cria buscas web variadas, profundas e originais que descobrem ângulos NOVOS ainda não pesquisados.",
                messages=[Message(role="user", content=textwrap.dedent(f"""\
                    Tema: {topic_name}
                    Query base: {base_query}
                    Foco: {guidance or 'pesquisa geral'}
                    Data: {now.strftime('%Y-%m-%d')}
                    Perspectiva desta rodada: {perspective}

                    O QUE O VAULT JÁ SABE (evite repetir esses achados, busque lacunas):
                    {vault_block}

                    QUERIES JÁ USADAS — NÃO repita:
                    {recent_block}

                    Gere exatamente {queries_per_topic} queries NOVAS que exploram ÂNGULOS DIFERENTES e cobrem lacunas do vault.

                    Obrigatório:
                    - 2 queries com o ano {year}
                    - 1 query em português brasileiro com dados do Brasil
                    - 1 query com "reddit" ou "forum" ou "community"
                    - 1 query buscando PORCENTAGENS/ESTATÍSTICAS ("% growth", "market share", "statistics")
                    - 1 query buscando PLATAFORMAS específicas (fiverr, upwork, workana, 99freelas)
                    - 1 query buscando PREÇOS/SALÁRIOS reais
                    - 1 query sobre NICHO ESPECÍFICO dentro do tema

                    Retorne SOMENTE as {queries_per_topic} queries, uma por linha, sem numeração nem explicação.
                """))],
                temperature=0.85,
                max_tokens=400,
                model=self.model,
            ))
            queries = [q.strip() for q in completion.text.strip().splitlines() if q.strip()]
            return queries[:queries_per_topic] if queries else [f"{base_query} {year}"]
        except Exception as exc:
            print(f"[radar] sub_queries falhou ({exc}), usando queries padrão")
            fallback_queries = [
                f"{base_query} {year}",
                f"{base_query} brasil mercado {year}",
                f"{base_query} reddit forum discussion",
                f"{base_query} preços valores cobrados freelancer",
                f"{base_query} tendências crescimento percentual {year}",
                f"site:reddit.com {base_query}",
                f"{base_query} salario remuneracao media",
                f"{base_query} plataformas contratacao fiverr upwork",
            ]
            return fallback_queries[:queries_per_topic]

    def _telegram_notify(self, title: str, message: str) -> None:
        """Envia notificação via Telegram bot (funciona no Railway/Linux)."""
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        if not token or not chat_id:
            return
        try:
            import urllib.request
            text = f"🎯 *{title}*\n\n{message}"[:4096]
            payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}).encode()
            req = urllib.request.Request(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=10)
        except Exception:
            pass

    def _notify(self, title: str, message: str) -> None:
        """Envia notificação via Telegram. Balloon tip Windows removido — causava flash de CMD."""
        self._telegram_notify(title, message)

    def _run_search_query(
        self,
        topic_name: str,
        query: str,
        query_index: int,
        total_queries: int,
        max_results: int,
    ) -> list[dict]:
        self._search_slots.acquire()
        try:
            print(f"[radar] [{topic_name}] busca {query_index}/{total_queries}: {query[:80]}")
            result = self.search_tool.run(query=query, max_results=max_results)
            if not result.success or not isinstance(result.output, list):
                if result.error:
                    print(f"[radar] [{topic_name}] busca falhou: {result.error}")
                return []
            return result.output
        finally:
            self._search_slots.release()

    def _collect_query_results(
        self,
        topic_name: str,
        sub_queries: list[str],
        seen_urls: set[str],
        max_results: int,
        pause_seconds: int,
        query_agents: int,
    ) -> tuple[list[dict], set[str]]:
        all_items: list[dict] = []
        all_new_urls: set[str] = set()
        total_queries = len(sub_queries)

        if total_queries == 0:
            return all_items, all_new_urls

        batch_size = max(1, min(query_agents, total_queries))
        batch_pause_seconds = pause_seconds if batch_size == 1 else max(int(pause_seconds / batch_size), 1)

        for start in range(0, total_queries, batch_size):
            batch = sub_queries[start : start + batch_size]
            batch_number = (start // batch_size) + 1
            total_batches = (total_queries + batch_size - 1) // batch_size
            if batch_size > 1:
                print(
                    f"[radar] [{topic_name}] lote {batch_number}/{total_batches} com "
                    f"{len(batch)} agente(s) de busca"
                )

            with ThreadPoolExecutor(max_workers=len(batch)) as executor:
                future_map = {}
                for offset, query in enumerate(batch):
                    query_index = start + offset + 1
                    future = executor.submit(
                        self._run_search_query,
                        topic_name,
                        query,
                        query_index,
                        total_queries,
                        max_results,
                    )
                    future_map[future] = query

                for future in as_completed(future_map):
                    try:
                        batch_items = future.result()
                    except Exception as exc:
                        print(f"[radar] [{topic_name}] lote com erro: {exc}")
                        continue

                    for item in batch_items:
                        url = str(item.get("url", "")).strip()
                        if url and url not in seen_urls and url not in all_new_urls:
                            all_items.append(item)
                            all_new_urls.add(url)

            if start + batch_size < total_queries and batch_pause_seconds > 0:
                print(f"[radar] [{topic_name}] aguardando {batch_pause_seconds}s antes do proximo lote...")
                time.sleep(batch_pause_seconds)

        return all_items, all_new_urls

    def _process_topic(self, topic: dict, config: dict, topic_state: dict) -> dict:
        topic_name = str(topic.get("name", "Tema sem nome"))
        topic_key = _slugify(topic_name)
        topic_state = copy.deepcopy(topic_state or {})
        # Mantem uma janela ajustavel: memoria suficiente sem deixar o state crescer sem limite.
        seen_urls_window = max(int(config.get("seen_urls_window", 120)), 20)
        seen_queries_window = max(int(config.get("seen_queries_window", 48)), 8)
        topic_state["seen_urls"] = topic_state.get("seen_urls", [])[-seen_urls_window:]
        topic_state["seen_queries"] = topic_state.get("seen_queries", [])[-seen_queries_window:]
        seen_urls = set(topic_state["seen_urls"])
        seen_queries: list[str] = topic_state["seen_queries"]
        cycle_index: int = topic_state.get("cycle_index", 0)
        deep_minutes = int(config.get("deep_research_minutes", 40))
        max_results = max(int(config.get("max_results_per_topic", 8)), 1)
        query_agents = max(int(config.get("query_agents_per_topic", 1)), 1)

        # Gera ângulos de busca NOVOS (evita repetir queries já usadas)
        sub_queries = self._generate_sub_queries(topic, seen_queries=seen_queries, config=config, cycle_index=cycle_index)
        total_queries = len(sub_queries)
        pause_seconds = max(int((deep_minutes * 60) / total_queries), max(int(config.get("query_pause_min_seconds", 20)), 0))

        print(f"[radar] '{topic_name}': {total_queries} buscas, ~{pause_seconds}s entre cada uma (~{deep_minutes} min total)")

        all_items, all_new_urls = self._collect_query_results(
            topic_name=topic_name,
            sub_queries=sub_queries,
            seen_urls=seen_urls,
            max_results=max_results,
            pause_seconds=pause_seconds,
            query_agents=query_agents,
        )

        if not all_items:
            topic_state["last_run_at"] = datetime.now().isoformat(timespec="seconds")
            topic_state["last_error"] = "nenhum resultado novo encontrado"
            # Salva as queries mesmo sem resultado para não repetir na próxima rodada
            updated_queries = seen_queries + sub_queries
            topic_state["seen_queries"] = updated_queries[-seen_queries_window:]
            topic_state["cycle_index"] = cycle_index + 1
            return {
                "topic": topic_name,
                "topic_key": topic_key,
                "ok": False,
                "error": "nenhum resultado novo",
                "topic_state": topic_state,
            }

        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        note_title = f"Radar - {topic_name} - {datetime.now().strftime('%Y-%m-%d %H%M')}"
        folder = str(topic.get("folder", f"Memoria/Radar/{topic_key}")).strip() or f"Memoria/Radar/{topic_key}"
        folder = f"{folder}/{datetime.now().strftime('%Y-%m-%d')}"

        note_content = self._build_note(
            topic=topic,
            items=all_items,
            generated_at=generated_at,
            sub_queries=sub_queries,
            config=config,
        )
        note_path = self.store.create_note(title=note_title, content=note_content, folder=folder)

        topic_state["last_run_at"] = datetime.now().isoformat(timespec="seconds")
        topic_state["last_note_path"] = note_path.relative_to(self.vault_path).as_posix()
        topic_state["last_error"] = ""
        merged_urls = list(seen_urls.union(all_new_urls))
        topic_state["seen_urls"] = merged_urls[-seen_urls_window:]

        # Salva as queries usadas neste ciclo para evitar repetição futura
        updated_queries = seen_queries + sub_queries
        topic_state["seen_queries"] = updated_queries[-seen_queries_window:]
        topic_state["cycle_index"] = cycle_index + 1

        print(f"[radar] '{topic_name}' concluído: {len(all_items)} fontes coletadas")

        # Adiciona bloco novo no feed diário
        now_str = datetime.now().strftime("%H:%M")
        return {
            "topic": topic_name,
            "topic_key": topic_key,
            "ok": True,
            "note_path": topic_state["last_note_path"],
            "results_found": len(all_items),
            "sub_queries": total_queries,
            "provider_ready": self.provider.is_available(),
            "topic_state": topic_state,
            "feed_payload": {
                "topic_name": topic_name,
                "items": all_items,
                "sub_queries": sub_queries,
                "note_path": topic_state["last_note_path"],
                "generated_at": generated_at,
            },
            "notification": {
                "title": f"CRONUS - Nova pesquisa ({now_str})",
                "message": f"{topic_name}: {len(all_items)} fontes coletadas e salvas no Obsidian.",
            },
        }
    def _append_to_feed(
        self,
        topic_name: str,
        items: list[dict],
        sub_queries: list[str],
        note_path: str,
        generated_at: str,
    ) -> None:
        """Acrescenta um bloco novo ao feed diário do Obsidian a cada pesquisa concluída."""
        now = datetime.now()
        feed_folder = self.vault_path / "Memoria" / "Feed"
        feed_folder.mkdir(parents=True, exist_ok=True)
        feed_file = feed_folder / f"feed-{now.strftime('%Y-%m-%d')}.md"

        # Resumo direto das fontes — sem chamada extra à API
        summary_items = max(int(self.load_config().get("feed_summary_items", 6)), 3)
        snippets = [
            f"- **{it.get('title', 'Sem título')}** — {it.get('snippet', '')[:150]}"
            for it in items[:summary_items]
        ]
        summary_text = "\n".join(snippets) if snippets else f"{len(items)} fontes coletadas."

        queries_inline = " · ".join(f"`{q}`" for q in sub_queries[:3])
        note_name = note_path.split("/")[-1].replace(".md", "")
        block = textwrap.dedent(f"""\

            ---

            ## {now.strftime('%H:%M')} — {topic_name}

            {summary_text}

            > Buscas: {queries_inline}
            > [[{note_name}]]
        """)

        if not feed_file.exists():
            yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
            yesterday_link = f"← [[feed-{yesterday}]]" if (feed_folder / f"feed-{yesterday}.md").exists() else ""
            header = (
                f"# Feed de Pesquisas — {now.strftime('%d/%m/%Y')}\n"
                f"_Atualizado automaticamente pelo CRONUS Radar_ {yesterday_link}\n"
            )
            self.store.atomic_write_text(feed_file, header + block)
        else:
            existing = feed_file.read_text(encoding="utf-8", errors="ignore")
            self.store.atomic_write_text(feed_file, existing + block)

        print(f"[radar] feed atualizado: {feed_file.name}")

    def _build_note(
        self,
        topic: dict,
        items: list[dict],
        generated_at: str,
        sub_queries: list[str] | None = None,
        config: dict | None = None,
    ) -> str:
        topic_name = str(topic.get("name", "Tema"))
        guidance = str(topic.get("notes", "")).strip()
        memory_context, memory_hits = self.store.build_context(f"{topic_name}\n{guidance}", limit=10, max_chars=4000)
        queries_block = "\n".join(f"- {q}" for q in (sub_queries or [])) or "- busca padrão"

        use_ai_provider = bool((config or {}).get("use_ai_provider", True))
        if use_ai_provider and self.provider.is_available() and not self._is_ai_cooling_down():
            # Limita fontes para controlar tokens de entrada
            items_for_ai = items[:6]
            sources_block = self._format_sources(items_for_ai)

            system = textwrap.dedent(
                """\
                Você é um analista de mercado. Transforme as fontes em nota Markdown concisa.
                Responda em português. Cite % sempre que encontrar nas fontes.
                Se não houver %, estime e sinalize com (estimativa).
                IMPORTANTE: Sempre que citar uma empresa, ferramenta, nicho ou conceito relevante, envolva a palavra em colchetes duplos para criar um link no Obsidian, exemplo: [[Nome do Conceito]].
                """
            )
            user_prompt = textwrap.dedent(
                f"""\
                Tema: {topic_name} | Data: {generated_at}
                Foco: {guidance or 'pesquisa geral'}

                Fontes ({len(items_for_ai)}):
                {sources_block}

                Estrutura OBRIGATÓRIA da nota — seja conciso, máximo 900 tokens no total:

                # {topic_name} — {generated_at}

                ## Resumo executivo
                (2-3 linhas com os achados mais importantes)

                ## 📊 Porcentagens e variações
                (OBRIGATÓRIO — use o formato abaixo para cada %)
                ▲ X% — [o que cresceu]
                ▼ X% — [o que caiu]
                → X% — [dado estático]
                Se não houver dados reais, estime e sinalize com (estimativa).

                ## Tendências e dados
                (3-5 bullet points com números, preços ou tamanhos de mercado)

                ## Problemas e oportunidades
                (o que o mercado pede e ainda não tem)

                ## Ações recomendadas
                (2 ações concretas baseadas nos dados)

                ## Conexões e Grafo
                (Liste de 3 a 5 [[Wikilinks]] relacionados a este tema e assuntos complementares)

                ## Fontes
                (título + URL, apenas as principais)

                Não invente fatos fora das fontes listadas.
                """
            )
            try:
                wait_for_slot("radar:build_note")
                completion = self._complete_with_provider(
                    CompletionRequest(
                        system=system,
                        messages=[Message(role="user", content=user_prompt)],
                        temperature=self.temperature,
                        max_tokens=1000,
                        model=self.model,
                    )
                )
                note_body = completion.text.strip()
            except Exception as exc:
                print(f"[radar] build_note falhou ({exc}), salvando fontes sem síntese IA")
                note_body = self._fallback_note(topic_name=topic_name, guidance=guidance, generated_at=generated_at, items=items)
        else:
            note_body = self._fallback_note(topic_name=topic_name, guidance=guidance, generated_at=generated_at, items=items)

        memory_paths = ", ".join(hit.path for hit in memory_hits) if memory_hits else "nenhuma"
        metadata_block = textwrap.dedent(
            f"""\
            ---
            gerado_em: {generated_at}
            tema: {topic_name}
            fontes: {len(items)}
            memoria_consultada: {memory_paths}
            ---
            """
        ).strip()

        # Wikilinks para o grafo do Obsidian
        feed_link = f"[[feed-{datetime.now().strftime('%Y-%m-%d')}]]"
        memory_links = " · ".join(
            f"[[{hit.path.split('/')[-1].replace('.md', '')}]]"
            for hit in memory_hits
        ) if memory_hits else ""
        links_block = f"\n---\n**Ver também:** {feed_link}"
        if memory_links:
            links_block += f" · {memory_links}"

        return f"{metadata_block}\n\n{note_body}\n{links_block}\n"

    def _format_sources(self, items: list[dict]) -> str:
        if not items:
            return "Nenhuma fonte encontrada."
        rows = []
        for index, item in enumerate(items, start=1):
            snippet = str(item.get("snippet", ""))[:100]  # trunca snippet
            rows.append(
                textwrap.dedent(
                    f"""\
                    Fonte {index}
                    Título: {item.get('title', '')}
                    URL: {item.get('url', '')}
                    Resumo: {snippet}
                    """
                ).strip()
            )
        return "\n\n".join(rows)

    def _fallback_note(self, topic_name: str, guidance: str, generated_at: str, items: list[dict]) -> str:
        if not items:
            return textwrap.dedent(
                f"""\
                ## Resumo executivo
                Nenhuma fonte nova foi encontrada nesta rodada.

                ## O que mudou
                Sem mudanças confirmadas em {generated_at}.

                ## Por que importa
                O radar continua ativo, mas esta rodada nao encontrou fontes novas.

                ## Possíveis ações
                - Ajustar a busca do tema.
                - Aguardar a proxima rodada.
                - Manter a IA em cooldown caso exista limite temporario.

                ## Fontes
                - Nenhuma
                """
            ).strip()

        source_lines = []
        for item in items:
            source_lines.append(f"- [{item.get('title', 'Sem título')}]({item.get('url', '')})")
            snippet = str(item.get("snippet", "")).strip()
            if snippet:
                source_lines.append(f"  - {snippet}")

        return textwrap.dedent(
            f"""\
            ## Resumo executivo
            Coleta automática sem síntese por IA para o tema **{topic_name}**.

            ## O que mudou
            Foram encontrados {len(items)} resultado(s) nesta rodada.

            ## Por que importa
            {guidance or 'Este tema continua sendo monitorado para alimentar o vault com sinais públicos.'}

            ## Possíveis ações
            - Revisar as fontes abaixo.
            - Refinar a query do tema.
            - Aguardar a IA sair do cooldown se houver limite temporario.

            ## Fontes
            {chr(10).join(source_lines)}
            """
        ).strip()


def main() -> None:
    _load_dotenv(ROOT / ".env")

    parser = argparse.ArgumentParser(description="Worker continuo para preencher o Obsidian com pesquisa")
    parser.add_argument("--vault", default=os.environ.get("OBSIDIAN_AI_VAULT", "obsidian-ai-vault"))
    parser.add_argument("--config", default=os.environ.get("OBSIDIAN_RADAR_CONFIG", str(DEFAULT_CONFIG_PATH)))
    parser.add_argument("--state", default=os.environ.get("OBSIDIAN_RADAR_STATE", str(DEFAULT_STATE_PATH)))
    parser.add_argument("--provider", default=os.environ.get("OBSIDIAN_AI_PROVIDER", ""))
    parser.add_argument("--model", default=os.environ.get("OBSIDIAN_AI_MODEL", ""))
    parser.add_argument("--temperature", type=float, default=float(os.environ.get("OBSIDIAN_RADAR_TEMPERATURE", "0.3")))
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    worker = ObsidianRadarWorker(
        vault_path=_resolve_vault_path(args.vault),
        config_path=Path(args.config).resolve() if Path(args.config).is_absolute() else (ROOT / Path(args.config)).resolve(),
        state_path=Path(args.state).resolve() if Path(args.state).is_absolute() else (ROOT / Path(args.state)).resolve(),
        provider_alias=args.provider,
        model=args.model,
        temperature=args.temperature,
    )

    if args.once:
        worker.run_cycle()
        return

    print("Radar contínuo do Obsidian iniciado.")
    print(f"Vault: {worker.vault_path}")
    print(f"Config: {worker.config_path}")
    print(f"State: {worker.state_path}")
    worker.run_forever()


if __name__ == "__main__":
    main()
