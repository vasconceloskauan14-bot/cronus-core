"""
HR Automation — ULTIMATE CRONUS
Automação completa de RH: recrutamento, onboarding, performance e cultura.

Uso:
    python hr_automation.py recruit --job data/vaga.json --candidates data/candidatos.json
    python hr_automation.py onboard --employee data/novo_funcionario.json
    python hr_automation.py performance --reviews data/avaliacoes.json
    python hr_automation.py culture --survey data/pesquisa.json
    python hr_automation.py compensation --market data/mercado_salarios.json --team data/equipe.json
    python hr_automation.py workforce-plan --company data/empresa.json --goals data/metas.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))
from base_agent import BaseAgent

SYSTEM_HR = """Você é o especialista em People & Culture do ULTIMATE CRONUS.
Você domina recrutamento, desenvolvimento de pessoas, gestão de performance e cultura organizacional.
Pense como um CHRO estratégico: pessoas são o maior ativo da empresa.
Equilibre eficiência operacional com construção de uma cultura de alta performance."""


class HrAutomation(BaseAgent):
    def __init__(self):
        super().__init__(name="HR", output_dir="automation/reports")

    def recruitment_pipeline(self, job: dict, candidates: list) -> dict:
        """Gerencia pipeline completo de recrutamento."""
        self.logger.info(f"Recruiting: {job.get('titulo', '?')}")
        prompt = f"""Gerencie o pipeline de recrutamento para esta vaga:

VAGA:
{json.dumps(job, indent=2, ensure_ascii=False)[:2000]}

CANDIDATOS ({len(candidates)}):
{json.dumps(candidates[:15], indent=2, ensure_ascii=False)[:4000]}

Retorne JSON com:
- candidatos_rankeados: lista ordenada por fit com:
  - id: identificador
  - nome: nome do candidato
  - score_total: 0-100
  - score_tecnico: 0-100
  - score_cultural: 0-100
  - pontos_fortes: o que se destaca
  - pontos_atenção: o que investigar mais
  - recomendacao: "avancar"|"talvez"|"nao_avancar"
  - perguntas_entrevista: 5 perguntas específicas para este candidato
- shortlist: top 3-5 candidatos para entrevistar
- red_flags: candidatos com sinais de alerta e por quê
- tempo_estimado_contratacao: semanas até oferta
- descricao_vaga_otimizada: texto de job description melhorado
- onde_buscar_mais: canais para atrair mais candidatos qualificados"""

        result = self.ask_json(prompt, system=SYSTEM_HR)
        rankeados = result.get("candidatos_rankeados", [])
        shortlist = result.get("shortlist", [])
        print(f"\n👥 Recruitment — {job.get('titulo', '?')}: {len(rankeados)} candidatos")
        print(f"  Shortlist: {len(shortlist) if isinstance(shortlist, list) else '?'} para entrevista")
        self.save_result(result, prefix="recruitment")
        return result

    def onboarding_program(self, employee: dict) -> dict:
        """Cria programa de onboarding personalizado."""
        self.logger.info(f"Onboarding: {employee.get('nome', '?')} — {employee.get('cargo', '?')}")
        prompt = f"""Crie um programa de onboarding completo para este novo colaborador:

COLABORADOR:
{json.dumps(employee, indent=2, ensure_ascii=False)[:2000]}

Retorne JSON com:
- objetivo_onboarding: o que este colaborador precisa alcançar para ter sucesso
- plano_30_60_90:
  - primeiros_30_dias: objetivos e atividades
  - dias_31_60: objetivos e atividades
  - dias_61_90: objetivos e atividades
- primeira_semana:
  - dia_1: agenda detalhada do primeiro dia
  - semana_1: atividades da primeira semana
