"""
RADAR Agent — ULTIMATE CRONUS
Monitoramento Contínuo 24/7 de mercado, concorrentes e oportunidades.

Uso:
    python radar_agent.py --targets "OpenAI,Anthropic,Google" --interval 60
    python radar_agent.py --targets "OpenAI,Anthropic" --once
    python radar_agent.py --targets "SaaS B2B,automação" --report
"""

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from base_agent import BaseAgent

STATE_FILE = "radar_state.json"
ANOMALY_THRESHOLD = 0.35

SYSTEM_RADAR = """Você é o RADAR, agente de Monitoramento Contínuo 24/7 do ULTIMATE CRONUS.
Você monitora sinais de mercado, atividade de concorrentes e oportunidades emergentes.
Forneça inteligência estruturada e acionável com detecção clara de mudanças.
Responda SEMPRE no formato JSON solicitado."""


@dataclass
class Signal:
    target: str
    timestamp: str
    summary: str
    sentiment_score: float = 0.0   # -1.0 (negativo) a +1.0 (positivo)
    activity_level: float = 0.0    # 0.0 (silencioso) a 1.0 (muito ativo)
    key_events: list = field(default_factory=list)
    opportunities: list = field(default_factory=list)
    risks: list = field(default_factory=list)


@dataclass
class ScanResult:
    scan_id: str
    started_at: str
    finished_at: str = ""
    signals: list = field(default_factory=list)
    alerts: list = field(default_factory=list)
    anomalies_detected: int = 0


class RadarAgent(BaseAgent):
    def __init__(self, anomaly_threshold: float = ANOMALY_THRESHOLD):
        super().__init__(name="RADAR", output_dir="agents/output")
        self.anomaly_threshold = anomaly_threshold
        self._state: dict = self._load_radar_state()
        Path("agents/reports").mkdir(parents=True, exist_ok=True)

    def _load_radar_state(self) -> dict:
        state_path = Path("agents/state") / STATE_FILE
        if state_path.exists():
            try:
                return json.loads(state_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def _save_radar_state(self):
        state_path = Path("agents/state") / STATE_FILE
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(self._state, indent=2, ensure_ascii=False), encoding="utf-8")

    def scan_once(self, targets: list[str]) -> ScanResult:
        """Executa um único ciclo de scan e retorna o resultado."""
        scan_id = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        started_at = datetime.now().isoformat()
        self.logger.info(f"Scan {scan_id} iniciado | targets={len(targets)}")

        result = ScanResult(scan_id=scan_id, started_at=started_at)

        for target in targets:
            self.logger.info(f"  Scaneando: {target}")
            signal = self._scan_target(target)
            result.signals.append(signal)

        result.alerts = self._detect_anomalies(result.signals)
        result.anomalies_detected = len(result.alerts)
        result.finished_at = datetime.now().isoformat()

        self._update_state(result)

        # Salva JSON do scan
        self.save_result(
            {"scan_id": scan_id, "targets": targets,
             "signals": [asdict(s) for s in result.signals],
             "alerts": result.alerts, "anomalies": result.anomalies_detected},
            prefix="radar"
        )

        self.logger.info(f"Scan completo | signals={len(result.signals)} | anomalias={result.anomalies_detected}")
        return result

    def scan(self, targets: list[str], interval_minutes: int = 60):
        """Loop contínuo de monitoramento. Bloqueia até Ctrl+C."""
        self.logger.info(f"RADAR contínuo iniciado | targets={targets} | interval={interval_minutes}min")

        while True:
            result = self.scan_once(targets)

            if result.alerts:
                print(f"\n🚨 {len(result.alerts)} ALERTA(S) DETECTADO(S):")
                for alert in result.alerts:
                    print(f"  ⚠️  {alert['target']}: delta_sentiment={alert['sentiment_delta']:.2f}")

            # Relatório diário na primeira scan do dia
            today = datetime.now().strftime("%Y-%m-%d")
            report_path = Path("agents/reports") / f"radar_{today}.md"
            if not report_path.exists():
                self._write_daily_report(targets, result)

            self.logger.info(f"Próximo scan em {interval_minutes} minutos...")
            time.sleep(interval_minutes * 60)

    def generate_report(self, targets: list[str]) -> str:
        """Gera relatório de inteligência para os targets sem fazer scan."""
        self.logger.info(f"Gerando relatório para {targets}")
        result = self.scan_once(targets)
        return self._write_daily_report(targets, result)

    def _scan_target(self, target: str) -> Signal:
        prompt = f"""Analise o sinal de mercado atual para: **{target}**

Data: {datetime.now().strftime('%Y-%m-%d')}

Responda APENAS com JSON no seguinte formato:
{{
  "summary": "resumo em 2-3 frases",
  "sentiment_score": <float de -1.0 a 1.0>,
  "activity_level": <float de 0.0 a 1.0>,
  "key_events": ["evento1", "evento2"],
  "opportunities": ["oportunidade1"],
  "risks": ["risco1"]
}}"""

        ts = datetime.now().isoformat()
        raw = ""
        try:
            raw = self.ask(prompt, system=SYSTEM_RADAR, max_tokens=1024)
            start = raw.find("{")
            end = raw.rfind("}") + 1
            data: dict = json.loads(raw[start:end])
            return Signal(
                target=target, timestamp=ts,
                summary=data.get("summary", ""),
                sentiment_score=float(data.get("sentiment_score", 0.0)),
                activity_level=float(data.get("activity_level", 0.0)),
                key_events=data.get("key_events", []),
                opportunities=data.get("opportunities", []),
                risks=data.get("risks", []),
            )
        except Exception as e:
            self.logger.error(f"Falha ao scanear '{target}': {e}")
            return Signal(target=target, timestamp=ts, summary=f"Erro: {e}")

    def _detect_anomalies(self, signals: list[Signal]) -> list[dict]:
        alerts = []
        previous: dict = self._state.get("last_signals", {})

        for sig in signals:
            prev = previous.get(sig.target)
            if prev is None:
                continue

            delta_sentiment = abs(sig.sentiment_score - prev.get("sentiment_score", 0.0))
            delta_activity = abs(sig.activity_level - prev.get("activity_level", 0.0))

            if delta_sentiment >= self.anomaly_threshold or delta_activity >= self.anomaly_threshold:
                alert = {
                    "target": sig.target,
                    "detected_at": sig.timestamp,
                    "sentiment_delta": round(delta_sentiment, 3),
                    "activity_delta": round(delta_activity, 3),
                    "current_sentiment": sig.sentiment_score,
                    "previous_sentiment": prev.get("sentiment_score"),
                    "summary": sig.summary,
                    "key_events": sig.key_events,
                }
                alerts.append(alert)
                self.logger.warning(
                    f"ANOMALIA | {sig.target} | delta_sentiment={delta_sentiment:.2f} | delta_activity={delta_activity:.2f}"
                )
        return alerts

    def _update_state(self, result: ScanResult):
        last_signals: dict = self._state.get("last_signals", {})
        for sig in result.signals:
            last_signals[sig.target] = {
                "sentiment_score": sig.sentiment_score,
                "activity_level": sig.activity_level,
                "timestamp": sig.timestamp,
                "summary": sig.summary,
            }
        self._state["last_signals"] = last_signals
        self._state["last_scan_id"] = result.scan_id
        self._state["last_scan_at"] = result.finished_at
        self._save_radar_state()

    def _write_daily_report(self, targets: list[str], result: ScanResult) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        signals_json = json.dumps([asdict(s) for s in result.signals], indent=2, ensure_ascii=False)

        prompt = f"""Gere um relatório diário de inteligência de mercado em Markdown para {today}.
Targets monitorados: {', '.join(targets)}

Dados do scan:
{signals_json[:4000]}

Estrutura obrigatória:

# 📡 RADAR Intelligence Report — {today}

## 🎯 Executive Summary
[3-4 linhas sobre o panorama geral]

## 📊 Análise por Target
[para cada target: status, eventos, oportunidades, riscos]

## 💡 Top Oportunidades
[top 3 oportunidades identificadas]

## ⚠️ Riscos a Monitorar
[principais riscos]

## 🚀 Ações Recomendadas para Hoje
[3-5 ações concretas]

---
*ULTIMATE CRONUS RADAR — {datetime.now().strftime('%d/%m/%Y %H:%M')}*"""

        try:
            report = self.ask(prompt, system=SYSTEM_RADAR, max_tokens=3000)
        except Exception as e:
            self.logger.error(f"Falha ao gerar relatório: {e}")
            report = f"# RADAR Daily Report — {today}\n\nErro na geração: {e}\n"

        report_path = Path("agents/reports") / f"radar_{today}.md"
        report_path.write_text(report, encoding="utf-8")
        self.logger.info(f"Relatório diário salvo → {report_path}")
        print(f"\n📄 Relatório RADAR salvo → {report_path}")
        return report


