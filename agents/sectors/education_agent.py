"""
Education Agent — ULTIMATE CRONUS
Automações para EdTech: cursos, engajamento, LMS e aprendizado adaptativo.

Uso:
    python education_agent.py course-design --topic "Python para Iniciantes" --audience data/audiencia.json
    python education_agent.py engagement --cohort data/cohort.json
    python education_agent.py assessment --content data/conteudo.json
    python education_agent.py learning-path --learner data/aprendiz.json --catalog data/cursos.json
    python education_agent.py edtech-metrics --data data/lms_metrics.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_agent import BaseAgent

SYSTEM_EDUCATION = """Você é especialista em EdTech e design instrucional do ULTIMATE CRONUS.
Você domina aprendizado adulto, engajamento em cursos online, LMS e aprendizado adaptativo.
Pense como um Chief Learning Officer que combina pedagogia moderna com growth hacking.
Foque em completion rate, NPS do curso e transferência real de habilidades."""


class EducationAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="EDUCATION", output_dir="agents/output")

    def design_course(self, topic: str, audience: dict) -> dict:
        """Cria design instrucional completo para um curso."""
        self.logger.info(f"Course design: {topic}")
        prompt = f"""Crie um design instrucional completo para este curso:

TÓPICO: {topic}

AUDIÊNCIA:
{json.dumps(audience, indent=2, ensure_ascii=False)[:2000]}

Retorne JSON com:
- titulo_curso: título atrativo e orientado a resultado
- tagline: proposta de valor em 1 frase
- transformacao_prometida: antes e depois do aluno
- pre_requisitos: o que o aluno precisa saber
- objetivos_aprendizagem: lista de outcomes mensuráveis (formato: "Ao final, o aluno será capaz de...")
- modulos: lista de módulos com:
  - numero: sequência
  - titulo: nome do módulo
  - objetivo: o que aprende neste módulo
  - aulas: lista de aulas com título e formato (video|texto|quiz|exercicio|projeto)
  - duracao_estimada: horas
  - atividade_pratica: exercício ou projeto do módulo
- projeto_final: descrição do projeto capstone
- avaliacao: como medir aprendizado (quizzes, projetos, certificado)
- duracao_total_horas: tempo de estudo
- formato_recomendado: síncrono|assíncrono|híbrido
- estrategias_engajamento: como manter alunos engajados até o final
- pricing_recomendado: faixa de preço com justificativa
- diferenciais_vs_concorrentes: o que torna este curso único"""

        result = self.ask_json(prompt, system=SYSTEM_EDUCATION)
        modulos = result.get("modulos", [])
        duracao = result.get("duracao_total_horas", "?")
        print(f"\n🎓 Course Design — {topic}")
        print(f"  {len(modulos)} módulos | {duracao}h total")
        print(f"  Título: {result.get('titulo_curso', '')}")
        self.save_result(result, prefix="course_design")
        return result

    def engagement_strategy(self, cohort: dict) -> dict:
        """Cria estratégia para aumentar engajamento e completion rate."""
        self.logger.info("Engagement strategy")
        prompt = f"""Crie uma estratégia para melhorar engajamento e completion rate:

DADOS DO COHORT:
{json.dumps(cohort, indent=2, ensure_ascii=False)[:4000]}

Retorne JSON com:
- diagnostico_engajamento:
  - completion_rate_atual_pct: % que completa o curso
  - pontos_de_abandono: onde os alunos desistem
  - padroes_engajamento: quando e como alunos mais engajam
- segmentos_alunos:
  - engajados: perfil e % do total
  - em_risco: perfil e % do total
  - inativos: perfil e % do total
- intervencoes_por_segmento: para cada segmento, ações específicas
- gamificacao: pontos, badges e rankings recomendados
- sequencia_emails_engajamento: emails automáticos para reengajar
- conteudo_bônus: que conteúdo extra reativa alunos inativos
- comunidade: como criar senso de comunidade entre alunos
- mentoria_pares: programa de buddy system
- meta_completion_rate: onde deve chegar após intervenções
- kpis_engajamento: métricas para monitorar semanalmente"""

        result = self.ask_json(prompt, system=SYSTEM_EDUCATION)
        meta = result.get("meta_completion_rate", "?")
        diag = result.get("diagnostico_engajamento", {})
        print(f"\n📈 Engagement Strategy")
        print(f"  Completion atual: {diag.get('completion_rate_atual_pct', '?')}% → Meta: {meta}%")
        self.save_result(result, prefix="engagement_strategy")
        return result

    def generate_assessment(self, content: dict) -> dict:
        """Gera avaliações e exercícios para conteúdo de curso."""
        self.logger.info("Assessment generation")
        content_text = content.get("texto") or content.get("content") or json.dumps(content)
        prompt = f"""Gere avaliações e exercícios para este conteúdo de curso:

CONTEÚDO:
{content_text[:4000]}

Retorne JSON com:
- quiz_verificacao: 10 questões de múltipla escolha (4 alternativas, 1 correta) com:
  - pergunta: texto da questão
  - alternativas: lista com 4 opções
  - resposta_correta: letra (A/B/C/D)
  - explicacao: por que esta resposta está correta
  - dificuldade: "fácil"|"médio"|"difícil"
