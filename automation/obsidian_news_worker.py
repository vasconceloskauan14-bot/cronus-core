"""
CRONUS News Worker
Lê notas novas do Obsidian e converte em artigos de jornal via IA.
Serve como fonte para a aba de notícias do site.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import textwrap
import time
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agents.providers.base_provider import CompletionRequest, Message
from agents.providers.factory import ProviderFactory
from automation.rate_limiter import wait_for_slot


ARTICLES_PATH = ROOT / "state" / "news_articles.json"
MAX_ARTICLES = 200  # máximo de artigos guardados


def _load_dotenv(env_path: Path) -> None:
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _load_articles() -> list[dict]:
    if not ARTICLES_PATH.exists():
        return []
    try:
        return json.loads(ARTICLES_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_articles(articles: list[dict]) -> None:
    ARTICLES_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTICLES_PATH.write_text(
        json.dumps(articles, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def _note_id(path: Path) -> str:
    return hashlib.md5(str(path).encode()).hexdigest()[:12]


def _find_new_notes(vault_path: Path, processed_ids: set[str], max_age_minutes: int = 15) -> list[Path]:
    """Encontra notas criadas/modificadas nos últimos N minutos que ainda não viraram artigo."""
    folders = [
        vault_path / "Memoria" / "Radar",
        vault_path / "Memoria" / "Pesquisas",
    ]
    cutoff = time.time() - (max_age_minutes * 60)
    new_notes = []

    for folder in folders:
        if not folder.exists():
            continue
        for md_file in folder.rglob("*.md"):
            if md_file.stat().st_mtime >= cutoff:
                note_id = _note_id(md_file)
                if note_id not in processed_ids:
                    new_notes.append(md_file)

    # Ordena da mais recente para a mais antiga
    new_notes.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return new_notes


class NewsWorker:
    CATEGORIES = [
        "Mercado",
        "Tendências",
        "Preços",
        "Ferramentas",
        "Nichos",
        "Oportunidades",
        "Dados",
    ]

    def __init__(self, vault_path: Path, loop_minutes: int = 5):
        self.vault_path = vault_path
        self.loop_minutes = loop_minutes

        provider_alias = (
            os.environ.get("OBSIDIAN_AI_PROVIDER", "")
            or os.environ.get("CRONUS_PROVIDER", "")
            or "openai"
        )
        model = os.environ.get("OBSIDIAN_AI_MODEL", "")
        self.provider = ProviderFactory.create(
            provider_alias=provider_alias,
            model=model,
            agent_name="CRONUS_NEWS",
        )
        self.model = model

    def run_forever(self) -> None:
        # Delay inicial: aguarda 5 minutos para radar e síntese iniciarem primeiro
        print("[news] Aguardando 5 minutos antes do primeiro ciclo...")
        time.sleep(300)
        print(f"[news] News worker iniciado — ciclo a cada {self.loop_minutes} minuto(s).")
        while True:
            try:
                self.run_cycle()
            except Exception as exc:
                print(f"[news] erro no ciclo: {exc}")
            time.sleep(self.loop_minutes * 60)

    def run_cycle(self) -> None:
        articles = _load_articles()
        processed_ids = {a["source_id"] for a in articles}

        new_notes = _find_new_notes(self.vault_path, processed_ids, max_age_minutes=20)
        if not new_notes:
            print(f"[news] Nenhuma nota nova encontrada.")
            return

        print(f"[news] {len(new_notes)} nota(s) nova(s) para converter em artigo.")

        for note_path in new_notes[:5]:  # máximo 5 por ciclo para não sobrecarregar a API
            try:
                article = self._convert_to_article(note_path)
                if article:
                    articles.insert(0, article)
                    print(f"[news] Artigo criado: {article['title'][:60]}")
                time.sleep(8)  # pausa entre chamadas à API
            except Exception as exc:
                print(f"[news] erro ao converter {note_path.name}: {exc}")

        # Mantém só os últimos MAX_ARTICLES
        articles = articles[:MAX_ARTICLES]
        _save_articles(articles)
        print(f"[news] {len(articles)} artigos no banco. Ciclo concluído.")

    def _convert_to_article(self, note_path: Path) -> dict | None:
        try:
            content = note_path.read_text(encoding="utf-8")
        except Exception:
            return None

        if len(content.strip()) < 200:
            return None

        # Trunca para não gastar tokens demais
        content_excerpt = content[:3000]
        now = datetime.now()

        if not self.provider.is_available():
            return None

        wait_for_slot("news:article")
        completion = self.provider.complete(CompletionRequest(
            system=textwrap.dedent("""\
                Você é o editor-chefe de um jornal digital especializado no mercado de edição de vídeo, foto, motion e criação de conteúdo no Brasil.
                Seu trabalho é transformar relatórios de pesquisa em artigos de jornal atraentes e informativos.
                Escreva SEMPRE em português brasileiro. Seja direto, use linguagem jornalística clara.
                OBRIGATÓRIO: inclua pelo menos 1 dado percentual (▲ ou ▼) no artigo se houver nas fontes.
                Retorne SOMENTE o JSON válido, sem markdown, sem explicação.
            """),
            messages=[Message(role="user", content=textwrap.dedent(f"""\
                Transforme este relatório de pesquisa em um artigo de jornal digital.

                Data: {now.strftime('%d/%m/%Y %H:%M')}

                RELATÓRIO:
                {content_excerpt}

                Retorne um JSON com exatamente estes campos:
                {{
                  "title": "Título chamativo do artigo (máx 80 chars)",
                  "subtitle": "Subtítulo com dado ou insight chave (máx 120 chars)",
                  "category": "uma das categorias: Mercado | Tendências | Preços | Ferramentas | Nichos | Oportunidades | Dados",
                  "tags": ["tag1", "tag2", "tag3", "tag4"],
                  "summary": "Resumo em 2 frases diretas.",
                  "body": "Corpo do artigo em 2-3 parágrafos concisos. Inclua percentagens se disponíveis.",
                  "highlight": "Dado mais impactante do artigo (1 frase curta)",
                  "percentages": ["▲ X% — descrição", "▼ X% — descrição"]
                }}
            """))],
            temperature=0.4,
            max_tokens=500,
            model=self.model,
        ))

        raw = completion.text.strip()

        # Remove blocos de código markdown se existirem
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Tenta extrair JSON do texto
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    data = json.loads(raw[start:end])
                except Exception:
                    print(f"[news] JSON inválido para {note_path.name}")
                    return None
            else:
                return None

        source_id = _note_id(note_path)
        relative_path = note_path.relative_to(self.vault_path).as_posix()

        return {
            "id": source_id,
            "source_id": source_id,
            "source_note": relative_path,
            "title": str(data.get("title", "Sem título"))[:100],
            "subtitle": str(data.get("subtitle", ""))[:150],
            "category": str(data.get("category", "Mercado")),
            "tags": list(data.get("tags", []))[:6],
            "summary": str(data.get("summary", "")),
            "body": str(data.get("body", "")),
            "highlight": str(data.get("highlight", "")),
            "percentages": list(data.get("percentages", [])),
            "published_at": now.isoformat(timespec="seconds"),
            "reading_time": max(1, len(str(data.get("body", "")).split()) // 200),
        }


def main() -> None:
    _load_dotenv(ROOT / ".env")

    vault_raw = os.environ.get("OBSIDIAN_AI_VAULT", "obsidian-ai-vault")
    base = vault_raw.strip() or "obsidian-ai-vault"
    vault_path = Path(base) if Path(base).is_absolute() else (ROOT / base).resolve()

    loop_minutes = int(os.environ.get("OBSIDIAN_NEWS_INTERVAL", "5"))

    worker = NewsWorker(vault_path=vault_path, loop_minutes=loop_minutes)
    worker.run_forever()


if __name__ == "__main__":
    main()
