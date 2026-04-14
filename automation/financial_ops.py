"""
Financial Ops — ULTIMATE CRONUS
Operações financeiras: DRE, fluxo de caixa, precificação, M&A e fundraising.

Uso:
    python financial_ops.py dre --data data/financeiro.json --period "Q1 2026"
    python financial_ops.py cash-flow --data data/caixa.json --months 12
    python financial_ops.py pricing --product data/produto.json --costs data/custos.json
    python financial_ops.py fundraising --company data/empresa.json --round "Series A"
    python financial_ops.py ma-analysis --target data/empresa_alvo.json --acquirer data/adquirente.json
    python financial_ops.py tax-planning --financials data/financeiro.json --regime "Lucro Real"
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))
from base_agent import BaseAgent

SYSTEM_FINOPS = """Você é o CFO Virtual do ULTIMATE CRONUS.
Você domina contabilidade gerencial, finanças corporativas, M&A, tributação e fundraising.
Pense como um CFO de empresa de alto crescimento + advisor de investimento.
Seja preciso com números, use frameworks financeiros reconhecidos e sempre apresente cenários."""


class FinancialOps(BaseAgent):
    def __init__(self):
        super().__init__(name="FINOPS", output_dir="automation/reports")

    def income_statement(self, data: dict, period: str) -> dict:
        """Analisa DRE e gera insights financeiros."""
        self.logger.info(f"DRE: {period}")
        prompt = f"""Analise esta DRE e gere análise financeira completa:

PERÍODO: {period}
DADOS FINANCEIROS:
{json.dumps(data, indent=2, ensure_ascii=False)[:5000]}

Retorne JSON com:
- dre_consolidado:
  - receita_bruta: R$
  - deducoes: R$
  - receita_liquida: R$
  - cogs: custo dos serviços/produtos
  - lucro_bruto: R$
  - margem_bruta_pct: %
  - despesas_operacionais: R$
  - ebitda: R$
  - margem_ebitda_pct: %
  - depreciacao: R$
  - ebit: R$
  - resultado_financeiro: R$
  - lucro_antes_ir: R$
  - ir_csll: R$
  - lucro_liquido: R$
  - margem_liquida_pct: %
- analise_vertical: cada linha como % da receita
- analise_horizontal: variação vs período anterior se disponível
- alertas: linhas com comportamento anormal
- drivers_receita: o que gerou crescimento ou queda
- drivers_custo: principais fatores de custo
- benchmark_setor: como compara com médias do setor
- acoes_melhora_margem: top 3 alavancas para melhorar margem"""

        result = self.ask_json(prompt, system=SYSTEM_FINOPS)
        dre = result.get("dre_consolidado", {})
        print(f"\n📊 DRE — {period}")
        print(f"  Receita Líquida: R$ {dre.get('receita_liquida', 0):,.0f}")
        print(f"  EBITDA: R$ {dre.get('ebitda', 0):,.0f} ({dre.get('margem_ebitda_pct', 0)}%)")
        print(f"  Lucro Líquido: R$ {dre.get('lucro_liquido', 0):,.0f} ({dre.get('margem_liquida_pct', 0)}%)")
        self.save_result(result, prefix=f"dre_{period.replace(' ', '_')}")
        return result

    def cash_flow_forecast(self, data: dict, months: int = 12) -> dict:
        """Projeta fluxo de caixa e identifica riscos de liquidez."""
        self.logger.info(f"Cash flow forecast: {months} meses")
        prompt = f"""Projete o fluxo de caixa para os próximos {months} meses:

DADOS ATUAIS:
{json.dumps(data, indent=2, ensure_ascii=False)[:5000]}

Retorne JSON com:
- posicao_caixa_atual: R$
- projecao_mensal: lista de {months} meses com:
  - mes: mês/ano
  - entradas: R$
  - saidas: R$
  - fluxo_liquido: R$
  - saldo_acumulado: R$
  - alerta: "ok"|"atencao"|"critico"
- cenarios:
  - otimista: saldo ao fim do período (receita +20%)
  - base: saldo mais provável
  - pessimista: saldo em cenário adverso (receita -20%)
- runway_meses: quanto tempo de caixa tem no cenário base
- meses_criticos: meses com maior risco de liquidez
- necessidade_capital: se e quanto precisa captar
- alavancas_caixa: como melhorar o fluxo de caixa rapidamente
- ciclo_financeiro: prazo médio de recebimento e pagamento
- capital_de_giro: necessidade de capital de giro"""

        result = self.ask_json(prompt, system=SYSTEM_FINOPS)
        saldo = result.get("posicao_caixa_atual", 0)
        runway = result.get("runway_meses", "?")
        print(f"\n💰 Cash Flow Forecast — {months} meses")
        print(f"  Caixa atual: R$ {saldo:,.0f} | Runway: {runway} meses")
        cenarios = result.get("cenarios", {})
        if cenarios:
            print(f"  Cenário base: {cenarios.get('base', '?')}")
        self.save_result(result, prefix="cash_flow_forecast")
        return result

    def pricing_strategy(self, product: dict, costs: dict) -> dict:
        """Cria estratégia de precificação baseada em custos e valor."""
        self.logger.info(f"Pricing: {product.get('nome', '?')}")
        prompt = f"""Crie uma estratégia de precificação completa:

PRODUTO/SERVIÇO:
{json.dumps(product, indent=2, ensure_ascii=False)[:2000]}

ESTRUTURA DE CUSTOS:
{json.dumps(costs, indent=2, ensure_ascii=False)[:2000]}

Retorne JSON com:
- custos_unitarios:
  - custo_variavel: R$ por unidade
  - custo_fixo_alocado: R$ por unidade
  - custo_total_unitario: R$
- margens_por_preco:
  - preco_minimo: break-even price em R$
  - preco_mercado: valor de mercado estimado
  - preco_valor: preço baseado em valor percebido
  - preco_premium: preço com posicionamento premium
- analise_sensibilidade: como a margem muda com variações de preço
- estrategia_recomendada:
  - modelo: "cost-plus"|"value-based"|"competitive"|"freemium"|"dynamic"
  - preco_lancamento: R$
  - preco_alvo_12m: R$
  - justificativa: por que estes preços
- estrutura_desconto: política de desconto e limites
- tiers_de_preco: se produto tem versões, precificação de cada tier
- impacto_no_mrr: projeção de receita com este pricing
- payback_cliente: em quanto tempo o cliente tem ROI"""

        result = self.ask_json(prompt, system=SYSTEM_FINOPS)
        custos = result.get("custos_unitarios", {})
        estrategia = result.get("estrategia_recomendada", {})
        print(f"\n💎 Pricing Strategy — {product.get('nome', '?')}")
        print(f"  Custo total: R$ {custos.get('custo_total_unitario', '?')} | Modelo: {estrategia.get('modelo', '?')}")
        print(f"  Preço recomendado: R$ {estrategia.get('preco_lancamento', '?')}")
        self.save_result(result, prefix="pricing_strategy")
        return result

    def fundraising_deck(self, company: dict, round_type: str) -> dict:
        """Prepara estratégia e materiais para fundraising."""
        self.logger.info(f"Fundraising: {round_type}")
        prompt = f"""Prepare uma estratégia completa de fundraising:

EMPRESA:
{json.dumps(company, indent=2, ensure_ascii=False)[:3000]}

RODADA: {round_type}

Retorne JSON com:
- tese_de_investimento: por que investir nesta empresa agora (2-3 parágrafos)
- valuation_sugerido:
  - pre_money: R$ ou USD
  - metodologia: como chegou neste valor
  - justificativa: benchmarks e múltiplos usados
- captacao_alvo: quanto captar e por quê este valor
- uso_dos_recursos: como o dinheiro será usado (% por categoria)
- metricas_chave_para_investidores: os KPIs que mais importam
- perfil_investidor_ideal: quem buscar para esta rodada
- pitch_deck_outline: estrutura completa do pitch deck (12-14 slides)
- red_flags_a_mitigar: problemas que investidores vão perguntar
- diligencia_preparacao: documentos para ter prontos
- timeline_fundraising: cronograma da rodada
- alternativas_captacao: se o VC não der, o que mais considerar"""

        result = self.ask_json(prompt, system=SYSTEM_FINOPS)
        valuation = result.get("valuation_sugerido", {})
        captacao = result.get("captacao_alvo", "?")
        print(f"\n🚀 Fundraising Strategy — {round_type}")
        print(f"  Valuation: {valuation.get('pre_money', '?')} | Captação: {captacao}")
        self.save_result(result, prefix=f"fundraising_{round_type.replace(' ', '_').lower()}")
        return result

    def ma_analysis(self, target: dict, acquirer: dict) -> dict:
        """Análise de M&A: valuation, sinergias e due diligence."""
        self.logger.info(f"M&A: {target.get('nome', '?')}")
        prompt = f"""Realize análise completa de M&A:

EMPRESA ALVO:
{json.dumps(target, indent=2, ensure_ascii=False)[:2500]}

ADQUIRENTE:
{json.dumps(acquirer, indent=2, ensure_ascii=False)[:2500]}

Retorne JSON com:
- valuation_alvo:
  - valor_standalone: valor sem sinergias
  - multiplo_utilizado: EV/EBITDA ou EV/Revenue
  - faixa_oferta_justa: mínimo e máximo em R$
