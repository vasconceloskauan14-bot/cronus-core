"""
CRONUS Cloud Starter
Inicia todos os workers em background + servidor HTTP na porta $PORT.
Deploy: Railway, Render, DigitalOcean, Oracle Cloud, etc.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _load_dotenv() -> None:
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _resolve_vault(raw: str) -> Path:
    raw = raw.strip() or "obsidian-ai-vault"
    p = Path(raw)
    if not p.is_absolute():
        p = ROOT / p
    return p.resolve()


def main() -> None:
    _load_dotenv()

    # Railway injeta PORT automaticamente
    port = int(os.environ.get("PORT", os.environ.get("OBSIDIAN_AI_PORT", "8787")))
    host = os.environ.get("OBSIDIAN_AI_HOST", "0.0.0.0")

    python = sys.executable

    workers = [
        ("obsidian-radar",     [python, str(ROOT / "automation/obsidian_radar_worker.py")]),
        ("obsidian-synthesis", [python, str(ROOT / "automation/obsidian_synthesis_worker.py")]),
        ("obsidian-news",      [python, str(ROOT / "automation/obsidian_news_worker.py")]),
        ("git-sync",           [python, str(ROOT / "automation/git_sync_worker.py")]),
    ]

    procs: list[tuple[str, subprocess.Popen]] = []
    for name, cmd in workers:
        print(f"[cloud] iniciando worker: {name}")
        p = subprocess.Popen(cmd, cwd=str(ROOT))
        procs.append((name, p))
        time.sleep(1)

    # Importa aqui para não bloquear antes dos workers subirem
    sys.path.insert(0, str(ROOT))
    from automation.obsidian_memory_ai import create_server

    vault_path = _resolve_vault(os.environ.get("OBSIDIAN_AI_VAULT", "obsidian-ai-vault"))
    vault_path.mkdir(parents=True, exist_ok=True)
    (ROOT / "state").mkdir(parents=True, exist_ok=True)

    server = create_server(
        host=host,
        port=port,
        vault_path=vault_path,
        provider_alias=os.environ.get("OBSIDIAN_AI_PROVIDER", ""),
        model=os.environ.get("OBSIDIAN_AI_MODEL", ""),
    )

    print(f"[cloud] CRONUS rodando em http://{host}:{port}")
    print(f"[cloud] API de noticias: http://{host}:{port}/api/news")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[cloud] Encerrando...")
        for name, p in procs:
            p.terminate()
            print(f"[cloud] worker {name} encerrado")


if __name__ == "__main__":
    main()
