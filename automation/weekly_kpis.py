"""
Weekly KPIs — ULTIMATE CRONUS
Relatório semanal de métricas com comparação, trends e alertas.

Uso:
    python weekly_kpis.py                  # semana atual
    python weekly_kpis.py --week 2026-W15  # semana específica
"""

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))
from base_agent import BaseAgent

REPORTS_DIR = Path(__file__).parent / "reports" / "weekly"
CONFIG_DIR = Path(__file__).parent / "config"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM = """Você é o analista de KPIs do ULTIMATE CRONUS.
Interpreta dados de negócio com precisão e gera insights estratégicos acionáveis.
Seja direto: o que os números significam para o crescimento da empresa."""


def get_week_label(target_date: date) -> str:
    iso = target_date.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def load_kpi_config() -> list[dict]:
    config_file = CONFIG_DIR / "kpis.json"
    if config_file.exists():
        return json.loads(config_file.read_text(encoding="utf-8"))
    return []


def load_week_data(week_label: str) -> dict:
    """Carrega dados da semana. Usa dados de exemplo se não houver arquivo."""
    data_file = Path(__file__).parent / "data" / f"kpis_{week_label}.json"
    if data_file.exists():
        return json.loads(data_file.read_text(encoding="utf-8"))

    # Dados de exemplo
    return {
        "week": week_label,
        "current": {
            "mrr": 45000, "arr": 540000, "novos_clientes": 32, "churn_rate": 2.1,
            "cac": 1200, "ltv": 18000, "ltv_cac_ratio": 15.0, "nps": 72,
            "leads": 180, "conversao_lead_cliente": 17.8, "ticket_medio": 1406,
            "receita_expansao": 8500, "receita_nova": 38000, "receita_total": 45000,
        },
        "previous": {
            "mrr": 42000, "arr": 504000, "novos_clientes": 28, "churn_rate": 2.8,
            "cac": 1400, "ltv": 16800, "ltv_cac_ratio": 12.0, "nps": 68,
            "leads": 155, "conversao_lead_cliente": 18.1, "ticket_medio": 1500,
            "receita_expansao": 7200, "receita_nova": 34000, "receita_total": 42000,
        },
    }


def compute_deltas(current: dict, previous: dict) -> list[dict]:
    rows = []
    for key, val in current.items():
        prev = previous.get(key)
        if isinstance(val, (int, float)) and isinstance(prev, (int, float)) and prev != 0:
            delta_abs = val - prev
            delta_pct = round(delta_abs / prev * 100, 1)
            trend = "▲" if delta_abs > 0 else "▼" if delta_abs < 0 else "●"
            rows.append({
                "kpi": key.replace("_", " ").title(),
                "atual": val,
                "anterior": prev,
                "delta_abs": delta_abs,
                "delta_pct": delta_pct,
                "trend": trend,
            })
    return rows


def build_table(rows: list[dict]) -> str:
    lines = ["| KPI | Atual | Semana Ant. | Delta | % |", "|-----|-------|-------------|-------|---|"]
    for r in rows:
        lines.append(
            f"| {r['kpi']} | {r['atual']:,.1f} | {r['anterior']:,.1f} | "
            f"{r['trend']} {abs(r['delta_abs']):,.1f} | {r['delta_pct']:+.1f}% |"
        )
    return "\n".join(lines)


def detect_alerts(rows: list[dict], kpi_config: list[dict]) -> list[str]:
    alerts = []
    thresholds = {k["name"]: k for k in kpi_config if "name" in k}
    for r in rows:
        key = r["kpi"].lower().replace(" ", "_")
        cfg = thresholds.get(key, {})
        if cfg.get("direction") == "down" and r["delta_pct"] > 10:
            alerts.append(f"🔴 **{r['kpi']}** subiu {r['delta_pct']:+.1f}% (meta: reduzir)")
        elif cfg.get("direction") == "up" and r["delta_pct"] < -5:
            alerts.append(f"🔴 **{r['kpi']}** caiu {r['delta_pct']:+.1f}% (meta: crescer)")
        elif r["delta_pct"] > 20:
            alerts.append(f"🟢 **{r['kpi']}** cresceu {r['delta_pct']:+.1f}% — pico positivo")
        elif r["delta_pct"] < -15:
            alerts.append(f"🟠 **{r['kpi']}** caiu {r['delta_pct']:+.1f}% — investigar")
    return alerts


def generate_report(week_label: str) -> Path:
    agent = BaseAgent(name="weekly_kpis", output_dir=str(REPORTS_DIR))
    data = load_week_data(week_label)
    kpi_config = load_kpi_config()

    rows = compute_deltas(data["current"], data["previous"])
    table = build_table(rows)
    alerts = detect_alerts(rows, kpi_config)
    alerts_str = "\n".join(alerts) if alerts else "- Nenhum alerta crítico esta semana"

    prompt = f"""Gere o relatório semanal de KPIs para a semana {week_label}.

TABELA DE KPIs:
{table}

ALERTAS AUTOMÁTICOS:
{alerts_str}

Estrutura obrigatória:

# 📊 Weekly KPIs — {week_label}
> Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}

## 🎯 Resumo Executivo
[3-4 linhas sobre o estado geral da semana]

## 🚦 Status dos KPIs Críticos
[semáforo visual: verde/amarelo/vermelho para cada KPI principal]

## 📈 Destaques da Semana
[top 3 vitórias com contexto]

## ⚠️ Alertas e Riscos
{alerts_str}

## 📊 Tabela Completa de KPIs
{table}

## 🔍 Análise de Trends
[o que os números revelam sobre a trajetória do negócio]

## 🚀 Prioridades para a Próxima Semana
1. [ação com métrica alvo e responsável]
2. [ação com métrica alvo e responsável]
3. [ação com métrica alvo e responsável]

---
*ULTIMATE CRONUS — Relatório Automático Semanal*"""

    report = agent.ask(prompt, system=SYSTEM, max_tokens=4096)

    out_path = REPORTS_DIR / f"{week_label}.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"\n✅ Relatório semanal gerado → {out_path}\n")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Weekly KPIs — ULTIMATE CRONUS")
    parser.add_argument("--week", default=get_week_label(date.today()), help="Semana (ex: 2026-W15)")
    args = parser.parse_args()
    generate_report(args.week)


if __name__ == "__main__":
    main()
