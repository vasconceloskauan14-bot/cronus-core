"""
Competitor Intelligence — ULTIMATE CRONUS
Inteligência competitiva contínua: análise profunda, monitoramento e counter-strategies.

Uso:
    python competitor_intelligence.py deep-dive --competitor data/concorrente.json
    python competitor_intelligence.py compare --us data/nos.json --them data/concorrente.json
    python competitor_intelligence.py pricing-spy --competitors data/concorrentes.json
    python competitor_intelligence.py counter-strategy --threat data/ameaca.json --us data/nos.json
    python competitor_intelligence.py win-loss --deals data/deals.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))
from base_agent import BaseAgent

SYSTEM_CI = """Você é o especialista em Inteligência Competitiva do ULTIMATE CRONUS.
Você analisa concorrentes com profundidade cirúrgica: estratégia, produto, precificação e posicionamento.
Pense como um ex-consultor de estratégia + analista de inteligência competitiva.
Informação é vantagem. Cada insight deve ser acionável."""


class CompetitorIntelligence(BaseAgent):
    def __init__(self):
        super().__init__(name="COMPETITOR_INTEL", output_dir="automation/reports")

    def deep_dive(self, competitor: dict) -> dict:
        """Análise profunda de um concorrente específico."""
        self.logger.info(f"Deep dive: {competitor.get('nome', '?')}")
        prompt = f"""Faça uma análise profunda deste concorrente:

CONCORRENTE:
{json.dumps(competitor, indent=2, ensure_ascii=False)[:4000]}

Retorne JSON com:
- perfil_estrategico:
  - posicionamento: como se posiciona no mercado
  - segmento_alvo: quem é o cliente ideal deles
  - proposta_valor: o que prometem entregar
  - modelo_de_negocio: como ganham dinheiro
- produto_e_tecnologia:
  - features_unicas: o que só eles têm
  - gaps_produto: o que está faltando no produto deles
  - tech_stack: tecnologia que provavelmente usam
  - roadmap_provavel: onde provavelmente estão indo
- go_to_market:
  - canais_aquisicao: como adquirem clientes
  - estrategia_vendas: modelo de vendas (PLG, sales-led, etc)
  - estrategia_conteudo: que conteúdo produzem
  - parceiros: ecossistema de parceiros
- financeiro_estimado:
  - receita_estimada: faixa de receita
  - valuation_estimado: se relevante
  - funding_historico: rodadas de investimento
  - burn_estimado: se startup
- time_e_cultura:
  - tamanho_time: estimativa
  - forcas_do_time: onde são fortes em pessoas
  - cultura_aparente: como se apresentam para o mercado
- vulnerabilidades: onde podem ser atacados
- ameacas_que_representam: em que nos prejudicam
- o_que_aprender: o que eles fazem bem que deveríamos copiar"""

        result = self.ask_json(prompt, system=SYSTEM_CI)
        nome = competitor.get("nome", "?")
        print(f"\n🕵️  Deep Dive — {nome}")
        vul = result.get("vulnerabilidades", [])
        print(f"  Vulnerabilidades: {len(vul) if isinstance(vul, list) else '?'}")
        self.save_result(result, prefix=f"competitor_dive_{nome.replace(' ', '_').lower()[:20]}")
        return result

    def competitive_comparison(self, us: dict, competitor: dict) -> dict:
        """Comparação lado a lado com concorrente."""
        self.logger.info(f"Compare: nós vs {competitor.get('nome', '?')}")
        prompt = f"""Compare nossa empresa com este concorrente:

NOSSA EMPRESA:
{json.dumps(us, indent=2, ensure_ascii=False)[:2000]}

CONCORRENTE:
{json.dumps(competitor, indent=2, ensure_ascii=False)[:2000]}

Retorne JSON com:
- vencedor_geral: quem está melhor posicionado e por quê
- comparacao_detalhada: tabela comparativa por dimensão:
  - dimensao: nome
  - nos: situação atual (texto)
  - eles: situação atual (texto)
  - vantagem: "nos"|"eles"|"empate"
  - importancia: 0-10 (quão importante é esta dimensão)
