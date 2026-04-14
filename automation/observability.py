"""
Observability — ULTIMATE CRONUS
Logging estruturado, métricas, alertas e dashboards de observabilidade.

Uso:
    python observability.py dashboard         # Gera dashboard completo
    python observability.py metrics --collect # Coleta métricas de todos os agentes
    python observability.py alert --check     # Verifica alertas
    python observability.py trace --run-id "abc123"  # Trace de uma execução
    python observability.py report --period "7d"     # Relatório de observabilidade
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))
from base_agent import BaseAgent

# ─── Structured Logger ────────────────────────────────────────────────────────

class StructuredLogger:
    """Logger estruturado em JSON para correlação de traces."""

    def __init__(self, service: str, log_dir: str = "automation/logs"):
        self.service = service
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"{service}_{datetime.now().strftime('%Y-%m-%d')}.jsonl"

    def log(self, level: str, message: str, **kwargs):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "service": self.service,
            "level": level,
            "message": message,
            **kwargs
        }
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def info(self, message: str, **kwargs): self.log("INFO", message, **kwargs)
    def warning(self, message: str, **kwargs): self.log("WARNING", message, **kwargs)
    def error(self, message: str, **kwargs): self.log("ERROR", message, **kwargs)
    def metric(self, name: str, value: float, unit: str = "", **kwargs):
        self.log("METRIC", name, value=value, unit=unit, **kwargs)


# ─── Metrics Collector ────────────────────────────────────────────────────────

class MetricsCollector:
    """Coleta métricas de todos os agentes."""

    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.metrics_file = self.base_dir / "automation" / "metrics_store.json"
        self._load_store()

    def _load_store(self):
        if self.metrics_file.exists():
            try:
                self.store = json.loads(self.metrics_file.read_text(encoding="utf-8"))
            except Exception:
                self.store = {"metrics": [], "counters": {}}
        else:
            self.store = {"metrics": [], "counters": {}}

    def _save_store(self):
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        self.metrics_file.write_text(
            json.dumps(self.store, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def record(self, metric_name: str, value: float, labels: dict = None):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "metric": metric_name,
            "value": value,
            "labels": labels or {}
        }
        self.store["metrics"].append(entry)
        # Keep last 10000 metrics
        if len(self.store["metrics"]) > 10000:
            self.store["metrics"] = self.store["metrics"][-10000:]
        self._save_store()

    def increment(self, counter_name: str, by: int = 1):
        self.store["counters"][counter_name] = self.store["counters"].get(counter_name, 0) + by
        self._save_store()

    def collect_system_metrics(self) -> dict:
        """Coleta métricas do sistema ULTIMATE CRONUS."""
        metrics = {}

        # Count output files per agent
        for output_dir in ["agents/output", "automation/reports"]:
            d = self.base_dir / output_dir
            if d.exists():
                for subdir in [""] :
                    files = list(d.glob("*.json"))
                    metrics[f"output_files_{output_dir.replace('/', '_')}"] = len(files)
                    if files:
                        latest = max(files, key=lambda f: f.stat().st_mtime)
                        metrics[f"last_output_{output_dir.replace('/', '_')}"] = datetime.fromtimestamp(latest.stat().st_mtime).isoformat()

        # Count agent files
        agent_files = list((self.base_dir / "agents").glob("*.py"))
        metrics["total_agents"] = len(agent_files)

        # Count sector agents
        sector_files = list((self.base_dir / "agents" / "sectors").glob("*.py"))
        metrics["sector_agents"] = len(sector_files)

        # Count automation scripts
        automation_files = list((self.base_dir / "automation").glob("*.py"))
        metrics["automation_scripts"] = len(automation_files)

        return metrics


# ─── Alert Manager ────────────────────────────────────────────────────────────

class AlertManager:
    """Gerencia alertas baseados em regras."""

    def __init__(self, config_path: str = "config/alerts.json"):
        self.config_path = Path(config_path)
        self.alerts_fired = []

        # Default alert rules
        self.default_rules = [
            {
                "name": "no_output_24h",
                "description": "Nenhum output gerado em 24h",
                "severity": "warning",
                "check": "last_output_age_hours > 24"
            },
            {
                "name": "high_error_rate",
                "description": "Taxa de erro alta",
                "severity": "critical",
                "check": "error_rate_pct > 10"
            },
            {
                "name": "low_agent_count",
                "description": "Poucos agentes ativos",
                "severity": "info",
                "check": "total_agents < 5"
            }
        ]

    def check_alerts(self, metrics: dict) -> list:
        """Verifica regras e retorna alertas disparados."""
        fired = []

        # Check last output age
        now = datetime.now()
        for key, val in metrics.items():
            if key.startswith("last_output_") and isinstance(val, str):
                try:
                    last_time = datetime.fromisoformat(val)
                    age_hours = (now - last_time).total_seconds() / 3600
                    if age_hours > 24:
                        fired.append({
                            "rule": "no_output_24h",
                            "severity": "warning",
                            "message": f"{key}: último output há {age_hours:.1f}h",
                            "timestamp": now.isoformat()
                        })
                except Exception:
                    pass

        return fired

    def format_slack_alert(self, alert: dict) -> str:
        icons = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️"}
        icon = icons.get(alert.get("severity", "info"), "●")
        return f"{icon} *ALERT [{alert.get('severity', '?').upper()}]* — {alert.get('message', '')}"


# ─── Observability Agent ──────────────────────────────────────────────────────

class ObservabilityAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="OBSERVABILITY", output_dir="automation/reports")
        self.structured_log = StructuredLogger("OBSERVABILITY")
        self.metrics = MetricsCollector()
        self.alerts = AlertManager()

    def generate_dashboard(self) -> dict:
        """Gera dashboard completo de observabilidade."""
        system_metrics = self.metrics.collect_system_metrics()
        active_alerts = self.alerts.check_alerts(system_metrics)

        # Read recent logs
        log_summaries = []
        log_dir = Path("automation/logs")
        if log_dir.exists():
            for log_file in sorted(log_dir.glob("*.jsonl"))[-3:]:
                try:
                    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
                    entries = [json.loads(l) for l in lines[-20:] if l]
                    log_summaries.append({
                        "file": log_file.name,
                        "recent_entries": len(entries),
                        "latest": entries[-1] if entries else None
                    })
                except Exception:
                    pass

        prompt = f"""Gere um dashboard de observabilidade para o ULTIMATE CRONUS:

