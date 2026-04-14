"""
Fintech Agent — ULTIMATE CRONUS
Automações para fintechs: pagamentos, crédito, open finance e compliance regulatório.

Uso:
    python fintech_agent.py credit-risk --applicant data/solicitante.json
    python fintech_agent.py fraud-analysis --transactions data/transacoes.json
    python fintech_agent.py open-finance --data data/open_finance.json
    python fintech_agent.py product-design --segment "MEI" --product "cartão"
    python fintech_agent.py regulatory --company data/fintech.json --licenses "IP,SCD"
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_agent import BaseAgent

SYSTEM_FINTECH = """Você é especialista em Fintech do ULTIMATE CRONUS.
Você domina pagamentos, crédito, open finance, regulação (BACEN, CVM) e produtos financeiros.
Pense como um Head of Product de fintech + compliance officer.
IMPORTANTE: Análises de crédito e risco são modelos preditivos, não decisões definitivas.
Sempre considerar regulamentação BACEN, Resolução CMN e LGPD."""


class FintechAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="FINTECH", output_dir="agents/output")

    def credit_risk_model(self, applicant: dict) -> dict:
        """Modelo de análise de risco de crédito."""
        self.logger.info(f"Credit risk: {applicant.get('nome', '?')}")
        prompt = f"""Analise o risco de crédito deste solicitante (modelo preditivo, não decisão final):

SOLICITANTE:
{json.dumps(applicant, indent=2, ensure_ascii=False)[:3000]}

Retorne JSON com:
- score_credito: 0-1000 (similar ao score de mercado)
- nivel_risco: "muito_baixo"|"baixo"|"medio"|"alto"|"muito_alto"
- probabilidade_inadimplencia_pct: % estimado de inadimplência
- variaveis_positivas: fatores que reduzem o risco
- variaveis_negativas: fatores que aumentam o risco
- limite_recomendado: R$ de limite de crédito sugerido
- taxa_juros_sugerida: % ao mês baseada no risco
- prazo_maximo_meses: prazo máximo recomendado
- garantias_necessarias: se deve exigir garantias
- documentos_adicionais: documentação adicional a solicitar
- flags_atencao: alertas específicos sobre este perfil
- politica_aplicada: qual política de crédito foi aplicada
- disclaimer: esta é uma análise preditiva, não substitui análise de crédito formal"""

        result = self.ask_json(prompt, system=SYSTEM_FINTECH)
        score = result.get("score_credito", 0)
        nivel = result.get("nivel_risco", "?")
        icons = {"muito_alto": "🚨", "alto": "🔴", "medio": "🟡", "baixo": "🟢", "muito_baixo": "💚"}
        print(f"\n{icons.get(nivel, '●')} Credit Risk — Score: {score}/1000 ({nivel})")
        print(f"  Limite sugerido: R$ {result.get('limite_recomendado', '?')} | Taxa: {result.get('taxa_juros_sugerida', '?')}% a.m.")
        self.save_result(result, prefix="credit_risk")
        return result

    def fraud_detection(self, transactions: list) -> dict:
        """Análise de fraude em transações financeiras."""
        self.logger.info(f"Fraud analysis: {len(transactions)} transações")
        total = sum(t.get("valor", 0) for t in transactions)
        prompt = f"""Analise estas transações financeiras para detecção de fraude:

TRANSAÇÕES ({len(transactions)} transações, total R$ {total:,.2f}):
{json.dumps(transactions[:30], indent=2, ensure_ascii=False)[:5000]}

Retorne JSON com:
- score_risco_portfolio: 0-100 (100 = altíssimo risco de fraude)
- transacoes_suspeitas: lista de transações com:
  - id: identificador
  - valor: R$
  - motivo_suspeita: por que é suspeita
  - score_fraude: 0-100
  - acao_recomendada: "bloquear"|"revisar"|"alertar_cliente"|"aprovar"
- padroes_detectados: padrões anômalos no conjunto de transações
- tipos_fraude_identificados: categorias de fraude potencial
- valor_em_risco: R$ total das transações suspeitas
- regras_disparadas: quais regras antifraude foram ativadas
- falsos_positivos_estimados: % de alertas que provavelmente são legítimos
- acoes_imediatas: o que fazer nas próximas 1-2 horas
- melhorias_modelo: como melhorar a detecção no futuro"""

        result = self.ask_json(prompt, system=SYSTEM_FINTECH)
        score = result.get("score_risco_portfolio", 0)
        suspeitas = result.get("transacoes_suspeitas", [])
        valor_risco = result.get("valor_em_risco", 0)
        print(f"\n🔍 Fraud Detection — Score: {score}/100 | {len(suspeitas)} suspeitas | R$ {valor_risco:,.2f} em risco")
        self.save_result(result, prefix="fraud_analysis")
        return result

    def open_finance_insights(self, data: dict) -> dict:
        """Gera insights de Open Finance para personalização de produtos."""
        self.logger.info("Open Finance insights")
        prompt = f"""Analise estes dados de Open Finance e gere insights para personalização:

DADOS OPEN FINANCE:
{json.dumps(data, indent=2, ensure_ascii=False)[:5000]}

Retorne JSON com:
- perfil_financeiro:
  - nivel_renda: estimativa de faixa de renda
  - comportamento_gastos: onde gasta mais (categorias)
  - padrao_poupanca: se poupa e quanto
  - uso_credito: como usa crédito disponível
  - saude_financeira_score: 0-100
