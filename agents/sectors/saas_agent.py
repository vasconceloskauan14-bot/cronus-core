"""
SaaS Agent — ULTIMATE CRONUS
Automações específicas para SaaS: MRR, churn, expansion, PLG.

Uso:
    python saas_agent.py health --data data/saas_metrics.json
    python saas_agent.py growth-levers --metrics data/metrics.json
    python saas_agent.py pricing --current data/pricing.json --market data/concorrentes.json
    python saas_agent.py plg-analysis --product data/produto.json --usage data/uso.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_agent import BaseAgent

SYSTEM_SAAS = """Você é especialista em SaaS B2B do ULTIMATE CRONUS.
Você domina métricas de SaaS (MRR, ARR, NRR, CAC, LTV, Churn, NPS).
Pense como um investidor de Série B: crescimento eficiente com margens saudáveis."""


class SaasAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="SAAS", output_dir="agents/output")

    def health_dashboard(self, data: dict) -> dict:
        """Dashboard completo de saúde do SaaS."""
        prompt = f"""Analise a saúde completa deste SaaS e gere um dashboard executivo:

MÉTRICAS:
{json.dumps(data, indent=2, ensure_ascii=False)[:5000]}

Retorne JSON com:
- score_saude_saas: 0-100
- nivel: "unicorn_track"|"healthy"|"growing"|"struggling"|"critical"
- metricas_calculadas:
  - nrr: Net Revenue Retention %
  - quick_ratio: (new+expansion MRR) / (churned+contraction MRR)
  - magic_number: eficiência de crescimento
  - payback_period_meses: CAC payback
  - rule_of_40: crescimento% + margem%
- semaforos: verde/amarelo/vermelho para cada métrica principal
- analise_cohorts: insight sobre retenção por cohort se houver dados
- expansao_vs_novo: de onde vem a receita nova
- top_3_alavancas: onde focar para crescer mais rápido
- alarmes: métricas preocupantes que precisam de ação imediata
- comparacao_benchmarks: como se compara com SaaS médio/top quartile"""

        result = self.ask_json(prompt, system=SYSTEM_SAAS)
        nivel = result.get("nivel","?")
        score = result.get("score_saude_saas",0)
        icons = {"unicorn_track":"🦄","healthy":"💚","growing":"📈","struggling":"⚠️","critical":"🚨"}
        print(f"\n{icons.get(nivel,'●')} SaaS Health: {score}/100 ({nivel.upper()})")
        metricas = result.get("metricas_calculadas",{})
        print(f"  NRR: {metricas.get('nrr','?')}% | Quick Ratio: {metricas.get('quick_ratio','?')} | Rule of 40: {metricas.get('rule_of_40','?')}")
        self.save_result(result, prefix="saas_health")
        return result

    def growth_levers(self, metrics: dict) -> dict:
        """Identifica as alavancas de crescimento mais impactantes."""
        prompt = f"""Identifique as alavancas de crescimento mais impactantes para este SaaS:

MÉTRICAS ATUAIS:
{json.dumps(metrics, indent=2, ensure_ascii=False)[:4000]}

Retorne JSON com:
- alavancas_rankeadas: lista ordenada por impacto potencial com:
  - alavanca: nome da alavanca
  - categoria: "aquisicao"|"ativacao"|"retencao"|"receita"|"referral"
  - impacto_mrr_estimado_pct: % de aumento no MRR em 90 dias
  - esforco: "baixo"|"médio"|"alto"
  - como_implementar: 3-5 passos concretos
  - kpi_para_medir: métrica para monitorar
  - prazo_resultados: quando ver resultado
- foco_recomendado: qual alavanca atacar primeiro e por quê
- plano_90_dias: roadmap de crescimento para os próximos 90 dias"""

        result = self.ask_json(prompt, system=SYSTEM_SAAS)
        alavancas = result.get("alavancas_rankeadas",[])
        print(f"\n🚀 SaaS Growth Levers — {len(alavancas)} alavancas identificadas")
        for a in alavancas[:5]:
            print(f"  +{a.get('impacto_mrr_estimado_pct','?')}% MRR | {a.get('alavanca','?')}")
        self.save_result(result, prefix="saas_growth_levers")
        return result

    def pricing_optimization(self, current_pricing: dict, market_data: dict) -> dict:
        """Otimiza estratégia de pricing com base em mercado e dados."""
        prompt = f"""Otimize a estratégia de pricing deste SaaS:

PRICING ATUAL:
{json.dumps(current_pricing, indent=2, ensure_ascii=False)[:2000]}

DADOS DE MERCADO/CONCORRENTES:
{json.dumps(market_data, indent=2, ensure_ascii=False)[:2000]}

Retorne JSON com:
- analise_pricing_atual: pontos fortes e fracos
- oportunidades_pricing: onde há espaço para ajuste
- recomendacao_modelo: "por-usuário"|"por-uso"|"por-feature"|"flat"|"híbrido"
- novos_planos_sugeridos: lista de planos com nome, preço e features
- ancoragem_psicologica: como usar psicologia de preços
- aumento_preco_seguro_pct: quanto pode aumentar sem perder clientes
- estrategia_freemium: recomendação sobre tier gratuito
- impacto_esperado_mrr_pct: impacto estimado no MRR
- como_comunicar_mudanca: como anunciar mudança de preço"""

        result = self.ask_json(prompt, system=SYSTEM_SAAS)
        print(f"\n💎 SaaS Pricing — Impacto esperado: +{result.get('impacto_esperado_mrr_pct','?')}% MRR")
        self.save_result(result, prefix="saas_pricing")
        return result


def main():
    parser = argparse.ArgumentParser(description="SaaS Agent — ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("health").add_argument("--data", required=True)
    sub.add_parser("growth-levers").add_argument("--metrics", required=True)
    p_p = sub.add_parser("pricing"); p_p.add_argument("--current", required=True); p_p.add_argument("--market", required=True)

    args = parser.parse_args()
    agent = SaasAgent()
    def load(p): return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else {}

    if args.command == "health": agent.health_dashboard(load(args.data))
    elif args.command == "growth-levers": agent.growth_levers(load(args.metrics))
    elif args.command == "pricing": agent.pricing_optimization(load(args.current), load(args.market))
    else: parser.print_help()


if __name__ == "__main__":
    main()
