"""
CAPITAL Agent — ULTIMATE CRONUS
Sistema Financeiro Autônomo: caixa, margem, risco e alocação de capital.

Uso:
    python capital_agent.py health --data data/financeiro.json
    python capital_agent.py allocate --budget 100000 --projects data/projetos.json
    python capital_agent.py forecast --data data/receita.json --months 6
    python capital_agent.py risk --portfolio data/portfolio.json
    python capital_agent.py runway --data data/caixa.json
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from base_agent import BaseAgent

SYSTEM_CAPITAL = """Você é o CAPITAL, agente de Sistema Financeiro Autônomo do ULTIMATE CRONUS.
Você analisa caixa, margem, risco e aloca capital de forma inteligente.
Seja preciso com números, conservador com riscos e ousado com oportunidades claras.
Sempre apresente cenários: otimista, base e pessimista."""


class CapitalAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="CAPITAL", output_dir="agents/output")

    def health_check(self, data: dict) -> dict:
        """Diagnóstico completo da saúde financeira."""
        self.logger.info("Diagnóstico financeiro iniciado")
        prompt = f"""Faça um diagnóstico completo da saúde financeira desta empresa:

DADOS FINANCEIROS:
{json.dumps(data, indent=2, ensure_ascii=False)[:5000]}

Retorne JSON com:
- score_saude: 0-100
- status: "excelente"|"saudável"|"atenção"|"crítico"
- runway_meses: quantos meses de caixa restam
- burn_rate_mensal: gasto mensal em R$
- mrr: receita recorrente mensal
- margem_bruta_pct: margem bruta %
- margem_liquida_pct: margem líquida %
- ltv_cac_ratio: relação LTV/CAC
- pontos_criticos: lista de problemas urgentes
- pontos_positivos: lista de forças financeiras
- acoes_imediatas: top 3 ações para os próximos 30 dias
- projecao_12_meses: cenário base para próximos 12 meses"""

        result = self.ask_json(prompt, system=SYSTEM_CAPITAL)
        score = result.get("score_saude", 0)
        status = result.get("status", "?")
        icons = {"excelente": "💚", "saudável": "🟢", "atenção": "🟡", "crítico": "🔴"}
        print(f"\n{icons.get(status,'●')} CAPITAL Health Check — Score: {score}/100 ({status.upper()})")
        print(f"  Runway: {result.get('runway_meses','?')} meses")
        print(f"  MRR: R$ {result.get('mrr','?'):,.0f}" if isinstance(result.get('mrr'), (int,float)) else f"  MRR: {result.get('mrr','?')}")
        print(f"  Margem Líquida: {result.get('margem_liquida_pct','?')}%")
        self.save_result(result, prefix="capital_health")
        return result

    def allocate_budget(self, total_budget: float, projects: list) -> dict:
        """Aloca budget entre projetos usando otimização por ROI esperado."""
        self.logger.info(f"Alocando R$ {total_budget:,.0f} entre {len(projects)} projetos")
        prompt = f"""Você tem R$ {total_budget:,.2f} para alocar entre os seguintes projetos/iniciativas.

PROJETOS:
{json.dumps(projects, indent=2, ensure_ascii=False)[:4000]}

Otimize a alocação maximizando ROI esperado com gestão de risco.
Retorne JSON com:
- alocacoes: lista de objetos com:
  - projeto: nome
  - valor_alocado: R$
  - percentual: % do budget total
  - roi_esperado_pct: % de retorno esperado
  - prazo_retorno_meses: em meses
  - justificativa: por que alocar este valor
  - risco: baixo|médio|alto
- total_alocado: soma das alocações
- roi_portfolio_esperado: ROI médio ponderado do portfolio
- reserva_emergencia: valor mantido em reserva
- estrategia: resumo da lógica de alocação
- alertas: riscos e condições a monitorar"""

        result = self.ask_json(prompt, system=SYSTEM_CAPITAL)
        print(f"\n💰 CAPITAL Allocation — R$ {total_budget:,.0f}")
        for alloc in result.get("alocacoes", []):
            print(f"  {alloc.get('projeto','?'):<30} R$ {alloc.get('valor_alocado',0):>12,.0f}  ({alloc.get('percentual',0):.1f}%)")
        print(f"  ROI Portfolio Esperado: {result.get('roi_portfolio_esperado','?')}%")
        self.save_result(result, prefix="capital_allocation")
        return result

    def financial_forecast(self, historical_data: dict, months: int = 6) -> dict:
        """Previsão financeira para os próximos N meses."""
        self.logger.info(f"Forecast financeiro: {months} meses")
        prompt = f"""Com base nos dados históricos financeiros, gere uma previsão para os próximos {months} meses.

DADOS HISTÓRICOS:
{json.dumps(historical_data, indent=2, ensure_ascii=False)[:4000]}

Retorne JSON com:
- meses: lista de {months} objetos com:
  - mes: "YYYY-MM"
  - receita_prevista: R$
  - despesas_previstas: R$
  - lucro_previsto: R$
  - mrr_previsto: R$
  - caixa_final_previsto: R$
  - confianca: 0-100
