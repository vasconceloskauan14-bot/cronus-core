"""
Product Analytics — ULTIMATE CRONUS
Análise de produto: activation, retention, NPS, feature flags e roadmap.

Uso:
    python product_analytics.py funnel --events data/eventos.json
    python product_analytics.py retention --cohorts data/cohorts.json
    python product_analytics.py feature-impact --feature "novo_dashboard" --data data/ab_test.json
    python product_analytics.py nps-analysis --responses data/nps.json
    python product_analytics.py roadmap --feedback data/feedback.json --metrics data/kpis.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))
from base_agent import BaseAgent

SYSTEM_PRODUCT = """Você é o Head of Product Analytics do ULTIMATE CRONUS.
Você transforma dados de produto em decisões de roadmap e melhorias de experiência.
Pense como um PM data-driven que só prioriza o que tem evidence.
North Star Metric é a bússola. Retention é o que importa mais que tudo."""


class ProductAnalytics(BaseAgent):
    def __init__(self):
        super().__init__(name="PRODUCT_ANALYTICS", output_dir="automation/reports")

    def activation_funnel(self, events: dict) -> dict:
        """Analisa funil de ativação e identifica onde usuários dropam."""
        self.logger.info("Activation funnel analysis")
        prompt = f"""Analise o funil de ativação do produto:

EVENTOS/DADOS:
{json.dumps(events, indent=2, ensure_ascii=False)[:5000]}

Retorne JSON com:
- funil_ativacao: cada etapa do funil com:
  - etapa: nome
  - usuarios_entraram: quantidade
  - usuarios_completaram: quantidade
  - taxa_conversao_pct: %
  - taxa_drop_pct: % que saíram nesta etapa
  - tempo_medio_etapa_min: tempo médio para completar
- maior_gargalo: etapa com maior drop e análise do porquê
- usuarios_ativados_pct: % que completa toda a jornada de ativação
- tempo_para_ativacao: mediana de tempo até ativação completa
- benchmark_saas: comparação com médias do mercado
- segmentos: variação por segmento (canal de aquisição, plano, etc)
- hipoteses_drop: por que os usuários abandonam em cada etapa
- experimentos_recomendados: A/B tests para melhorar ativação
- quick_wins: melhorias imediatas com maior impacto no funil
- projecao: se melhorar ativação em X%, impacto no MRR"""

        result = self.ask_json(prompt, system=SYSTEM_PRODUCT)
        ativados = result.get("usuarios_ativados_pct", 0)
        gargalo = result.get("maior_gargalo", "?")
        print(f"\n🚀 Activation Funnel — {ativados}% ativados")
        print(f"  Maior gargalo: {str(gargalo)[:100]}")
        self.save_result(result, prefix="activation_funnel")
        return result

    def retention_analysis(self, cohorts: dict) -> dict:
        """Analisa retenção por cohort e identifica padrões."""
        self.logger.info("Retention analysis")
        prompt = f"""Analise a retenção de usuários por cohort:

DADOS DE COHORT:
{json.dumps(cohorts, indent=2, ensure_ascii=False)[:5000]}

Retorne JSON com:
- curva_retencao: D1, D7, D14, D30, D60, D90, D180, D365 médias
- analise_por_cohort: variação de retenção entre cohorts (melhora/piora)
- retention_rate_atual:
  - d7: % retidos no dia 7
  - d30: % retidos no dia 30
  - d90: % retidos no dia 90
