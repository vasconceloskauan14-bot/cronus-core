"""
MOAT Agent — ULTIMATE CRONUS
Vantagem competitiva sustentável: análise, construção e defesa do moat.

Uso:
    python moat_agent.py analyze --company data/empresa.json --competitors data/concorrentes.json
    python moat_agent.py build --company data/empresa.json --timeframe "12 meses"
    python moat_agent.py defend --threat data/ameaca.json --company data/empresa.json
    python moat_agent.py score --company data/empresa.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from base_agent import BaseAgent

SYSTEM_MOAT = """Você é o MOAT, agente de Vantagem Competitiva do ULTIMATE CRONUS.
Você identifica, constrói e defende moats (fossos competitivos) sustentáveis.
Pense como Warren Buffett analisando vantagens duráveis + Peter Thiel em Zero to One.
Foque em vantagens estruturais que ficam mais fortes com o tempo, não apenas diferenciação temporária."""


class MoatAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="MOAT", output_dir="agents/output")

    def analyze_moat(self, company: dict, competitors: list) -> dict:
        """Analisa o moat atual da empresa."""
        self.logger.info(f"Moat analysis: {company.get('nome', '?')}")
        prompt = f"""Analise o fosso competitivo (moat) desta empresa:

EMPRESA:
{json.dumps(company, indent=2, ensure_ascii=False)[:3000]}

CONCORRENTES:
{json.dumps(competitors[:5], indent=2, ensure_ascii=False)[:2000]}

Retorne JSON com:
- moat_score: 0-100 (força do moat atual)
- tipo_moat_dominante: "network_effects"|"switching_costs"|"cost_advantages"|"intangible_assets"|"efficient_scale"|"nenhum"
- analise_por_tipo:
  - network_effects: score 0-10 + justificativa
  - switching_costs: score 0-10 + justificativa
  - cost_advantages: score 0-10 + justificativa
  - intangible_assets: marcas, patentes, licenças — score 0-10
  - efficient_scale: mercado pequeno que só suporta 1-2 players — score 0-10
- durabilidade_estimada: "1 ano"|"3 anos"|"5+ anos"|"décadas"
- vulnerabilidades: onde o moat pode ser atacado
- vantagens_vs_concorrentes: o que a empresa tem que concorrentes não têm
- o_que_concorrentes_tem: vantagens dos competidores
- score_por_concorrente: ranking de força do moat vs cada concorrente
- veredicto: a empresa tem um moat real ou está em território contestável?"""

        result = self.ask_json(prompt, system=SYSTEM_MOAT)
        score = result.get("moat_score", 0)
        tipo = result.get("tipo_moat_dominante", "?")
        durabilidade = result.get("durabilidade_estimada", "?")
        print(f"\n🏰 Moat Analysis — {company.get('nome', '?')}")
        print(f"  Score: {score}/100 | Tipo: {tipo} | Durabilidade: {durabilidade}")
        tipos = result.get("analise_por_tipo", {})
        for t, info in tipos.items():
            if isinstance(info, dict):
                s = info.get("score", 0)
                print(f"  {t:<20} {'█' * s}{'░' * (10-s)} {s}/10")
        self.save_result(result, prefix="moat_analysis")
        return result

    def build_moat_strategy(self, company: dict, timeframe: str = "12 meses") -> dict:
        """Cria estratégia para construir moat mais forte."""
        self.logger.info(f"Build moat: {timeframe}")
        prompt = f"""Crie uma estratégia para construir um moat mais forte:

EMPRESA:
{json.dumps(company, indent=2, ensure_ascii=False)[:3000]}

HORIZONTE: {timeframe}

Retorne JSON com:
- moat_alvo: qual tipo de moat focar para construir (1-2 tipos principais)
- justificativa_escolha: por que este(s) tipo(s) para esta empresa
- iniciativas_por_tipo:
  - para_network_effects: se aplicável, como construir efeitos de rede
  - para_switching_costs: se aplicável, como aumentar custo de troca
  - para_custo: se aplicável, como construir vantagem de custo
  - para_marca_ip: se aplicável, como fortalecer ativos intangíveis
- roadmap_moat: cronograma trimestre a trimestre
- investimentos_necessarios: o que priorizar financeiramente
- kpis_moat: como medir que o moat está crescendo
- armadilhas_evitar: erros comuns ao tentar construir moat
- quick_wins: o que pode fazer nos próximos 30 dias que fortalece o moat
- flywheel: descreva o flywheel que se auto-reforça quando o moat funciona"""

        result = self.ask_json(prompt, system=SYSTEM_MOAT)
        moat_alvo = result.get("moat_alvo", "?")
        print(f"\n🏗️  Build Moat Strategy ({timeframe})")
        print(f"  Foco: {moat_alvo}")
        flywheel = result.get("flywheel", "")
        if flywheel:
            print(f"  Flywheel: {str(flywheel)[:100]}")
        self.save_result(result, prefix="moat_strategy")
        return result

    def defend_against_threat(self, threat: dict, company: dict) -> dict:
        """Cria plano de defesa contra ameaça competitiva específica."""
        self.logger.info(f"Defend: {threat.get('nome', '?')}")
        prompt = f"""Crie um plano de defesa contra esta ameaça competitiva:

AMEAÇA:
{json.dumps(threat, indent=2, ensure_ascii=False)[:2000]}

EMPRESA DEFENDENDO:
{json.dumps(company, indent=2, ensure_ascii=False)[:2000]}

Retorne JSON com:
- nivel_ameaca: "baixo"|"médio"|"alto"|"existencial"
- analise_ameaca:
  - pontos_fortes_atacante: o que o atacante tem a favor
  - pontos_fracos_atacante: vulnerabilidades do atacante
  - velocidade_ameaca: quanto tempo antes de impacto real
- estrategias_defesa:
  - defesa_imediata: ações para os próximos 30 dias
  - defesa_medio_prazo: ações para 3-6 meses
  - contra_ataque: onde atacar de volta na fraqueza do atacante
- o_que_nao_fazer: erros clássicos de defesa a evitar
- cenarios:
  - se_ignorar: o que acontece em 6 meses
  - se_defender_bem: melhor resultado possível
  - se_defender_mal: pior resultado provável
- decisao_recomendada: resposta estratégica ideal
- recursos_necessarios: o que precisar para executar a defesa"""

        result = self.ask_json(prompt, system=SYSTEM_MOAT)
        nivel = result.get("nivel_ameaca", "?")
        icons = {"existencial": "🚨", "alto": "🔴", "médio": "🟡", "baixo": "🟢"}
        print(f"\n{icons.get(nivel, '●')} Defense Plan vs {threat.get('nome', '?')} [{nivel.upper()}]")
        print(f"  Decisão: {result.get('decisao_recomendada', '')[:100]}")
        self.save_result(result, prefix="moat_defense")
        return result

    def competitive_score(self, company: dict) -> dict:
        """Score completo de vantagem competitiva com benchmarks."""
        self.logger.info(f"Competitive score: {company.get('nome', '?')}")
        prompt = f"""Gere um scorecard completo de vantagem competitiva:

EMPRESA:
{json.dumps(company, indent=2, ensure_ascii=False)[:4000]}

Retorne JSON com:
- competitive_score_total: 0-100
- categoria_competitiva: "monopoly"|"oligopoly"|"competitive"|"commodity"
- dimensoes:
  - produto: score 0-10 (quão melhor é o produto?)
  - distribuicao: score 0-10 (canais exclusivos ou superiores?)
  - marca: score 0-10 (reconhecimento e lealdade?)
  - dados: score 0-10 (dados exclusivos ou superiores?)
  - tecnologia: score 0-10 (tech proprietária ou diferenciada?)
  - equipe: score 0-10 (talento difícil de replicar?)
  - relacionamentos: score 0-10 (clientes cativos, parcerias exclusivas?)
  - regulatorio: score 0-10 (licenças, compliance, barreiras regulatórias?)
- comparacao_setor: como se compara com a média do setor e com o top quartile
- poder_de_precificacao: qual é o poder de pricing atual (1-10)?
- sustentabilidade: o quanto a vantagem é sustentável sem reinvestimento?
- recomendacao_prioritaria: a ÚNICA coisa que mais aumentaria o score"""

        result = self.ask_json(prompt, system=SYSTEM_MOAT)
        total = result.get("competitive_score_total", 0)
        categoria = result.get("categoria_competitiva", "?")
        print(f"\n🏆 Competitive Score — {company.get('nome', '?')}: {total}/100 ({categoria})")
        dims = result.get("dimensoes", {})
        for d, info in dims.items():
            s = info if isinstance(info, int) else info.get("score", 0) if isinstance(info, dict) else 0
            print(f"  {d:<18} {'█' * s}{'░' * (10-s)} {s}/10")
        self.save_result(result, prefix="competitive_score")
        return result


def main():
    parser = argparse.ArgumentParser(description="MOAT Agent — ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")

    p_a = sub.add_parser("analyze")
    p_a.add_argument("--company", required=True)
    p_a.add_argument("--competitors", required=True)

    p_b = sub.add_parser("build")
    p_b.add_argument("--company", required=True)
    p_b.add_argument("--timeframe", default="12 meses")

    p_d = sub.add_parser("defend")
    p_d.add_argument("--threat", required=True)
    p_d.add_argument("--company", required=True)

    sub.add_parser("score").add_argument("--company", required=True)

    args = parser.parse_args()
    agent = MoatAgent()
    def load(p): return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else {}

    if args.command == "analyze":
        comps = load(args.competitors)
        agent.analyze_moat(load(args.company), comps if isinstance(comps, list) else [])
    elif args.command == "build":
        agent.build_moat_strategy(load(args.company), args.timeframe)
    elif args.command == "defend":
        agent.defend_against_threat(load(args.threat), load(args.company))
    elif args.command == "score":
        agent.competitive_score(load(args.company))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