- produtos_relevantes: produtos financeiros que fazem sentido para este perfil
- ofertas_personalizadas: ofertas específicas com probabilidade de conversão
- momento_financeiro: fase da vida financeira (crescimento, consolidação, etc)
- oportunidades_cross_sell: o que mais vender para este cliente
- risco_churn_financeiro: probabilidade de migrar para outro banco
- mensagem_personalizada: abordagem ideal para este cliente
- alertas_negativos: sinais que merecem atenção (endividamento, etc)
- compliance_lgpd: confirmar que análise respeita consentimento do cliente"""

        result = self.ask_json(prompt, system=SYSTEM_FINTECH)
        saude = result.get("perfil_financeiro", {}).get("saude_financeira_score", 0)
        print(f"\n🏦 Open Finance Insights — Saúde financeira: {saude}/100")
        ofertas = result.get("ofertas_personalizadas", [])
        print(f"  Ofertas personalizadas: {len(ofertas) if isinstance(ofertas, list) else '?'}")
        self.save_result(result, prefix="open_finance_insights")
        return result

    def product_design(self, segment: str, product_type: str) -> dict:
        """Cria design de produto financeiro para segmento específico."""
        self.logger.info(f"Product design: {product_type} para {segment}")
        prompt = f"""Crie o design de um produto financeiro:

SEGMENTO ALVO: {segment}
TIPO DE PRODUTO: {product_type}

Retorne JSON com:
- nome_produto: nome atrativo e regulatoriamente correto
- proposta_de_valor: benefício central para o segmento
- features_principais: funcionalidades do produto
- precificacao:
  - modelo: tarifas, spread, mensalidade, etc
  - valores: R$ ou % específicos
  - justificativa: como se posiciona vs mercado
- elegibilidade: quem pode ter o produto
- jornada_de_onboarding: como o cliente começa a usar
- limites_iniciais: valores iniciais (crédito, transação, etc)
- evolucao_limites: como o cliente evolui ao longo do tempo
- programa_fidelidade: se há e como funciona
- diferenciais_competitivos: por que escolher vs bancos e outras fintechs
- regulamentacao_aplicavel: quais normas BACEN regulam este produto
- tecnologia_necessaria: stack para construir
- unit_economics: LTV, CAC esperado, payback period"""

        result = self.ask_json(prompt, system=SYSTEM_FINTECH)
        nome = result.get("nome_produto", "?")
        print(f"\n💳 Product Design — {nome} para {segment}")
        print(f"  Proposta: {result.get('proposta_de_valor', '')[:100]}")
        self.save_result(result, prefix=f"product_design_{product_type.replace(' ', '_').lower()}")
        return result

    def regulatory_compliance(self, company: dict, licenses: list) -> dict:
        """Análise de compliance regulatório para fintech."""
        self.logger.info(f"Regulatory: {licenses}")
        prompt = f"""Analise o status regulatório desta fintech:

EMPRESA:
{json.dumps(company, indent=2, ensure_ascii=False)[:3000]}

LICENÇAS EM ANÁLISE: {', '.join(licenses)}

Licenças BACEN:
- IP: Instituição de Pagamento
- SCD: Sociedade de Crédito Direto
- SCM: Sociedade de Crédito ao Microempreendedor
- SEP: Sociedade de Empréstimo entre Pessoas (P2P)
- DTVM: Distribuidora de Títulos e Valores Mobiliários
- Correspondente: Correspondente Bancário

Retorne JSON com:
- status_por_licenca: para cada licença solicitada:
  - licenca: nome
  - necessidade: por que precisa desta licença
  - requisitos_principais: o que o BACEN exige
  - capital_minimo: patrimônio líquido mínimo exigido
  - prazo_estimado_aprovacao: meses
  - dificuldade: "baixa"|"média"|"alta"|"muito_alta"
  - documentos_necessarios: principais documentos
- compliance_atual:
  - pci_dss: status de compliance com PCI-DSS
  - lgpd: status LGPD
  - pld_ft: Prevenção à Lavagem de Dinheiro e Financiamento ao Terrorismo
  - bacen_4658: política de cibersegurança
- riscos_regulatorios: principais riscos de não conformidade
- roadmap_regularizacao: ordem recomendada para obter licenças
- custo_estimado: investimento em compliance (estrutura + advogados)"""

        result = self.ask_json(prompt, system=SYSTEM_FINTECH)
        print(f"\n⚖️  Regulatory Compliance — {len(licenses)} licenças analisadas")
        for lic in result.get("status_por_licenca", [])[:3]:
            if isinstance(lic, dict):
                print(f"  {lic.get('licenca', '?')}: {lic.get('dificuldade', '?')} | {lic.get('prazo_estimado_aprovacao', '?')} meses")
        self.save_result(result, prefix="fintech_regulatory")
        return result


def main():
    parser = argparse.ArgumentParser(description="Fintech Agent — ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("credit-risk").add_argument("--applicant", required=True)
    sub.add_parser("fraud-analysis").add_argument("--transactions", required=True)
    sub.add_parser("open-finance").add_argument("--data", required=True)

    p_pd = sub.add_parser("product-design")
    p_pd.add_argument("--segment", required=True)
    p_pd.add_argument("--product", required=True, dest="product_type")

    p_reg = sub.add_parser("regulatory")
    p_reg.add_argument("--company", required=True)
    p_reg.add_argument("--licenses", required=True)

    args = parser.parse_args()
    agent = FintechAgent()
    def load(p): return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else {}

    if args.command == "credit-risk":
        agent.credit_risk_model(load(args.applicant))
    elif args.command == "fraud-analysis":
        data = load(args.transactions)
        agent.fraud_detection(data if isinstance(data, list) else data.get("transactions", []))
    elif args.command == "open-finance":
        agent.open_finance_insights(load(args.data))
    elif args.command == "product-design":
        agent.product_design(args.segment, args.product_type)
    elif args.command == "regulatory":
        agent.regulatory_compliance(load(args.company), [l.strip() for l in args.licenses.split(",")])
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
