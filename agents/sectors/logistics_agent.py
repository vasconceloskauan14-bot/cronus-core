"""
Logistics Agent — ULTIMATE CRONUS
Automações para logística e supply chain: rotas, estoque, fornecedores e last-mile.

Uso:
    python logistics_agent.py route-optimization --orders data/pedidos.json --fleet data/frota.json
    python logistics_agent.py inventory --stock data/estoque.json --demand data/demanda.json
    python logistics_agent.py supplier-risk --suppliers data/fornecedores.json
    python logistics_agent.py last-mile --deliveries data/entregas.json
    python logistics_agent.py supply-chain-audit --company data/empresa.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_agent import BaseAgent

SYSTEM_LOGISTICS = """Você é especialista em Logística e Supply Chain do ULTIMATE CRONUS.
Você domina gestão de estoque, roteirização, last-mile, suppliers e cadeia de suprimentos.
Pense como um VP de Supply Chain com foco em custo, velocidade e resiliência.
Equilibre eficiência de custo com nível de serviço ao cliente."""


class LogisticsAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="LOGISTICS", output_dir="agents/output")

    def route_optimization(self, orders: list, fleet: list) -> dict:
        """Otimiza rotas de entrega para reduzir custo e tempo."""
        self.logger.info(f"Route optimization: {len(orders)} pedidos, {len(fleet)} veículos")
        total_value = sum(o.get("valor", 0) for o in orders)
        prompt = f"""Otimize as rotas de entrega para minimizar custo e tempo:

PEDIDOS ({len(orders)} pedidos, R$ {total_value:,.2f}):
{json.dumps(orders[:20], indent=2, ensure_ascii=False)[:3000]}

FROTA ({len(fleet)} veículos):
{json.dumps(fleet, indent=2, ensure_ascii=False)[:2000]}

Retorne JSON com:
- rotas_otimizadas: lista de rotas com:
  - veiculo_id: qual veículo
  - sequencia_entregas: ordem de entrega
  - distancia_total_km: distância estimada
  - tempo_estimado_horas: tempo de rota
  - capacidade_utilizada_pct: % da capacidade do veículo
  - pedidos_incluidos: lista de IDs dos pedidos
- metricas_otimizacao:
  - km_total_frota: quilometragem total
  - entregas_por_veiculo_media: eficiência
  - custo_estimado_combustivel: R$
  - economia_vs_sem_otimizacao_pct: % de economia estimada
- pedidos_sem_rota: pedidos que não couberam (precisam de rota extra)
- janelas_criticas: entregas com urgência ou janela de tempo restrita
- sugestoes_operacionais: melhorias no processo de roteirização
- alertas: capacidade excedida, janelas impossíveis, etc"""

        result = self.ask_json(prompt, system=SYSTEM_LOGISTICS)
        rotas = result.get("rotas_otimizadas", [])
        m = result.get("metricas_otimizacao", {})
        print(f"\n🚚 Route Optimization — {len(rotas)} rotas | {m.get('km_total_frota', '?')} km total")
        print(f"  Economia estimada: {m.get('economia_vs_sem_otimizacao_pct', '?')}%")
        self.save_result(result, prefix="route_optimization")
        return result

    def inventory_management(self, stock: dict, demand: dict) -> dict:
        """Gestão inteligente de estoque com previsão de demanda."""
        self.logger.info("Inventory management")
        prompt = f"""Analise o estoque e crie plano de reabastecimento:

ESTOQUE ATUAL:
{json.dumps(stock, indent=2, ensure_ascii=False)[:4000]}

DADOS DE DEMANDA:
{json.dumps(demand, indent=2, ensure_ascii=False)[:3000]}

Retorne JSON com:
- score_estoque: 0-100 (saúde do inventário)
- produtos_criticos:
  - ruptura_iminente: produtos que vão faltar em menos de 7 dias
  - excesso_estoque: produtos com mais de 90 dias de cobertura
  - giro_lento: produtos com baixa rotatividade
- analise_por_produto: para os top 20 SKUs:
  - sku: código
  - nome: nome do produto
  - estoque_atual: unidades
  - dias_cobertura: quantos dias o estoque cobre
  - ponto_de_pedido: quando pedir (em dias de cobertura)
  - quantidade_pedir: quanto pedir no próximo pedido
  - prioridade: "urgente"|"normal"|"monitorar"