- benchmark_por_tipo: comparação com benchmarks (SaaS/consumer/etc)
- power_users: quem retém melhor e o que têm em comum
- usuarios_risco_churn: sinais de quem vai cancelar
- comportamentos_retencao: o que usuários que ficam fazem diferente
- magic_moment: se há um "aha moment" associado à retenção
- intervencoes_recomendadas: o que fazer no D1, D7, D30 para melhorar retenção
- impacto_no_ltv: como melhorar retenção em 10% impacta o LTV
- projecao_anual: retenção esperada nos próximos 12 meses"""

        result = self.ask_json(prompt, system=SYSTEM_PRODUCT)
        ret = result.get("retention_rate_atual", {})
        print(f"\n📈 Retention Analysis")
        print(f"  D7: {ret.get('d7','?')}% | D30: {ret.get('d30','?')}% | D90: {ret.get('d90','?')}%")
        self.save_result(result, prefix="retention_analysis")
        return result

    def feature_impact(self, feature: str, data: dict) -> dict:
        """Analisa impacto de feature ou A/B test nos KPIs."""
        self.logger.info(f"Feature impact: {feature}")
        prompt = f"""Analise o impacto desta feature/experimento nos KPIs do produto:

FEATURE/EXPERIMENTO: {feature}

DADOS DO A/B TEST:
{json.dumps(data, indent=2, ensure_ascii=False)[:5000]}

Retorne JSON com:
- resultado_estatistico:
  - significancia_estatistica_pct: % de confiança no resultado
  - p_value: valor p do teste
  - tamanho_amostral: adequado para o teste?
  - duracao_teste: foi suficiente?
- impacto_metrica_primaria:
  - metrica: qual foi a métrica principal
  - controle: valor no grupo controle
  - variante: valor no grupo variante
  - uplift_pct: % de melhora
  - uplift_absoluto: diferença absoluta
- impacto_metricas_secundarias: outras métricas afetadas
- efeitos_colaterais: métricas que pioraram
- segmentacao: variação de impacto por segmento de usuário
- estimativa_impacto_anual: se lançar para 100%, impacto no MRR/engajamento
- recomendacao: lançar|iterar|descartar — com justificativa
- proximo_experimento: o que testar em seguida"""

        result = self.ask_json(prompt, system=SYSTEM_PRODUCT)
        rec = result.get("recomendacao","?")
        uplift = result.get("impacto_metrica_primaria",{}).get("uplift_pct","?")
        sig = result.get("resultado_estatistico",{}).get("significancia_estatistica_pct","?")
        print(f"\n🧪 Feature Impact — {feature}")
        print(f"  Uplift: {uplift}% | Significância: {sig}% | Recomendação: {rec}")
        self.save_result(result, prefix=f"feature_impact_{feature.replace(' ','_').lower()[:20]}")
        return result

    def nps_analysis(self, responses: list) -> dict:
        """Analisa respostas de NPS e gera insights acionáveis."""
        self.logger.info(f"NPS analysis: {len(responses)} respostas")
        promoters = [r for r in responses if isinstance(r, dict) and r.get("nota",0) >= 9]
        detractors = [r for r in responses if isinstance(r, dict) and r.get("nota",0) <= 6]
        nps = ((len(promoters) - len(detractors)) / max(len(responses),1)) * 100
        prompt = f"""Analise estas respostas de NPS:

TOTAL: {len(responses)} respostas
NPS CALCULADO: {nps:.0f}
PROMOTORES: {len(promoters)} | DETRATORES: {len(detractors)}

RESPOSTAS (amostra):
{json.dumps(responses[:30], indent=2, ensure_ascii=False)[:5000]}

Retorne JSON com:
- nps_score: {nps:.0f}
- classificacao: "excelente (>50)"|"bom (30-50)"|"aceitavel (0-30)"|"ruim (<0)"
- segmentacao:
  - promotores_pct: %
  - neutros_pct: %
  - detratores_pct: %
- analise_texto_livre: temas mais mencionados nas respostas abertas
- principais_elogios: top 5 razões pelas quais amam o produto
- principais_criticas: top 5 razões pelas quais criticam
- temas_churn_risk: o que mais frequentemente precede cancelamento
- segmentacao_por_perfil: variação de NPS por tipo de cliente
- acoes_por_segmento:
  - para_promotores: como transformar em embaixadores
  - para_neutros: como converter em promotores
  - para_detratores: como recuperar e reter
