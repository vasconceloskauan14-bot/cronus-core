"""
E-commerce Agent — ULTIMATE CRONUS
Automações para e-commerce: conversão, abandono, recompra, sazonalidade.

Uso:
    python ecommerce_agent.py health --data data/ecommerce.json
    python ecommerce_agent.py cart-recovery --abandoned data/carrinhos.json
    python ecommerce_agent.py reorder --customers data/clientes.json --catalog data/produtos.json
    python ecommerce_agent.py seasonal --calendar data/calendario.json --catalog data/produtos.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_agent import BaseAgent

SYSTEM_ECOMM = """Você é especialista em E-commerce do ULTIMATE CRONUS.
Você domina conversão, ticket médio, recompra, abandono de carrinho e sazonalidade.
Foque em receita por visita, LTV do cliente e eficiência de marketing."""


class EcommerceAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="ECOMMERCE", output_dir="agents/output")

    def health_dashboard(self, data: dict) -> dict:
        """Dashboard de saúde do e-commerce."""
        prompt = f"""Analise a saúde deste e-commerce:

DADOS:
{json.dumps(data, indent=2, ensure_ascii=False)[:5000]}

Retorne JSON com:
- score_saude: 0-100
- metricas_calculadas:
  - taxa_conversao_pct: visitas que compram
  - taxa_abandono_carrinho_pct
  - ticket_medio: R$
  - receita_por_visita: R$
  - taxa_recompra_pct
  - clv_medio: customer lifetime value
- gargalos_principais: onde a loja perde mais receita
- produtos_mais_rentaveis: top produtos por margem
- segmentos_clientes: RFM analysis (Recency, Frequency, Monetary)
- acoes_impacto_imediato: top 3 para aumentar faturamento hoje
- projecao_30_dias: estimativa de receita"""

        result = self.ask_json(prompt, system=SYSTEM_ECOMM)
        print(f"\n🛒 E-commerce Health: {result.get('score_saude',0)}/100")
        m = result.get("metricas_calculadas",{})
        print(f"  Conversão: {m.get('taxa_conversao_pct','?')}% | Ticket: R${m.get('ticket_medio','?')} | Abandono: {m.get('taxa_abandono_carrinho_pct','?')}%")
        self.save_result(result, prefix="ecomm_health")
        return result

    def cart_recovery(self, abandoned_carts: list) -> dict:
        """Cria campanha de recuperação de carrinhos abandonados."""
        total_value = sum(c.get("valor",0) for c in abandoned_carts)
        prompt = f"""Crie uma campanha de recuperação de carrinhos abandonados:

CARRINHOS ABANDONADOS ({len(abandoned_carts)} carrinhos, R$ {total_value:,.2f} em risco):
{json.dumps(abandoned_carts[:10], indent=2, ensure_ascii=False)[:3000]}

Retorne JSON com:
- segmentacao: como segmentar os carrinhos (por valor, produto, cliente)
- sequencia_emails: lista de emails com:
  - tempo_apos_abandono: "1h"|"24h"|"72h"|"7d"
  - assunto: linha de assunto
  - copy_principal: texto do email
  - cta: botão de ação
  - oferta: desconto ou incentivo (se aplicável)
- sms_recovery: mensagem SMS para high-value carts
- taxa_recuperacao_esperada_pct: % de carrinhos recuperados
- receita_recuperavel_estimada: R$
- segmento_prioritario: qual segmento focar primeiro"""

        result = self.ask_json(prompt, system=SYSTEM_ECOMM)
        print(f"\n🛒 Cart Recovery — {len(abandoned_carts)} carrinhos (R$ {total_value:,.2f})")
        print(f"  Recuperável: R$ {result.get('receita_recuperavel_estimada',0):,.2f} ({result.get('taxa_recuperacao_esperada_pct','?')}%)")
        self.save_result(result, prefix="cart_recovery")
        return result

    def reorder_campaign(self, customers: list, catalog: list) -> dict:
        """Cria campanha de recompra baseada em comportamento."""
        prompt = f"""Crie uma campanha de recompra personalizada:

CLIENTES:
{json.dumps(customers[:15], indent=2, ensure_ascii=False)[:3000]}

CATÁLOGO:
{json.dumps(catalog[:20], indent=2, ensure_ascii=False)[:2000]}

Retorne JSON com:
- segmentos: clientes segmentados por comportamento de compra
- recomendacoes_por_segmento: para cada segmento:
  - segmento: nome
  - produto_recomendado: o que recomendar
  - timing_ideal: quando enviar
  - canal: email|sms|push|whatsapp
  - mensagem: copy personalizado
  - oferta: se há desconto ou não
- receita_potencial_estimada: R$
- taxa_conversao_esperada_pct: %"""

        result = self.ask_json(prompt, system=SYSTEM_ECOMM)
        print(f"\n🔄 Reorder Campaign — {len(customers)} clientes")
        print(f"  Receita potencial: R$ {result.get('receita_potencial_estimada',0):,.2f}")
        self.save_result(result, prefix="reorder_campaign")
        return result

    def seasonal_strategy(self, calendar: dict, catalog: list) -> dict:
        """Cria estratégia sazonal para datas comemorativas."""
        prompt = f"""Crie uma estratégia de vendas sazonais:

CALENDÁRIO DE DATAS:
{json.dumps(calendar, indent=2, ensure_ascii=False)[:2000]}

CATÁLOGO:
{json.dumps(catalog[:20], indent=2, ensure_ascii=False)[:2000]}

Retorne JSON com:
- datas_prioritarias: top 5 datas por potencial de receita
- estrategia_por_data: para cada data:
  - data: nome e data
  - potencial_receita_extra_pct: % acima do normal
  - produtos_destaque: quais produtos promover
  - antecipacao_marketing: quando começar a comunicar
  - campanha_email: assunto e copy
  - oferta_especial: desconto ou bundle
  - pos_data: como ativar quem não comprou
- plano_anual: visão geral do calendário sazonal
- receita_adicional_estimada_anual: R$"""

        result = self.ask_json(prompt, system=SYSTEM_ECOMM)
        datas = result.get("datas_prioritarias",[])
        print(f"\n📅 Seasonal Strategy — {len(datas)} datas prioritárias")
        print(f"  Receita adicional estimada: R$ {result.get('receita_adicional_estimada_anual',0):,.2f}/ano")
        self.save_result(result, prefix="seasonal_strategy")
        return result


def main():
    parser = argparse.ArgumentParser(description="E-commerce Agent — ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("health").add_argument("--data", required=True)
    sub.add_parser("cart-recovery").add_argument("--abandoned", required=True)
    p_r = sub.add_parser("reorder"); p_r.add_argument("--customers", required=True); p_r.add_argument("--catalog", required=True)
    p_s = sub.add_parser("seasonal"); p_s.add_argument("--calendar", required=True); p_s.add_argument("--catalog", required=True)

    args = parser.parse_args()
    agent = EcommerceAgent()
    def load(p): return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else {}

    if args.command == "health": agent.health_dashboard(load(args.data))
    elif args.command == "cart-recovery":
        data = load(args.abandoned); agent.cart_recovery(data if isinstance(data, list) else data.get("carts",[]))
    elif args.command == "reorder":
        c = load(args.customers); cat = load(args.catalog)
        agent.reorder_campaign(c if isinstance(c, list) else [], cat if isinstance(cat, list) else [])
    elif args.command == "seasonal":
        cat = load(args.catalog); agent.seasonal_strategy(load(args.calendar), cat if isinstance(cat, list) else [])
    else: parser.print_help()


if __name__ == "__main__":
    main()