- metricas_estoque:
  - giro_medio: vezes por ano
  - cobertura_media_dias: cobertura média
  - valor_estoque_total: R$
  - valor_estoque_excesso: R$ parado desnecessariamente
- plano_reabastecimento: pedidos a fazer esta semana
- otimizacoes: como reduzir capital imobilizado em estoque
- previsao_demanda_30_dias: demanda esperada nos próximos 30 dias"""

        result = self.ask_json(prompt, system=SYSTEM_LOGISTICS)
        score = result.get("score_estoque", 0)
        criticos = result.get("produtos_criticos", {})
        ruptura = criticos.get("ruptura_iminente", [])
        print(f"\n📦 Inventory — Score: {score}/100 | Rupturas iminentes: {len(ruptura) if isinstance(ruptura, list) else '?'}")
        self.save_result(result, prefix="inventory_management")
        return result

    def supplier_risk(self, suppliers: list) -> dict:
        """Avalia e monitora risco de fornecedores."""
        self.logger.info(f"Supplier risk: {len(suppliers)} fornecedores")
        prompt = f"""Avalie o risco dos fornecedores e crie estratégia de mitigação:

FORNECEDORES ({len(suppliers)}):
{json.dumps(suppliers, indent=2, ensure_ascii=False)[:5000]}

Retorne JSON com:
- portfolio_fornecedores:
  - score_geral: 0-100 (saúde do portfolio)
  - fornecedores_criticos: únicos ou estratégicos sem backup
  - concentracao_risco: % do gasto nos top 3 fornecedores
- avaliacao_por_fornecedor: para cada fornecedor:
  - nome: nome do fornecedor
  - score_risco: 0-100 (100 = máximo risco)
  - categoria_risco: "baixo"|"médio"|"alto"|"crítico"
  - dimensoes:
    - financeiro: risco de falência ou instabilidade financeira
    - qualidade: histórico de qualidade
    - entrega: confiabilidade de prazo
    - geopolitico: exposição a riscos geopolíticos
    - dependencia: % do nosso suprimento que depende deste fornecedor
  - acoes_recomendadas: o que fazer para mitigar o risco
- diversificacao_recomendada: onde buscar fornecedores alternativos
- plano_contingencia: o que fazer se fornecedor crítico falhar
- economias_negociacao: oportunidades de reduzir custos com fornecedores
- kpis_monitoramento: métricas para monitorar fornecedores continuamente"""

        result = self.ask_json(prompt, system=SYSTEM_LOGISTICS)
        score = result.get("portfolio_fornecedores", {}).get("score_geral", 0)
        criticos = result.get("portfolio_fornecedores", {}).get("fornecedores_criticos", [])
        print(f"\n⚠️  Supplier Risk — Score: {score}/100 | Críticos: {len(criticos) if isinstance(criticos, list) else '?'}")
        self.save_result(result, prefix="supplier_risk")
        return result

    def last_mile_analysis(self, deliveries: dict) -> dict:
        """Analisa e otimiza operação de last-mile delivery."""
        self.logger.info("Last-mile analysis")
        prompt = f"""Analise e otimize a operação de last-mile delivery:

DADOS DE ENTREGAS:
{json.dumps(deliveries, indent=2, ensure_ascii=False)[:5000]}

Retorne JSON com:
- score_last_mile: 0-100
- metricas_atuais:
  - taxa_entrega_primeira_tentativa_pct: % entregue na primeira vez
  - tempo_medio_entrega_horas: do despacho à entrega
  - custo_por_entrega: R$
  - taxa_avaria_pct: % de entregas com problema
  - nps_entrega: satisfação do recebedor
- analise_falhas: por que entregas não são feitas na primeira tentativa
- zonas_problematicas: regiões com pior performance
- modelos_entrega_recomendados:
  - modelo: ex: "pontos de coleta", "janela agendada", "locker"
  - quando_usar: para quais pedidos/regiões
  - impacto_estimado: como melhora as métricas
