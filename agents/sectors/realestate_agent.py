"""
Real Estate Agent — ULTIMATE CRONUS
Automações para mercado imobiliário: corretagem, incorporação, gestão de ativos.

Uso:
    python realestate_agent.py valuation --property data/imovel.json --market data/mercado.json
    python realestate_agent.py lead-qualify --leads data/leads.json
    python realestate_agent.py listing --property data/imovel.json --target "comprador"
    python realestate_agent.py portfolio --assets data/portfolio.json
    python realestate_agent.py market-report --region "São Paulo - Pinheiros" --type "apartamento"
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_agent import BaseAgent

SYSTEM_REALESTATE = """Você é especialista em mercado imobiliário do ULTIMATE CRONUS.
Você domina avaliação, vendas, gestão de portfólio e tendências do mercado imobiliário brasileiro.
Pense como um broker experiente + analista de investimento imobiliário.
Seja preciso com valores, foque em ROI e cap rate para decisões de investimento."""


class RealEstateAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="REALESTATE", output_dir="agents/output")

    def property_valuation(self, property_data: dict, market: dict) -> dict:
        """Avalia propriedade com múltiplas metodologias."""
        self.logger.info(f"Valuation: {property_data.get('endereco', '?')[:50]}")
        prompt = f"""Faça uma avaliação completa deste imóvel:

IMÓVEL:
{json.dumps(property_data, indent=2, ensure_ascii=False)[:3000]}

DADOS DE MERCADO:
{json.dumps(market, indent=2, ensure_ascii=False)[:2000]}

Retorne JSON com:
- valor_estimado_venda: R$ (faixa min-max)
- valor_estimado_aluguel: R$/mês
- metodologias_avaliacao:
  - comparativo_mercado: valor por comparação (R$/m²)
  - renda: valor pela renda de aluguel
  - custo: valor pelo custo de reposição
- metricas_investimento:
  - cap_rate_pct: taxa de capitalização anual
  - yield_bruto_pct: yield bruto de aluguel
  - payback_anos: anos para retorno do investimento
  - roi_5_anos_pct: ROI projetado em 5 anos
- analise_localizacao:
  - score_localizacao: 0-100
  - pontos_positivos: o que valoriza
  - pontos_negativos: o que desvaloriza
  - tendencia_bairro: valorizando|estavel|desvalorizando
- comparaveis_mercado: imóveis similares vendidos recentemente
- melhorias_que_valorizam: o que pode aumentar o valor e quanto
- recomendacao: comprar|vender|alugar|aguardar"""

        result = self.ask_json(prompt, system=SYSTEM_REALESTATE)
        valor = result.get("valor_estimado_venda", "?")
        aluguel = result.get("valor_estimado_aluguel", "?")
        print(f"\n🏠 Property Valuation — {property_data.get('endereco', '?')[:40]}")
        print(f"  Venda: {valor} | Aluguel: R$ {aluguel}/mês")
        m = result.get("metricas_investimento", {})
        print(f"  Cap Rate: {m.get('cap_rate_pct', '?')}% | Yield: {m.get('yield_bruto_pct', '?')}%")
        self.save_result(result, prefix="property_valuation")
        return result

    def qualify_leads(self, leads: list) -> dict:
        """Qualifica e prioriza leads de compradores/locatários."""
        self.logger.info(f"Qualifying {len(leads)} leads")
        prompt = f"""Qualifique e priorize estes leads imobiliários:

LEADS ({len(leads)} leads):
{json.dumps(leads[:20], indent=2, ensure_ascii=False)[:4000]}

Retorne JSON com:
- leads_qualificados: lista ordenada por prioridade com:
  - id: identificador
  - nome: nome do lead
  - score: 0-100
  - perfil: "comprador_final"|"investidor"|"locatario"|"especulador"
  - intenção: "imediata"|"3_meses"|"6_meses"|"1_ano+"
  - capacidade_financeira: estimativa de budget
  - tipo_imovel_buscado: o que precisa
  - proximo_contato: quando e como contatar
  - mensagem_personalizada: abordagem para este lead específico
- distribuicao_por_intencao: quantos por urgência
- hot_leads: top 5 leads mais quentes para contato imediato
- estrategia_nurturing: como trabalhar leads de médio/longo prazo"""

        result = self.ask_json(prompt, system=SYSTEM_REALESTATE)
        qualificados = result.get("leads_qualificados", [])
        hot = result.get("hot_leads", [])
        print(f"\n🎯 Lead Qualification — {len(qualificados)} leads qualificados")
        print(f"  Hot leads: {len(hot) if isinstance(hot, list) else '?'}")
        self.save_result(result, prefix="realestate_leads")
        return result

    def create_listing(self, property_data: dict, target: str) -> dict:
        """Cria anúncio completo para um imóvel."""
        self.logger.info(f"Listing: {property_data.get('endereco', '?')[:40]}")
        prompt = f"""Crie um anúncio completo para este imóvel direcionado para: {target}

IMÓVEL:
{json.dumps(property_data, indent=2, ensure_ascii=False)[:3000]}