- treinamentos_obrigatorios: lista de treinamentos e prazos
- pessoas_para_conhecer: stakeholders chave e por que
- recursos_e_acessos: o que precisa ter no dia 1
- buddy_program: perfil ideal de buddy e responsabilidades
- check_ins: quando e como fazer acompanhamento
- metricas_sucesso_onboarding: como saber se está indo bem
- comunicacao_equipe: como apresentar o novo membro"""

        result = self.ask_json(prompt, system=SYSTEM_HR)
        print(f"\n🚀 Onboarding — {employee.get('nome', '?')} ({employee.get('cargo', '?')})")
        plano = result.get("plano_30_60_90", {})
        for periodo, atividades in plano.items():
            print(f"  {periodo}: {str(atividades)[:80]}")
        self.save_result(result, prefix="hr_onboarding")
        return result

    def performance_review(self, reviews: list) -> dict:
        """Processa e analisa ciclo de avaliação de performance."""
        self.logger.info(f"Performance review: {len(reviews)} colaboradores")
        prompt = f"""Analise este ciclo de avaliação de performance:

AVALIAÇÕES ({len(reviews)} colaboradores):
{json.dumps(reviews[:20], indent=2, ensure_ascii=False)[:5000]}

Retorne JSON com:
- resumo_geral:
  - media_geral: score médio da equipe
  - distribuicao: % em cada categoria (excepcional/acima/adequado/abaixo)
  - desvio_padrao: variação de performance
- top_performers: top 10% com análise de o que os diferencia
- low_performers: bottom 10% com plano de desenvolvimento
- patterns: padrões observados na equipe
- areas_desenvolvimento_coletivas: onde a equipe como um todo precisa crescer
- recomendacoes_promocao: candidatos prontos para próximo nível
- riscos_retencao: quem pode sair e por quê
- planos_desenvolvimento: para cada colaborador abaixo do esperado
- calibracao_bias: alertas de possíveis vieses nas avaliações
- proximos_passos_rh: ações de RH baseadas nos resultados"""

        result = self.ask_json(prompt, system=SYSTEM_HR)
        resumo = result.get("resumo_geral", {})
        print(f"\n📊 Performance Review — {len(reviews)} colaboradores")
        print(f"  Média geral: {resumo.get('media_geral', '?')} | Distribuição: {resumo.get('distribuicao', '?')}")
        self.save_result(result, prefix="performance_review")
        return result

    def culture_pulse(self, survey: dict) -> dict:
        """Analisa pesquisa de cultura e clima organizacional."""
        self.logger.info("Culture pulse survey analysis")
        prompt = f"""Analise esta pesquisa de cultura e clima organizacional:

RESULTADOS DA PESQUISA:
{json.dumps(survey, indent=2, ensure_ascii=False)[:5000]}

Retorne JSON com:
- eNPS: Employee Net Promoter Score calculado
- score_cultura: 0-100
- dimensoes:
  - lideranca: 0-10
  - comunicacao: 0-10
  - crescimento: 0-10
  - autonomia: 0-10
  - colaboracao: 0-10
  - bem_estar: 0-10
  - proposito: 0-10
- pontos_fortes_cultura: o que a equipe valoriza
- pontos_dor: maiores insatisfações
- temas_recorrentes: padrões nas respostas abertas
- segmentacao: diferenças por área, nível, tempo de casa
- riscos_retencao: o que pode gerar turnover
- acoes_prioritarias: top 5 ações de alta alavancagem
- comunicacao_resultados: como compartilhar resultados com equipe
- benchmarks: como comparar com mercado"""

        result = self.ask_json(prompt, system=SYSTEM_HR)
        eNPS = result.get("eNPS", "?")
        score = result.get("score_cultura", 0)
        print(f"\n❤️  Culture Pulse — eNPS: {eNPS} | Score: {score}/100")
        dims = result.get("dimensoes", {})
        for d, v in dims.items():
            bar = "█" * v + "░" * (10 - v)
            print(f"  {d:<18} {bar} {v}/10")
        self.save_result(result, prefix="culture_pulse")
        return result

    def compensation_analysis(self, market_data: dict, team: list) -> dict:
        """Analisa e otimiza estratégia de remuneração."""
        self.logger.info(f"Compensation analysis: {len(team)} colaboradores")
        prompt = f"""Analise a estratégia de remuneração:

DADOS DE MERCADO (salários):
{json.dumps(market_data, indent=2, ensure_ascii=False)[:2000]}

EQUIPE ATUAL:
{json.dumps(team[:20], indent=2, ensure_ascii=False)[:3000]}