- nossa_vantagem_sustentavel: onde somos melhores e por quê
- nossa_desvantagem_critica: onde estamos perdendo e o que fazer
- batalhas_ganhar: em quais dimensões investir para vencer
- batalhas_evitar: onde não competir diretamente
- mensagem_de_vendas_vs_eles: como nos posicionar em deals contra eles
- objecoes_e_respostas: quando cliente mencionar concorrente, o que responder
- score_competitivo: 0-100 (nossa posição relativa a eles)"""

        result = self.ask_json(prompt, system=SYSTEM_CI)
        score = result.get("score_competitivo", 0)
        vencedor = result.get("vencedor_geral", "?")
        print(f"\n⚔️  Competitive Comparison vs {competitor.get('nome', '?')}")
        print(f"  Score: {score}/100 | Vencedor atual: {str(vencedor)[:80]}")
        self.save_result(result, prefix="competitive_comparison")
        return result

    def pricing_intelligence(self, competitors: list) -> dict:
        """Mapeia e analisa estratégias de precificação dos concorrentes."""
        self.logger.info(f"Pricing spy: {len(competitors)} concorrentes")
        prompt = f"""Analise as estratégias de precificação dos concorrentes:

CONCORRENTES ({len(competitors)}):
{json.dumps(competitors, indent=2, ensure_ascii=False)[:5000]}

Retorne JSON com:
- mapa_precos: para cada concorrente:
  - nome: nome do concorrente
  - modelo_precificacao: por usuário|por uso|flat|freemium|etc
  - planos: lista de planos com nome, preço e features
  - posicionamento_preco: "budget"|"mid-market"|"premium"|"enterprise"
  - estrategia_discount: como dão desconto
  - preco_mais_popular: qual plano mais vendem (se souber)
- benchmark_precos:
  - menor_preco_mercado: R$
  - maior_preco_mercado: R$
  - preco_medio_mercado: R$
  - tendencia: subindo|estavel|caindo
- analise_elasticidade: o mercado é sensível a preço neste segmento?
- oportunidades_pricing:
  - espaco_premium: tem espaço para posicionamento premium?
  - espaco_disruptivo: alguém pode entrar com preço muito menor?
  - bundling_oportunidade: oportunidade de bundle não explorada?
- recomendacao_nossa_precificacao: como devemos precificar dado este mercado"""

        result = self.ask_json(prompt, system=SYSTEM_CI)
        benchmark = result.get("benchmark_precos", {})
        print(f"\n💰 Pricing Intelligence — {len(competitors)} concorrentes")
        print(f"  Range: R$ {benchmark.get('menor_preco_mercado', '?')} – R$ {benchmark.get('maior_preco_mercado', '?')}")
        print(f"  Médio: R$ {benchmark.get('preco_medio_mercado', '?')}")
        self.save_result(result, prefix="pricing_intelligence")
        return result

    def counter_strategy(self, threat: dict, us: dict) -> dict:
        """Cria estratégia de contra-ataque para ameaça competitiva."""
        self.logger.info(f"Counter strategy vs {threat.get('nome', '?')}")
        prompt = f"""Crie uma estratégia de contra-ataque para esta ameaça competitiva:

AMEAÇA:
{json.dumps(threat, indent=2, ensure_ascii=False)[:2000]}

NOSSA EMPRESA:
{json.dumps(us, indent=2, ensure_ascii=False)[:2000]}

Retorne JSON com:
- nivel_ameaca: "baixo"|"moderado"|"alto"|"existencial"
- prazo_urgencia: quantos meses temos antes do impacto real
- opcoes_estrategicas:
  - opcao_a: estratégia agressiva (atacar as fraquezas deles)
  - opcao_b: estratégia defensiva (fortalecer nossas vantagens)
  - opcao_c: estratégia de nicho (focar em segmento que eles não servem bem)
  - opcao_d: estratégia de parceria (se não puder vencer, juntar)