- cenario_otimista: receita total em {months} meses
- cenario_base: receita total em {months} meses
- cenario_pessimista: receita total em {months} meses
- crescimento_esperado_pct: % de crescimento no período
- riscos_principais: lista de riscos financeiros
- oportunidades: lista de oportunidades de receita
- recomendacoes: top 3 ações para maximizar resultado"""

        result = self.ask_json(prompt, system=SYSTEM_CAPITAL)
        print(f"\n🔮 CAPITAL Forecast — {months} meses")
        print(f"  Cenário Base: R$ {result.get('cenario_base',0):,.0f}")
        print(f"  Cenário Otimista: R$ {result.get('cenario_otimista',0):,.0f}")
        print(f"  Crescimento Esperado: {result.get('crescimento_esperado_pct','?')}%")

        # Gera relatório Markdown
        md = f"# 📊 CAPITAL Forecast — {months} meses\n\n"
        md += f"**Gerado em:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        md += f"| Mês | Receita | Despesas | Lucro | MRR |\n|-----|---------|---------|-------|-----|\n"
        for m in result.get("meses", []):
            md += f"| {m.get('mes','')} | R${m.get('receita_prevista',0):,.0f} | R${m.get('despesas_previstas',0):,.0f} | R${m.get('lucro_previsto',0):,.0f} | R${m.get('mrr_previsto',0):,.0f} |\n"
        self.save_markdown(md, prefix="capital_forecast")
        self.save_result(result, prefix="capital_forecast")
        return result

    def risk_analysis(self, portfolio: dict) -> dict:
        """Análise de risco do portfolio financeiro."""
        self.logger.info("Análise de risco iniciada")
        prompt = f"""Analise os riscos financeiros deste portfolio/situação:

PORTFOLIO:
{json.dumps(portfolio, indent=2, ensure_ascii=False)[:4000]}

Retorne JSON com:
- score_risco: 0-100 (0=mínimo risco, 100=máximo risco)
- nivel_risco: "baixo"|"moderado"|"alto"|"crítico"
- riscos: lista de objetos com:
  - tipo: tipo do risco
  - probabilidade: baixa|média|alta
  - impacto: baixo|médio|alto|catastrófico
  - score: 0-100
  - descricao: descrição do risco
  - mitigacao: como mitigar
- concentracao_risco: onde está mais concentrado o risco
- diversificacao_score: 0-100 (100=perfeitamente diversificado)
- recomendacoes_mitigacao: top 5 ações para reduzir risco
- stress_test: o que acontece no pior cenário"""

        result = self.ask_json(prompt, system=SYSTEM_CAPITAL)
        nivel = result.get("nivel_risco", "?")
        icons = {"baixo": "🟢", "moderado": "🟡", "alto": "🔴", "crítico": "🚨"}
        print(f"\n{icons.get(nivel,'●')} CAPITAL Risk — Nível: {nivel.upper()} (score: {result.get('score_risco','?')}/100)")
        for r in result.get("riscos", [])[:5]:
            print(f"  [{r.get('impacto','?').upper():<12}] {r.get('tipo','?')}")
        self.save_result(result, prefix="capital_risk")
        return result

    def runway_analysis(self, cash_data: dict) -> dict:
        """Análise de runway e recomendações para extensão."""
        self.logger.info("Análise de runway iniciada")
        prompt = f"""Analise o runway desta empresa e gere recomendações:

DADOS DE CAIXA:
{json.dumps(cash_data, indent=2, ensure_ascii=False)[:3000]}

Retorne JSON com:
- caixa_atual: R$
- burn_rate_mensal: R$
- runway_meses: quantos meses de caixa
- runway_data_fim: data estimada de fim de caixa (YYYY-MM-DD)
- status: "seguro(>18m)"|"atenção(6-18m)"|"urgente(<6m)"|"crítico(<3m)"
- formas_estender_runway: lista de ações para reduzir burn ou aumentar receita
- cortes_possiveis: onde pode cortar sem impactar crescimento
- alavancas_receita: formas de aumentar receita rapidamente
- cenario_default_burn: quando o dinheiro acaba sem mudanças
- cenario_otimizado: runway após implementar recomendações
- urgencia: "normal"|"alta"|"crítica"
- proximos_passos: top 3 ações imediatas"""

        result = self.ask_json(prompt, system=SYSTEM_CAPITAL)
        runway = result.get("runway_meses", "?")
        status = result.get("status", "?")
        print(f"\n💵 CAPITAL Runway — {runway} meses ({status})")
        print(f"  Burn mensal: R$ {result.get('burn_rate_mensal',0):,.0f}" if isinstance(result.get('burn_rate_mensal'), (int,float)) else "")
        print(f"  Data de fim de caixa: {result.get('runway_data_fim','?')}")
        self.save_result(result, prefix="capital_runway")
        return result


def main():
    parser = argparse.ArgumentParser(description="CAPITAL — Sistema Financeiro ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("health", help="Health check financeiro").add_argument("--data", required=True)
    p_alloc = sub.add_parser("allocate", help="Alocar budget")
    p_alloc.add_argument("--budget", type=float, required=True)
    p_alloc.add_argument("--projects", required=True)
    p_fore = sub.add_parser("forecast", help="Forecast financeiro")
    p_fore.add_argument("--data", required=True)
    p_fore.add_argument("--months", type=int, default=6)
    sub.add_parser("risk", help="Análise de risco").add_argument("--portfolio", required=True)
    sub.add_parser("runway", help="Análise de runway").add_argument("--data", required=True)

    args = parser.parse_args()
    agent = CapitalAgent()

    def load(path): return json.loads(Path(path).read_text(encoding="utf-8"))

    if args.command == "health": agent.health_check(load(args.data))
    elif args.command == "allocate":
        projects = load(args.projects)
        agent.allocate_budget(args.budget, projects if isinstance(projects, list) else projects.get("projects", []))
    elif args.command == "forecast": agent.financial_forecast(load(args.data), args.months)
    elif args.command == "risk": agent.risk_analysis(load(args.portfolio))
    elif args.command == "runway": agent.runway_analysis(load(args.data))
    else: parser.print_help()


if __name__ == "__main__":
    main()