- impacto_no_crescimento: relação entre NPS e crescimento orgânico
- meta_nps_6_meses: onde o NPS deve estar e como chegar lá"""

        result = self.ask_json(prompt, system=SYSTEM_PRODUCT)
        nps_score = result.get("nps_score", nps)
        classificacao = result.get("classificacao","?")
        print(f"\n💜 NPS Analysis — Score: {nps_score:.0f} ({classificacao})")
        criticas = result.get("principais_criticas",[])
        if isinstance(criticas, list):
            for c in criticas[:3]:
                print(f"  ⚠️  {str(c)[:80]}")
        self.save_result(result, prefix="nps_analysis")
        return result

    def roadmap_prioritization(self, feedback: dict, metrics: dict) -> dict:
        """Prioriza roadmap de produto baseado em dados e feedback."""
        self.logger.info("Roadmap prioritization")
        prompt = f"""Priorize o roadmap de produto baseado em dados e feedback:

FEEDBACK DE USUÁRIOS:
{json.dumps(feedback, indent=2, ensure_ascii=False)[:3000]}

MÉTRICAS ATUAIS:
{json.dumps(metrics, indent=2, ensure_ascii=False)[:2000]}

Retorne JSON com:
- oportunidades_identificadas: lista de iniciativas detectadas no feedback e dados
- priorizacao_ice: para cada iniciativa, score ICE:
  - iniciativa: nome
  - impact: 0-10 (impacto nos KPIs principais)
  - confidence: 0-10 (certeza de que vai funcionar)
  - ease: 0-10 (facilidade de implementar)
  - ice_score: impact * confidence * ease
  - quadrimestre_recomendado: Q1|Q2|Q3|Q4
  - evidencias: dados ou feedback que justificam
- roadmap_proposto:
  - q1_now: o que fazer agora (top 3-5 itens)
  - q2_next: próximo trimestre
  - q3_later: mais tarde
  - backlog: para considerar no futuro
- o_que_nao_construir: iniciativas que NÃO devem entrar no roadmap e por quê
- north_star_impact: como cada item do roadmap move a North Star Metric
- dependencias: o que precisa de o que para ser construído
- recursos_necessarios: estimativa de equipe para o roadmap proposto"""

        result = self.ask_json(prompt, system=SYSTEM_PRODUCT)
        q1 = result.get("roadmap_proposto",{}).get("q1_now",[])
        print(f"\n🗺️  Roadmap Prioritization")
        print(f"  Q1 (agora): {len(q1) if isinstance(q1, list) else '?'} iniciativas")
        if isinstance(q1, list):
            for item in q1[:4]:
                ice = item.get("ice_score","?") if isinstance(item, dict) else "?"
                nome = item.get("iniciativa","?") if isinstance(item, dict) else str(item)
                print(f"  ICE {ice} | {str(nome)[:70]}")
        self.save_result(result, prefix="roadmap_prioritization")
        return result


def main():
    parser = argparse.ArgumentParser(description="Product Analytics — ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("funnel").add_argument("--events", required=True)
    sub.add_parser("retention").add_argument("--cohorts", required=True)

    p_fi = sub.add_parser("feature-impact")
    p_fi.add_argument("--feature", required=True)
    p_fi.add_argument("--data", required=True)

    sub.add_parser("nps-analysis").add_argument("--responses", required=True)

    p_rm = sub.add_parser("roadmap")
    p_rm.add_argument("--feedback", required=True)
    p_rm.add_argument("--metrics", required=True)

    args = parser.parse_args()
    agent = ProductAnalytics()
    def load(p): return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else {}

    if args.command == "funnel":
        agent.activation_funnel(load(args.events))
    elif args.command == "retention":
        agent.retention_analysis(load(args.cohorts))
    elif args.command == "feature-impact":
        agent.feature_impact(args.feature, load(args.data))
    elif args.command == "nps-analysis":
        data = load(args.responses)
        agent.nps_analysis(data if isinstance(data, list) else data.get("responses",[]))
    elif args.command == "roadmap":
        agent.roadmap_prioritization(load(args.feedback), load(args.metrics))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
