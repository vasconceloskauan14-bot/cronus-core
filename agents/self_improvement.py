"""
Self-Improvement Agent — ULTIMATE CRONUS
Auto-evolução: analisa performance dos agentes, detecta falhas e propõe melhorias.

Uso:
    python self_improvement.py audit --logs agents/logs/ --days 7
    python self_improvement.py optimize-prompt --agent "HUNTER" --task "qualify_lead"
    python self_improvement.py benchmark --agents all --dataset data/benchmark.json
    python self_improvement.py evolve --report data/audit_report.json
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from base_agent import BaseAgent

SYSTEM_SELF_IMPROVE = """Você é o agente de Auto-Evolução do ULTIMATE CRONUS.
Você analisa a performance do sistema, identifica padrões de falha e propõe melhorias sistêmicas.
Pense como um engenheiro de ML + produto que analisa friamente os dados e otimiza continuamente.
Seu objetivo: fazer o sistema melhorar a cada ciclo, tornando-se mais eficiente e preciso."""


class SelfImprovementAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="SELF_IMPROVE", output_dir="agents/output")

    def audit_performance(self, logs_dir: str, days: int = 7) -> dict:
        """Audita performance dos agentes nos últimos N dias."""
        self.logger.info(f"Auditing performance: {days} days from {logs_dir}")

        # Collect log data from output files
        logs_path = Path(logs_dir)
        recent_files = []
        cutoff = datetime.now() - timedelta(days=days)

        if logs_path.exists():
            for f in logs_path.glob("**/*.json"):
                if f.stat().st_mtime > cutoff.timestamp():
                    try:
                        recent_files.append({
                            "file": f.name,
                            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                            "size_bytes": f.stat().st_size
                        })
                    except Exception:
                        pass

        prompt = f"""Audite a performance do sistema ULTIMATE CRONUS:

PERÍODO: Últimos {days} dias
ARQUIVOS DE OUTPUT ENCONTRADOS: {len(recent_files)}
DETALHES:
{json.dumps(recent_files[:50], indent=2)[:3000]}

Retorne JSON com:
- resumo_auditoria:
  - total_execucoes: número estimado de execuções
  - agentes_ativos: quais agentes foram usados
  - volume_output_mb: volume de dados gerados
- analise_saude_sistema:
  - score_geral: 0-100
  - pontos_fortes: o que está funcionando bem
  - pontos_melhoria: o que pode ser otimizado
- gargalos_identificados: onde o sistema perde eficiência
- padroes_uso: quais agentes e funcionalidades são mais usados
- oportunidades_automacao: o que pode ser mais automatizado
- melhorias_priorizadas: lista ordenada de melhorias por impacto
- proxima_evolucao: próximos passos para evolução do sistema
- kpis_sistema: métricas para monitorar a saúde contínua"""

        result = self.ask_json(prompt, system=SYSTEM_SELF_IMPROVE)
        score = result.get("analise_saude_sistema", {}).get("score_geral", 0)
        print(f"\n🔍 System Audit — Score: {score}/100 | {len(recent_files)} arquivos analisados")
        melhorias = result.get("melhorias_priorizadas", [])
        if isinstance(melhorias, list):
            for i, m in enumerate(melhorias[:5], 1):
                print(f"  {i}. {str(m)[:80]}")
        self.save_result(result, prefix="system_audit")
        return result

    def optimize_prompt(self, agent_name: str, task: str) -> dict:
        """Otimiza o prompt de um agente para uma tarefa específica."""
        self.logger.info(f"Optimizing prompt: {agent_name}/{task}")
        prompt = f"""Otimize o prompt para o agente {agent_name} na tarefa: {task}

Gere variações otimizadas de prompt considerando:
- Clareza e especificidade das instruções
- Estrutura do output (JSON schema claro)
- Exemplos que guiam o comportamento
- Restrições que evitam erros comuns

Retorne JSON com:
- analise_prompt_atual: problemas potenciais em prompts genéricos para esta tarefa
- principios_otimizacao: o que torna um prompt excelente para este caso
- variacao_1:
  - prompt: texto do prompt otimizado
  - inovacao: o que muda em relação ao padrão
  - quando_usar: contextos ideais
- variacao_2:
  - prompt: texto alternativo
  - inovacao: abordagem diferente
  - quando_usar: contextos ideais
- few_shot_examples: 2-3 exemplos de input/output para few-shot
- instrucoes_sistema: system prompt otimizado para este agente
- metricas_avaliacao: como medir se o prompt melhorou
- a_b_test_plan: como testar qual variação é melhor"""

        result = self.ask_json(prompt, system=SYSTEM_SELF_IMPROVE)
        print(f"\n⚙️  Prompt Optimization — {agent_name}/{task}")
        print(f"  Variações geradas: {2}")
        self.save_result(result, prefix=f"prompt_opt_{agent_name.lower()}_{task.lower().replace(' ', '_')[:20]}")
        return result

    def benchmark_agents(self, agent_names: list, dataset: dict) -> dict:
        """Benchmarks múltiplos agentes em dataset padronizado."""
        self.logger.info(f"Benchmarking: {agent_names}")
        prompt = f"""Execute um benchmark sistemático dos agentes do ULTIMATE CRONUS:

AGENTES A AVALIAR: {', '.join(agent_names)}

DATASET DE BENCHMARK:
{json.dumps(dataset, indent=2, ensure_ascii=False)[:4000]}