Retorne JSON com:
- posicionamento_atual: onde a empresa está vs mercado (P25/P50/P75)
- colaboradores_abaixo_mercado: quem precisa de ajuste urgente
- colaboradores_acima_mercado: quem está supercompensado
- gap_total_remuneracao: custo de corrigir defasagens (R$/mês)
- estrategia_remuneracao_recomendada: filosofia de comp (P50, P75, etc)
- estrutura_salarios: bandas salariais sugeridas por nível
- beneficios_vs_mercado: análise de pacote de benefícios
- incentivos_variaveis: recomendação de bônus e equity
- custo_retencao: custo de reter top performers vs custo de perder
- plano_ajustes: cronograma de ajustes salariais por prioridade
- comunicacao_comp: como falar sobre remuneração com transparência"""

        result = self.ask_json(prompt, system=SYSTEM_HR)
        posicionamento = result.get("posicionamento_atual", "?")
        gap = result.get("gap_total_remuneracao", "?")
        print(f"\n💰 Compensation Analysis — Posicionamento: {posicionamento}")
        print(f"  Gap de remuneração: R$ {gap}/mês")
        self.save_result(result, prefix="compensation_analysis")
        return result

    def workforce_planning(self, company: dict, goals: dict) -> dict:
        """Plano estratégico de workforce para atingir objetivos."""
        self.logger.info("Workforce planning")
        prompt = f"""Crie um plano estratégico de workforce:

EMPRESA ATUAL:
{json.dumps(company, indent=2, ensure_ascii=False)[:2000]}

OBJETIVOS ESTRATÉGICOS:
{json.dumps(goals, indent=2, ensure_ascii=False)[:2000]}

Retorne JSON com:
- gap_atual: capacidades que a empresa não tem e precisará
- plano_contratacoes:
  - urgente_0_3m: cargos críticos para contratar agora
  - curto_prazo_3_6m: cargos para próximos 6 meses
  - medio_prazo_6_12m: cargos para o ano
- make_vs_buy: o que desenvolver internamente vs contratar pronto
- estrutura_times: como organizar times para escalar
- custo_headcount: projeção de custos de pessoas por trimestre
- risco_pessoas: riscos de pessoas que podem travar a estratégia
- capacidades_criticas: skills que serão diferencial competitivo
- plano_desenvolvimento: o que treinar internamente
- automacao_e_ia: onde IA pode substituir ou aumentar capacidade humana
- kpis_rh_estrategicos: métricas de people para o board"""

        result = self.ask_json(prompt, system=SYSTEM_HR)
        contratacoes_urgentes = result.get("plano_contratacoes", {}).get("urgente_0_3m", [])
        print(f"\n📋 Workforce Planning")
        print(f"  Contratações urgentes: {len(contratacoes_urgentes) if isinstance(contratacoes_urgentes, list) else '?'} posições")
        self.save_result(result, prefix="workforce_plan")
        return result


def main():
    parser = argparse.ArgumentParser(description="HR Automation — ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")

    p_r = sub.add_parser("recruit")
    p_r.add_argument("--job", required=True)
    p_r.add_argument("--candidates", required=True)

    sub.add_parser("onboard").add_argument("--employee", required=True)
    sub.add_parser("performance").add_argument("--reviews", required=True)
    sub.add_parser("culture").add_argument("--survey", required=True)

    p_c = sub.add_parser("compensation")
    p_c.add_argument("--market", required=True)
    p_c.add_argument("--team", required=True)

    p_wp = sub.add_parser("workforce-plan")
    p_wp.add_argument("--company", required=True)
    p_wp.add_argument("--goals", required=True)

    args = parser.parse_args()
    agent = HrAutomation()
    def load(p): return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else {}

    if args.command == "recruit":
        cands = load(args.candidates)
        agent.recruitment_pipeline(load(args.job), cands if isinstance(cands, list) else cands.get("candidates", []))
    elif args.command == "onboard":
        agent.onboarding_program(load(args.employee))
    elif args.command == "performance":
        data = load(args.reviews)
        agent.performance_review(data if isinstance(data, list) else data.get("reviews", []))
    elif args.command == "culture":
        agent.culture_pulse(load(args.survey))
    elif args.command == "compensation":
        team = load(args.team)
        agent.compensation_analysis(load(args.market), team if isinstance(team, list) else team.get("team", []))
    elif args.command == "workforce-plan":
        agent.workforce_planning(load(args.company), load(args.goals))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
