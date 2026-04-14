from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
import re
import textwrap
import unicodedata
import uuid


WORD_RE = re.compile(r"[0-9A-Za-zÀ-ÿ][0-9A-Za-zÀ-ÿ_-]{2,}")


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = "".join(char for char in normalized if not unicodedata.combining(char))
    ascii_value = ascii_value.casefold()
    ascii_value = re.sub(r"[^a-z0-9]+", "-", ascii_value)
    return ascii_value.strip("-") or f"nota-{int(datetime.now().timestamp())}"


def _tokenize(value: str) -> list[str]:
    return [match.group(0).casefold() for match in WORD_RE.finditer(value)]


def _clean_excerpt(value: str, max_chars: int = 220) -> str:
    compact = " ".join(value.split())
    return compact[: max_chars - 1] + "…" if len(compact) > max_chars else compact


@dataclass
class MemoryHit:
    title: str
    path: str
    score: float
    snippet: str
    modified_at: str

    def to_dict(self) -> dict:
        return asdict(self)


class ObsidianMemoryStore:
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path.resolve()
        self.obsidian_dir = self.vault_path / ".obsidian"
        self.inbox_dir = self.vault_path / "Inbox"
        self.memory_dir = self.vault_path / "Memoria"
        self.sessions_dir = self.memory_dir / "Conversas"
        self.daily_dir = self.memory_dir / "Diario"
        self.zeus_dir = self.memory_dir / "Zeus"
        self.zeus_records_dir = self.zeus_dir / "Registros"
        self.zeus_core_path = self.zeus_dir / "00 - Nucleo.md"
        self.zeus_commands_path = self.zeus_dir / "Comandos.md"
        self.zeus_speech_path = self.zeus_dir / "Falas.md"
        self.zeus_evolution_path = self.zeus_dir / "Evolucao.md"

    def bootstrap(self) -> None:
        for directory in (
            self.vault_path,
            self.obsidian_dir,
            self.inbox_dir,
            self.memory_dir,
            self.sessions_dir,
            self.daily_dir,
            self.zeus_dir,
            self.zeus_records_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

        self._write_if_missing(
            self.obsidian_dir / "app.json",
            '{\n  "alwaysUpdateLinks": true,\n  "spellcheck": true\n}\n',
        )
        self._write_if_missing(
            self.vault_path / "00 - Home.md",
            textwrap.dedent(
                """\
                # IA com Memoria no Obsidian

                Este vault guarda a memoria da IA local.

                ## Comeco rapido
                - Abra esta pasta no Obsidian.
                - Converse com a IA pelo servidor local.
                - Edite as notas em `Memoria/` para ensinar contexto permanente.

                ## Areas principais
                - [[Memoria/Identidade]]
                - [[Memoria/Fatos Importantes]]
                - [[01 - Zeus]]
                - [[Inbox/Como usar]]
                """
            ),
        )
        self._write_if_missing(
            self.vault_path / "01 - Zeus.md",
            textwrap.dedent(
                """\
                # Zeus

                Este e o cerebro operacional do Zeus dentro do vault.

                ## Nucleo
                - [[Memoria/Zeus/00 - Nucleo]]
                - [[Memoria/Zeus/Comandos]]
                - [[Memoria/Zeus/Falas]]
                - [[Memoria/Zeus/Evolucao]]

                ## Como ensinar
                - Use a interface local para registrar novos comandos e falas.
                - Salve regras estaveis no nucleo.
                - Consulte a evolucao para acompanhar o que o Zeus aprendeu.
                """
            ),
        )
        self._write_if_missing(
            self.inbox_dir / "Como usar.md",
            textwrap.dedent(
                """\
                # Como usar

                Use esta pasta para jogar contexto novo para a IA:

                - briefings
                - ideias
                - links resumidos
                - processos
                - preferencias

                Quanto mais claro estiver o titulo e o texto, melhor a recuperacao.
                """
            ),
        )
        self._write_if_missing(
            self.memory_dir / "Identidade.md",
            textwrap.dedent(
                """\
                # Identidade

                Descreva aqui quem a IA deve ser, como responder e quais prioridades seguir.

                ## Exemplo
                - Responder em portugues.
                - Ser objetiva e pratica.
                - Priorizar automacao local e memoria confiavel.
                """
            ),
        )
        self._write_if_missing(
            self.memory_dir / "Fatos Importantes.md",
            textwrap.dedent(
                """\
                # Fatos Importantes

                Guarde aqui informacoes estaveis que a IA precisa lembrar.

                ## Negocio
                -

                ## Preferencias
                -

                ## Projetos em andamento
                -
                """
            ),
        )
        self._write_if_missing(
            self.zeus_core_path,
            textwrap.dedent(
                """\
                # Nucleo do Zeus

                Zeus e o cerebro operacional desta base.

                ## Missao
                - Aprender comandos, falas, preferencias e regras do usuario.
                - Recuperar isso nas proximas conversas.
                - Evoluir sem perder o historico do que foi ensinado.

                ## Regras operacionais
                - Confirmar quando estiver inferindo.
                - Priorizar memoria do vault antes de inventar respostas.
                - Manter linguagem pratica, direta e colaborativa.

                ## Preferencias do usuario
                - Responder em portugues.
                - Aprender a partir de exemplos reais enviados pelo usuario.
                """
            ),
        )
        self._write_if_missing(
            self.zeus_commands_path,
            textwrap.dedent(
                """\
                # Comandos do Zeus

                Aqui ficam os comandos, atalhos, macros e instrucoes operacionais ensinadas pelo usuario.
                """
            ),
        )
        self._write_if_missing(
            self.zeus_speech_path,
            textwrap.dedent(
                """\
                # Falas do Zeus

                Aqui ficam frases, intencoes, gatilhos e formas de interpretar o jeito do usuario falar.
                """
            ),
        )
        self._write_if_missing(
            self.zeus_evolution_path,
            textwrap.dedent(
                """\
                # Evolucao do Zeus

                Este arquivo registra tudo que o Zeus aprendeu ao longo do tempo.
                """
            ),
        )

    def note_count(self) -> int:
        return len(self._all_markdown_files())

    def session_count(self) -> int:
        return len(list(self.sessions_dir.glob("*.md")))

    def new_session_id(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"sessao-{timestamp}-{uuid.uuid4().hex[:8]}"

    def search(self, query: str, limit: int = 5) -> list[MemoryHit]:
        query = query.strip()
        if not query:
            return []

        query_tokens = set(_tokenize(query))
        if not query_tokens:
            return []

        results: list[MemoryHit] = []
        for path in self._all_markdown_files():
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            lowered = text.casefold()
            title = path.stem
            title_lower = title.casefold()
            note_tokens = set(_tokenize(text))

            overlap = sum(1 for token in query_tokens if token in note_tokens)
            if not overlap and query.casefold() not in lowered and all(token not in title_lower for token in query_tokens):
                continue

            score = float(overlap)
            if query.casefold() in lowered:
                score += 4.0
            if any(token in title_lower for token in query_tokens):
                score += 2.0

            modified_at = datetime.fromtimestamp(path.stat().st_mtime)
            age_days = max((datetime.now() - modified_at).days, 0)
            if age_days <= 1:
                score += 1.25
            elif age_days <= 7:
                score += 0.5

            results.append(
                MemoryHit(
                    title=title,
                    path=path.relative_to(self.vault_path).as_posix(),
                    score=round(score, 2),
                    snippet=self._build_snippet(text, query_tokens),
                    modified_at=modified_at.isoformat(timespec="seconds"),
                )
            )

        results.sort(key=lambda item: (-item.score, item.modified_at))
        return results[:limit]

    def build_context(self, query: str, limit: int = 5, max_chars: int = 5000) -> tuple[str, list[MemoryHit]]:
        hits = self.search(query=query, limit=limit)
        if not hits:
            return "", []

        chunks: list[str] = []
        current_size = 0
        for hit in hits:
            source_path = self.vault_path / Path(hit.path)
            try:
                body = source_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            excerpt = _clean_excerpt(body, max_chars=900)
            chunk = f"[{hit.path}]\n{excerpt}"
            extra = len(chunk) + 2
            if current_size + extra > max_chars:
                break
            chunks.append(chunk)
            current_size += extra

        return "\n\n".join(chunks), hits

    def read_identity_context(self) -> str:
        return self._read_optional(self.memory_dir / "Identidade.md")

    def read_facts_context(self) -> str:
        return self._read_optional(self.memory_dir / "Fatos Importantes.md")

    def read_zeus_context(self) -> str:
        chunks = [
            self._read_optional(self.zeus_core_path),
            self._read_optional(self.zeus_commands_path),
            self._read_optional(self.zeus_speech_path),
            self._read_optional(self.zeus_evolution_path),
        ]
        return "\n\n".join(chunk for chunk in chunks if chunk.strip())

    def recent_session_context(self, session_id: str, max_chars: int = 4000) -> str:
        session_path = self.session_path(session_id)
        if not session_path.exists():
            return ""
        content = session_path.read_text(encoding="utf-8", errors="ignore")
        return content[-max_chars:]

    def save_exchange(self, session_id: str, user_message: str, assistant_message: str, memory_hits: list[MemoryHit]) -> Path:
        session_path = self.session_path(session_id)
        self._ensure_session_file(session_path=session_path, session_id=session_id)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        memory_paths = ", ".join(hit.path for hit in memory_hits) if memory_hits else "nenhuma nota recuperada"
        with session_path.open("a", encoding="utf-8") as handle:
            handle.write(f"\n### {timestamp} | usuario\n\n{user_message.strip()}\n")
            handle.write(f"\n### {timestamp} | assistente\n\n{assistant_message.strip()}\n")
            handle.write(f"\n> memoria_consultada: {memory_paths}\n")

        daily_path = self.daily_dir / f"{datetime.now().strftime('%Y-%m-%d')}.md"
        if not daily_path.exists():
            daily_path.write_text("# Diario da IA\n", encoding="utf-8")
        with daily_path.open("a", encoding="utf-8") as handle:
            handle.write(f"\n## {timestamp} | {session_id}\n")
            handle.write(f"**Usuario:** {_clean_excerpt(user_message, max_chars=240)}\n\n")
            handle.write(f"**Assistente:** {_clean_excerpt(assistant_message, max_chars=320)}\n\n")
            handle.write(f"**Memoria:** {memory_paths}\n")

        return session_path

    def create_note(self, title: str, content: str, folder: str = "Inbox") -> Path:
        title = title.strip() or "Nova nota"
        content = content.strip()
        relative_folder = Path(folder.strip() or "Inbox")
        if relative_folder.is_absolute():
            raise ValueError("A pasta da nota precisa ser relativa ao vault.")

        target_dir = (self.vault_path / relative_folder).resolve()
        if not str(target_dir).startswith(str(self.vault_path)):
            raise ValueError("Pasta de nota fora do vault.")

        target_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{_slugify(title)}.md"
        target_path = target_dir / filename

        if target_path.exists():
            target_path = target_dir / f"{_slugify(title)}-{uuid.uuid4().hex[:6]}.md"

        target_path.write_text(f"# {title}\n\n{content}\n", encoding="utf-8")
        return target_path

    def teach_zeus(
        self,
        title: str,
        content: str,
        category: str = "comando",
        source: str = "manual",
    ) -> dict:
        title = title.strip() or "Novo ensinamento"
        content = content.strip()
        if not content:
            raise ValueError("Conteudo vazio para ensinar o Zeus.")

        normalized_category = self._normalize_zeus_category(category)
        target_path = self._zeus_target_path(normalized_category)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_folder = datetime.now().strftime("%Y-%m-%d")
        archive_folder = f"Memoria/Zeus/Registros/{date_folder}"

        archive_content = textwrap.dedent(
            f"""\
            categoria: {normalized_category}
            fonte: {source}
            registrado_em: {timestamp}

            {content}
            """
        ).strip()
        archive_path = self.create_note(
            title=f"{normalized_category} - {title}",
            content=archive_content,
            folder=archive_folder,
        )

        entry = textwrap.dedent(
            f"""\

            ## {title}
            - categoria: {normalized_category}
            - fonte: {source}
            - atualizado_em: {timestamp}
            - registro: {archive_path.relative_to(self.vault_path).as_posix()}

            {content}
            """
        )
        with target_path.open("a", encoding="utf-8") as handle:
            handle.write(entry)
            if not entry.endswith("\n"):
                handle.write("\n")

        if target_path != self.zeus_evolution_path:
            evolution_entry = textwrap.dedent(
                f"""\

                ## {timestamp} | {normalized_category}
                - titulo: {title}
                - registro: {archive_path.relative_to(self.vault_path).as_posix()}
                - resumo: {_clean_excerpt(content, max_chars=220)}
                """
            )
            with self.zeus_evolution_path.open("a", encoding="utf-8") as handle:
                handle.write(evolution_entry)
                if not evolution_entry.endswith("\n"):
                    handle.write("\n")

        return {
            "title": title,
            "category": normalized_category,
            "target_path": target_path.relative_to(self.vault_path).as_posix(),
            "archive_path": archive_path.relative_to(self.vault_path).as_posix(),
            "recorded_at": timestamp,
        }

    def stats(self) -> dict:
        return {
            "vault_path": str(self.vault_path),
            "note_count": self.note_count(),
            "session_count": self.session_count(),
        }

    def session_path(self, session_id: str) -> Path:
        safe_session_id = re.sub(r"[^a-zA-Z0-9_-]+", "-", session_id).strip("-") or self.new_session_id()
        return self.sessions_dir / f"{safe_session_id}.md"

    def _ensure_session_file(self, session_path: Path, session_id: str) -> None:
        if session_path.exists():
            return
        session_path.parent.mkdir(parents=True, exist_ok=True)
        created_at = datetime.now().isoformat(timespec="seconds")
        session_path.write_text(
            textwrap.dedent(
                f"""\
                ---
                type: session
                session_id: {session_id}
                created_at: {created_at}
                ---

                # Sessao {session_id}
                """
            ),
            encoding="utf-8",
        )

    def _all_markdown_files(self) -> list[Path]:
        return [
            path
            for path in self.vault_path.rglob("*.md")
            if ".obsidian" not in path.parts
        ]

    def _build_snippet(self, text: str, query_tokens: set[str]) -> str:
        lowered = text.casefold()
        first_index = None
        for token in query_tokens:
            token_index = lowered.find(token)
            if token_index >= 0 and (first_index is None or token_index < first_index):
                first_index = token_index

        if first_index is None:
            return _clean_excerpt(text)

        start = max(first_index - 90, 0)
        end = min(first_index + 160, len(text))
        return _clean_excerpt(text[start:end])

    def _read_optional(self, path: Path) -> str:
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")

    def _write_if_missing(self, path: Path, content: str) -> None:
        if path.exists():
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _normalize_zeus_category(self, category: str) -> str:
        value = category.strip().casefold()
        aliases = {
            "comando": "comando",
            "comandos": "comando",
            "command": "comando",
            "commands": "comando",
            "fala": "fala",
            "falas": "fala",
            "speech": "fala",
            "frase": "fala",
            "frases": "fala",
            "preferencia": "preferencia",
            "preferencias": "preferencia",
            "regra": "regra",
            "regras": "regra",
            "evolucao": "evolucao",
            "aprendizado": "evolucao",
        }
        return aliases.get(value, "comando")

    def _zeus_target_path(self, category: str) -> Path:
        mapping = {
            "comando": self.zeus_commands_path,
            "fala": self.zeus_speech_path,
            "preferencia": self.zeus_core_path,
            "regra": self.zeus_core_path,
            "evolucao": self.zeus_evolution_path,
        }
        return mapping.get(category, self.zeus_commands_path)
