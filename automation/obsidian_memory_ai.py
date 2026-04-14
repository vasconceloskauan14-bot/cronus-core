from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agents.providers.base_provider import CompletionRequest, Message
from agents.providers.factory import ProviderFactory
from agents.tools.web_search import WebSearchTool
from automation.obsidian_calendar_sync import ObsidianCalendarSync
from automation.obsidian_memory_store import ObsidianMemoryStore


STATIC_DIR = Path(__file__).resolve().parent / "static"
BASE_SYSTEM_PROMPT = """Voce e Zeus, uma IA local com memoria persistente em um vault do Obsidian.
Use a memoria recuperada quando ela realmente ajudar.
Se a memoria nao trouxer base suficiente, diga isso com clareza.
Responda em portugues, de forma pratica, objetiva e colaborativa.
Sempre priorize fatos presentes no vault e deixe explicito quando voce estiver inferindo algo."""


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


class ObsidianMemoryAIService:
    def __init__(self, vault_path: Path, provider_alias: str = "", model: str = "", temperature: float = 0.4):
        self.vault_path = vault_path
        self.provider_alias = provider_alias or os.environ.get("OBSIDIAN_AI_PROVIDER", "") or os.environ.get("CRONUS_PROVIDER", "") or "openai"
        self.model = model or os.environ.get("OBSIDIAN_AI_MODEL", "")
        self.temperature = temperature

        self.store = ObsidianMemoryStore(vault_path=self.vault_path)
        self.store.bootstrap()
        self.search_tool = WebSearchTool(max_results=6)
        self.provider = ProviderFactory.create(
            provider_alias=self.provider_alias,
            model=self.model,
            agent_name="OBSIDIAN_AI",
        )

    def status(self) -> dict:
        stats = self.store.stats()
        provider_ready = self.provider.is_available()
        model_name = self.model or getattr(self.provider, "default_model", "")
        return {
            "ok": True,
            "assistant_name": "Zeus",
            "provider": self.provider_alias,
            "model": model_name,
            "provider_ready": provider_ready,
            "vault_path": stats["vault_path"],
            "note_count": stats["note_count"],
            "session_count": stats["session_count"],
            "message": None if provider_ready else self._missing_provider_message(),
        }

    def create_session(self) -> dict:
        session_id = self.store.new_session_id()
        session_path = self.store.session_path(session_id)
        self.store._ensure_session_file(session_path=session_path, session_id=session_id)
        return {
            "ok": True,
            "session_id": session_id,
            "session_path": str(session_path),
        }

    def search_memory(self, query: str, limit: int = 6) -> dict:
        hits = [hit.to_dict() for hit in self.store.search(query=query, limit=limit)]
        return {"ok": True, "hits": hits, "query": query}

    def create_note(self, title: str, content: str, folder: str = "Inbox") -> dict:
        target = self.store.create_note(title=title, content=content, folder=folder)
        return {
            "ok": True,
            "path": str(target),
            "relative_path": target.relative_to(self.store.vault_path).as_posix(),
        }

    def teach_zeus(
        self,
        title: str,
        content: str,
        category: str = "comando",
        source: str = "manual",
    ) -> dict:
        record = self.store.teach_zeus(
            title=title,
            content=content,
            category=category,
            source=source,
        )
        return {
            "ok": True,
            "assistant_name": "Zeus",
            **record,
        }

    def sync_calendar(self) -> dict:
        source = os.environ.get("OBSIDIAN_CALENDAR_SOURCE", "").strip()
        window_days = int(os.environ.get("OBSIDIAN_CALENDAR_WINDOW_DAYS", "1"))
        state_path_raw = os.environ.get("OBSIDIAN_CALENDAR_STATE", "state/obsidian_calendar_state.json").strip()
        state_path = Path(state_path_raw)
        if not state_path.is_absolute():
            state_path = (ROOT / state_path).resolve()

        syncer = ObsidianCalendarSync(
            source=source,
            state_path=state_path,
            window_days=window_days,
        )
        return syncer.sync(research_callback=lambda query, folder: self.research_and_memorize(query=query, folder=folder))

    def research_and_memorize(self, query: str, session_id: str = "", folder: str = "Memoria/Pesquisas") -> dict:
        research_query = query.strip()
        if not research_query:
            raise ValueError("Pergunta de pesquisa vazia.")
        if not self.provider.is_available():
            raise RuntimeError(self._missing_provider_message())

        search_result = self.search_tool.run(query=research_query, max_results=6)
        if not search_result.success:
            detail = (search_result.error or "").strip() or "a busca nao retornou resposta valida no ambiente atual"
            raise RuntimeError(f"Falha na busca web: {detail}")

        items = search_result.output if isinstance(search_result.output, list) else []
        if not items:
            raise RuntimeError("A busca web nao retornou resultados para essa pergunta.")

        memory_context, memory_hits = self.store.build_context(research_query, limit=4, max_chars=2800)
        zeus_context = self.store.read_zeus_context()
        sources_text = self._format_sources(items)
        system = textwrap.dedent(
            """\
            Você é Zeus atuando como pesquisador operacional.
            Sua função é pesquisar na web, sintetizar o que importa e transformar isso em memória útil no Obsidian.
            Responda em português.
            Use datas absolutas quando possível.
            Seja pragmático e deixe claro o que vem das fontes e o que é inferência.
            """
        )
        prompt = textwrap.dedent(
            f"""\
            Pergunta do usuario:
            {research_query}

            Nucleo atual do Zeus:
            {zeus_context or 'Ainda não há um núcleo do Zeus preenchido.'}

            Memoria relevante já existente:
            {memory_context or 'Nenhuma memória relevante encontrada.'}

            Fontes coletadas agora:
            {sources_text}

            Gere duas partes:
            1. Um resumo curto para responder ao usuario agora.
            2. Uma nota completa em Markdown para guardar no Obsidian.

            Estrutura obrigatoria da nota:
            # Titulo
            ## Resumo executivo
            ## O que foi encontrado
            ## Padrões percebidos
            ## Oportunidades ou implicações
            ## Fontes

            Separe as duas partes usando exatamente esta linha:
            ===NOTA_OBSIDIAN===
            """
        )

        completion = self.provider.complete(
            CompletionRequest(
                system=system,
                messages=[Message(role="user", content=prompt)],
                temperature=min(self.temperature, 0.35),
                max_tokens=2200,
                model=self.model,
            )
        )

        answer_text, note_markdown = self._split_research_response(completion.text, research_query, items)
        session_id = session_id.strip() or self.store.new_session_id()
        session_path = self.store.save_exchange(
            session_id=session_id,
            user_message=f"[pesquisa] {research_query}",
            assistant_message=answer_text,
            memory_hits=memory_hits,
        )

        target_folder = f"{folder.strip().rstrip('/')}/{datetime.now().strftime('%Y-%m-%d')}"
        note_path = self.store.create_note(
            title=f"Pesquisa - {research_query[:80]}",
            content=note_markdown,
            folder=target_folder,
        )

        return {
            "ok": True,
            "answer": answer_text,
            "session_id": session_id,
            "session_path": str(session_path),
            "note_path": str(note_path),
            "note_relative_path": note_path.relative_to(self.store.vault_path).as_posix(),
            "memory_hits": [hit.to_dict() for hit in memory_hits],
            "sources": items,
            "provider": completion.provider,
            "model": completion.model,
            "usage": {
                "input_tokens": completion.input_tokens,
                "output_tokens": completion.output_tokens,
                "cost_usd": completion.cost_usd,
                "latency_ms": completion.latency_ms,
            },
        }

    def chat(self, message: str, session_id: str = "") -> dict:
        user_message = message.strip()
        if not user_message:
            raise ValueError("Mensagem vazia.")

        session_id = session_id.strip() or self.store.new_session_id()
        memory_context, memory_hits = self.store.build_context(user_message, limit=5)
        recent_context = self.store.recent_session_context(session_id=session_id, max_chars=3500)
        identity_context = self.store.read_identity_context()
        facts_context = self.store.read_facts_context()
        zeus_context = self.store.read_zeus_context()

        if not self.provider.is_available():
            raise RuntimeError(self._missing_provider_message())

        system_parts = [
            BASE_SYSTEM_PROMPT,
            f"## Nucleo do Zeus\n{zeus_context or 'Ainda nao preenchido.'}",
            f"## Identidade da IA\n{identity_context or 'Ainda nao definida.'}",
            f"## Fatos importantes\n{facts_context or 'Ainda nao definidos.'}",
            f"## Memoria recuperada do vault\n{memory_context or 'Nenhuma nota relevante foi encontrada.'}",
            f"## Historico recente da sessao\n{recent_context or 'Sem historico anterior.'}",
        ]

        completion = self.provider.complete(
            CompletionRequest(
                system="\n\n".join(system_parts),
                messages=[Message(role="user", content=user_message)],
                temperature=self.temperature,
                max_tokens=2200,
                model=self.model,
            )
        )

        session_path = self.store.save_exchange(
            session_id=session_id,
            user_message=user_message,
            assistant_message=completion.text,
            memory_hits=memory_hits,
        )

        return {
            "ok": True,
            "answer": completion.text,
            "session_id": session_id,
            "session_path": str(session_path),
            "provider": completion.provider,
            "model": completion.model,
            "memory_hits": [hit.to_dict() for hit in memory_hits],
            "usage": {
                "input_tokens": completion.input_tokens,
                "output_tokens": completion.output_tokens,
                "cost_usd": completion.cost_usd,
                "latency_ms": completion.latency_ms,
            },
        }

    def _missing_provider_message(self) -> str:
        return (
            "Nenhum provider de IA esta pronto. Configure OPENAI_API_KEY "
            "ou use um provider local como Ollama com CRONUS_PROVIDER=ollama."
        )

    def _format_sources(self, items: list[dict]) -> str:
        rows = []
        for index, item in enumerate(items, start=1):
            rows.append(
                textwrap.dedent(
                    f"""\
                    Fonte {index}
                    Titulo: {item.get('title', '')}
                    URL: {item.get('url', '')}
                    Resumo: {item.get('snippet', '')}
                    """
                ).strip()
            )
        return "\n\n".join(rows)

    def _split_research_response(self, text: str, query: str, items: list[dict]) -> tuple[str, str]:
        separator = "===NOTA_OBSIDIAN==="
        if separator in text:
            answer_part, note_part = text.split(separator, 1)
            answer_text = answer_part.strip()
            note_text = note_part.strip()
        else:
            answer_text = text.strip()
            note_text = self._fallback_research_note(query, items, answer_text)

        if not note_text:
            note_text = self._fallback_research_note(query, items, answer_text)
        if not answer_text:
            answer_text = "Pesquisa concluida e nota salva no Obsidian."
        return answer_text, note_text

    def _fallback_research_note(self, query: str, items: list[dict], answer_text: str) -> str:
        source_lines = []
        for item in items:
            title = str(item.get("title", "Sem titulo")).strip()
            url = str(item.get("url", "")).strip()
            snippet = str(item.get("snippet", "")).strip()
            source_lines.append(f"- [{title}]({url})")
            if snippet:
                source_lines.append(f"  - {snippet}")

        return textwrap.dedent(
            f"""\
            # Pesquisa - {query}

            ## Resumo executivo
            {answer_text or 'Pesquisa realizada com sucesso.'}

            ## O que foi encontrado
            Foram encontrados {len(items)} resultado(s) para esta pergunta.

            ## Padrões percebidos
            - Revisar as fontes abaixo para consolidar os padrões.

            ## Oportunidades ou implicações
            - Transformar os achados em decisões, ofertas ou playbooks.

            ## Fontes
            {chr(10).join(source_lines) if source_lines else '- Nenhuma fonte'}
            """
        ).strip()


