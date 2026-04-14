"""
ANALYST Agent — ULTIMATE CRONUS
Dados, Business Intelligence, forecast e detecção de anomalias.

Uso:
    python analyst_agent.py analyze --data data/metrics.csv --question "Qual o trend de CAC?"
    python analyst_agent.py report --metrics data/kpis.json --period "Q1 2026"
    python analyst_agent.py anomalies --data data/series.json
    python analyst_agent.py forecast --data data/historical.json --periods 30
    python analyst_agent.py compare --current data/this_week.json --previous data/last_week.json
"""

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from base_agent import BaseAgent

SYSTEM_ANALYST = """Você é o ANALYST, agente especialista em dados e Business Intelligence do ULTIMATE CRONUS.
Você transforma dados brutos em insights acionáveis e claros para líderes de negócio.
Seja preciso, direto e sempre conecte números a ações concretas.
Use linguagem de negócio, não jargão estatístico desnecessário."""


class AnalystAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="ANALYST", output_dir="agents/reports")
        Path("agents/reports").mkdir(parents=True, exist_ok=True)

    def _load_data(self, data_source: str) -> str:
        """Carrega dados de CSV, JSON ou string."""
        path = Path(data_source)
        if not path.exists():
            return data_source  # assume que é texto/JSON inline

        if path.suffix == ".csv":
            rows = []
            with open(path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(row)
            return json.dumps(rows[:200], ensure_ascii=False)  # limita 200 linhas
        elif path.suffix == ".json":
            return path.read_text(encoding="utf-8")[:8000]
        else:
            return path.read_text(encoding="utf-8")[:8000]

    def analyze(self, data_source: str, question: str) -> str:
        """Analisa dados e responde uma pergunta de negócio."""
        self.logger.info(f"Analisando: {question[:60]}")
        data_str = self._load_data(data_source)

        prompt = f"""Analise os dados abaixo e responda a pergunta de negócio.

PERGUNTA: {question}

DADOS:
{data_str[:6000]}

Estruture sua resposta em Markdown com:
## 📊 Resposta Direta
[resposta clara em 1-2 frases]

## 🔍 Análise Detalhada
[detalhamento com números e contexto]

## 📈 Trend Identificado
[tendência principal nos dados]

## ⚡ Ações Recomendadas
[3 ações concretas baseadas nos dados]

## ⚠️ Limitações da Análise
[o que os dados não mostram ou limitações importantes]"""

        result = self.ask(prompt, system=SYSTEM_ANALYST, max_tokens=4096)
        path = self.save_markdown(result, prefix="analysis")
        print(f"\n📊 Análise concluída → {path}\n")
        print(result[:600] + ("..." if len(result) > 600 else ""))
        return result

    def generate_report(self, metrics: dict, period: str) -> str:
        """Gera relatório de BI completo para um período."""
        self.logger.info(f"Gerando relatório para {period}")

        prompt = f"""Gere um relatório completo de Business Intelligence para o período: {period}

MÉTRICAS:
{json.dumps(metrics, indent=2, ensure_ascii=False)[:5000]}

O relatório deve ser rico, profissional e acionável. Inclua:

# 📊 Relatório de BI — {period}

## Executive Summary
[3-4 linhas sobre o estado geral]

## 🏆 Top 3 Destaques
[vitórias e marcos do período]

## 📈 Análise por Área

### Receita & Crescimento
[análise com números]

### Aquisição & Marketing
[análise com números]

### Retenção & Customer Success
[análise com números]

### Operação & Eficiência
[análise com números]

## 🔮 Projeções (próximos 30 dias)
[baseado nos trends atuais]

## 🚀 Prioridades Estratégicas
[top 5 ações para o próximo período]

## 📉 Riscos a Monitorar
[alertas e riscos identificados]

---
*ULTIMATE CRONUS ANALYST — {datetime.now().strftime('%d/%m/%Y')}*"""

        result = self.ask(prompt, system=SYSTEM_ANALYST, max_tokens=8096)
        path = self.save_markdown(result, prefix="bi_report")
        print(f"\n📋 Relatório de BI gerado → {path}")
        return result

    def detect_anomalies(self, data: list | str) -> list[dict]:
        """Detecta anomalias em séries temporais ou conjuntos de dados."""
        self.logger.info("Detectando anomalias")

        if isinstance(data, str):
            data_str = self._load_data(data)
        else:
            data_str = json.dumps(data, ensure_ascii=False)

        prompt = f"""Analise esta série de dados e detecte anomalias, outliers e padrões incomuns.

DADOS:
{data_str[:5000]}

Retorne JSON com:
- anomalias: lista de objetos com:
  - tipo: "spike" | "drop" | "outlier" | "trend_break" | "missing"
  - campo: qual métrica/coluna
  - valor_anomalo: o valor problemático
  - valor_esperado: o que seria esperado
  - severidade: "baixa" | "media" | "alta" | "critica"
  - data_ou_indice: quando aconteceu
  - possivel_causa: hipótese sobre a causa
  - acao_recomendada: o que fazer
- resumo: string com sumário geral das anomalias
- score_saude_dados: 0-100 (100 = dados perfeitos, sem anomalias)"""

        result = self.ask_json(prompt, system=SYSTEM_ANALYST)
        anomalies = result.get("anomalias", [])
        score = result.get("score_saude_dados", "?")

        print(f"\n🔍 Detecção de Anomalias — Score de Saúde: {score}/100")
        if anomalies:
            for a in anomalies:
                sev = a.get("severidade", "?")
                icon = {"critica": "🚨", "alta": "🔴", "media": "🟡", "baixa": "🟢"}.get(sev, "●")
                print(f"  {icon} [{sev.upper()}] {a.get('campo','?')}: {a.get('tipo','?')}")
                print(f"     {a.get('possivel_causa','')}")
        else:
            print("  ✅ Nenhuma anomalia significativa detectada")

        self.save_result(result, prefix="anomalies")
        return anomalies

    def forecast(self, historical_data: list | str, periods: int = 30) -> dict:
        """Gera previsão simples para os próximos N períodos."""
        self.logger.info(f"Forecast para {periods} períodos")

        if isinstance(historical_data, str):
            data_str = self._load_data(historical_data)
        else:
            data_str = json.dumps(historical_data, ensure_ascii=False)

        prompt = f"""Com base nos dados históricos abaixo, gere uma previsão para os próximos {periods} períodos.

DADOS HISTÓRICOS:
{data_str[:5000]}

Retorne JSON com:
- metrica_principal: nome da métrica principal identificada
- tendencia: "crescimento" | "queda" | "estável" | "sazonal" | "volátil"
- taxa_crescimento_media: % por período
- previsoes: lista de {min(periods, 12)} objetos com:
  - periodo: identificador (ex: "Semana 1", "Mês 1")
  - valor_previsto: número
  - intervalo_min: mínimo do intervalo de confiança
  - intervalo_max: máximo do intervalo de confiança
  - confianca: 0-100
- cenario_otimista: valor ao final de {periods} períodos
- cenario_base: valor ao final de {periods} períodos
- cenario_pessimista: valor ao final de {periods} períodos
- fatores_de_risco: lista de fatores que podem mudar a previsão
- recomendacao: o que fazer para atingir o cenário otimista"""

        result = self.ask_json(prompt, system=SYSTEM_ANALYST)

        print(f"\n🔮 Forecast — {periods} períodos")
        print(f"  Tendência: {result.get('tendencia','?')} ({result.get('taxa_crescimento_media','?')}%/período)")
        print(f"  Cenário base: {result.get('cenario_base','?')}")
        print(f"  Cenário otimista: {result.get('cenario_otimista','?')}")
        print(f"  Cenário pessimista: {result.get('cenario_pessimista','?')}")

        self.save_result(result, prefix="forecast")
        return result

    def compare_periods(self, current: dict | str, previous: dict | str) -> dict:
        """Compara dois períodos e identifica mudanças significativas."""
        self.logger.info("Comparando períodos")

        if isinstance(current, str):
            current = json.loads(self._load_data(current))
        if isinstance(previous, str):
            previous = json.loads(self._load_data(previous))

        prompt = f"""Compare estes dois períodos e identifique mudanças significativas:

PERÍODO ATUAL:
{json.dumps(current, indent=2, ensure_ascii=False)[:3000]}

PERÍODO ANTERIOR:
{json.dumps(previous, indent=2, ensure_ascii=False)[:3000]}

Retorne JSON com:
- melhorias: lista de métricas que melhoraram (com delta % e significância)
- pioras: lista de métricas que pioraram (com delta % e urgência)
- estavel: lista de métricas sem mudança significativa
- mudanca_mais_importante: qual métrica teve o maior impacto
- narrativa: 2-3 frases explicando o que aconteceu entre os períodos
- score_periodo_atual: 0-100
- score_periodo_anterior: 0-100
- veredicto: "melhorou" | "piorou" | "estável" | "misto"
- acoes_prioritarias: top 3 ações baseadas na comparação"""

        result = self.ask_json(prompt, system=SYSTEM_ANALYST)

        veredicto = result.get("veredicto", "?")
        icons = {"melhorou": "✅", "piorou": "❌", "estável": "➡️", "misto": "⚠️"}
        print(f"\n{icons.get(veredicto,'●')} Comparação de Períodos: {veredicto.upper()}")
        print(f"  Score atual: {result.get('score_periodo_atual','?')} | Anterior: {result.get('score_periodo_anterior','?')}")
        print(f"  {result.get('narrativa','')[:150]}")

        self.save_result(result, prefix="comparison")
        return result


def main():
    parser = argparse.ArgumentParser(description="ANALYST — Dados e BI ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")

    p_analyze = sub.add_parser("analyze", help="Analisar dados")
    p_analyze.add_argument("--data", required=True)
    p_analyze.add_argument("--question", required=True)

    p_report = sub.add_parser("report", help="Gerar relatório de BI")
    p_report.add_argument("--metrics", required=True)
    p_report.add_argument("--period", default="Período Atual")

    p_anom = sub.add_parser("anomalies", help="Detectar anomalias")
    p_anom.add_argument("--data", required=True)

    p_fore = sub.add_parser("forecast", help="Previsão futura")
    p_fore.add_argument("--data", required=True)
    p_fore.add_argument("--periods", type=int, default=30)

    p_comp = sub.add_parser("compare", help="Comparar períodos")
    p_comp.add_argument("--current", required=True)
    p_comp.add_argument("--previous", required=True)

    args = parser.parse_args()
    agent = AnalystAgent()

    if args.command == "analyze":
        agent.analyze(args.data, args.question)
    elif args.command == "report":
        metrics = json.loads(Path(args.metrics).read_text(encoding="utf-8"))
        agent.generate_report(metrics, args.period)
    elif args.command == "anomalies":
        agent.detect_anomalies(args.data)
    elif args.command == "forecast":
        agent.forecast(args.data, args.periods)
    elif args.command == "compare":
        agent.compare_periods(args.current, args.previous)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