- sinergias:
  - receita: sinergias de receita estimadas (R$/ano)
  - custo: sinergias de custo estimadas (R$/ano)
  - total_valor_sinergias: valor presente das sinergias
- racional_estrategico: por que faz sentido esta aquisição
- riscos_principais:
  - integracao: riscos de integração
  - cultural: fit cultural
  - regulatorio: aprovação de concorrência
  - financeiro: impacto no balanço
- due_diligence_checklist: áreas e itens a verificar
- estrutura_deal: como estruturar (cash, equity, earnout)
- timeline_processo: cronograma do deal
- alternativas: o que fazer se não fechar (build, parceria, outro alvo)
- recomendacao: fazer|negociar|desistir e por quê"""

        result = self.ask_json(prompt, system=SYSTEM_FINOPS)
        val = result.get("valuation_alvo", {})
        rec = result.get("recomendacao", "?")
        print(f"\n🤝 M&A Analysis — {target.get('nome', '?')}")
        print(f"  Valuation: {val.get('faixa_oferta_justa', '?')}")
        print(f"  Recomendação: {rec}")
        self.save_result(result, prefix="ma_analysis")
        return result

    def tax_planning(self, financials: dict, regime: str) -> dict:
        """Planejamento tributário para otimizar carga fiscal."""
        self.logger.info(f"Tax planning: {regime}")
        prompt = f"""Faça um planejamento tributário para esta empresa:

DEMONSTRATIVOS FINANCEIROS:
{json.dumps(financials, indent=2, ensure_ascii=False)[:4000]}

REGIME ATUAL: {regime}

IMPORTANTE: Apenas planejamento tributário legal (elisão fiscal), nunca evasão.

Retorne JSON com:
- carga_tributaria_atual:
  - total_impostos_pct: % da receita em impostos
  - principais_tributos: lista com valor de cada tributo
- avaliacao_regime_atual: se o regime atual é o mais adequado
- comparacao_regimes: Simples x Lucro Presumido x Lucro Real — qual melhor?
- oportunidades_legais:
  - incentivos_fiscais: benefícios fiscais que pode aproveitar
  - regime_tributario_otimo: qual regime para mudar se aplicável
  - estruturacao_societaria: se há ganhos com reestruturação
  - juros_sobre_capital_proprio: se aplicável e vantajoso
- economia_potencial_anual: R$ estimados de redução de carga fiscal
- riscos_fiscais: passivos tributários ou riscos de autuação
- acoes_prioritarias: top 5 ações de planejamento tributário
- prazo_implementacao: quando implementar cada ação
- aviso_legal: sempre consultar contador/advogado tributarista"""

        result = self.ask_json(prompt, system=SYSTEM_FINOPS)
        carga = result.get("carga_tributaria_atual", {})
        economia = result.get("economia_potencial_anual", "?")
        print(f"\n🧾 Tax Planning — {regime}")
        print(f"  Carga tributária: {carga.get('total_impostos_pct', '?')}% da receita")
        print(f"  Economia potencial: R$ {economia}/ano")
        self.save_result(result, prefix="tax_planning")
        return result


def main():
    parser = argparse.ArgumentParser(description="Financial Ops — ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")

    p_dre = sub.add_parser("dre")
    p_dre.add_argument("--data", required=True)
    p_dre.add_argument("--period", default=f"Q{((datetime.now().month-1)//3)+1} {datetime.now().year}")

    p_cf = sub.add_parser("cash-flow")
    p_cf.add_argument("--data", required=True)
    p_cf.add_argument("--months", type=int, default=12)

    p_pr = sub.add_parser("pricing")
    p_pr.add_argument("--product", required=True)
    p_pr.add_argument("--costs", required=True)

    p_fr = sub.add_parser("fundraising")
    p_fr.add_argument("--company", required=True)
    p_fr.add_argument("--round", required=True, dest="round_type")

    p_ma = sub.add_parser("ma-analysis")
    p_ma.add_argument("--target", required=True)
    p_ma.add_argument("--acquirer", required=True)

    p_tax = sub.add_parser("tax-planning")
    p_tax.add_argument("--financials", required=True)
    p_tax.add_argument("--regime", default="Lucro Presumido")

    args = parser.parse_args()
    agent = FinancialOps()
    def load(p): return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else {}

    if args.command == "dre":
        agent.income_statement(load(args.data), args.period)
    elif args.command == "cash-flow":
        agent.cash_flow_forecast(load(args.data), args.months)
    elif args.command == "pricing":
        agent.pricing_strategy(load(args.product), load(args.costs))
    elif args.command == "fundraising":
        agent.fundraising_deck(load(args.company), args.round_type)
    elif args.command == "ma-analysis":
        agent.ma_analysis(load(args.target), load(args.acquirer))
    elif args.command == "tax-planning":
        agent.tax_planning(load(args.financials), args.regime)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
