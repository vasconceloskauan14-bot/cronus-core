"""
Agro Agent — ULTIMATE CRONUS
Automações para agronegócio: gestão de fazenda, commodities, rastreabilidade e ESG.

Uso:
    python agro_agent.py farm-ops --farm data/fazenda.json
    python agro_agent.py commodity-analysis --commodity "soja" --position data/posicao.json
    python agro_agent.py crop-planning --farm data/fazenda.json --season "2026/27"
    python agro_agent.py esg-report --farm data/fazenda.json
    python agro_agent.py supply-chain --product "soja" --chain data/cadeia.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_agent import BaseAgent

SYSTEM_AGRO = """Você é especialista em Agronegócio do ULTIMATE CRONUS.
Você domina gestão de fazendas, commodities, mercado agrícola e ESG no agro.
Pense como um consultor agrícola de alta performance + trader de commodities.
Brasil é maior exportador de soja, cana e café. Contexto climático e cambial são críticos."""


class AgroAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="AGRO", output_dir="agents/output")

    def farm_operations(self, farm: dict) -> dict:
        """Analisa e otimiza operações da fazenda."""
        self.logger.info(f"Farm ops: {farm.get('nome','?')}")
        prompt = f"""Analise as operações desta fazenda e identifique oportunidades de melhoria:

FAZENDA:
{json.dumps(farm, indent=2, ensure_ascii=False)[:4000]}

Retorne JSON com:
- score_operacional: 0-100
- metricas_produtividade:
  - produtividade_ha: sacas ou ton/ha por cultura
  - custo_producao_ha: R$/ha
  - receita_ha: R$/ha
  - margem_bruta_ha: R$/ha
  - break_even_saca: preço mínimo para cobrir custos
- analise_por_cultura: para cada cultura plantada
- gargalos_operacionais: o que limita a produtividade
- oportunidades_tecnologia:
  - agricultura_precisao: GPS, drones, sensores
  - irrigacao_inteligente: quando e onde implementar
  - maquinario: investimentos com melhor ROI
- gestao_insumos: como otimizar uso de fertilizantes e defensivos
- calendario_agricola: cronograma otimizado de plantio e colheita
- riscos: clima, praga, câmbio, preço de commodity
- seguros_e_instrumentos: seguro rural, CPR, hedge cambial
- metas_safra: projeção para próxima safra"""

        result = self.ask_json(prompt, system=SYSTEM_AGRO)
        score = result.get("score_operacional", 0)
        m = result.get("metricas_produtividade", {})
        print(f"\n🌱 Farm Ops — {farm.get('nome','?')}: {score}/100")
        print(f"  Produtividade: {m.get('produtividade_ha','?')} sc/ha | Margem: R$ {m.get('margem_bruta_ha','?')}/ha")
        self.save_result(result, prefix="farm_ops")
        return result

    def commodity_analysis(self, commodity: str, position: dict) -> dict:
        """Analisa mercado de commodity e recomenda estratégia de comercialização."""
        self.logger.info(f"Commodity analysis: {commodity}")
        prompt = f"""Analise o mercado de {commodity} e crie estratégia de comercialização:

COMMODITY: {commodity}
POSIÇÃO ATUAL:
{json.dumps(position, indent=2, ensure_ascii=False)[:2000]}

Retorne JSON com:
- analise_mercado:
  - preco_atual: R$/saca ou R$/ton
  - tendencia: alta|estavel|queda
  - fatores_alta: o que pode puxar o preço para cima
  - fatores_queda: o que pode puxar o preço para baixo
  - sazonalidade: comportamento típico ao longo do ano
- estrategia_comercializacao:
  - percentual_vender_agora_pct: quanto vender imediatamente
  - percentual_travar_pct: quanto fixar em preço
  - percentual_aguardar_pct: quanto manter sem fixar
  - preco_alvo: preço ideal para vender o restante
  - prazo_decisao: quando precisar decidir no máximo
- instrumentos_hedge:
  - contratos_futuros: uso de B3 para proteção
  - opcoes: put/call para proteção com custo definido
  - ndf: para proteção cambial
- custo_financeiro: custo de carregar estoque vs vender agora
- cenarios:
  - otimista: se o preço subir X%
  - base: cenário mais provável
  - pessimista: se o preço cair X%
- recomendacao_final: ação recomendada com justificativa"""

        result = self.ask_json(prompt, system=SYSTEM_AGRO)
        estrategia = result.get("estrategia_comercializacao", {})
        print(f"\n📊 Commodity Analysis — {commodity}")
        print(f"  Vender agora: {estrategia.get('percentual_vender_agora_pct','?')}% | Travar: {estrategia.get('percentual_travar_pct','?')}%")
        print(f"  Recomendação: {str(result.get('recomendacao_final','?'))[:100]}")
        self.save_result(result, prefix=f"commodity_{commodity.lower()}")
        return result

    def crop_planning(self, farm: dict, season: str) -> dict:
        """Cria planejamento de safra completo."""
        self.logger.info(f"Crop planning: {season}")
        prompt = f"""Crie um planejamento de safra completo:

FAZENDA:
{json.dumps(farm, indent=2, ensure_ascii=False)[:3000]}

SAFRA: {season}

Retorne JSON com:
- recomendacao_culturas: quais culturas plantar e em que área
- cronograma_safra:
  - preparacao_solo: quando e como
  - plantio: janela ideal por cultura
  - tratos_culturais: adubação, defensivos, irrigação
  - colheita: janela prevista
- projecao_financeira:
  - receita_projetada: R$
  - custo_producao: R$
  - margem_projetada: R$
  - roi_safra_pct: %