Retorne JSON com:
- titulo_principal: título impactante (máx 80 chars)
- descricao_completa: descrição detalhada e persuasiva (300-500 palavras)
- descricao_curta: versão resumida (100 palavras) para portais
- diferenciais: 5-7 bullet points dos maiores atrativos
- para_quem_e_ideal: descrição do perfil ideal do comprador/locatário
- objecoes_e_respostas: 5 objeções comuns e como rebater
- copy_whatsapp: mensagem de abordagem via WhatsApp
- copy_instagram: legenda para Instagram + hashtags
- copy_email: email de apresentação formal
- fotos_prioritarias: lista do que fotografar e em que ordem
- video_script: roteiro para vídeo tour (60 segundos)
- preco_estrategia: como posicionar o preço na negociação"""

        result = self.ask_json(prompt, system=SYSTEM_REALESTATE)
        print(f"\n📋 Property Listing — {property_data.get('endereco', '?')[:40]}")
        print(f"  Título: {result.get('titulo_principal', '')[:80]}")
        self.save_result(result, prefix="property_listing")
        return result

    def portfolio_analysis(self, assets: list) -> dict:
        """Analisa portfólio imobiliário completo."""
        self.logger.info(f"Portfolio: {len(assets)} ativos")
        total_value = sum(a.get("valor_atual", 0) for a in assets)
        prompt = f"""Analise este portfólio imobiliário:

ATIVOS ({len(assets)} imóveis, valor total estimado: R$ {total_value:,.0f}):
{json.dumps(assets, indent=2, ensure_ascii=False)[:5000]}

Retorne JSON com:
- valor_total_portfolio: R$
- score_portfolio: 0-100
- metricas_portfolio:
  - yield_medio_pct: yield médio ponderado
  - cap_rate_medio_pct: cap rate médio
  - diversificacao_geografica: distribuição por região
  - diversificacao_tipo: por tipo de imóvel
  - vacancia_media_pct: % de vacância
- ativos_por_performance:
  - estrelas: melhores performers (top 25%)
  - ok: performers medianos
  - problemas: piores performers (bottom 25%)
- recomendacoes_por_ativo: para cada ativo — manter|vender|melhorar
- otimizacao_portfolio:
  - vender_agora: o que desinvestir e por quê
  - manter: o que segurar
  - comprar: que tipo de ativo adicionar para otimizar
- projecao_5_anos: valor e renda esperados em 5 anos
- risco_concentracao: alertas de concentração excessiva"""

        result = self.ask_json(prompt, system=SYSTEM_REALESTATE)
        score = result.get("score_portfolio", 0)
        valor = result.get("valor_total_portfolio", 0)
        print(f"\n💼 Portfolio Analysis — R$ {valor:,.0f} | Score: {score}/100")
        m = result.get("metricas_portfolio", {})
        print(f"  Yield médio: {m.get('yield_medio_pct', '?')}% | Vacância: {m.get('vacancia_media_pct', '?')}%")
        self.save_result(result, prefix="realestate_portfolio")
        return result

    def market_report(self, region: str, property_type: str) -> dict:
        """Gera relatório de mercado imobiliário para região/tipo."""
        self.logger.info(f"Market report: {region} / {property_type}")
        prompt = f"""Gere um relatório completo do mercado imobiliário:

REGIÃO: {region}
TIPO DE IMÓVEL: {property_type}

Retorne JSON com:
- panorama_mercado: visão geral atual
- preco_medio_m2: R$/m² (venda e aluguel)
- tendencia_precos: valorizando|estável|desvalorizando + percentual estimado
- oferta_vs_demanda: balanço de mercado atual
- tempo_medio_venda_dias: dias para vender
- perfil_compradores: quem está comprando nesta região
- bairros_mais_aquecidos: sub-regiões com maior atividade
- novos_lancamentos: empreendimentos recentes ou planejados
- fatores_valorizacao: o que está impulsionando o mercado
- fatores_risco: riscos para o mercado nos próximos 12 meses
- oportunidades_investimento: melhor estratégia neste mercado agora
- previsao_12_meses: perspectivas para o próximo ano"""

        result = self.ask_json(prompt, system=SYSTEM_REALESTATE)
        print(f"\n📊 Market Report — {region} ({property_type})")
        print(f"  Tendência: {result.get('tendencia_precos', '?')}")
        print(f"  Tempo médio venda: {result.get('tempo_medio_venda_dias', '?')} dias")
        self.save_result(result, prefix=f"market_report_{region.replace(' ', '_').lower()[:20]}")
        return result


def main():
    parser = argparse.ArgumentParser(description="Real Estate Agent — ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")

    p_v = sub.add_parser("valuation")
    p_v.add_argument("--property", required=True)
    p_v.add_argument("--market", required=True)

    sub.add_parser("lead-qualify").add_argument("--leads", required=True)

    p_l = sub.add_parser("listing")
    p_l.add_argument("--property", required=True)
    p_l.add_argument("--target", default="comprador")

    sub.add_parser("portfolio").add_argument("--assets", required=True)

    p_mr = sub.add_parser("market-report")
    p_mr.add_argument("--region", required=True)
    p_mr.add_argument("--type", required=True, dest="property_type")

    args = parser.parse_args()
    agent = RealEstateAgent()
    def load(p): return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else {}

    if args.command == "valuation":
        agent.property_valuation(load(args.property), load(args.market))
    elif args.command == "lead-qualify":
        data = load(args.leads)
        agent.qualify_leads(data if isinstance(data, list) else data.get("leads", []))
    elif args.command == "listing":
        agent.create_listing(load(args.property), args.target)
    elif args.command == "portfolio":
        data = load(args.assets)
        agent.portfolio_analysis(data if isinstance(data, list) else data.get("assets", []))
    elif args.command == "market-report":
        agent.market_report(args.region, args.property_type)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
