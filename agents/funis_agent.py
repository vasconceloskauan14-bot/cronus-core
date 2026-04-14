"""
FUNIS Agent — ULTIMATE CRONUS
Conversão Automatizada: construção, análise e otimização de funis.

Uso:
    python funis_agent.py build --product "SaaS de RH" --audience "PMEs" --goal "trial"
    python funis_agent.py analyze --data data/funil.json
    python funis_agent.py optimize --funnel data/funil_atual.json
    python funis_agent.py ab-test --variants data/variantes.json --results data/resultados.json
    python funis_agent.py upsell --customer data/cliente.json --catalog data/produtos.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from base_agent import BaseAgent

SYSTEM_FUNIS = """Você é o FUNIS, agente especialista em Conversão Automatizada do ULTIMATE CRONUS.
Você constrói, analisa e otimiza funis de conversão com precisão cirúrgica.
Seu objetivo é maximizar conversão em cada etapa do funil.
Use frameworks como AIDA, StoryBrand, Product-Led Growth e Jobs-to-be-Done."""


class FunisAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="FUNIS", output_dir="agents/output")

    def build_funnel(self, product: str, audience: str, goal: str) -> dict:
        """Constrói funil completo do zero."""
        self.logger.info(f"Construindo funil: {product} → {goal}")
        prompt = f"""Construa um funil de conversão completo e otimizado:

PRODUTO/SERVIÇO: {product}
PÚBLICO-ALVO: {audience}
OBJETIVO DO FUNIL: {goal}

Retorne JSON com:
- nome_funil: nome descritivo
- tipo: "B2B"|"B2C"|"PLG"|"Sales-Led"|"Marketing-Led"
- etapas: lista de objetos com:
  - numero: 1, 2, 3...
  - nome: nome da etapa (ex: "Consciência")
  - objetivo: o que o usuário deve fazer
  - canal: onde acontece (landing page, email, app, etc)
  - copy_principal: mensagem-chave desta etapa
  - cta: call-to-action específico
  - fricoes_comuns: o que impede a conversão
  - taxa_conversao_esperada_pct: benchmark realista
  - automacao_recomendada: como automatizar esta etapa
- metricas_chave: KPIs do funil (CAC, taxa global, etc)
- pontos_criticos: onde mais pessoas desistem
- quick_wins: melhorias rápidas de alto impacto
- ferramentas_recomendadas: stack de ferramentas"""

        result = self.ask_json(prompt, system=SYSTEM_FUNIS)
        etapas = result.get("etapas", [])
        print(f"\n🌊 FUNIS Build — {len(etapas)} etapas")
        for e in etapas:
            conv = e.get("taxa_conversao_esperada_pct", "?")
            print(f"  {e.get('numero','?')}. {e.get('nome','?'):<20} → {conv}% conversão")
        self.save_result(result, prefix="funil_build")

        md = f"# 🌊 Funil: {result.get('nome_funil','')}\n\n"
        for e in etapas:
            md += f"## Etapa {e.get('numero')}: {e.get('nome','')}\n"
            md += f"**Objetivo:** {e.get('objetivo','')}\n"
            md += f"**CTA:** {e.get('cta','')}\n"
            md += f"**Conversão esperada:** {e.get('taxa_conversao_esperada_pct','?')}%\n\n"
        self.save_markdown(md, prefix="funil_build")
        return result

    def analyze_funnel(self, data: dict) -> dict:
        """Analisa performance atual do funil e identifica gargalos."""
        self.logger.info("Analisando funil existente")
        prompt = f"""Analise este funil de conversão e identifique gargalos e oportunidades:

DADOS DO FUNIL:
{json.dumps(data, indent=2, ensure_ascii=False)[:5000]}

Retorne JSON com:
- taxa_conversao_global_pct: % geral do funil
- gargalos: lista de etapas com maior perda, ordenadas por impacto
- etapa_critica: a etapa mais problemática
- potencial_melhoria_pct: quanto a taxa global pode melhorar
- analise_por_etapa: lista com análise de cada etapa:
  - nome: nome da etapa
  - taxa_atual_pct: taxa de conversão atual
  - benchmark_mercado_pct: o que o mercado normalmente tem
  - status: "excelente"|"ok"|"abaixo"|"crítico"
  - causa_provavel_perda: por que as pessoas saem aqui
  - solucao_recomendada: como corrigir
- receita_perdida_mensal: estimativa de receita perdida pelos gargalos
- quick_wins: as 3 mudanças mais rápidas de implementar
- experimentos_ab: testes A/B sugeridos"""

        result = self.ask_json(prompt, system=SYSTEM_FUNIS)
        print(f"\n📊 FUNIS Analysis — Taxa global: {result.get('taxa_conversao_global_pct','?')}%")
        print(f"  Etapa crítica: {result.get('etapa_critica','?')}")
        print(f"  Potencial melhoria: +{result.get('potencial_melhoria_pct','?')}%")
        self.save_result(result, prefix="funil_analysis")
        return result

    def optimize_funnel(self, funnel: dict) -> dict:
        """Gera plano de otimização detalhado para o funil."""
        self.logger.info("Otimizando funil")
        prompt = f"""Crie um plano de otimização completo para este funil:

FUNIL ATUAL:
{json.dumps(funnel, indent=2, ensure_ascii=False)[:5000]}

