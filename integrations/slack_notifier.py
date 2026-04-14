"""
Slack Notifier — ULTIMATE CRONUS
Envia alertas, relatórios e updates de KPIs para canais Slack.

Uso:
    python slack_notifier.py --message "RADAR detectou anomalia" --urgency high
    python slack_notifier.py --report reports/daily/2026-04-08.md --channel #cronus-reports
    python slack_notifier.py --kpis data/kpis_today.json
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def _get_webhook() -> str:
    url = os.environ.get("SLACK_WEBHOOK_URL", "")
    if not url:
        print("⚠️  Configure a variável SLACK_WEBHOOK_URL no seu .env")
        sys.exit(1)
    return url


def send_alert(message: str, channel: str = "", urgency: str = "normal") -> bool:
    """Envia alerta com emoji por nível de urgência."""
    import urllib.request

    icons = {"low": "ℹ️", "normal": "📢", "high": "⚠️", "critical": "🚨"}
    icon = icons.get(urgency, "📢")

    payload: dict = {
        "text": f"{icon} *ULTIMATE CRONUS* — {message}",
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"{icon} *{urgency.upper()}*\n{message}"},
            },
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": f"_{datetime.now().strftime('%d/%m/%Y %H:%M')}_"}],
            },
        ],
    }
    if channel:
        payload["channel"] = channel

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(_get_webhook(), data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            ok = resp.status == 200
            print(f"{'✅' if ok else '❌'} Slack: {message[:60]}")
            return ok
    except Exception as e:
        print(f"❌ Erro Slack: {e}")
        return False


def send_report(report_path: str, channel: str = "") -> bool:
    """Envia relatório Markdown formatado para Slack."""
    import urllib.request

    path = Path(report_path)
    if not path.exists():
        print(f"❌ Arquivo não encontrado: {report_path}")
        return False

    content = path.read_text(encoding="utf-8")
    # Pega título e primeiras 500 chars
    lines = content.splitlines()
    title = next((l.lstrip("# ") for l in lines if l.startswith("#")), path.stem)
    preview = " ".join(l for l in lines[1:] if l.strip())[:400]

    payload: dict = {
        "text": f"📊 *{title}*",
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": f"📊 {title}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": preview + "..."}},
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": f"_Relatório: `{path.name}` — {datetime.now().strftime('%d/%m %H:%M')}_"}],
            },
        ],
    }
    if channel:
        payload["channel"] = channel

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(_get_webhook(), data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            ok = resp.status == 200
            print(f"{'✅' if ok else '❌'} Relatório enviado: {title}")
            return ok
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


def send_kpi_update(kpis_path: str, channel: str = "") -> bool:
    """Envia update de KPIs com formatação rica."""
    import urllib.request

    path = Path(kpis_path)
    if not path.exists():
        print(f"❌ Arquivo não encontrado: {kpis_path}")
        return False

    data_obj = json.loads(path.read_text(encoding="utf-8"))
    current = data_obj.get("current", {})
    previous = data_obj.get("previous", {})

    lines = ["*📊 KPI Update — ULTIMATE CRONUS*\n"]
    for key, val in list(current.items())[:8]:
        prev = previous.get(key)
        if isinstance(val, (int, float)) and isinstance(prev, (int, float)) and prev:
            delta_pct = (val - prev) / prev * 100
            trend = "▲" if delta_pct > 0 else "▼"
            color = "🟢" if delta_pct > 0 else "🔴"
            lines.append(f"{color} *{key.replace('_',' ').title()}*: {val:,.0f} {trend} {abs(delta_pct):.1f}%")
        else:
            lines.append(f"● *{key.replace('_',' ').title()}*: {val}")

    payload: dict = {
        "text": "\n".join(lines),
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(lines)}},
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": f"_{datetime.now().strftime('%d/%m/%Y %H:%M')}_"}],
            },
        ],
    }
    if channel:
        payload["channel"] = channel

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(_get_webhook(), data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            ok = resp.status == 200
            print(f"{'✅' if ok else '❌'} KPI update enviado")
            return ok
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Slack Notifier — ULTIMATE CRONUS")
    parser.add_argument("--message", help="Mensagem de alerta")
    parser.add_argument("--urgency", default="normal", choices=["low", "normal", "high", "critical"])
    parser.add_argument("--report", help="Caminho para relatório .md")
    parser.add_argument("--kpis", help="Caminho para JSON de KPIs")
    parser.add_argument("--channel", default="", help="Canal Slack (ex: #cronus-reports)")
    args = parser.parse_args()

    if args.message:
        send_alert(args.message, args.channel, args.urgency)
    elif args.report:
        send_report(args.report, args.channel)
    elif args.kpis:
        send_kpi_update(args.kpis, args.channel)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