class ObsidianRequestHandler(BaseHTTPRequestHandler):
    service: ObsidianMemoryAIService

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/painel"):
            return self._serve_file(STATIC_DIR / "painel.html", content_type="text/html; charset=utf-8")
        if parsed.path == "/favicon.ico":
            return self._send_empty(HTTPStatus.NO_CONTENT)
        if parsed.path == "/api/status":
            return self._send_json(self.service.status())
        if parsed.path == "/api/memory/search":
            limit = 6
            query_params = parse_qs(parsed.query)
            if "limit" in query_params:
                try:
                    limit = max(1, min(int(query_params["limit"][0]), 12))
                except ValueError:
                    limit = 6
            query = query_params.get("q", [""])[0]
            return self._send_json(self.service.search_memory(query=query, limit=limit))
        if parsed.path == "/api/radar/config":
            radar_path = ROOT / "config" / "obsidian_radar.json"
            if radar_path.exists():
                return self._send_json(json.loads(radar_path.read_text(encoding="utf-8")))
            return self._send_json({"ok": False, "error": "Config nao encontrado."}, status=HTTPStatus.NOT_FOUND)
        if parsed.path == "/api/news":
            query_params = parse_qs(parsed.query)
            limit = int(query_params.get("limit", ["50"])[0])
            offset = int(query_params.get("offset", ["0"])[0])
            category = query_params.get("category", [""])[0]
            articles_path = ROOT / "state" / "news_articles.json"
            if not articles_path.exists():
                return self._send_json({"ok": True, "articles": [], "total": 0})
            articles = json.loads(articles_path.read_text(encoding="utf-8"))
            if category:
                articles = [a for a in articles if a.get("category", "").lower() == category.lower()]
            total = len(articles)
            page = articles[offset: offset + limit]
            return self._send_json({
                "ok": True,
                "articles": page,
                "total": total,
                "updated_at": datetime.now().isoformat(timespec="seconds"),
            })
        return self._send_json({"ok": False, "error": "Rota nao encontrada."}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        payload = self._read_json()

        if parsed.path == "/api/session":
            return self._send_json(self.service.create_session())

        if parsed.path == "/api/memory/note":
            title = str(payload.get("title", ""))
            content = str(payload.get("content", ""))
            folder = str(payload.get("folder", "Inbox"))
            if not content.strip():
                return self._send_json({"ok": False, "error": "Conteudo vazio."}, status=HTTPStatus.BAD_REQUEST)
            try:
                return self._send_json(self.service.create_note(title=title, content=content, folder=folder))
            except ValueError as exc:
                return self._send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

        if parsed.path == "/api/zeus/teach":
            title = str(payload.get("title", ""))
            content = str(payload.get("content", ""))
            category = str(payload.get("category", "comando"))
            source = str(payload.get("source", "manual"))
            if not content.strip():
                return self._send_json({"ok": False, "error": "Conteudo vazio."}, status=HTTPStatus.BAD_REQUEST)
            try:
                return self._send_json(
                    self.service.teach_zeus(
                        title=title,
                        content=content,
                        category=category,
                        source=source,
                    )
                )
            except ValueError as exc:
                return self._send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

        if parsed.path == "/api/calendar/sync":
            try:
                return self._send_json(self.service.sync_calendar())
            except RuntimeError as exc:
                return self._send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.SERVICE_UNAVAILABLE)
            except Exception as exc:
                return self._send_json({"ok": False, "error": f"Falha ao sincronizar calendario: {exc}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

        if parsed.path == "/api/research":
            message = str(payload.get("message", ""))
            session_id = str(payload.get("session_id", ""))
            folder = str(payload.get("folder", "Memoria/Pesquisas"))
            try:
                return self._send_json(self.service.research_and_memorize(query=message, session_id=session_id, folder=folder))
            except ValueError as exc:
                return self._send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            except RuntimeError as exc:
                return self._send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.SERVICE_UNAVAILABLE)
            except Exception as exc:
                return self._send_json({"ok": False, "error": f"Falha na pesquisa: {exc}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

        if parsed.path == "/api/chat":
            message = str(payload.get("message", ""))
            session_id = str(payload.get("session_id", ""))
            try:
                return self._send_json(self.service.chat(message=message, session_id=session_id))
            except ValueError as exc:
                return self._send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            except RuntimeError as exc:
                return self._send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.SERVICE_UNAVAILABLE)
            except Exception as exc:
                return self._send_json({"ok": False, "error": f"Falha ao responder: {exc}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

        if parsed.path == "/api/radar/config":
            radar_path = ROOT / "config" / "obsidian_radar.json"
            try:
                config_data = json.loads(payload.get("__raw__") or json.dumps(payload))
                radar_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                return self._send_json({"ok": True})
            except Exception as exc:
                return self._send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        return self._send_json({"ok": False, "error": "Rota nao encontrada."}, status=HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args) -> None:
        return

    def _read_json(self) -> dict:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            content_length = 0
        if content_length <= 0:
            return {}
        raw_body = self.rfile.read(content_length)
        if not raw_body:
            return {}
        try:
            return json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def _send_empty(self, status: HTTPStatus) -> None:
        self.send_response(status)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def _serve_file(self, file_path: Path, content_type: str) -> None:
        if not file_path.exists():
            return self._send_json({"ok": False, "error": "Arquivo nao encontrado."}, status=HTTPStatus.NOT_FOUND)
        data = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)


def create_server(host: str, port: int, vault_path: Path, provider_alias: str = "", model: str = "", temperature: float = 0.4) -> ThreadingHTTPServer:
    service = ObsidianMemoryAIService(
        vault_path=vault_path,
        provider_alias=provider_alias,
        model=model,
        temperature=temperature,
    )

    class BoundHandler(ObsidianRequestHandler):
        pass

    BoundHandler.service = service
    return ThreadingHTTPServer((host, port), BoundHandler)


def main() -> None:
    _load_dotenv(ROOT / ".env")

    parser = argparse.ArgumentParser(description="Servidor local de IA com memoria no Obsidian")
    parser.add_argument("--host", default=os.environ.get("OBSIDIAN_AI_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("OBSIDIAN_AI_PORT", "8787")))
    parser.add_argument("--vault", default=os.environ.get("OBSIDIAN_AI_VAULT", "obsidian-ai-vault"))
    parser.add_argument("--provider", default=os.environ.get("OBSIDIAN_AI_PROVIDER", ""))
    parser.add_argument("--model", default=os.environ.get("OBSIDIAN_AI_MODEL", ""))
    parser.add_argument("--temperature", type=float, default=float(os.environ.get("OBSIDIAN_AI_TEMPERATURE", "0.4")))
    args = parser.parse_args()

    server = create_server(
        host=args.host,
        port=args.port,
        vault_path=_resolve_vault_path(args.vault),
        provider_alias=args.provider,
        model=args.model,
        temperature=args.temperature,
    )

    print(f"IA com memoria no Obsidian rodando em http://{args.host}:{args.port}")
    print(f"Vault: {_resolve_vault_path(args.vault)}")
    server.serve_forever()


if __name__ == "__main__":
    main()