Retorne JSON com:
- prioridade_alta: lista de otimizações críticas (impacto alto, esforço baixo)
- prioridade_media: lista de otimizações importantes
- prioridade_baixa: nice-to-haves
- Para cada otimização:
  - titulo: nome da otimização
  - etapa_afetada: qual etapa do funil
  - tipo: "copy"|"design"|"ux"|"email"|"preço"|"oferta"|"timing"
  - impacto_esperado_pct: aumento de conversão esperado
  - esforco: "horas"|"dias"|"semanas"
  - como_implementar: passos concretos
  - como_medir: métrica para validar sucesso
- resultado_esperado_90_dias: impacto total das otimizações em 90 dias
- cronograma: plano de implementação semana a semana (4 semanas)"""

        result = self.ask_json(prompt, system=SYSTEM_FUNIS)
        alta = result.get("prioridade_alta", [])
        print(f"\n⚡ FUNIS Optimize — {len(alta)} otimizações de alta prioridade")
        for o in alta[:5]:
            print(f"  +{o.get('impacto_esperado_pct','?')}% | {o.get('titulo','?')}")
        self.save_result(result, prefix="funil_optimization")
        return result

    def ab_test_analysis(self, variants: list, results: dict) -> dict:
        """Analisa resultados de teste A/B e determina vencedor."""
        self.logger.info("Analisando teste A/B")
        prompt = f"""Analise os resultados deste teste A/B e determine o vencedor:

VARIANTES:
{json.dumps(variants, indent=2, ensure_ascii=False)[:3000]}

RESULTADOS:
{json.dumps(results, indent=2, ensure_ascii=False)[:3000]}

Retorne JSON com:
- vencedor: qual variante ganhou
- confianca_estatistica_pct: nível de confiança
- diferenca_relativa_pct: quanto melhor o vencedor
- significancia_estatistica: true|false
- tamanho_amostral_suficiente: true|false
- analise_por_variante: resultados detalhados de cada variante
- insight_principal: o que aprendemos com este teste
- proximo_teste_recomendado: o que testar em seguida
- impacto_anualizado: impacto financeiro anualizado do vencedor
- implementar_agora: true|false (e por quê)"""

        result = self.ask_json(prompt, system=SYSTEM_FUNIS)
        print(f"\n🧪 A/B Test — Vencedor: {result.get('vencedor','?')} ({result.get('confianca_estatistica_pct','?')}% confiança)")
        print(f"  Melhoria: +{result.get('diferenca_relativa_pct','?')}%")
        self.save_result(result, prefix="funil_abtest")
        return result

    def generate_upsell(self, customer: dict, catalog: list) -> dict:
        """Gera estratégia de upsell/cross-sell personalizada para um cliente."""
        self.logger.info("Gerando upsell personalizado")
        prompt = f"""Crie uma estratégia de upsell/cross-sell personalizada:

CLIENTE:
{json.dumps(customer, indent=2, ensure_ascii=False)[:2000]}

CATÁLOGO DE PRODUTOS/PLANOS:
{json.dumps(catalog, indent=2, ensure_ascii=False)[:2000]}

Retorne JSON com:
- produto_recomendado: qual produto/upgrade recomendar
- justificativa: por que este produto faz sentido para este cliente
- momento_ideal: quando fazer a oferta
- abordagem: como apresentar (email, in-app, call, etc)
- mensagem_personalizada: mensagem específica para este cliente
- oferta_especial: desconto ou benefício para incentivar
- objecoes_previstas: o que ele pode objetar
- respostas_objecoes: como responder
- probabilidade_conversao_pct: estimativa de conversão
- valor_potencial: aumento de receita se converter"""

        result = self.ask_json(prompt, system=SYSTEM_FUNIS)
        print(f"\n💎 Upsell — {result.get('produto_recomendado','?')} (prob: {result.get('probabilidade_conversao_pct','?')}%)")
        print(f"  {result.get('justificativa','')[:100]}")
        self.save_result(result, prefix="funil_upsell")
        return result


def main():
    parser = argparse.ArgumentParser(description="FUNIS — Conversão ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")

    p_b = sub.add_parser("build"); p_b.add_argument("--product", required=True); p_b.add_argument("--audience", required=True); p_b.add_argument("--goal", default="conversão")
    sub.add_parser("analyze").add_argument("--data", required=True)
    sub.add_parser("optimize").add_argument("--funnel", required=True)
    p_ab = sub.add_parser("ab-test"); p_ab.add_argument("--variants", required=True); p_ab.add_argument("--results", required=True)
    p_up = sub.add_parser("upsell"); p_up.add_argument("--customer", required=True); p_up.add_argument("--catalog", required=True)

    args = parser.parse_args()
    agent = FunisAgent()
    def load(p): return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else json.loads(p)

    if args.command == "build": agent.build_funnel(args.product, args.audience, args.goal)
    elif args.command == "analyze": agent.analyze_funnel(load(args.data))
    elif args.command == "optimize": agent.optimize_funnel(load(args.funnel))
    elif args.command == "ab-test": agent.ab_test_analysis(load(args.variants), load(args.results))
    elif args.command == "upsell":
        cat = load(args.catalog); agent.generate_upsell(load(args.customer), cat if isinstance(cat, list) else cat.get("products",[]))
    else: parser.print_help()


if __name__ == "__main__":
    main()
