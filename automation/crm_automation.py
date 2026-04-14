"""
CRM Automation — ULTIMATE CRONUS
Automação completa de CRM: pipeline, scoring, follow-up, revenue ops.

Uso:
    python crm_automation.py pipeline --data data/pipeline.json
    python crm_automation.py score-leads --leads data/leads.json
    python crm_automation.py follow-up --overdue data/atrasados.json
    python crm_automation.py revenue-ops --data data/vendas.json
    python crm_automation.py forecast --pipeline data/pipeline.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))
from base_agent import BaseAgent

SYSTEM_CRM = """Você é o especialista em CRM e Revenue Operations do ULTIMATE CRONUS.
Você analisa pipelines, qualifica leads e maximiza taxa de fechamento.
Pense como um VP de Vendas com acesso a todos os dados."""


class CrmAutomation(BaseAgent):
    def __init__(self):
        super().__init__(name="CRM", output_dir="automation/reports")

    def analyze_pipeline(self, data: dict) -> dict:
        """Analisa pipeline completo e identifica gargalos."""
        prompt = f"""Analise este pipeline de vendas:

PIPELINE:
{json.dumps(data, indent=2, ensure_ascii=False)[:5000]}

Retorne JSON com:
- valor_total_pipeline: R$
- valor_ponderado_probabilidade: R$
- deals_por_stage: distribuição dos deals
- velocidade_media_pipeline_dias: tempo médio de fechamento
- taxa_conversao_por_stage: % de avanço entre stages
- gargalos: onde os deals ficam presos
- deals_em_risco: deals com sinais de risco
- deals_quentes: deals mais próximos do fechamento
- forecast_30_dias: receita esperada nos próximos 30 dias
- acoes_prioritarias: top 5 ações para fechar mais rápido
- health_score_pipeline: 0-100"""

        result = self.ask_json(prompt, system=SYSTEM_CRM)
        print(f"\n📞 CRM Pipeline — R$ {result.get('valor_total_pipeline',0):,.0f} em pipeline")
        print(f"  Forecast 30d: R$ {result.get('forecast_30_dias',0):,.0f}")
        print(f"  Health Score: {result.get('health_score_pipeline',0)}/100")
        self.save_result(result, prefix="crm_pipeline")
        return result

    def score_leads(self, leads: list) -> list:
        """Pontua e prioriza leads por probabilidade de fechamento."""
        prompt = f"""Pontue e priorize estes leads por probabilidade de fechamento:

LEADS ({len(leads)} leads):
{json.dumps(leads[:30], indent=2, ensure_ascii=False)[:5000]}

Para cada lead, retorne score e prioridade. Retorne JSON com:
- leads_scored: lista ordenada por score com:
  - id: identificador do lead
  - nome: nome/empresa
  - score: 0-100
  - categoria: "hot"|"warm"|"cold"|"disqualify"
  - razao_score: por que este score
  - proximo_passo: ação imediata recomendada
  - prazo_followup: quando contatar
- distribuicao: contagem por categoria
- top_10_hot: os 10 leads mais quentes"""

        result = self.ask_json(prompt, system=SYSTEM_CRM)
        scored = result.get("leads_scored",[])
        dist = result.get("distribuicao",{})
        print(f"\n🎯 CRM Lead Scoring — {len(scored)} leads")
        print(f"  Hot: {dist.get('hot',0)} | Warm: {dist.get('warm',0)} | Cold: {dist.get('cold',0)}")
        self.save_result(result, prefix="crm_scoring")
        return scored

    def generate_followups(self, overdue_deals: list) -> list:
        """Gera follow-ups personalizados para deals em atraso."""
        prompt = f"""Gere follow-ups personalizados para estes deals em atraso:

DEALS:
{json.dumps(overdue_deals[:20], indent=2, ensure_ascii=False)[:4000]}

Para cada deal, retorne JSON com:
- followups: lista de objetos com:
  - deal_id: identificador
  - nome_contato: com quem falar
  - dias_sem_contato: dias parados
  - motivo_provavel_silencio: hipótese
  - mensagem_email: email personalizado pronto para enviar
  - mensagem_whatsapp: versão curta para WhatApp
  - assunto_ligacao: se ligar, o que falar
  - oferta_para_desbloquear: se necessário fazer oferta
  - probabilidade_resposta_pct: % de chance de resposta"""

        result = self.ask_json(prompt, system=SYSTEM_CRM)
        followups = result.get("followups",[])
        print(f"\n📧 CRM Follow-ups — {len(followups)} mensagens geradas")
        self.save_result(result, prefix="crm_followups")
        return followups

    def revenue_ops_report(self, sales_data: dict) -> str:
        """Relatório completo de Revenue Operations."""
        prompt = f"""Gere um relatório de Revenue Operations completo:

DADOS DE VENDAS:
{json.dumps(sales_data, indent=2, ensure_ascii=False)[:5000]}

Relatório em Markdown com:
# 📞 Revenue Operations Report

## Executive Summary
## Pipeline Health
## Win/Loss Analysis
## Rep Performance
## Forecast Accuracy
## Process Bottlenecks
## Recommended Actions (priorizadas)
## KPIs Dashboard"""

        report = self.ask(prompt, system=SYSTEM_CRM, max_tokens=4096)
        path = self.save_markdown(report, prefix="revenue_ops")
        print(f"\n📊 Revenue Ops Report gerado → {path}")
        return report


def main():
    parser = argparse.ArgumentParser(description="CRM Automation — ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("pipeline").add_argument("--data", required=True)
    sub.add_parser("score-leads").add_argument("--leads", required=True)
    sub.add_parser("follow-up").add_argument("--overdue", required=True)
    sub.add_parser("revenue-ops").add_argument("--data", required=True)

    args = parser.parse_args()
    agent = CrmAutomation()
    def load(p): return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else {}

    if args.command == "pipeline": agent.analyze_pipeline(load(args.data))
    elif args.command == "score-leads":
        data = load(args.leads); agent.score_leads(data if isinstance(data, list) else data.get("leads",[]))
    elif args.command == "follow-up":
        data = load(args.overdue); agent.generate_followups(data if isinstance(data, list) else data.get("deals",[]))
    elif args.command == "revenue-ops": agent.revenue_ops_report(load(args.data))
    else: parser.print_help()


if __name__ == "__main__":
    main()