- questoes_abertas: 3 questões dissertativas para reflexão
- exercicio_pratico: atividade hands-on com:
  - objetivo: o que o aluno pratica
  - instrucoes: passo a passo
  - entregavel: o que deve entregar
  - criterios_avaliacao: como será avaliado
- estudo_de_caso: caso real ou fictício para análise
- projeto_mini: projeto de 2-4 horas que aplica o conteúdo
- rubricas_avaliacao: critérios para avaliar projetos e atividades abertas"""

        result = self.ask_json(prompt, system=SYSTEM_EDUCATION)
        quiz = result.get("quiz_verificacao", [])
        print(f"\n📝 Assessment Generated")
        print(f"  Quiz: {len(quiz)} questões | Exercício prático: ✅ | Projeto mini: ✅")
        self.save_result(result, prefix="course_assessment")
        return result

    def personalized_learning_path(self, learner: dict, catalog: list) -> dict:
        """Cria trilha de aprendizado personalizada."""
        self.logger.info(f"Learning path: {learner.get('nome', '?')}")
        prompt = f"""Crie uma trilha de aprendizado personalizada:

APRENDIZ:
{json.dumps(learner, indent=2, ensure_ascii=False)[:2000]}

CATÁLOGO DISPONÍVEL:
{json.dumps(catalog[:20], indent=2, ensure_ascii=False)[:3000]}

Retorne JSON com:
- diagnostico_nivel: avaliação do nível atual do aprendiz
- objetivo_aprendizagem: o que o aprendiz quer alcançar
- gaps_identificados: o que precisa aprender para atingir o objetivo
- trilha_recomendada: sequência de cursos/módulos em ordem:
  - ordem: número
  - curso: nome do curso/conteúdo
  - objetivo: por que este curso neste momento
  - duracao_estimada: horas
  - prioridade: "obrigatório"|"recomendado"|"opcional"
- cronograma_sugerido: distribuição ao longo do tempo
- milestones: marcos de progresso a celebrar
- recursos_complementares: livros, podcasts, projetos práticos
- comunidade: grupos e comunidades relevantes
- mentoria: se deve buscar mentoria e em que área
- retorno_esperado: o que muda na carreira/vida após completar a trilha"""

        result = self.ask_json(prompt, system=SYSTEM_EDUCATION)
        trilha = result.get("trilha_recomendada", [])
        print(f"\n🗺️  Learning Path — {learner.get('nome', '?')}")
        print(f"  {len(trilha)} cursos na trilha")
        for item in trilha[:4]:
            print(f"  {item.get('ordem', '?')}. {item.get('curso', '?')[:60]}")
        self.save_result(result, prefix="learning_path")
        return result

    def edtech_metrics(self, data: dict) -> dict:
        """Analisa métricas de plataforma EdTech."""
        self.logger.info("EdTech metrics analysis")
        prompt = f"""Analise as métricas desta plataforma EdTech:

DADOS:
{json.dumps(data, indent=2, ensure_ascii=False)[:5000]}

Retorne JSON com:
- score_plataforma: 0-100
- metricas_chave:
  - completion_rate_pct: % que completa cursos
  - nps_alunos: satisfação
  - time_to_first_lesson_horas: tempo até primeira aula após compra
  - dau_mau_ratio: daily/monthly active users
  - receita_por_aluno: R$
  - churn_mensal_pct: % que cancela/inativa por mês
  - viral_coefficient: quantos alunos cada aluno indica
- analise_cohorts: retenção por cohort de entrada
- cursos_mais_exitosos: top performers e por quê
- cursos_problema: baixo engajamento e o que fazer
- oportunidades_crescimento: onde expandir a oferta
- benchmarks_edtech: comparação com benchmarks do setor
- acoes_prioritarias: top 5 melhorias com maior impacto no negócio"""

        result = self.ask_json(prompt, system=SYSTEM_EDUCATION)
        score = result.get("score_plataforma", 0)
        m = result.get("metricas_chave", {})
        print(f"\n🎓 EdTech Metrics — Score: {score}/100")
        print(f"  Completion: {m.get('completion_rate_pct', '?')}% | NPS: {m.get('nps_alunos', '?')} | Churn: {m.get('churn_mensal_pct', '?')}%")
        self.save_result(result, prefix="edtech_metrics")
        return result


def main():
    parser = argparse.ArgumentParser(description="Education Agent — ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")

    p_cd = sub.add_parser("course-design")
    p_cd.add_argument("--topic", required=True)
    p_cd.add_argument("--audience", required=True)

    sub.add_parser("engagement").add_argument("--cohort", required=True)
    sub.add_parser("assessment").add_argument("--content", required=True)

    p_lp = sub.add_parser("learning-path")
    p_lp.add_argument("--learner", required=True)
    p_lp.add_argument("--catalog", required=True)

    sub.add_parser("edtech-metrics").add_argument("--data", required=True)

    args = parser.parse_args()
    agent = EducationAgent()
    def load(p): return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else {}

    if args.command == "course-design":
        agent.design_course(args.topic, load(args.audience))
    elif args.command == "engagement":
        agent.engagement_strategy(load(args.cohort))
    elif args.command == "assessment":
        agent.generate_assessment(load(args.content))
    elif args.command == "learning-path":
        cat = load(args.catalog)
        agent.personalized_learning_path(load(args.learner), cat if isinstance(cat, list) else [])
    elif args.command == "edtech-metrics":
        agent.edtech_metrics(load(args.data))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
