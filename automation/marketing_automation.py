"""
Marketing Automation — ULTIMATE CRONUS
Automação completa de marketing: campanhas, ABM, growth hacking e performance.

Uso:
    python marketing_automation.py campaign --brief data/brief.json --budget 10000
    python marketing_automation.py abm --accounts data/contas.json
    python marketing_automation.py growth-hack --company data/empresa.json --goal "1000 usuários"
    python marketing_automation.py performance --metrics data/marketing_metrics.json
    python marketing_automation.py attribution --data data/attribution.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))
from base_agent import BaseAgent

SYSTEM_MARKETING = """Você é o Chief Marketing Officer do ULTIMATE CRONUS.
Você domina performance marketing, growth hacking, ABM, brand e marketing de produto.
Pense em termos de CAC, LTV, ROAS e attribution. Cada ação deve ser mensurável.
Combine dados com criatividade para gerar crescimento sustentável."""


class MarketingAutomation(BaseAgent):
    def __init__(self):
        super().__init__(name="MARKETING", output_dir="automation/reports")

    def campaign_strategy(self, brief: dict, budget: float) -> dict:
        """Cria estratégia completa de campanha de marketing."""
        self.logger.info(f"Campaign strategy: budget R$ {budget:,.0f}")
        prompt = f"""Crie uma estratégia completa de campanha de marketing:

BRIEF:
{json.dumps(brief, indent=2, ensure_ascii=False)[:3000]}

BUDGET TOTAL: R$ {budget:,.2f}

Retorne JSON com:
- objetivo_principal: o que esta campanha deve alcançar
- kpis_campanha: métricas de sucesso com metas específicas
- audiencia:
  - primaria: perfil detalhado
  - secundaria: segmento de suporte
  - exclusoes: quem NÃO faz sentido
- canais_e_budget:
  - canal: Google Ads | Meta | LinkedIn | SEO | Email | etc
  - budget_r$: valor alocado
  - budget_pct: % do total
  - objetivo_canal: o que cada canal faz na campanha
  - kpi_canal: métrica principal
- mensagens_por_funil:
  - topo: awareness (o que comunicar a quem não nos conhece)
  - meio: consideração (o que comunicar a quem nos conhece)
  - fundo: conversão (o que comunicar a quem está pronto para comprar)
- calendario_campanha: cronograma semanal de execução
- criativos_necessarios: lista de peças a produzir
- ab_tests_planejados: experimentos para otimizar durante a campanha
- projecoes:
  - impressoes: estimativa
  - cliques: estimativa
  - conversoes: estimativa
  - cac_estimado: R$
  - roas_esperado: X:1"""

        result = self.ask_json(prompt, system=SYSTEM_MARKETING)
        print(f"\n📢 Campaign Strategy — Budget: R$ {budget:,.0f}")
        kpis = result.get("kpis_campanha", {})
        print(f"  Objetivo: {result.get('objetivo_principal', '')[:80]}")
        self.save_result(result, prefix="campaign_strategy")
        return result

    def abm_playbook(self, accounts: list) -> dict:
        """Cria playbook de Account-Based Marketing."""
        self.logger.info(f"ABM: {len(accounts)} contas")
        total_opp = sum(a.get("oportunidade_estimada", 0) for a in accounts)
        prompt = f"""Crie um playbook de Account-Based Marketing (ABM):

CONTAS ALVO ({len(accounts)} contas, R$ {total_opp:,.0f} em oportunidade):
{json.dumps(accounts[:10], indent=2, ensure_ascii=False)[:4000]}

Retorne JSON com:
- tier_contas:
  - tier_1: contas de maior prioridade (1:1 marketing)
  - tier_2: contas de média prioridade (1:few)
  - tier_3: contas de menor prioridade (1:many)
- estrategia_por_tier:
  - tier: número
  - numero_contas: quantas
  - canais: como chegar
  - frequencia_contato: com que frequência
  - conteudo_personalizado: que conteúdo criar
  - eventos_especificos: se há eventos/webinars para este tier
  - budget_por_conta: R$ para personalização
- plano_por_conta_top: para as top 5 contas, plano detalhado:
  - conta: nome
  - stakeholders_mapeados: quem influencia a decisão
  - conteudo_personalizado: que criar especificamente para esta conta
  - sequencia_outreach: passo a passo do relacionamento
  - evento_trigger: o que aciona o contato
- metricas_abm: como medir sucesso do ABM
- tecnologia_necessaria: ferramentas para executar"""

        result = self.ask_json(prompt, system=SYSTEM_MARKETING)
        tiers = result.get("tier_contas", {})
        print(f"\n🎯 ABM Playbook — {len(accounts)} contas")
        print(f"  Tier 1: {len(tiers.get('tier_1', []))} | Tier 2: {len(tiers.get('tier_2', []))} | Tier 3: {len(tiers.get('tier_3', []))}")
        self.save_result(result, prefix="abm_playbook")
        return result

    def growth_hacking(self, company: dict, goal: str) -> dict:
        """Gera experimentos de growth hacking para atingir objetivo."""
        self.logger.info(f"Growth hack: {goal[:50]}")
        prompt = f"""Gere experimentos de growth hacking para atingir este objetivo:

EMPRESA:
{json.dumps(company, indent=2, ensure_ascii=False)[:2000]}

OBJETIVO: {goal}

