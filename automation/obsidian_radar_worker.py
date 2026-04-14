from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import textwrap
import time
from datetime import datetime, timedelta
from pathlib import Path


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
    "max_results_per_topic": 5,
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
        self.search_tool = WebSearchTool(max_results=5)
        self.provider_alias = provider_alias or os.environ.get("OBSIDIAN_AI_PROVIDER", "") or os.environ.get("CRONUS_PROVIDER", "") or "openai"
        self.model = model or os.environ.get("OBSIDIAN_AI_MODEL", "")
        self.provider = ProviderFactory.create(
            provider_alias=self.provider_alias,
            model=self.model,
            agent_name="OBSIDIAN_RADAR",
        )

        self._ensure_config()

    def _ensure_config(self) -> None:
        if self.config_path.exists():
            return
        _write_json(self.config_path, DEFAULT_CONFIG)

    def load_config(self) -> dict:
        cfg = _read_json(self.config_path, DEFAULT_CONFIG)
        cfg.setdefault("enabled", True)
        cfg.setdefault("loop_minutes", 120)
        cfg.setdefault("max_topics_per_cycle", 2)
        cfg.setdefault("max_results_per_topic", 5)
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

        for idx, topic in enumerate(selected_topics):
            outcome = self._process_topic(topic=topic, config=config, state=state)
            results.append(outcome)
            # Pausa entre tópicos para não sobrecarregar a API
            if idx < len(selected_topics) - 1:
                print(f"[radar] pausa 60s antes do próximo tópico...")
                time.sleep(60)

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

    def _generate_sub_queries(self, topic: dict, seen_queries: list[str], cycle_index: int = 0) -> list[str]:
        """Gera 5 queries NOVAS, evitando repetir o que já foi pesquisado antes."""
        topic_name = str(topic.get("name", ""))
        base_query = str(topic.get("query", topic_name)).strip()
        guidance = str(topic.get("notes", "")).strip()

        now = datetime.now()
        year = now.strftime("%Y")

        # Perspectiva desta rodada (rotaciona a cada ciclo)
        perspective = self._PERSPECTIVES[cycle_index % len(self._PERSPECTIVES)]

        # Últimas 20 queries já usadas para evitar repetição
        recent_queries = seen_queries[-20:] if seen_queries else []
        recent_block = "\n".join(f"- {q}" for q in recent_queries) if recent_queries else "Nenhuma ainda."

        if not self.provider.is_available():
            # Fallback sem IA: variações com data e fonte
            return [
                f"{base_query} {year}",
                f"{base_query} reddit forum",
                f"{base_query} preços valores cobrados",
                f"site:reddit.com {base_query}",
                f"{base_query} tendências {year}",
            ]

        try:
            wait_for_slot("radar:sub_queries")
            completion = self.provider.complete(CompletionRequest(
                system="Você é um pesquisador especialista em criar buscas web variadas, atualizadas e originais.",
                messages=[Message(role="user", content=textwrap.dedent(f"""\
                    Tema: {topic_name}
                    Query base de referência: {base_query}
                    Foco editorial: {guidance or 'pesquisa geral'}
                    Data atual: {now.strftime('%Y-%m-%d')}
                    Perspectiva desta rodada: {perspective}

                    QUERIES JÁ USADAS ANTES — NÃO repita estas nem variações próximas:
                    {recent_block}

                    Gere exatamente 5 queries de busca NOVAS e DIFERENTES das já listadas acima.

                    Regras obrigatórias:
                    - Pelo menos 2 queries devem incluir o ano {year}
                    - Uma query deve conter "reddit" ou "forum" ou "discussion"
                    - Uma query deve ser em português brasileiro natural
                    - Uma query deve buscar especificamente PORCENTAGENS: inclua palavras como "growth percentage", "cresceu %", "aumento percentual", "statistics 2026", "market share %"
                    - Use palavras-chave diferentes das queries já usadas
                    - Adapte o foco para: {perspective}

                    Retorne SOMENTE as 5 queries, uma por linha, sem numeração nem explicação.
                """))],
                temperature=0.7,
                max_tokens=300,
                model=self.model,
            ))
            queries = [q.strip() for q in completion.text.strip().splitlines() if q.strip()]
            return queries[:5] if queries else [f"{base_query} {year}"]
        except Exception as exc:
            print(f"[radar] sub_queries falhou ({exc}), usando queries padrão")
            return [
                f"{base_query} {year}",
                f"{base_query} reddit forum",
                f"{base_query} preços valores cobrados",
                f"site:reddit.com {base_query}",
                f"{base_query} tendências {year}",
            ]

    def _notify(self, title: str, message: str) -> None:
        """Exibe notificação toast nativa do Windows."""
        try:
            safe_title = title.replace("'", "").replace('"', "")
            safe_msg = message.replace("'", "").replace('"', "")
            ps = (
                "[reflection.assembly]::loadwithpartialname('System.Windows.Forms')|Out-Null;"
                "[reflection.assembly]::loadwithpartialname('System.Drawing')|Out-Null;"
                "$n=New-Object System.Windows.Forms.NotifyIcon;"
                "$n.Icon=[System.Drawing.SystemIcons]::Information;"
                "$n.Visible=$true;"
                f"$n.BalloonTipTitle='{safe_title}';"
                f"$n.BalloonTipText='{safe_msg}';"
                "$n.ShowBalloonTip(10000);"
                "Start-Sleep 11;"
                "$n.Dispose()"
            )
            subprocess.Popen(
                ["powershell.exe", "-NoProfile", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-Command", ps],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

    def _process_topic(self, topic: dict, config: dict, state: dict) -> dict:
        topic_name = str(topic.get("name", "Tema sem nome"))
        topic_key = _slugify(topic_name)
        topic_state = state["topics"].setdefault(topic_key, {})
        seen_urls = set(topic_state.get("seen_urls", []))
        seen_queries: list[str] = topic_state.get("seen_queries", [])
        cycle_index: int = topic_state.get("cycle_index", 0)
        deep_minutes = int(config.get("deep_research_minutes", 40))
        max_results = max(int(config.get("max_results_per_topic", 8)), 1)

        # Gera ângulos de busca NOVOS (evita repetir queries já usadas)
        sub_queries = self._generate_sub_queries(topic, seen_queries=seen_queries, cycle_index=cycle_index)
        total_queries = len(sub_queries)
        pause_seconds = max(int((deep_minutes * 60) / total_queries), 30)

        print(f"[radar] '{topic_name}': {total_queries} buscas, ~{pause_seconds}s entre cada uma (~{deep_minutes} min total)")

        all_items: list[dict] = []
        all_new_urls: set[str] = set()

        for idx, query in enumerate(sub_queries, start=1):
            print(f"[radar] busca {idx}/{total_queries}: {query[:80]}")
            result = self.search_tool.run(query=query, max_results=max_results)
            if result.success and isinstance(result.output, list):
                for item in result.output:
                    url = str(item.get("url", "")).strip()
                    if url and url not in seen_urls and url not in all_new_urls:
                        all_items.append(item)
                        all_new_urls.add(url)

            # Pausa entre buscas para pesquisa profunda
            if idx < total_queries:
                print(f"[radar] aguardando {pause_seconds}s antes da próxima busca...")
                time.sleep(pause_seconds)

        if not all_items:
            topic_state["last_run_at"] = datetime.now().isoformat(timespec="seconds")
            topic_state["last_error"] = "nenhum resultado novo encontrado"
            # Salva as queries mesmo sem resultado para não repetir na próxima rodada
            updated_queries = seen_queries + sub_queries
            topic_state["seen_queries"] = updated_queries[-60:]
            topic_state["cycle_index"] = cycle_index + 1
            return {"topic": topic_name, "ok": False, "error": "nenhum resultado novo"}

        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        note_title = f"Radar - {topic_name} - {datetime.now().strftime('%Y-%m-%d %H%M')}"
        folder = str(topic.get("folder", f"Memoria/Radar/{topic_key}")).strip() or f"Memoria/Radar/{topic_key}"
        folder = f"{folder}/{datetime.now().strftime('%Y-%m-%d')}"

        note_content = self._build_note(topic=topic, items=all_items, generated_at=generated_at, sub_queries=sub_queries)
        note_path = self.store.create_note(title=note_title, content=note_content, folder=folder)

        topic_state["last_run_at"] = datetime.now().isoformat(timespec="seconds")
        topic_state["last_note_path"] = note_path.relative_to(self.vault_path).as_posix()
        topic_state["last_error"] = ""
        merged_urls = list(seen_urls.union(all_new_urls))
        topic_state["seen_urls"] = merged_urls[-400:]

        # Salva as queries usadas neste ciclo para evitar repetição futura
        updated_queries = seen_queries + sub_queries
        topic_state["seen_queries"] = updated_queries[-60:]  # guarda até 60 queries
        topic_state["cycle_index"] = cycle_index + 1

        print(f"[radar] '{topic_name}' concluído: {len(all_items)} fontes coletadas")

        # Adiciona bloco novo no feed diário
        self._append_to_feed(
            topic_name=topic_name,
            items=all_items,
            sub_queries=sub_queries,
            note_path=topic_state["last_note_path"],
            generated_at=generated_at,
        )

        # Notificação Windows
        now_str = datetime.now().strftime("%H:%M")
        self._notify(
            title=f"CRONUS — Nova pesquisa ({now_str})",
            message=f"{topic_name}: {len(all_items)} fontes coletadas e salvas no Obsidian.",
        )
        return {
            "topic": topic_name,
            "ok": True,
            "note_path": topic_state["last_note_path"],
            "results_found": len(all_items),
            "sub_queries": total_queries,
            "provider_ready": self.provider.is_available(),
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
        snippets = [
            f"- **{it.get('title', 'Sem título')}** — {it.get('snippet', '')[:150]}"
            for it in items[:4]
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
            header = (
                f"# Feed de Pesquisas — {now.strftime('%d/%m/%Y')}\n"
                f"_Atualizado automaticamente pelo CRONUS Radar_\n"
            )
            feed_file.write_text(header + block, encoding="utf-8")
        else:
            with feed_file.open("a", encoding="utf-8") as f:
                f.write(block)

        print(f"[radar] feed atualizado: {feed_file.name}")

    def _build_note(self, topic: dict, items: list[dict], generated_at: str, sub_queries: list[str] | None = None) -> str:
        topic_name = str(topic.get("name", "Tema"))
        guidance = str(topic.get("notes", "")).strip()
        memory_context, memory_hits = self.store.build_context(f"{topic_name}\n{guidance}", limit=3, max_chars=800)
        queries_block = "\n".join(f"- {q}" for q in (sub_queries or [])) or "- busca padrão"

        if self.provider.is_available():
            # Limita fontes para controlar tokens de entrada
            items_for_ai = items[:6]
            sources_block = self._format_sources(items_for_ai)

            system = textwrap.dedent(
                """\
                Você é um analista de mercado. Transforme as fontes em nota Markdown concisa.
                Responda em português. Cite % sempre que encontrar nas fontes.
                Se não houver %, estime e sinalize com (estimativa).
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

                ## Fontes
                (título + URL, apenas as principais)

                Não invente fatos fora das fontes listadas.
                """
            )
            try:
                wait_for_slot("radar:build_note")
                completion = self.provider.complete(
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

        return f"{metadata_block}\n\n{note_body}\n"

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
                O radar precisa de um provider de IA ou de novas fontes para gerar notas mais ricas.

                ## Possíveis ações
                - Ajustar a busca do tema.
                - Configurar um provider de IA.
                - Aguardar a próxima rodada.

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
            - Configurar um provider para gerar síntese automática.

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
