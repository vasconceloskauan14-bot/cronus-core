"""
Daily Report — ULTIMATE CRONUS
Gera relatório executivo diário com análise por Claude.

Uso:
    python daily_report.py                    # relatório de hoje
    python daily_report.py --date 2026-04-07  # relatório de data específica
    python daily_report.py --send-slack       # envia para Slack após gerar
"""

import argparse
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))
from base_agent import BaseAgent

REPORTS_DIR = Path(__file__).parent / "reports" / "daily"
DATA_DIR = Path(__file__).parent / "data"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM = """Você é o analista executivo do ULTIMATE CRONUS.
Gera relatórios diários claros, acionáveis e diretos ao ponto.
Foque em: o que mudou, por quê importa, o que fazer amanhã."""


def load_todays_data(target_date: str) -> dict:
    """Carrega dados do dia — métricas, logs, eventos."""
    data: dict = {"date": target_date, "metrics": {}, "events": [], "agent_logs": []}

    # Métricas do dia
    metrics_file = DATA_DIR / f"metrics_{target_date}.json"
    if metrics_file.exists():
        data["metrics"] = json.loads(metrics_file.read_text(encoding="utf-8"))
    else:
        # Dados de exemplo se não houver arquivo real
        data["metrics"] = {
            "mrr": {"value": 45000, "prev": 42000, "unit": "R$"},
            "novos_clientes": {"value": 8, "prev": 5, "unit": "clientes"},
            "churn": {"value": 1, "prev": 2, "unit": "clientes"},
            "cac": {"value": 1200, "prev": 1400, "unit": "R$"},
            "nps": {"value": 72, "prev": 68, "unit": "pontos"},
            "tickets_abertos": {"value": 12, "prev": 18, "unit": "tickets"},
            "leads_gerados": {"value": 34, "prev": 28, "unit": "leads"},
        }

    # Eventos do dia (agentes que rodaram, alertas, etc)
    events_file = DATA_DIR / f"events_{target_date}.json"
    if events_file.exists():
        data["events"] = json.loads(events_file.read_text(encoding="utf-8"))

    return data


def format_metrics_table(metrics: dict) -> str:
    """Formata métricas como tabela Markdown com delta."""
    rows = ["| Métrica | Hoje | Ontem | Delta |", "|---------|------|-------|-------|"]
    for key, m in metrics.items():
        if isinstance(m, dict):
            val = m.get("value", "-")
            prev = m.get("prev", "-")
            unit = m.get("unit", "")
            if isinstance(val, (int, float)) and isinstance(prev, (int, float)):
                delta = val - prev
                pct = round((delta / prev * 100), 1) if prev else 0
                sign = "▲" if delta > 0 else "▼" if delta < 0 else "●"
                delta_str = f"{sign} {abs(delta):,.0f} ({pct:+.1f}%)"
            else:
                delta_str = "-"
            rows.append(f"| {key.replace('_', ' ').title()} | {val} {unit} | {prev} {unit} | {delta_str} |")
    return "\n".join(rows)


def generate_report(target_date: str, send_slack: bool = False) -> Path:
    agent = BaseAgent(name="daily_report", output_dir=str(REPORTS_DIR))
    data = load_todays_data(target_date)

    metrics_table = format_metrics_table(data["metrics"])
    events_str = "\n".join([f"- {e}" for e in data["events"]]) if data["events"] else "- Nenhum evento registrado"

    prompt = f"""Gere um relatório executivo diário para {target_date}.

MÉTRICAS DO DIA:
{metrics_table}

EVENTOS/ALERTAS:
{events_str}

O relatório deve ter exatamente esta estrutura em Markdown:

# 📊 Relatório Diário — {target_date}

## 🎯 Resumo Executivo (3 linhas)
[resumo direto do dia]

## 📈 Destaques Positivos
[bullet points do que foi bem]

## ⚠️ Atenção
[bullet points do que precisa de atenção]

## 🚀 Top 3 Ações para Amanhã
1. [ação concreta com responsável e deadline]
2. [ação concreta com responsável e deadline]
3. [ação concreta com responsável e deadline]

## 📊 Métricas
{metrics_table}

---
*Gerado automaticamente pelo ULTIMATE CRONUS às {datetime.now().strftime('%H:%M')}*"""

    report = agent.ask(prompt, system=SYSTEM)

    out_path = REPORTS_DIR / f"{target_date}.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"\n✅ Relatório diário gerado → {out_path}\n")
    print(report[:500] + "...\n")

    if send_slack:
        _send_to_slack(report, target_date)

    return out_path


def _send_to_slack(report: str, date_str: str):
    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook:
        print("⚠️  SLACK_WEBHOOK_URL não configurado — pulando envio")
        return
    try:
        import requests
        summary = report.split("\n\n")[1][:300] if "\n\n" in report else report[:300]
        payload = {"text": f"*📊 Relatório Diário {date_str}*\n{summary}\n_Ver relatório completo em reports/daily/{date_str}.md_"}
        requests.post(webhook, json=payload, timeout=10)
        print("✅ Enviado para Slack")
    except Exception as e:
        print(f"⚠️  Erro ao enviar para Slack: {e}")


def main():
    parser = argparse.ArgumentParser(description="Daily Report — ULTIMATE CRONUS")
    parser.add_argument("--date", default=str(date.today()), help="Data do relatório (YYYY-MM-DD)")
    parser.add_argument("--send-slack", action="store_true", help="Envia relatório para Slack")
    args = parser.parse_args()
    generate_report(args.date, args.send_slack)


if __name__ == "__main__":
    main()
