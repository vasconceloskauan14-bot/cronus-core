"""
Servidor do Painel de Pesquisas — porta 8788
Gerencia leitura e escrita do config do radar.
"""
from __future__ import annotations

import json
import os
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

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


class PainelHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/radar/config":
            path = ROOT / "config" / "obsidian_radar.json"
            if path.exists():
                return self._json(json.loads(path.read_text(encoding="utf-8")))
            return self._json({"topics": []})
        self._json({"ok": False, "error": "not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self):
        if self.path == "/api/radar/config":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            data = json.loads(body.decode("utf-8"))
            path = ROOT / "config" / "obsidian_radar.json"
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            return self._json({"ok": True})
        self._json({"ok": False, "error": "not found"}, HTTPStatus.NOT_FOUND)

    def _json(self, payload, status=HTTPStatus.OK):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    _load_dotenv()
    port = int(os.environ.get("PAINEL_PORT", "8788"))
    srv = ThreadingHTTPServer(("127.0.0.1", port), PainelHandler)
    print(f"Painel server rodando em http://127.0.0.1:{port}")
    srv.serve_forever()
