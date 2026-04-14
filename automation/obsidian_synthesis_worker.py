from __future__ import annotations

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
from automation.obsidian_memory_store import ObsidianMemoryStore
from automation.rate_limiter import wait_for_slot


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


def _read_recent_notes(vault_path: Path, folders: list[str], max_notes: int = 30) -> list[dict]:
    """Lê as notas mais recentes das pastas do radar."""
    notes = []
    for folder in folders:
        folder_path = vault_path / folder
        if not folder_path.exists():
            continue
        for md_file in sorted(folder_path.rglob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)[:max_notes]:
            try:
                content = md_file.read_text(encoding="utf-8")
                notes.append({
                    "title": md_file.stem,
                    "path": md_file.relative_to(vault_path).as_posix(),
                    "content": content[:3000],
                    "modified_at": datetime.fromtimestamp(md_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                })
            except Exception:
                pass
    notes.sort(key=lambda n: n["modified_at"], reverse=True)
    return notes[:max_notes]


class ObsidianSynthesisWorker:
    INSIGHTS_PATH = "Memoria/Insights/painel-de-insights.md"
    CONNECTIONS_PATH = "Memoria/Insights/mapa-de-conexoes.md"
    RADAR_FOLDERS = [
        "Memoria/Radar",
        "Memoria/Pesquisas",
    ]

    def __init__(self, vault_path: Path, provider_alias: str = "", model: str = "", loop_minutes: int = 30):
        self.vault_path = vault_path
        self.loop_minutes = loop_minutes
        self.store = ObsidianMemoryStore(vault_path=vault_path)
        self.store.bootstrap()

        provider_alias = provider_alias or os.environ.get("OBSIDIAN_AI_PROVIDER", "") or os.environ.get("CRONUS_PROVIDER", "") or "openai"
        model = model or os.environ.get("OBSIDIAN_AI_MODEL", "")
        self.provider = ProviderFactory.create(provider_alias=provider_alias, model=model, agent_name="OBSIDIAN_SYNTHESIS")
        self.model = model

    def run_forever(self) -> None:
        # Delay inicial: aguarda 3 minutos para o radar iniciar primeiro
        print("[síntese] Aguardando 3 minutos antes do primeiro ciclo (evita conflito com radar)...")
        time.sleep(180)
        print(f"Síntese iniciada — rodando a cada {self.loop_minutes} minutos.")
        while True:
            try:
                self.run_cycle()
            except Exception as exc:
                print(f"[síntese] erro no ciclo: {exc}")
            print(f"Aguardando {self.loop_minutes} minuto(s)...")
            time.sleep(self.loop_minutes * 60)

    def run_cycle(self) -> None:
        notes = _read_recent_notes(self.vault_path, self.RADAR_FOLDERS, max_notes=30)
        if not notes:
            print("[síntese] Nenhuma nota encontrada ainda.")
            return

        print(f"[síntese] Analisando {len(notes)} notas...")
        self._update_insights(notes)
        print("[síntese] Aguardando 20s antes das conexões...")
        time.sleep(20)
        self._update_connections(notes)
        print(f"[síntese] Ciclo concluído em {datetime.now().strftime('%H:%M:%S')}")

    def _update_insights(self, notes: list[dict]) -> None:
        notes_block = self._format_notes_block(notes)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        wait_for_slot("synthesis:insights")
        completion = self.provider.complete(CompletionRequest(
            system=textwrap.dedent("""\
                Você é um analista de inteligência de mercado.
                Lê notas de pesquisa contínua e extrai os padrões mais importantes.
                Responda em português. Seja direto e concreto.
                Não repita o que está nas fontes — sintetize e interprete.
            """),
            messages=[Message(role="user", content=textwrap.dedent(f"""\
                Analise as notas de pesquisa abaixo e gere um PAINEL DE INSIGHTS atualizado.

                Data/hora: {now}
                Total de notas analisadas: {len(notes)}

                NOTAS:
                {notes_block}

                Estrutura obrigatória — seja conciso, máximo 600 tokens:

                # Painel de Insights — {now}

                ## Tendências dominantes
                (3-4 bullets com os padrões mais fortes)

                ## Oportunidades
                (2-3 bullets: o que o mercado pede e poucos entregam)

                ## Ação recomendada agora
                (1-2 ações concretas)
            """))],
            temperature=0.3,
            max_tokens=700,
            model=self.model,
        ))

        target = self.vault_path / self.INSIGHTS_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(completion.text, encoding="utf-8")
        print(f"[síntese] Painel atualizado: {self.INSIGHTS_PATH}")

    def _update_connections(self, notes: list[dict]) -> None:
        notes_block = self._format_notes_block(notes)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        wait_for_slot("synthesis:connections")
        completion = self.provider.complete(CompletionRequest(
            system=textwrap.dedent("""\
                Você é um analista de conexões entre informações.
                Seu trabalho é encontrar links não óbvios entre notas de pesquisa.
                Responda em português. Use listas e tabelas quando ajudar.
            """),
            messages=[Message(role="user", content=textwrap.dedent(f"""\
                Analise as notas abaixo e gere EXATAMENTE 5 conexões entre elas.

                IMPORTANTE: Use o formato [[Título Exato da Nota]] para criar links clicáveis no Obsidian.
                O título exato de cada nota está no campo "Título" de cada nota abaixo.

                Data/hora: {now}

                NOTAS:
                {notes_block}

                Estrutura obrigatória — seja conciso, máximo 600 tokens:

                # Mapa de Conexões — {now}

                ## Conexões identificadas

                **Conexão 1:** [[Título Exato da Nota A]] ↔ [[Título Exato da Nota B]]
                → O que as liga e por que importa.

                **Conexão 2:** [[Título Exato da Nota A]] ↔ [[Título Exato da Nota B]]
                → O que as liga e por que importa.

                **Conexão 3:** [[Título Exato da Nota A]] ↔ [[Título Exato da Nota B]]
                → O que as liga e por que importa.

                ## Hipótese
                (o que essas conexões sugerem juntas em 1-2 frases?)

                ## Ação recomendada
                (1 ação concreta)
            """))],
            temperature=0.3,
            max_tokens=700,
            model=self.model,
        ))

        target = self.vault_path / self.CONNECTIONS_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(completion.text, encoding="utf-8")
        print(f"[síntese] Mapa de conexões atualizado: {self.CONNECTIONS_PATH}")

    def _format_notes_block(self, notes: list[dict]) -> str:
        blocks = []
        for note in notes:
            blocks.append(textwrap.dedent(f"""\
                ---
                Título: {note['title']}
                Caminho: {note['path']}
                Modificado: {note['modified_at']}
                Conteúdo:
                {note['content'][:1500]}
            """))
        return "\n".join(blocks)


def main() -> None:
    _load_dotenv(ROOT / ".env")

    vault_raw = os.environ.get("OBSIDIAN_AI_VAULT", "obsidian-ai-vault")
    vault_path = _resolve_vault_path(vault_raw)
    loop_minutes = int(os.environ.get("OBSIDIAN_SYNTHESIS_INTERVAL", "30"))

    worker = ObsidianSynthesisWorker(vault_path=vault_path, loop_minutes=loop_minutes)
    worker.run_forever()


if __name__ == "__main__":
    main()
