"""
GitHub Webhook — ULTIMATE CRONUS
Recebe eventos do GitHub e dispara automações: code review, análise de PR, changelog.

Uso:
    python github_webhook.py --start --port 5000
    python github_webhook.py --start --port 5000 --secret $GITHUB_WEBHOOK_SECRET
"""

import argparse
import hashlib
import hmac
import json
import os
import sys
import threading
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))


def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verifica assinatura HMAC do GitHub."""
    expected = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def handle_push(payload: dict):
    """Code review automático após push."""
    try:
        from base_agent import BaseAgent
        agent = BaseAgent(name="code_reviewer")

        repo = payload.get("repository", {}).get("full_name", "?")
        branch = payload.get("ref", "").replace("refs/heads/", "")
        commits = payload.get("commits", [])

        files_changed = []
        commit_msgs = []
        for c in commits[:5]:
            files_changed.extend(c.get("modified", []) + c.get("added", []))
            commit_msgs.append(c.get("message", ""))

        print(f"  📦 Push em {repo}/{branch} — {len(commits)} commit(s)")

        if not files_changed:
            return

        review = agent.ask(
            f"""Faça um code review rápido baseado nestas informações:

Repositório: {repo}
Branch: {branch}
Commits: {json.dumps(commit_msgs[:5])}
Arquivos alterados: {json.dumps(list(set(files_changed))[:20])}

Liste em bullets:
1. Possíveis problemas ou riscos
2. Boas práticas verificadas
3. Sugestões de melhoria
4. Aprovado para merge? (Sim/Não/Revisar)"""
        )

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = Path("output") / f"code_review_{ts}.md"
        out.parent.mkdir(exist_ok=True)
        out.write_text(f"# Code Review — {repo}/{branch}\n\n{review}\n", encoding="utf-8")
        print(f"  ✅ Code review salvo → {out}")
    except Exception as e:
        print(f"  ❌ Erro no code review: {e}")


def handle_pull_request(payload: dict):
    """Analisa PR automaticamente quando aberto."""
    action = payload.get("action")
    if action not in ("opened", "reopened", "synchronize"):
        return

    try:
        from base_agent import BaseAgent
        agent = BaseAgent(name="pr_analyzer")

        pr = payload.get("pull_request", {})
        title = pr.get("title", "")
        body = pr.get("body", "") or ""
        base = pr.get("base", {}).get("ref", "main")
        head = pr.get("head", {}).get("ref", "")
        url = pr.get("html_url", "")

        print(f"  🔀 PR {action}: {title}")

        analysis = agent.ask(
            f"""Analise este Pull Request e forneça feedback estruturado:

Título: {title}
Branch: {head} → {base}
URL: {url}
Descrição:
{body[:1000]}

Forneça:
1. Resumo do que muda
2. Riscos potenciais
3. Checklist de review (o que verificar manualmente)
4. Classificação: (feature/fix/refactor/docs/chore)
5. Impacto estimado: (alto/médio/baixo)
6. Recomendação: (aprovar/revisar/bloquear)"""
        )

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = Path("output") / f"pr_review_{ts}.md"
        out.parent.mkdir(exist_ok=True)
        out.write_text(f"# PR Review — {title}\n\n{analysis}\n", encoding="utf-8")
        print(f"  ✅ PR review salvo → {out}")
    except Exception as e:
        print(f"  ❌ Erro no PR review: {e}")


def start_server(port: int = 5000, secret: str = ""):
    try:
        from flask import Flask, jsonify, request
    except ImportError:
        print("❌ Flask não instalado. Rode: pip install flask")
        sys.exit(1)

    app = Flask("CRONUS_GitHub_Webhook")

    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "service": "CRONUS GitHub Webhook"})

    @app.route("/webhook", methods=["POST"])
    def webhook():
        # Verificar assinatura
        if secret:
            sig = request.headers.get("X-Hub-Signature-256", "")
            if not verify_signature(request.data, sig, secret):
                return jsonify({"error": "assinatura inválida"}), 403

        event = request.headers.get("X-GitHub-Event", "unknown")
        payload = request.get_json(silent=True) or {}
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{ts}] GitHub Event: {event}")

        if event == "push":
            threading.Thread(target=handle_push, args=(payload,), daemon=True).start()
        elif event == "pull_request":
            threading.Thread(target=handle_pull_request, args=(payload,), daemon=True).start()
        elif event == "ping":
            print(f"  🏓 Ping recebido — webhook configurado com sucesso!")

        return jsonify({"received": True, "event": event})

    print(f"\n🐙 GitHub Webhook Server rodando em http://localhost:{port}/webhook")
    print(f"   Configure no GitHub: Settings → Webhooks → http://SEU_IP:{port}/webhook")
    print(f"   Eventos: push, pull_request\n")
    app.run(host="0.0.0.0", port=port, debug=False)


def main():
    parser = argparse.ArgumentParser(description="GitHub Webhook — ULTIMATE CRONUS")
    parser.add_argument("--start", action="store_true")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--secret", default=os.environ.get("GITHUB_WEBHOOK_SECRET", ""))
    args = parser.parse_args()

    if args.start:
        start_server(args.port, args.secret)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
