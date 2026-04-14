"""
CRONUS Git Sync Worker
Roda no Railway: commita e faz push das notas novas para o GitHub a cada 30 min.
No PC local: Obsidian Git plugin faz pull automático.

Variáveis de ambiente necessárias no Railway:
  GIT_REPO_URL  = https://<token>@github.com/<user>/<repo>.git
  GIT_USER_NAME = CRONUS Bot
  GIT_USER_EMAIL = cronus@auto.bot
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _log(msg: str) -> None:
    print(f"[git-sync] {datetime.now().strftime('%H:%M:%S')} {msg}", flush=True)


def _run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    return result.returncode, (result.stdout + result.stderr).strip()


def _load_dotenv() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


def setup_git(vault: Path) -> bool:
    repo_url = os.environ.get("GIT_REPO_URL", "").strip()
    if not repo_url:
        _log("GIT_REPO_URL não configurada — sync desativado")
        return False

    name  = os.environ.get("GIT_USER_NAME", "CRONUS Bot")
    email = os.environ.get("GIT_USER_EMAIL", "cronus@auto.bot")

    # Inicia o repo se necessário
    git_dir = vault / ".git"
    if not git_dir.exists():
        _log("Inicializando repositório git no vault...")
        _run(["git", "init"], vault)
        _run(["git", "remote", "add", "origin", repo_url], vault)
        # Tenta fazer pull inicial para trazer notas já existentes no GitHub
        _run(["git", "fetch", "origin"], vault)
        code, _ = _run(["git", "checkout", "-B", "main", "origin/main"], vault)
        if code != 0:
            # Repo novo — primeiro commit
            _run(["git", "checkout", "-b", "main"], vault)

    _run(["git", "config", "user.name", name], vault)
    _run(["git", "config", "user.email", email], vault)
    _run(["git", "remote", "set-url", "origin", repo_url], vault)
    return True


def sync_once(vault: Path) -> bool:
    """Commita e faz push de tudo que mudou no vault. Retorna True se houve push."""
    # Verifica se há mudanças
    code, out = _run(["git", "status", "--porcelain"], vault)
    if code != 0:
        _log(f"Erro ao checar status git: {out}")
        return False

    if not out.strip():
        _log("Nenhuma nota nova para commitar")
        return False

    files_changed = len(out.strip().splitlines())
    _log(f"{files_changed} arquivo(s) alterado(s) — commitando...")

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    _run(["git", "add", "-A"], vault)
    _run(["git", "commit", "-m", f"CRONUS: notas atualizadas {now} ({files_changed} arquivo(s))"], vault)

    code, out = _run(["git", "push", "origin", "main", "--force-with-lease"], vault)
    if code == 0:
        _log(f"Push OK: {files_changed} arquivo(s) enviados para GitHub")
        return True
    else:
        # Tenta push forçado se houver conflito de histórico (primeiro push)
        code2, out2 = _run(["git", "push", "origin", "main", "--force"], vault)
        if code2 == 0:
            _log(f"Push forçado OK: {files_changed} arquivo(s)")
            return True
        _log(f"Erro no push: {out2}")
        return False


def run_forever(interval_minutes: int = 30) -> None:
    _load_dotenv()

    vault_raw = os.environ.get("OBSIDIAN_AI_VAULT", "obsidian-ai-vault").strip()
    vault = Path(vault_raw) if Path(vault_raw).is_absolute() else ROOT / vault_raw
    vault.mkdir(parents=True, exist_ok=True)

    _log(f"Vault: {vault}")
    _log(f"Sync a cada {interval_minutes} min")

    if not setup_git(vault):
        _log("Sync desativado — saindo")
        return

    while True:
        try:
            sync_once(vault)
        except Exception as e:
            _log(f"Erro inesperado: {e}")
        _log(f"Próximo sync em {interval_minutes} min...")
        time.sleep(interval_minutes * 60)


if __name__ == "__main__":
    interval = int(os.environ.get("GIT_SYNC_INTERVAL_MINUTES", "30"))
    run_forever(interval)
