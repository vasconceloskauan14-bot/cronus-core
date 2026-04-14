"""
CRONUS — Local Auto-Restart Manager
Mantém todos os workers vivos. Se um cair, reinicia em 30s.
Chamado pelo Agendador de Tarefas do Windows ao iniciar o PC.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UV = Path(os.environ.get("UV_PATH", r"C:\Users\adria\.local\bin\uv.exe"))
PYTHON = sys.executable

LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)


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


def _log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_DIR / "autostart.log", "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


WORKERS = [
    ("obsidian-ai",        ["run.py", "auto", "obsidian-ai"]),
    ("painel-config",      ["automation/painel_server.py"]),
    ("obsidian-radar",     ["run.py", "auto", "obsidian-radar"]),
    ("obsidian-synthesis", ["run.py", "auto", "obsidian-synthesis"]),
    ("obsidian-news",      ["run.py", "auto", "obsidian-news"]),
]


def _start(name: str, args: list[str]) -> subprocess.Popen:
    """Inicia um worker como processo independente."""
    cmd = [str(UV), "run", "--directory", str(ROOT), "python"] + args
    log_file = open(LOG_DIR / f"{name}.log", "a", encoding="utf-8", buffering=1)
    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        stdout=log_file,
        stderr=log_file,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    _log(f"[{name}] iniciado (PID {proc.pid})")
    return proc


def main() -> None:
    _load_dotenv()
    _log("=== CRONUS Local Manager iniciado ===")

    # Aguarda 5s para o sistema carregar antes de subir tudo
    time.sleep(5)

    procs: dict[str, subprocess.Popen | None] = {name: None for name, _ in WORKERS}
    worker_map = {name: args for name, args in WORKERS}

    # Inicia todos com 2s de intervalo
    for name, args in WORKERS:
        try:
            procs[name] = _start(name, args)
        except Exception as e:
            _log(f"[{name}] ERRO ao iniciar: {e}")
        time.sleep(2)

    _log("Todos os workers iniciados. Monitorando...")

    # Loop de watchdog — reinicia quem cair
    while True:
        time.sleep(30)
        for name, args in WORKERS:
            proc = procs.get(name)
            if proc is None or proc.poll() is not None:
                code = proc.returncode if proc else "N/A"
                _log(f"[{name}] caiu (código {code}), reiniciando...")
                try:
                    procs[name] = _start(name, worker_map[name])
                except Exception as e:
                    _log(f"[{name}] falhou ao reiniciar: {e}")
                    procs[name] = None


if __name__ == "__main__":
    main()