- insumos_necessarios: lista de insumos com quantidades e custos
- maquinario: o que precisará locar ou contratar
- mao_de_obra: pico de necessidade por período
- riscos_da_safra: principais riscos climáticos e de mercado
- plano_contingencia: o que fazer se a safra tiver problemas
- comercializacao_antecipada: quanto vender antes da colheita (pré-venda)"""

        result = self.ask_json(prompt, system=SYSTEM_AGRO)
        proj = result.get("projecao_financeira", {})
        print(f"\n🌾 Crop Planning — Safra {season}")
        print(f"  Receita: R$ {proj.get('receita_projetada','?')} | Margem: R$ {proj.get('margem_projetada','?')} | ROI: {proj.get('roi_safra_pct','?')}%")
        self.save_result(result, prefix=f"crop_plan_{season.replace('/','_')}")
        return result

    def esg_report(self, farm: dict) -> dict:
        """Gera relatório ESG para a fazenda."""
        self.logger.info(f"ESG report: {farm.get('nome','?')}")
        prompt = f"""Gere um relatório ESG completo para esta fazenda:

FAZENDA:
{json.dumps(farm, indent=2, ensure_ascii=False)[:4000]}

Retorne JSON com:
- score_esg_total: 0-100
- dimensao_ambiental:
  - score: 0-100
  - area_preservada_pct: % da propriedade em reserva/APP
  - uso_agrotoxicos: classificacao de uso (alto/medio/baixo)
  - sequestro_carbono: estimativa ton CO2/ano
  - uso_agua: eficiência hídrica
  - acoes_positivas: o que já faz de sustentável
  - acoes_necessarias: o que deve melhorar
- dimensao_social:
  - score: 0-100
  - empregos_diretos: gerados
  - conformidade_trabalhista: situação CLT e segurança
  - impacto_comunidade: relação com a comunidade local
- dimensao_governanca:
  - score: 0-100
  - rastreabilidade: sistema de rastreabilidade implementado
  - certificacoes: quais tem ou pode buscar (Rainforest, Orgânico, etc)
  - conformidade_car: Cadastro Ambiental Rural em dia
- certificacoes_recomendadas: quais buscar e o valor que agrega
- premium_esg: quanto pode ganhar a mais com produtos certificados
- relatorio_executivo: texto para publicação externa (1-2 páginas)"""

        result = self.ask_json(prompt, system=SYSTEM_AGRO)
        score = result.get("score_esg_total", 0)
        print(f"\n🌿 ESG Report — {farm.get('nome','?')}: {score}/100")
        for dim in ["dimensao_ambiental","dimensao_social","dimensao_governanca"]:
            s = result.get(dim, {}).get("score", 0)
            label = dim.replace("dimensao_","").capitalize()
            print(f"  {label:<15} {'█'*int(s/10)}{'░'*(10-int(s/10))} {s}/100")
        self.save_result(result, prefix="esg_report")
        return result

    def supply_chain_agro(self, product: str, chain: dict) -> dict:
        """Analisa cadeia de valor agrícola do campo ao consumidor."""
        self.logger.info(f"Agro supply chain: {product}")
        prompt = f"""Analise a cadeia de valor deste produto agrícola:

PRODUTO: {product}
CADEIA:
{json.dumps(chain, indent=2, ensure_ascii=False)[:4000]}

Retorne JSON com:
- mapeamento_cadeia: cada elo com:
  - elo: nome (produtor, beneficiador, exportador, etc)
  - margem_capturada_pct: % do valor final que fica neste elo
  - poder_negociacao: "alto"|"medio"|"baixo"
  - gargalos: principais ineficiências neste elo
- distribuicao_valor: quanto fica em cada elo (diagrama de valor)
- elos_mais_lucrativos: onde está a maior margem na cadeia
- onde_produtor_perde_valor: onde o agricultor perde poder de negociação
- estrategias_captura_valor: como o produtor pode capturar mais valor
  - verticalizacao: processar o produto antes de vender
  - cooperativas: como cooperativas aumentam poder de negociação
  - marca_propria: vender direto com marca própria
  - exportacao_direta: cenário de exportação sem intermediário
- rastreabilidade: impacto na captura de valor (premium por rastreabilidade)
- oportunidades_tecnologia: onde tech pode reduzir custos na cadeia"""

        result = self.ask_json(prompt, system=SYSTEM_AGRO)
        print(f"\n🔗 Agro Supply Chain — {product}")
        dist = result.get("distribuicao_valor", {})
        for elo, pct in (dist.items() if isinstance(dist, dict) else []):
            print(f"  {elo:<25} {pct}%")
        self.save_result(result, prefix=f"agro_supply_chain_{product.lower()}")
        return result


def main():
    parser = argparse.ArgumentParser(description="Agro Agent — ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("farm-ops").add_argument("--farm", required=True)

    p_c = sub.add_parser("commodity-analysis")
    p_c.add_argument("--commodity", required=True)
    p_c.add_argument("--position", required=True)

    p_cp = sub.add_parser("crop-planning")
    p_cp.add_argument("--farm", required=True)
    p_cp.add_argument("--season", default="2026/27")

    sub.add_parser("esg-report").add_argument("--farm", required=True)

    p_sc = sub.add_parser("supply-chain")
    p_sc.add_argument("--product", required=True)
    p_sc.add_argument("--chain", required=True)

    args = parser.parse_args()
    agent = AgroAgent()
    def load(p): return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else {}

    if args.command == "farm-ops":
        agent.farm_operations(load(args.farm))
    elif args.command == "commodity-analysis":
        agent.commodity_analysis(args.commodity, load(args.position))
    elif args.command == "crop-planning":
        agent.crop_planning(load(args.farm), args.season)
    elif args.command == "esg-report":
        agent.esg_report(load(args.farm))
    elif args.command == "supply-chain":
        agent.supply_chain_agro(args.product, load(args.chain))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
