"""
INNOVATION Agent — ULTIMATE CRONUS
P&D, inovação, hipóteses, experimentos e pipeline de inovação.

Uso:
    python innovation_agent.py ideation --context data/empresa.json --challenge "reduzir churn"
    python innovation_agent.py experiment --hypothesis data/hipotese.json
    python innovation_agent.py pipeline --innovations data/inovacoes.json
    python innovation_agent.py tech-radar --company data/empresa.json --industry "SaaS"
    python innovation_agent.py disrupt --industry "educacao" --horizon "3 anos"
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from base_agent import BaseAgent

SYSTEM_INNOVATION = """Você é o INNOVATION, agente de P&D e Inovação do ULTIMATE CRONUS.
Você combina design thinking, lean startup e first principles thinking para gerar inovações reais.
Pense como um Chief Innovation Officer que transforma ideias em vantagens competitivas mensuráveis.
Inovação sem execução é ficção — cada ideia deve ter um experimento validável."""


class InnovationAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="INNOVATION", output_dir="agents/output")

    def ideation_sprint(self, context: dict, challenge: str) -> dict:
        """Sprint de ideação para resolver um desafio específico."""
        self.logger.info(f"Ideation: {challenge[:50]}")
        prompt = f"""Execute um sprint de ideação para resolver este desafio:

DESAFIO: {challenge}

CONTEXTO:
{json.dumps(context, indent=2, ensure_ascii=False)[:3000]}

Retorne JSON com:
- reframing: 3 maneiras diferentes de ver o problema
- ideias_geradas: lista de 20 ideias (rápidas, sem julgamento)
- ideias_filtradas: top 5 ideias com maior potencial
- para_cada_ideia_top:
  - ideia: descrição
  - como_funciona: mecanismo principal
  - proposta_valor: benefício claro
  - analogia: empresa/produto análogo que funcionou
  - esforco: "baixo"|"médio"|"alto"
  - impacto_potencial: "baixo"|"médio"|"alto"|"disruptivo"
  - risco_principal: maior risco
  - mvp_minimo: menor experimento para validar
- ideia_vencedora: qual desenvolver primeiro e por quê
- proximos_passos: 3 ações para nas próximas 72 horas"""

        result = self.ask_json(prompt, system=SYSTEM_INNOVATION)
        ideias = result.get("ideias_filtradas", [])
        print(f"\n💡 Ideation Sprint: {challenge[:50]}")
        print(f"  {len(ideias)} ideias filtradas")
        vencedora = result.get("ideia_vencedora", "?")
        if isinstance(vencedora, dict):
            print(f"  Vencedora: {vencedora.get('ideia', '?')[:80]}")
        else:
            print(f"  Vencedora: {str(vencedora)[:80]}")
        self.save_result(result, prefix="ideation_sprint")
        return result

    def design_experiment(self, hypothesis: dict) -> dict:
        """Projeta experimento científico para validar hipótese."""
        self.logger.info(f"Experiment: {hypothesis.get('hipotese', '?')[:50]}")
        prompt = f"""Projete um experimento rigoroso para validar esta hipótese:

HIPÓTESE:
{json.dumps(hypothesis, indent=2, ensure_ascii=False)[:2000]}

Retorne JSON com:
- hipotese_reformulada: hipótese em formato testável (se X então Y)
- tipo_experimento: "a_b_test"|"smoke_test"|"concierge"|"wizard_of_oz"|"fake_door"|"mvp"
- metricas:
  - metrica_principal: o que medir para validar/invalidar
  - baseline: valor atual
  - threshold_sucesso: resultado que confirma a hipótese
  - threshold_falha: resultado que invalida
- protocolo:
  - duracao_dias: quanto tempo rodar
  - tamanho_amostra: quantas pessoas/eventos necessários
  - grupo_controle: quem/o que é o controle
  - grupo_teste: quem/o que é o teste
  - como_randomizar: método de randomização
- pre_mortum: o que pode dar errado no experimento em si
- custo_experimento: estimativa em R$ e horas
- decisao_pos_experimento: o que fazer em cada cenário (sucesso/falha/inconclusivo)
- cronograma: semana a semana do experimento"""

        result = self.ask_json(prompt, system=SYSTEM_INNOVATION)
        print(f"\n🧪 Experiment Design — {result.get('tipo_experimento', '?')}")
        print(f"  Duração: {result.get('protocolo', {}).get('duracao_dias', '?')} dias")
        print(f"  Custo: {result.get('custo_experimento', '?')}")
        self.save_result(result, prefix="experiment_design")
        return result

    def innovation_pipeline(self, innovations: list) -> dict:
        """Gerencia e prioriza pipeline de inovações."""
        self.logger.info(f"Pipeline: {len(innovations)} inovações")
        prompt = f"""Avalie e priorize este pipeline de inovações:

INOVAÇÕES:
{json.dumps(innovations, indent=2, ensure_ascii=False)[:5000]}

Retorne JSON com:
- portfolio_scorecard: para cada inovação:
  - id: identificador
  - nome: nome da inovação
  - score_potencial: 0-100
  - score_viabilidade: 0-100
  - score_estrategia: alinhamento estratégico 0-100
  - score_composto: média ponderada
  - stage: "ideacao"|"experimento"|"piloto"|"escala"|"descontinuar"
  - proxima_acao: o que fazer agora