def main():
    parser = argparse.ArgumentParser(description="RADAR — Monitoramento 24/7 ULTIMATE CRONUS")
    parser.add_argument("--targets", "-t", required=True, help="Targets separados por vírgula")
    parser.add_argument("--interval", "-i", type=int, default=60, help="Intervalo em minutos")
    parser.add_argument("--once", action="store_true", help="Roda um scan e sai")
    parser.add_argument("--report", action="store_true", help="Gera relatório e sai")
    parser.add_argument("--threshold", type=float, default=ANOMALY_THRESHOLD, help="Threshold de anomalia (0-1)")
    args = parser.parse_args()

    target_list = [t.strip() for t in args.targets.split(",") if t.strip()]
    agent = RadarAgent(anomaly_threshold=args.threshold)

    if args.report:
        agent.generate_report(target_list)
    elif args.once:
        result = agent.scan_once(target_list)
        print(f"\n{'='*72}")
        print(f"RADAR SCAN COMPLETO — {result.finished_at}")
        print(f"{'='*72}")
        for sig in result.signals:
            icon = "🟢" if sig.sentiment_score > 0.2 else "🔴" if sig.sentiment_score < -0.2 else "🟡"
            print(f"\n{icon} [{sig.target}] sentiment={sig.sentiment_score:+.2f} | activity={sig.activity_level:.2f}")
            print(f"   {sig.summary}")
            if sig.key_events:
                print(f"   Eventos: {'; '.join(sig.key_events[:3])}")
            if sig.opportunities:
                print(f"   Oportunidades: {sig.opportunities[0]}")
        if result.alerts:
            print(f"\n🚨 {len(result.alerts)} ALERTA(S) DETECTADO(S)")
    else:
        print(f"\n📡 RADAR iniciado | targets={target_list} | interval={args.interval}min")
        print("Pressione Ctrl+C para parar.\n")
        try:
            agent.scan(target_list, interval_minutes=args.interval)
        except KeyboardInterrupt:
            print("\n⏹️  RADAR parado.")


if __name__ == "__main__":
    main()
