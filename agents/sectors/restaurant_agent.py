"""
Restaurant Agent — ULTIMATE CRONUS
Automações para restaurantes, bares, dark kitchens e food service.

Uso:
    python restaurant_agent.py ops --data data/restaurante.json
    python restaurant_agent.py menu-engineering --menu data/cardapio.json --sales data/vendas.json
    python restaurant_agent.py delivery-strategy --data data/delivery.json
    python restaurant_agent.py review-response --reviews data/avaliacoes.json
    python restaurant_agent.py food-cost --recipes data/receitas.json --costs data/custos.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_agent import BaseAgent

SYSTEM_RESTAURANT = """Você é especialista em gestão de restaurantes e food service do ULTIMATE CRONUS.
Você domina operações de cozinha, engenharia de cardápio, delivery e gestão de food cost.
Pense como um consultor de restaurantes experiente + data analyst do setor.
Food cost ideal: 25-35%. CMV (Custo da Mercadoria Vendida) é a métrica mais crítica."""


class RestaurantAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="RESTAURANT", output_dir="agents/output")

    def operations_analysis(self, data: dict) -> dict:
        """Analisa e otimiza operações do restaurante."""
        self.logger.info(f"Restaurant ops: {data.get('nome', '?')}")
        prompt = f"""Analise as operações deste restaurante/food service:

DADOS:
{json.dumps(data, indent=2, ensure_ascii=False)[:4000]}

Retorne JSON com:
- score_operacional: 0-100
- metricas_calculadas:
  - ticket_medio: R$
  - giro_de_mesa: rotações por dia
  - taxa_ocupacao_pct: % das mesas ocupadas
  - cmv_pct: custo da mercadoria vendida como % da receita
  - lucro_operacional_pct: margem operacional
  - faturamento_por_m2: R$/m²
- diagnostico: pontos fortes e fracos da operação
- gargalos_criticos: o que está travando a eficiência
- oportunidades_receita: como aumentar ticket e volume sem aumentar custos
- reducao_desperdicio: como reduzir desperdício de alimentos (objetivo: <5%)
- gestao_equipe: insights sobre produtividade da equipe
- experiencia_cliente: melhorias de experiência que impactam recompra
- kpis_semana: top 5 métricas para monitorar toda semana
- plano_acao_30_dias: ações com responsável e prazo"""

        result = self.ask_json(prompt, system=SYSTEM_RESTAURANT)
        score = result.get("score_operacional", 0)
        m = result.get("metricas_calculadas", {})
        print(f"\n🍽️  Restaurant Ops — {data.get('nome','?')}: {score}/100")
        print(f"  Ticket médio: R$ {m.get('ticket_medio','?')} | CMV: {m.get('cmv_pct','?')}% | Ocupação: {m.get('taxa_ocupacao_pct','?')}%")
        self.save_result(result, prefix="restaurant_ops")
        return result

    def menu_engineering(self, menu: list, sales: dict) -> dict:
        """Analisa cardápio por rentabilidade e popularidade (matriz BCG do cardápio)."""
        self.logger.info(f"Menu engineering: {len(menu)} itens")
        prompt = f"""Faça a engenharia de cardápio (matrix Stars/Plowhorses/Puzzles/Dogs):

CARDÁPIO ({len(menu)} itens):
{json.dumps(menu[:30], indent=2, ensure_ascii=False)[:4000]}

DADOS DE VENDAS:
{json.dumps(sales, indent=2, ensure_ascii=False)[:2000]}

Retorne JSON com:
- classificacao_itens: para cada item:
  - nome: nome do prato
  - categoria: "star"|"plowhorse"|"puzzle"|"dog"
  - popularidade: alta|baixa (vs média)
  - rentabilidade: alta|baixa (contribuição)
  - acao_recomendada: manter|promover|reposicionar|substituir|remover
  - preco_sugerido: R$ (se deve ajustar)