- estrategia_recomendada: qual opção e por quê
- plano_90_dias: ações concretas dos próximos 3 meses
- recursos_necessarios: o que precisamos para executar
- metricas_sucesso: como saber se a estratégia está funcionando
- cenario_se_nao_agir: o que acontece em 12 meses sem resposta
- quick_wins: o que fazer esta semana para ganhar tempo
- mensagem_para_mercado: como comunicar nossa diferenciação"""

        result = self.ask_json(prompt, system=SYSTEM_CI)
        nivel = result.get("nivel_ameaca", "?")
        icons = {"existencial": "🚨", "alto": "🔴", "moderado": "🟡", "baixo": "🟢"}
        print(f"\n{icons.get(nivel, '●')} Counter Strategy vs {threat.get('nome', '?')} [{nivel.upper()}]")
        print(f"  Recomendação: {str(result.get('estrategia_recomendada', '?'))[:100]}")
        self.save_result(result, prefix="counter_strategy")
        return result

    def win_loss_analysis(self, deals: list) -> dict:
        """Analisa por que ganhamos e perdemos deals para clientes."""
        self.logger.info(f"Win/loss analysis: {len(deals)} deals")
        wins = [d for d in deals if d.get("resultado") == "ganho"]
        losses = [d for d in deals if d.get("resultado") == "perdido"]
        prompt = f"""Analise por que ganhamos e perdemos deals:

DEALS ANALISADOS: {len(deals)} total ({len(wins)} ganhos, {len(losses)} perdidos)
{json.dumps(deals[:25], indent=2, ensure_ascii=False)[:5000]}

Retorne JSON com:
- taxa_vitoria_geral_pct: % de deals ganhos
- analise_por_concorrente: para cada concorrente presente:
  - concorrente: nome
  - deals_contra: total de deals competindo contra eles
  - taxa_vitoria_vs_eles_pct: nossa taxa de vitória
  - por_que_ganhamos: padrões nos deals ganhos
  - por_que_perdemos: padrões nos deals perdidos
  - nossa_mensagem_diferenciadora: o que usar ao competir
- razoes_vitoria: top 5 razões por que ganhamos (em ordem de frequência)
- razoes_derrota: top 5 razões por que perdemos
- caracteristicas_deals_ganhos: perfil típico de deal que ganhamos
- caracteristicas_deals_perdidos: perfil típico de deal que perdemos
- score_icp: como melhorar o perfil de cliente ideal baseado nos dados
- acoes_comerciais: o que mudar no processo de vendas para ganhar mais
- acoes_produto: o que o produto precisa ter para ganhar mais deals"""

        result = self.ask_json(prompt, system=SYSTEM_CI)
        taxa = result.get("taxa_vitoria_geral_pct", 0)
        print(f"\n🏆 Win/Loss Analysis — {len(deals)} deals | Win rate: {taxa}%")
        razoes_derrota = result.get("razoes_derrota", [])
        if razoes_derrota:
            print(f"  Principal motivo de derrota: {str(razoes_derrota[0])[:80]}")
        self.save_result(result, prefix="win_loss_analysis")
        return result


def main():
    parser = argparse.ArgumentParser(description="Competitor Intelligence — ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("deep-dive").add_argument("--competitor", required=True)

    p_cmp = sub.add_parser("compare")
    p_cmp.add_argument("--us", required=True)
    p_cmp.add_argument("--them", required=True)

    sub.add_parser("pricing-spy").add_argument("--competitors", required=True)

    p_ct = sub.add_parser("counter-strategy")
    p_ct.add_argument("--threat", required=True)
    p_ct.add_argument("--us", required=True)

    sub.add_parser("win-loss").add_argument("--deals", required=True)

    args = parser.parse_args()
    agent = CompetitorIntelligence()
    def load(p): return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else {}

    if args.command == "deep-dive":
        agent.deep_dive(load(args.competitor))
    elif args.command == "compare":
        agent.competitive_comparison(load(args.us), load(args.them))
    elif args.command == "pricing-spy":
        data = load(args.competitors)
        agent.pricing_intelligence(data if isinstance(data, list) else data.get("competitors", []))
    elif args.command == "counter-strategy":
        agent.counter_strategy(load(args.threat), load(args.us))
    elif args.command == "win-loss":
        data = load(args.deals)
        agent.win_loss_analysis(data if isinstance(data, list) else data.get("deals", []))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
