"""
Event Triggers — ULTIMATE CRONUS
Monitor de eventos em tempo real: alterações de arquivos + webhook receiver.

Uso:
    python event_triggers.py --start              # inicia file watcher + webhook server
    python event_triggers.py --webhook-only       # só webhook (porta 8080)
    python event_triggers.py --watch-only         # só file watcher
    python event_triggers.py --port 9000          # porta customizada
"""

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.resolve()

# ── Configuração de triggers ─────────────────────────────────────────────────

FILE_TRIGGERS = [
    {
        "watch_dir": str(BASE_DIR / "data"),
        "pattern": "*.json",
        "action": "analyst",
        "description": "Nova métrica → rodar ANALYST",
    },
    {
        "watch_dir": str(BASE_DIR / "agents" / "output"),
        "pattern": "*.json",
        "action": "summarize",
        "description": "Novo resultado de agente → sumarizar",
    },
]

WEBHOOK_ROUTES = {
    "/github": "handle_github",
    "/stripe": "handle_stripe",
    "/slack":  "handle_slack",
    "/health": "handle_health",
}


# ── File Watcher ─────────────────────────────────────────────────────────────

class FileWatcher:
    def __init__(self):
        self._seen: dict[str, float] = {}
        self._running = False

    def start(self):
        self._running = True
        print("👁️  File Watcher iniciado")
        while self._running:
            for trigger in FILE_TRIGGERS:
                watch_dir = Path(trigger["watch_dir"])
                if not watch_dir.exists():
                    continue
                for pattern in [trigger["pattern"]]:
                    for f in watch_dir.glob(pattern):
                        mtime = f.stat().st_mtime
                        key = str(f)
                        if key not in self._seen or self._seen[key] != mtime:
                            if key in self._seen:  # arquivo modificado (não novo na primeira vez)
                                self._on_change(f, trigger)
                            self._seen[key] = mtime
            time.sleep(5)

    def stop(self):
        self._running = False

    def _on_change(self, filepath: Path, trigger: dict):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{ts}] 📁 Mudança detectada: {filepath.name}")
        print(f"       → {trigger['description']}")
        action = trigger["action"]
        if action == "analyst":
            self._run_analyst(filepath)
        elif action == "summarize":
            self._summarize(filepath)

    def _run_analyst(self, filepath: Path):
        try:
            sys.path.insert(0, str(BASE_DIR / "agents"))
            from analyst_agent import AnalystAgent
            agent = AnalystAgent()
            result = agent.analyze(str(filepath), "Quais são os principais insights deste arquivo?")
            print(f"  ✅ ANALYST concluído")
        except Exception as e:
            print(f"  ❌ ANALYST erro: {e}")

    def _summarize(self, filepath: Path):
        try:
            sys.path.insert(0, str(BASE_DIR / "agents"))
            from base_agent import BaseAgent
            agent = BaseAgent(name="summarizer")
            content = filepath.read_text(encoding="utf-8")[:3000]
            summary = agent.ask(f"Resuma em 3 bullets o resultado deste agente:\n\n{content}")
            print(f"  📝 Resumo: {summary[:200]}")
        except Exception as e:
            print(f"  ❌ Summarize erro: {e}")


# ── Webhook Server ────────────────────────────────────────────────────────────