- resumo_matrix:
  - stars: itens populares e rentáveis (promover)
  - plowhorses: populares mas pouco rentáveis (ajustar custo ou preço)
  - puzzles: rentáveis mas pouco vendidos (melhorar posicionamento)
  - dogs: impopulares e não rentáveis (remover ou substituir)
- itens_remover: candidatos a sair do cardápio
- itens_criar: gaps no cardápio que poderiam ser explorados
- otimizacao_menu: como reorganizar o cardápio visualmente para vender mais stars
- pricing_oportunidades: onde pode aumentar preço sem perder volume
- cmv_por_categoria: custo por categoria (bebidas, entradas, pratos, sobremesas)"""

        result = self.ask_json(prompt, system=SYSTEM_RESTAURANT)
        stars = result.get("resumo_matrix", {}).get("stars", [])
        dogs = result.get("resumo_matrix", {}).get("dogs", [])
        print(f"\n⭐ Menu Engineering — {len(menu)} itens")
        print(f"  Stars: {len(stars) if isinstance(stars, list) else '?'} | Dogs (remover): {len(dogs) if isinstance(dogs, list) else '?'}")
        self.save_result(result, prefix="menu_engineering")
        return result

    def delivery_strategy(self, data: dict) -> dict:
        """Cria e otimiza estratégia de delivery."""
        self.logger.info("Delivery strategy")
        prompt = f"""Analise e otimize a estratégia de delivery:

DADOS:
{json.dumps(data, indent=2, ensure_ascii=False)[:4000]}

Retorne JSON com:
- score_delivery: 0-100
- metricas_atuais:
  - percentual_delivery_receita_pct: % da receita vindo de delivery
  - ticket_medio_delivery: R$
  - tempo_preparo_medio_min: minutos do pedido ao pronto
  - tempo_entrega_medio_min: minutos do pronto à entrega
  - avaliacao_media: nota nas plataformas
  - taxa_cancelamento_pct: % de pedidos cancelados
- analise_plataformas: iFood, Rappi, 99Food — performance e custo de comissão
- cardapio_delivery_otimizado: o que deve (e não deve) estar no delivery
- dark_kitchen_oportunidade: faz sentido abrir uma dark kitchen? análise
- marca_propria_delivery: quando e como construir canal próprio (WhatsApp, site)
- embalagens: otimização de embalagens (custo e experiência)
- estrategia_alcance: como aumentar raio de entrega com qualidade
- campanhas_delivery: promoções específicas para aumentar pedidos
- plano_crescimento_delivery: como crescer 30% em 60 dias"""

        result = self.ask_json(prompt, system=SYSTEM_RESTAURANT)
        score = result.get("score_delivery", 0)
        m = result.get("metricas_atuais", {})
        print(f"\n🛵 Delivery Strategy — Score: {score}/100")
        print(f"  % Receita delivery: {m.get('percentual_delivery_receita_pct','?')}% | Nota média: {m.get('avaliacao_media','?')}")
        self.save_result(result, prefix="delivery_strategy")
        return result

    def respond_reviews(self, reviews: list) -> dict:
        """Gera respostas personalizadas para avaliações online."""
        self.logger.info(f"Responding to {len(reviews)} reviews")
        prompt = f"""Crie respostas profissionais para estas avaliações de restaurante:

AVALIAÇÕES ({len(reviews)}):
{json.dumps(reviews[:20], indent=2, ensure_ascii=False)[:5000]}

Retorne JSON com:
- respostas: para cada avaliação:
  - id: identificador
  - nota: 1-5
  - tipo: "positiva"|"negativa"|"neutra"
  - resposta: texto completo da resposta (máx 200 palavras)
  - tom: como foi o tom usado
- analise_sentimento:
  - nps_estimado: Net Promoter Score calculado
  - temas_positivos: o que mais elogiam
  - temas_negativos: o que mais criticam
  - urgencias: reclamações que precisam de ação imediata