- tecnologia_rastreamento: como melhorar a experiência de rastreamento
- comunicacao_cliente: sequência de notificações do pedido até a entrega
- reducao_custo_estimada_pct: % de economia com otimizações
- quick_wins: o que implementar esta semana para melhorar last-mile"""

        result = self.ask_json(prompt, system=SYSTEM_LOGISTICS)
        score = result.get("score_last_mile", 0)
        m = result.get("metricas_atuais", {})
        print(f"\n🏠 Last-Mile — Score: {score}/100")
        print(f"  1a tentativa: {m.get('taxa_entrega_primeira_tentativa_pct', '?')}% | Custo: R$ {m.get('custo_por_entrega', '?')}")
        self.save_result(result, prefix="last_mile_analysis")
        return result

    def supply_chain_audit(self, company: dict) -> dict:
        """Auditoria completa da cadeia de suprimentos."""
        self.logger.info(f"Supply chain audit: {company.get('nome', '?')}")
        prompt = f"""Realize uma auditoria completa da cadeia de suprimentos:

EMPRESA:
{json.dumps(company, indent=2, ensure_ascii=False)[:4000]}

Retorne JSON com:
- score_supply_chain: 0-100
- maturidade: "basico"|"em_desenvolvimento"|"avancado"|"classe_mundial"
- dimensoes_auditoria:
  - planejamento_demanda: score 0-10
  - gestao_estoque: score 0-10
  - gestao_fornecedores: score 0-10
  - logistica_interna: score 0-10
  - distribuicao: score 0-10
  - tecnologia_e_dados: score 0-10
  - sustentabilidade: score 0-10
- principais_gargalos: onde a supply chain perde mais eficiência
- custos_ocultos: custos que podem não estar sendo contabilizados
- riscos_sistemicos: vulnerabilidades que podem travar a operação
- benchmarks_setor: como se compara com melhores práticas
- roadmap_melhoria:
  - curto_prazo_3m: iniciativas de alto impacto rápido
  - medio_prazo_6_12m: transformações mais profundas
  - longo_prazo_1_3a: excelência operacional
- roi_estimado: retorno esperado das melhorias
- tecnologias_recomendadas: WMS, TMS, ERP, IoT, IA para supply chain"""

        result = self.ask_json(prompt, system=SYSTEM_LOGISTICS)
        score = result.get("score_supply_chain", 0)
        maturidade = result.get("maturidade", "?")
        print(f"\n🔗 Supply Chain Audit — {company.get('nome', '?')}: {score}/100 ({maturidade})")
        dims = result.get("dimensoes_auditoria", {})
        for d, info in dims.items():
            v = info if isinstance(info, int) else info.get("score", 0) if isinstance(info, dict) else 0
            print(f"  {d:<30} {'█' * v}{'░' * (10-v)} {v}/10")
        self.save_result(result, prefix="supply_chain_audit")
        return result


def main():
    parser = argparse.ArgumentParser(description="Logistics Agent — ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")

    p_r = sub.add_parser("route-optimization")
    p_r.add_argument("--orders", required=True)
    p_r.add_argument("--fleet", required=True)

    p_i = sub.add_parser("inventory")
    p_i.add_argument("--stock", required=True)
    p_i.add_argument("--demand", required=True)

    sub.add_parser("supplier-risk").add_argument("--suppliers", required=True)
    sub.add_parser("last-mile").add_argument("--deliveries", required=True)
    sub.add_parser("supply-chain-audit").add_argument("--company", required=True)

    args = parser.parse_args()
    agent = LogisticsAgent()
    def load(p): return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else {}

    if args.command == "route-optimization":
        orders = load(args.orders)
        fleet = load(args.fleet)
        agent.route_optimization(
            orders if isinstance(orders, list) else orders.get("orders", []),
            fleet if isinstance(fleet, list) else fleet.get("vehicles", [])
        )
    elif args.command == "inventory":
        agent.inventory_management(load(args.stock), load(args.demand))
    elif args.command == "supplier-risk":
        data = load(args.suppliers)
        agent.supplier_risk(data if isinstance(data, list) else data.get("suppliers", []))
    elif args.command == "last-mile":
        agent.last_mile_analysis(load(args.deliveries))
    elif args.command == "supply-chain-audit":
        agent.supply_chain_audit(load(args.company))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