class WebhookServer:
    def __init__(self, port: int = 8080):
        self.port = port

    def start(self):
        try:
            from flask import Flask, request, jsonify
        except ImportError:
            print("⚠️  Flask não instalado. Rode: pip install flask")
            return

        app = Flask("ULTIMATE_CRONUS_WEBHOOKS")

        @app.route("/health", methods=["GET"])
        def health():
            return jsonify({"status": "ok", "system": "ULTIMATE CRONUS", "time": datetime.now().isoformat()})

        @app.route("/github", methods=["POST"])
        def github():
            event = request.headers.get("X-GitHub-Event", "unknown")
            payload = request.get_json(silent=True) or {}
            print(f"\n🐙 GitHub Event: {event}")
            if event == "push":
                branch = payload.get("ref", "").replace("refs/heads/", "")
                repo = payload.get("repository", {}).get("name", "?")
                commits = len(payload.get("commits", []))
                print(f"   Push em {repo}/{branch} — {commits} commit(s)")
                threading.Thread(target=self._handle_push, args=(payload,), daemon=True).start()
            elif event == "pull_request":
                action = payload.get("action")
                pr_title = payload.get("pull_request", {}).get("title", "?")
                print(f"   PR {action}: {pr_title}")
                if action == "opened":
                    threading.Thread(target=self._handle_pr, args=(payload,), daemon=True).start()
            return jsonify({"received": True})

        @app.route("/stripe", methods=["POST"])
        def stripe():
            payload = request.get_json(silent=True) or {}
            event_type = payload.get("type", "unknown")
            print(f"\n💳 Stripe Event: {event_type}")
            if "payment" in event_type or "subscription" in event_type:
                amount = payload.get("data", {}).get("object", {}).get("amount", 0)
                print(f"   Valor: R$ {amount/100:.2f}")
            return jsonify({"received": True})

        @app.route("/slack", methods=["POST"])
        def slack():
            payload = request.get_json(silent=True) or {}
            # Slack challenge verification
            if "challenge" in payload:
                return jsonify({"challenge": payload["challenge"]})
            event = payload.get("event", {})
            if event.get("type") == "message" and "cronus" in event.get("text", "").lower():
                text = event.get("text", "")
                print(f"\n💬 Slack mention: {text[:100]}")
            return jsonify({"ok": True})

        print(f"🌐 Webhook Server iniciado em http://localhost:{self.port}")
        print(f"   Rotas: {', '.join(WEBHOOK_ROUTES.keys())}")
        app.run(host="0.0.0.0", port=self.port, debug=False, use_reloader=False)

    def _handle_push(self, payload: dict):
        """Dispara code review automático após push."""
        try:
            sys.path.insert(0, str(BASE_DIR / "agents"))
            from base_agent import BaseAgent
            agent = BaseAgent(name="code_reviewer")
            commits = payload.get("commits", [])
            if commits:
                files_changed = [f for c in commits for f in c.get("modified", []) + c.get("added", [])]
                review = agent.ask(
                    f"Faça um code review rápido. Arquivos alterados: {files_changed[:10]}. "
                    f"Commits: {[c.get('message','') for c in commits[:5]]}. "
                    "Liste possíveis problemas e sugestões em bullet points."
                )
                print(f"\n🔍 Code Review automático:\n{review[:500]}")
        except Exception as e:
            print(f"  ❌ Code review erro: {e}")

    def _handle_pr(self, payload: dict):
        """Analisa PR automaticamente."""
        try:
            pr = payload.get("pull_request", {})
            title = pr.get("title", "")
            body = pr.get("body", "")
            print(f"  🔍 Analisando PR: {title}")
        except Exception as e:
            print(f"  ❌ PR análise erro: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Event Triggers — ULTIMATE CRONUS")
    parser.add_argument("--start", action="store_true", help="Inicia file watcher + webhook")
    parser.add_argument("--webhook-only", action="store_true")
    parser.add_argument("--watch-only", action="store_true")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    if not any([args.start, args.webhook_only, args.watch_only]):
        args.start = True  # default: inicia tudo

    print("\n⚡ ULTIMATE CRONUS — Event Triggers\n")

    threads = []

    if args.start or args.watch_only:
        watcher = FileWatcher()
        t = threading.Thread(target=watcher.start, daemon=True)
        t.start()
        threads.append(t)

    if args.start or args.webhook_only:
        server = WebhookServer(port=args.port)
        t = threading.Thread(target=server.start, daemon=True)
        t.start()
        threads.append(t)

    print("\nPressione Ctrl+C para parar.\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹️  Parando Event Triggers...")


if __name__ == "__main__":
    main()