MÉTRICAS DO SISTEMA:
{json.dumps(system_metrics, indent=2)}

ALERTAS ATIVOS: {len(active_alerts)}
{json.dumps(active_alerts, indent=2)}

LOGS RECENTES:
{json.dumps(log_summaries, indent=2)[:2000]}

Retorne JSON com:
- saude_geral: "healthy"|"degraded"|"critical"
- score_saude: 0-100
- resumo_executivo: 2-3 frases sobre estado do sistema
- metricas_chave: as 5 métricas mais importantes agora
- alertas_ativos: alertas que precisam de atenção
- tendencias: padrões observados nos últimos dados
- anomalias: comportamentos inesperados
- recomendacoes: ações para melhorar observabilidade
- status_agentes: status de cada agente
- proximos_passos: o que monitorar nas próximas horas"""

        result = self.ask_json(prompt, system="Você é o sistema de observabilidade do ULTIMATE CRONUS. Analise e reporte o estado do sistema com precisão.")
        saude = result.get("saude_geral", "unknown")
        score = result.get("score_saude", 0)
        icons = {"healthy": "✅", "degraded": "⚠️", "critical": "🚨"}
        print(f"\n{icons.get(saude, '●')} Observability Dashboard — {saude.upper()} ({score}/100)")
        print(f"  Agentes: {system_metrics.get('total_agents', '?')} | Setoriais: {system_metrics.get('sector_agents', '?')} | Automações: {system_metrics.get('automation_scripts', '?')}")
        if active_alerts:
            print(f"  ⚠️  {len(active_alerts)} alertas ativos")
        self.save_result(result, prefix="observability_dashboard")
        return result

    def collect_metrics(self) -> dict:
        """Coleta e persiste métricas de todos os agentes."""
        metrics = self.metrics.collect_system_metrics()
        timestamp = datetime.now().isoformat()

        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                self.metrics.record(f"system.{key}", value)

        self.structured_log.info("Metrics collected", metrics=metrics)
        print(f"\n📊 Metrics collected at {timestamp}")
        for k, v in metrics.items():
            print(f"  {k}: {v}")
        return metrics

    def generate_report(self, period: str = "7d") -> str:
        """Gera relatório de observabilidade para período."""
        days = int(period.replace("d", "")) if "d" in period else 7
        metrics = self.metrics.collect_system_metrics()
        alerts = self.alerts.check_alerts(metrics)

        prompt = f"""Gere um relatório de observabilidade para os últimos {days} dias:

MÉTRICAS ATUAIS:
{json.dumps(metrics, indent=2)}

ALERTAS: {len(alerts)}

Crie um relatório em Markdown com:
# 🔭 Observability Report — ULTIMATE CRONUS
Data: {datetime.now().strftime('%d/%m/%Y')} | Período: {period}

## Executive Summary
## System Health
## Agent Activity
## Metrics & KPIs
## Alerts & Incidents
## Trends & Anomalies
## Recommendations
## Action Items"""

        report = self.ask(prompt, system="Você é o sistema de observabilidade do ULTIMATE CRONUS.", max_tokens=3000)
        path = self.save_markdown(report, prefix="observability_report")
        print(f"\n📋 Observability Report ({period}) → {path}")
        return report


def main():
    parser = argparse.ArgumentParser(description="Observability — ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("dashboard")
    sub.add_parser("metrics")

    p_alert = sub.add_parser("alert")
    p_alert.add_argument("--check", action="store_true")

    p_report = sub.add_parser("report")
    p_report.add_argument("--period", default="7d")

    args = parser.parse_args()
    agent = ObservabilityAgent()

    if args.command == "dashboard":
        agent.generate_dashboard()
    elif args.command == "metrics":
        agent.collect_metrics()
    elif args.command == "alert":
        metrics = agent.metrics.collect_system_metrics()
        fired = agent.alerts.check_alerts(metrics)
        if fired:
            print(f"\n⚠️  {len(fired)} alertas:")
            for a in fired:
                print(f"  {agent.alerts.format_slack_alert(a)}")
        else:
            print("\n✅ Nenhum alerta ativo")
    elif args.command == "report":
        agent.generate_report(args.period)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