Retorne JSON com:
- metodologia: como avaliar performance de agentes de IA
- criterios_avaliacao:
  - completude: 0-10 (o quanto o output é completo)
  - precisao: 0-10 (o quanto o output é correto/relevante)
  - formato: 0-10 (segue o schema esperado?)
  - utilidade: 0-10 (o output é acionável?)
  - velocidade: considerações sobre latência
- resultados_por_agente: para cada agente:
  - agente: nome
  - score_composto: 0-100
  - pontos_fortes: onde excele
  - pontos_fracos: onde erra
  - casos_de_borda: inputs que causam problemas
- ranking_geral: ordem do mais ao menos performante
- agente_mais_critico: qual agente mais impacta resultados gerais
- plano_melhoria: para cada agente no bottom 25%, o que melhorar
- sugestoes_novos_agentes: capacidades que o sistema ainda não tem"""

        result = self.ask_json(prompt, system=SYSTEM_SELF_IMPROVE)
        ranking = result.get("ranking_geral", [])
        print(f"\n📈 Agent Benchmark — {len(agent_names)} agentes")
        for i, a in enumerate(ranking[:5], 1):
            print(f"  {i}. {a}")
        self.save_result(result, prefix="agent_benchmark")
        return result

    def evolution_plan(self, audit_report: dict) -> dict:
        """Cria plano de evolução baseado em auditoria."""
        self.logger.info("Creating evolution plan")
        prompt = f"""Com base neste relatório de auditoria, crie um plano de evolução do sistema:

RELATÓRIO DE AUDITORIA:
{json.dumps(audit_report, indent=2, ensure_ascii=False)[:4000]}

Retorne JSON com:
- visao_sistema_ideal: como o ULTIMATE CRONUS deveria estar em 6 meses
- gap_atual_vs_ideal: o que está faltando
- roadmap_evolucao:
  - sprint_1_semanas_1_2: melhorias rápidas (quick wins)
  - sprint_2_semanas_3_4: melhorias de médio impacto
  - sprint_3_mes_2: features novas
  - mes_3_6: evolução estrutural
- novos_agentes_necessarios: que novos agentes o sistema deveria ter
- integracoes_prioritarias: novas integrações de alto valor
- arquitetura_proposta: mudanças na arquitetura do sistema
- metricas_evolucao: como medir progresso da evolução
- recursos_necessarios: o que é preciso para executar
- quick_wins: o que pode implementar hoje que gera impacto imediato"""

        result = self.ask_json(prompt, system=SYSTEM_SELF_IMPROVE)
        visao = result.get("visao_sistema_ideal", "")
        quick_wins = result.get("quick_wins", [])
        print(f"\n🧬 Evolution Plan")
        print(f"  Visão: {str(visao)[:100]}")
        print(f"  Quick wins: {len(quick_wins) if isinstance(quick_wins, list) else '?'}")
        self.save_result(result, prefix="evolution_plan")
        return result

    def generate_improvement_code(self, improvement: str, context: dict) -> dict:
        """Gera código de melhoria para o próprio sistema."""
        self.logger.info(f"Generating improvement: {improvement[:50]}")
        prompt = f"""Gere o código Python para implementar esta melhoria no ULTIMATE CRONUS:

MELHORIA: {improvement}

CONTEXTO DO SISTEMA:
{json.dumps(context, indent=2, ensure_ascii=False)[:2000]}

Retorne JSON com:
- descricao_melhoria: o que esta melhoria resolve
- arquivos_afetados: quais arquivos modificar ou criar
- codigo_implementacao: código Python completo e funcional
- instrucoes_instalacao: como integrar ao sistema
- testes_recomendados: como testar a melhoria
- rollback: como desfazer se necessário
- impacto_esperado: o que melhora com esta implementação"""

        result = self.ask_json(prompt, system=SYSTEM_SELF_IMPROVE)
        print(f"\n🔧 Improvement Code — {improvement[:50]}")
        arquivos = result.get("arquivos_afetados", [])
        print(f"  Arquivos: {arquivos}")
        self.save_result(result, prefix="improvement_code")
        return result


def main():
    parser = argparse.ArgumentParser(description="Self-Improvement Agent — ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")

    p_audit = sub.add_parser("audit")
    p_audit.add_argument("--logs", default="agents/output")
    p_audit.add_argument("--days", type=int, default=7)

    p_opt = sub.add_parser("optimize-prompt")
    p_opt.add_argument("--agent", required=True)
    p_opt.add_argument("--task", required=True)

    p_bm = sub.add_parser("benchmark")
    p_bm.add_argument("--agents", default="all")
    p_bm.add_argument("--dataset", required=True)

    sub.add_parser("evolve").add_argument("--report", required=True)

    args = parser.parse_args()
    agent = SelfImprovementAgent()
    def load(p): return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else {}

    if args.command == "audit":
        agent.audit_performance(args.logs, args.days)
    elif args.command == "optimize-prompt":
        agent.optimize_prompt(args.agent, args.task)
    elif args.command == "benchmark":
        agent_list = ["SWARM", "RADAR", "HUNTER", "ANALYST", "SCRIBE", "CEO", "CAPITAL"] if args.agents == "all" else args.agents.split(",")
        agent.benchmark_agents(agent_list, load(args.dataset))
    elif args.command == "evolve":
        agent.evolution_plan(load(args.report))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