- matriz_priorizacao: quadrante por impacto x esforço
- portfolio_balance:
  - inovacoes_incrementais: % que melhoram o existente
  - inovacoes_adjacentes: % em mercados próximos
  - inovacoes_disruptivas: % de aposta de futuro
- recomendacao_alocacao_recursos: como distribuir esforço
- vitrias_rapidas: o que pode gerar resultado em 30 dias
- descontinuacoes: o que parar de investir"""

        result = self.ask_json(prompt, system=SYSTEM_INNOVATION)
        scorecard = result.get("portfolio_scorecard", [])
        print(f"\n🚀 Innovation Pipeline — {len(scorecard)} inovações avaliadas")
        vitrias = result.get("vitrias_rapidas", [])
        print(f"  Vitórias rápidas: {len(vitrias) if isinstance(vitrias, list) else '?'}")
        self.save_result(result, prefix="innovation_pipeline")
        return result

    def tech_radar(self, company: dict, industry: str) -> dict:
        """Cria tech radar com tecnologias a adotar/avaliar/evitar."""
        self.logger.info(f"Tech radar: {industry}")
        prompt = f"""Crie um tech radar para esta empresa:

EMPRESA:
{json.dumps(company, indent=2, ensure_ascii=False)[:2000]}

INDÚSTRIA: {industry}

Retorne JSON com:
- adotar_agora: tecnologias maduras para implementar imediatamente
- avaliar: tecnologias promissoras para explorar nos próximos 6 meses
- experimentar: tecnologias emergentes para fazer POCs
- evitar: tecnologias que não valem o investimento
- para_cada_tecnologia:
  - nome: nome da tecnologia
  - categoria: "infra"|"ai_ml"|"dados"|"frontend"|"backend"|"mobile"|"seguranca"
  - justificativa: por que nesta categoria
  - caso_de_uso: como usaria na empresa
  - risco: risco de adotar
  - alternativas: opções similares
- oportunidades_ia: onde IA pode ter maior impacto nesta empresa
- divida_tecnica_critica: débito técnico urgente a resolver
- investimentos_prioritarios: onde investir em tecnologia nos próximos 12 meses"""

        result = self.ask_json(prompt, system=SYSTEM_INNOVATION)
        adotar = result.get("adotar_agora", [])
        avaliar = result.get("avaliar", [])
        print(f"\n📡 Tech Radar — {industry}")
        print(f"  Adotar agora: {len(adotar) if isinstance(adotar, list) else '?'} | Avaliar: {len(avaliar) if isinstance(avaliar, list) else '?'}")
        self.save_result(result, prefix="tech_radar")
        return result

    def disruption_analysis(self, industry: str, horizon: str) -> dict:
        """Analisa cenários de disrupção na indústria."""
        self.logger.info(f"Disruption: {industry} / {horizon}")
        prompt = f"""Analise cenários de disrupção para a indústria: {industry}
Horizonte: {horizon}

Retorne JSON com:
- estado_atual: como a indústria funciona hoje
- forcas_disruptivas: tecnologias e forças que podem mudar tudo
- cenarios_futuro:
  - cenario_otimista: industria transformada positivamente
  - cenario_pessimista: disrupção massiva e destruição de valor
  - cenario_base: evolução moderada mais provável
- disruptores_emergentes: startups ou players que podem disrumpir
- janelas_oportunidade: espaços que podem criar valor disruptivo
- tecnologias_habilitadoras: tech que tornará isso possível
- timeline: quando esperar cada mudança significativa
- implicacoes_estrategicas: o que empresas do setor devem fazer agora
- apostas_recomendadas: onde posicionar para ganhar em cada cenário"""

        result = self.ask_json(prompt, system=SYSTEM_INNOVATION)
        cenarios = result.get("cenarios_futuro", {})
        print(f"\n🔮 Disruption Analysis — {industry} ({horizon})")
        print(f"  Cenários mapeados: {len(cenarios)}")
        self.save_result(result, prefix="disruption_analysis")
        return result


def main():
    parser = argparse.ArgumentParser(description="INNOVATION Agent — ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")

    p_id = sub.add_parser("ideation")
    p_id.add_argument("--context", required=True)
    p_id.add_argument("--challenge", required=True)

    sub.add_parser("experiment").add_argument("--hypothesis", required=True)
    sub.add_parser("pipeline").add_argument("--innovations", required=True)

    p_tr = sub.add_parser("tech-radar")
    p_tr.add_argument("--company", required=True)
    p_tr.add_argument("--industry", required=True)

    p_dis = sub.add_parser("disrupt")
    p_dis.add_argument("--industry", required=True)
    p_dis.add_argument("--horizon", default="3 anos")

    args = parser.parse_args()
    agent = InnovationAgent()
    def load(p): return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else {}

    if args.command == "ideation":
        agent.ideation_sprint(load(args.context), args.challenge)
    elif args.command == "experiment":
        agent.design_experiment(load(args.hypothesis))
    elif args.command == "pipeline":
        data = load(args.innovations)
        agent.innovation_pipeline(data if isinstance(data, list) else data.get("innovations", []))
    elif args.command == "tech-radar":
        agent.tech_radar(load(args.company), args.industry)
    elif args.command == "disrupt":
        agent.disruption_analysis(args.industry, args.horizon)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