Retorne JSON com:
- experimentos: lista de 10-15 experimentos ordenados por potencial com:
  - nome: nome do experimento
  - hipotese: se fizermos X, então Y
  - canal: onde executar
  - esforco: dias para implementar
  - impacto_potencial: "baixo"|"médio"|"alto"|"viral"
  - como_validar: métrica e threshold de sucesso
  - custo_estimado: R$
  - exemplo_empresa: empresa que fez algo similar
- experimentos_prioritarios: top 3 para começar agora
- viral_loops: mecanismos para crescimento viral (se aplicável)
- product_led_growth: como o produto em si pode ser o canal de aquisição
- referral_program: design de programa de indicação
- quick_wins: o que pode fazer esta semana com zero custo
- metricas_north_star: a métrica mais importante para este objetivo"""

        result = self.ask_json(prompt, system=SYSTEM_MARKETING)
        experimentos = result.get("experimentos", [])
        print(f"\n⚡ Growth Hacking — {goal[:50]}")
        print(f"  {len(experimentos)} experimentos gerados")
        for exp in result.get("experimentos_prioritarios", [])[:3]:
            print(f"  → {str(exp)[:80]}")
        self.save_result(result, prefix="growth_hacking")
        return result

    def performance_analysis(self, metrics: dict) -> dict:
        """Analisa performance de marketing e otimiza."""
        self.logger.info("Marketing performance analysis")
        prompt = f"""Analise a performance de marketing e identifique otimizações:

MÉTRICAS:
{json.dumps(metrics, indent=2, ensure_ascii=False)[:5000]}

Retorne JSON com:
- score_marketing: 0-100
- metricas_calculadas:
  - cac_total: R$ (custo de aquisição de cliente)
  - cac_por_canal: breakdown por canal
  - ltv_cac_ratio: LTV/CAC
  - roas_total: Return on Ad Spend total
  - taxa_conversao_total_pct: % de visitantes que viram clientes
  - custo_por_lead: R$
  - lead_to_customer_rate_pct: % de leads que fecham
- analise_por_canal:
  - canal: nome
  - gasto_r$: valor investido
  - resultados: leads, clientes gerados
  - cac_canal: R$
  - roas_canal: X:1
  - veredicto: escalar|manter|reduzir|parar
- gargalos_funil: onde está perdendo mais eficiência
- otimizacoes_imediatas: o que mudar agora para melhorar ROAS
- redistribuicao_budget: como realocar budget para maximizar resultado
- projecao_otimizada: resultado esperado após otimizações"""

        result = self.ask_json(prompt, system=SYSTEM_MARKETING)
        score = result.get("score_marketing", 0)
        m = result.get("metricas_calculadas", {})
        print(f"\n📊 Marketing Performance — Score: {score}/100")
        print(f"  CAC: R$ {m.get('cac_total', '?')} | LTV/CAC: {m.get('ltv_cac_ratio', '?')} | ROAS: {m.get('roas_total', '?')}")
        self.save_result(result, prefix="marketing_performance")
        return result

    def attribution_analysis(self, data: dict) -> dict:
        """Analisa atribuição de conversões por canal."""
        self.logger.info("Attribution analysis")
        prompt = f"""Analise a atribuição de conversões nestes dados de marketing:

DADOS:
{json.dumps(data, indent=2, ensure_ascii=False)[:5000]}

Retorne JSON com:
- modelo_atual: qual modelo de atribuição os dados usam
- comparacao_modelos:
  - first_touch: qual canal ganha crédito (% por canal)
  - last_touch: qual canal ganha crédito
  - linear: distribuição igualitária
  - time_decay: mais peso para touchpoints recentes
  - data_driven: baseado em contribuição real
- modelo_recomendado: qual usar e por que para este negócio
- canais_subestimados: canais que aparecem pouco mas contribuem muito
- canais_superestimados: canais com muito crédito mas pouco impacto real
- jornada_tipica_cliente: touchpoints mais comuns antes da conversão
- insights_chave: o que os dados revelam sobre como clientes decidem
- recomendacoes_budget: como realocaria o budget com base na atribuição correta"""

        result = self.ask_json(prompt, system=SYSTEM_MARKETING)
        modelo = result.get("modelo_recomendado", "?")
        print(f"\n🔀 Attribution Analysis — Modelo recomendado: {modelo}")
        subestimados = result.get("canais_subestimados", [])
        if isinstance(subestimados, list) and subestimados:
            print(f"  Subestimados: {subestimados}")
        self.save_result(result, prefix="attribution_analysis")
        return result


def main():
    parser = argparse.ArgumentParser(description="Marketing Automation — ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")

    p_c = sub.add_parser("campaign")
    p_c.add_argument("--brief", required=True)
    p_c.add_argument("--budget", type=float, default=10000)

    sub.add_parser("abm").add_argument("--accounts", required=True)

    p_g = sub.add_parser("growth-hack")
    p_g.add_argument("--company", required=True)
    p_g.add_argument("--goal", required=True)

    sub.add_parser("performance").add_argument("--metrics", required=True)
    sub.add_parser("attribution").add_argument("--data", required=True)

    args = parser.parse_args()
    agent = MarketingAutomation()
    def load(p): return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else {}

    if args.command == "campaign":
        agent.campaign_strategy(load(args.brief), args.budget)
    elif args.command == "abm":
        data = load(args.accounts)
        agent.abm_playbook(data if isinstance(data, list) else data.get("accounts", []))
    elif args.command == "growth-hack":
        agent.growth_hacking(load(args.company), args.goal)
    elif args.command == "performance":
        agent.performance_analysis(load(args.metrics))
    elif args.command == "attribution":
        agent.attribution_analysis(load(args.data))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