- plano_melhoria: ações para resolver as reclamações recorrentes
- template_resposta_negativa: template para respostas a críticas
- template_resposta_positiva: template para respostas a elogios"""

        result = self.ask_json(prompt, system=SYSTEM_RESTAURANT)
        respostas = result.get("respostas", [])
        nps = result.get("analise_sentimento", {}).get("nps_estimado", "?")
        print(f"\n⭐ Review Responses — {len(respostas)} respostas | NPS estimado: {nps}")
        self.save_result(result, prefix="review_responses")
        return result

    def food_cost_analysis(self, recipes: list, costs: dict) -> dict:
        """Analisa food cost e otimiza rentabilidade das receitas."""
        self.logger.info(f"Food cost: {len(recipes)} receitas")
        prompt = f"""Analise o food cost das receitas e otimize a rentabilidade:

RECEITAS ({len(recipes)}):
{json.dumps(recipes[:20], indent=2, ensure_ascii=False)[:4000]}

CUSTOS DE INSUMOS:
{json.dumps(costs, indent=2, ensure_ascii=False)[:2000]}

Retorne JSON com:
- analise_por_receita: para cada receita:
  - nome: nome do prato
  - custo_total: R$ (soma de todos insumos)
  - preco_venda: R$
  - food_cost_pct: custo/preço em %
  - margem_contribuicao: R$
  - classificacao: "ótimo (<25%)"|"bom (25-30%)"|"aceitável (30-35%)"|"ruim (>35%)"
  - ingrediente_mais_caro: qual pesa mais
  - sugestao_reducao: como reduzir food cost sem impactar qualidade
- resumo_geral:
  - food_cost_medio_pct: % médio do portfólio
  - receita_mais_rentavel: qual tem melhor margem
  - receita_menos_rentavel: qual tem pior margem
  - economia_potencial_mensal: R$ economizáveis com otimizações
- estrategias_reducao_custo:
  - substituicao_ingredientes: alternativas de menor custo
  - sazonalidade: aproveitar ingredientes da época
  - desperdicio_zero: como usar sobras em outros pratos
  - negociacao_fornecedores: como negociar melhores preços
- metas_food_cost: onde cada categoria deve chegar"""

        result = self.ask_json(prompt, system=SYSTEM_RESTAURANT)
        resumo = result.get("resumo_geral", {})
        print(f"\n💰 Food Cost Analysis — {len(recipes)} receitas")
        print(f"  Food cost médio: {resumo.get('food_cost_medio_pct','?')}%")
        print(f"  Economia potencial: R$ {resumo.get('economia_potencial_mensal','?')}/mês")
        self.save_result(result, prefix="food_cost_analysis")
        return result


def main():
    parser = argparse.ArgumentParser(description="Restaurant Agent — ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("ops").add_argument("--data", required=True)

    p_me = sub.add_parser("menu-engineering")
    p_me.add_argument("--menu", required=True)
    p_me.add_argument("--sales", required=True)

    sub.add_parser("delivery-strategy").add_argument("--data", required=True)
    sub.add_parser("review-response").add_argument("--reviews", required=True)

    p_fc = sub.add_parser("food-cost")
    p_fc.add_argument("--recipes", required=True)
    p_fc.add_argument("--costs", required=True)

    args = parser.parse_args()
    agent = RestaurantAgent()
    def load(p): return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else {}

    if args.command == "ops":
        agent.operations_analysis(load(args.data))
    elif args.command == "menu-engineering":
        menu = load(args.menu)
        agent.menu_engineering(menu if isinstance(menu, list) else menu.get("items",[]), load(args.sales))
    elif args.command == "delivery-strategy":
        agent.delivery_strategy(load(args.data))
    elif args.command == "review-response":
        data = load(args.reviews)
        agent.respond_reviews(data if isinstance(data, list) else data.get("reviews",[]))
    elif args.command == "food-cost":
        recipes = load(args.recipes)
        agent.food_cost_analysis(recipes if isinstance(recipes, list) else recipes.get("recipes",[]), load(args.costs))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
