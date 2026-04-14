"""
CRONUS Git Sync Worker — via GitHub API
Envia apenas arquivos NOVOS/MODIFICADOS para o GitHub sem conflitos de histórico.
Railway não precisa de git local — só usa a API do GitHub com requests.

Variáveis de ambiente necessárias:
  GIT_REPO_URL  = https://<token>@github.com/<user>/<repo>.git
  GIT_USER_NAME = CRONUS Bot          (opcional)
  GIT_SYNC_INTERVAL_MINUTES = 30      (opcional, default 30)
"""
from __future__ import annotations

import base64
import json
import os
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _log(msg: str) -> None:
    print(f"[git-sync] {datetime.now().strftime('%H:%M:%S')} {msg}", flush=True)


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


def _parse_repo_url(url: str) -> tuple[str, str]:
    """Extrai (token, owner/repo) da URL https://<token>@github.com/<owner>/<repo>.git"""
    try:
        # https://TOKEN@github.com/owner/repo.git
        after_https = url.replace("https://", "")
        token, rest = after_https.split("@", 1)
        repo = rest.replace("github.com/", "").replace(".git", "")
        return token, repo
    except Exception:
        return "", ""


def _github_get(url: str, token: str) -> dict:
    import urllib.request
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception:
        return {}


def _github_put(url: str, token: str, data: dict) -> bool:
    import urllib.request
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, method="PUT")
    req.add_header("Authorization", f"token {token}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/vnd.github.v3+json")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status in (200, 201)
    except Exception as e:
        _log(f"Erro no PUT {url}: {e}")
        return False


def _get_file_sha(token: str, repo: str, path: str) -> str | None:
    """Retorna o SHA do arquivo no GitHub, ou None se não existir."""
    info = _github_get(f"https://api.github.com/repos/{repo}/contents/{path}", token)
    return info.get("sha")


def _upload_file(token: str, repo: str, rel_path: str, content_bytes: bytes, message: str) -> bool:
    """Cria ou atualiza um arquivo no GitHub via API."""
    encoded = base64.b64encode(content_bytes).decode()
    sha = _get_file_sha(token, repo, rel_path)
    data: dict = {"message": message, "content": encoded}
    if sha:
        data["sha"] = sha
    return _github_put(
        f"https://api.github.com/repos/{repo}/contents/{rel_path}",
        token, data
    )


def _get_known_shas(token: str, repo: str) -> dict[str, str]:
    """Retorna {path: sha} de todos os arquivos já no GitHub (para detectar mudanças)."""
    tree = _github_get(
        f"https://api.github.com/repos/{repo}/git/trees/main?recursive=1",
        token
    )
    return {item["path"]: item["sha"] for item in tree.get("tree", []) if item.get("type") == "blob"}


def _local_sha(content: bytes) -> str:
    """Git blob SHA: sha1("blob <size>\0<content>")"""
    import hashlib
    header = f"blob {len(content)}\0".encode()
    return hashlib.sha1(header + content).hexdigest()


def sync_once(vault: Path, token: str, repo: str) -> int:
    """Envia arquivos novos/modificados do vault para o GitHub. Retorna nº de arquivos enviados."""
    _log("Verificando arquivos novos no vault...")

    # Arquivos que já estão no GitHub (path → sha)
    known = _get_known_shas(token, repo)

    # Só sincroniza notas de pesquisa (Radar + probabilisticas + Feed + Insights)
    sync_patterns = [
        "Memoria/Radar/**/*.md",
        "Memoria/Feed/*.md",
        "Memoria/Insights/*.md",
        "Memoria/Pesquisas/**/*.md",
        "probabilisticas/**/*.md",
    ]

    to_upload: list[Path] = []
    for pattern in sync_patterns:
        to_upload.extend(vault.glob(pattern))

    if not to_upload:
        _log("Nenhuma nota de pesquisa encontrada ainda")
        return 0

    uploaded = 0
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    for local_path in to_upload:
        try:
            content = local_path.read_bytes()
        except Exception:
            continue

        rel = local_path.relative_to(vault).as_posix()
        local_blob_sha = _local_sha(content)

        # Só envia se for novo ou diferente
        if known.get(rel) == local_blob_sha:
            continue

        ok = _upload_file(token, repo, rel, content, f"CRONUS: {rel} ({now_str})")
        if ok:
            uploaded += 1
            _log(f"  ✓ {rel}")
        else:
            _log(f"  ✗ falhou: {rel}")

        # Pausa pequena para não saturar a API do GitHub
        time.sleep(0.5)

    return uploaded


def run_forever(interval_minutes: int = 30) -> None:
    _load_dotenv()

    repo_url = os.environ.get("GIT_REPO_URL", "").strip()
    if not repo_url:
        _log("GIT_REPO_URL não configurada — sync desativado")
        return

    token, repo = _parse_repo_url(repo_url)
    if not token or not repo:
        _log(f"GIT_REPO_URL inválida: {repo_url}")
        return

    vault_raw = os.environ.get("OBSIDIAN_AI_VAULT", "obsidian-ai-vault").strip()
    vault = Path(vault_raw) if Path(vault_raw).is_absolute() else ROOT / vault_raw
    vault.mkdir(parents=True, exist_ok=True)

    _log(f"Vault: {vault}")
    _log(f"Repo: {repo}")
    _log(f"Sync a cada {interval_minutes} min")

    while True:
        try:
            n = sync_once(vault, token, repo)
            if n > 0:
                _log(f"{n} arquivo(s) enviados para GitHub")
            else:
                _log("Nenhuma nota nova para enviar")
        except Exception as e:
            _log(f"Erro inesperado: {e}")

        _log(f"Próximo sync em {interval_minutes} min...")
        time.sleep(interval_minutes * 60)


if __name__ == "__main__":
    interval = int(os.environ.get("GIT_SYNC_INTERVAL_MINUTES", "30"))
    run_forever(interval)
