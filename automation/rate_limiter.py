"""
Limitador de taxa global para chamadas à API Groq.
Usa mutex atômico (O_CREAT | O_EXCL) para garantir que apenas 1 chamada
aconteça a cada MIN_INTERVAL_SECONDS, mesmo com múltiplos processos.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_LOCK_FILE = ROOT / "state" / ".api_lock"
_MUTEX_FILE = ROOT / "state" / ".api_mutex"
MIN_INTERVAL_SECONDS = 62  # 1 chamada por minuto — garante <= 6000 TPM no Groq free tier


def wait_for_slot(caller: str = "") -> None:
    """Bloqueia até ser seguro fazer uma chamada à API. Atômico entre processos."""
    _LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)

    while True:
        if not _acquire_mutex():
            time.sleep(0.3)
            continue

        wait = MIN_INTERVAL_SECONDS  # fallback
        try:
            now = time.time()
            last = _read_last()
            elapsed = now - last
            wait = MIN_INTERVAL_SECONDS - elapsed

            if wait <= 0:
                # Reserva o slot escrevendo o timestamp com mutex ainda ativo
                _write_last(now, caller)
                return  # finally vai liberar o mutex antes de retornar
        finally:
            _release_mutex()

        # wait > 0 — dorme FORA do mutex para não bloquear outros processos
        actual_wait = min(max(wait - 0.5, 1.0), 20.0)
        print(f"[rate_limiter] {caller} aguardando {wait:.0f}s...")
        time.sleep(actual_wait)


def _acquire_mutex(stale_seconds: float = 10.0) -> bool:
    """Cria o arquivo mutex atomicamente. Retorna True se adquirido."""
    try:
        fd = os.open(str(_MUTEX_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        try:
            os.write(fd, str(os.getpid()).encode())
        finally:
            os.close(fd)
        return True
    except FileExistsError:
        # Verifica se o mutex está travado (processo morreu sem liberar)
        try:
            age = time.time() - _MUTEX_FILE.stat().st_mtime
            if age > stale_seconds:
                try:
                    _MUTEX_FILE.unlink()
                except Exception:
                    pass
        except Exception:
            pass
        return False
    except Exception:
        return False


def _release_mutex() -> None:
    try:
        _MUTEX_FILE.unlink()
    except Exception:
        pass


def _read_last() -> float:
    try:
        raw = _LOCK_FILE.read_text(encoding="utf-8").strip()
        return float(raw.split("|")[0])
    except Exception:
        return 0.0


def _write_last(ts: float, caller: str) -> None:
    try:
        _LOCK_FILE.write_text(f"{ts}|{caller}", encoding="utf-8")
    except Exception:
        pass
