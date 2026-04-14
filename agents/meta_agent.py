"""
Meta Agent — ULTIMATE CRONUS
Agente que coordena outros agentes autonomamente.
Planeja, delega tarefas, consolida resultados — hierarquia real.
"""

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base_agent import BaseAgent
from agents.reasoning.chain_of_thought import ChainOfThought, ZeroShotCoT
from agents.reasoning.self_critique import SelfCritique


PLAN_SYSTEM = """Você é o META-AGENTE do ULTIMATE CRONUS — o coordenador central.
Seu papel: receber um objetivo de alto nível e criar um PLANO DE EXECUÇÃO.

Agentes disponíveis e suas especialidades:
- SWARM: pesquisa massiva e coleta de dados
- RADAR: monitoramento de mercado e concorrentes
- HUNTER: prospecção e qualificação de leads
- ANALYST: análise de dados e BI
- SCRIBE: criação de conteúdo e documentos
- CAPITAL: análise financeira e projeções
- CEO: decisão estratégica e priorização
- FUNIS: otimização de conversão
- ATENDIMENTO: customer success
- VISION: brand e identidade
- GLOBAL: expansão internacional
- INNOVATION: P&D e novos produtos
- MOAT: vantagem competitiva

Responda em JSON:
{
  "goal": "...",
  "steps": [
    {
      "step": 1,
      "agent": "NOME_AGENTE",
      "task": "descrição clara da tarefa",
      "depends_on": [],
      "parallel": true
    }
  ],
  "success_criteria": "como saber se o objetivo foi atingido"
}"""

CONSOLIDATE_SYSTEM = """Você é o META-AGENTE do ULTIMATE CRONUS — consolidador de resultados.
Receberá os outputs de múltiplos agentes e deve produzir:
1. Síntese executiva dos resultados
2. Insights principais e contradições encontradas
3. Próximas ações recomendadas
4. Score de sucesso (0-10) para o objetivo original

Seja direto, acionável e foque no que importa para o negócio."""


class MetaAgent(BaseAgent):
    """
    Agente de coordenação: planeja e delega para sub-agentes.
    """

    MODEL = "claude-opus-4-6"

    def __init__(self, max_workers: int = 4):
        super().__init__("META", provider="anthropic")
        self.max_workers = max_workers
        self._agent_cache: dict = {}

    # ── Planejamento ─────────────────────────────────────────────────────

    def plan(self, goal: str, context: str = "") -> dict:
        """
        Cria plano de execução para um objetivo de alto nível.
        Retorna estrutura JSON com steps, agentes e dependências.
        """
        self.logger.info(f"Planejando: {goal[:80]}")

        ctx_text = f"\nContexto adicional:\n{context}" if context else ""
        prompt = (
            f"Objetivo: {goal}{ctx_text}\n\n"
            "Crie um plano de execução detalhado usando os agentes disponíveis. "
            "Priorize paralelismo onde possível. Máximo 6 steps."
        )

        plan = self.ask_json(prompt, system=PLAN_SYSTEM)
        self.save_state({"last_plan": plan, "last_goal": goal})
        return plan

    def plan_with_cot(self, goal: str, context: str = "") -> dict:
        """
        Planejamento com Chain-of-Thought para objetivos complexos.
        """
        cot_prompt = ChainOfThought.build_prompt(
            question=f"Como alcançar este objetivo de negócio: {goal}",
            context=context,
            examples=ChainOfThought.few_shot_examples(),
        )
        reasoning = self.ask(cot_prompt)
        self.logger.info("Raciocínio CoT concluído")

        plan_prompt = (
            f"Objetivo: {goal}\n\n"
            f"Raciocínio estratégico:\n{reasoning}\n\n"
            "Baseado neste raciocínio, crie o plano de execução com agentes."
        )
        return self.ask_json(plan_prompt, system=PLAN_SYSTEM)

    # ── Execução ─────────────────────────────────────────────────────────

    def _get_agent(self, agent_name: str) -> BaseAgent | None:
        """Carrega agente do registry dinamicamente."""
        if agent_name in self._agent_cache:
            return self._agent_cache[agent_name]
        try:
            from agents import AGENT_REGISTRY
            cls = AGENT_REGISTRY.get(agent_name)
            if cls:
                agent = cls()
                self._agent_cache[agent_name] = agent
                return agent
        except Exception as e:
            self.logger.error(f"Erro ao carregar {agent_name}: {e}")
        return None

    def execute_step(self, step: dict, previous_results: dict) -> dict:
        """
        Executa um step do plano.
        Injeta resultados anteriores como contexto quando há dependências.
        """
        agent_name = step.get("agent", "")
        task = step.get("task", "")
        depends_on = step.get("depends_on", [])

        # Montar contexto de dependências
        context_parts = []
        for dep in depends_on:
            dep_key = f"step_{dep}"
            if dep_key in previous_results:
                dep_result = previous_results[dep_key]
                context_parts.append(f"[Resultado do Step {dep} — {dep_result.get('agent', '')}]\n{dep_result.get('output', '')[:1000]}")

        context = "\n\n".join(context_parts)
        full_task = f"{task}\n\nContexto de steps anteriores:\n{context}" if context else task

        t0 = time.time()
        agent = self._get_agent(agent_name)

        if agent:
            try:
                output = agent.ask(
                    full_task,
                    system=f"Você é o agente {agent_name} do ULTIMATE CRONUS. Execute a tarefa com precisão.",
                )
                success = True
            except Exception as e:
                output = f"Erro: {e}"
                success = False
        else:
            # Fallback: executa via próprio LLM com persona do agente
            self.logger.warning(f"Agente {agent_name} não disponível — usando fallback")
            output = self.ask(
                full_task,
                system=f"Você é o agente {agent_name} do ULTIMATE CRONUS. Execute a tarefa.",
            )
            success = True

        return {
            "step": step.get("step", 0),
            "agent": agent_name,
            "task": task,
            "output": output,
            "success": success,
            "duration_s": round(time.time() - t0, 2),
        }

    def execute_plan(self, plan: dict) -> dict:
        """
        Executa um plano respeitando dependências e paralelismo.
        """
        steps = plan.get("steps", [])
        results: dict = {}
        all_results: list = []

        # Agrupar steps por nível (baseado em depends_on)
        def get_level(step):
            deps = step.get("depends_on", [])
            if not deps:
                return 0
            return max(deps) if deps else 0

        levels: dict[int, list] = {}
        for step in steps:
            lvl = get_level(step)
            levels.setdefault(lvl, []).append(step)

        # Executar nível por nível
        for lvl in sorted(levels.keys()):
            level_steps = levels[lvl]
            parallel_steps = [s for s in level_steps if s.get("parallel", True)]
            sequential_steps = [s for s in level_steps if not s.get("parallel", True)]

            # Paralelos
            if parallel_steps:
                with ThreadPoolExecutor(max_workers=min(self.max_workers, len(parallel_steps))) as ex:
                    futures = {ex.submit(self.execute_step, s, results): s for s in parallel_steps}
                    for future in as_completed(futures):
                        result = future.result()
                        results[f"step_{result['step']}"] = result
                        all_results.append(result)

            # Sequenciais
            for step in sequential_steps:
                result = self.execute_step(step, results)
                results[f"step_{result['step']}"] = result
                all_results.append(result)

        return {"plan": plan, "results": all_results}

    # ── Consolidação ─────────────────────────────────────────────────────

    def consolidate(self, goal: str, execution: dict) -> str:
        """
        Consolida resultados de múltiplos agentes em síntese executiva.
        Aplica self-critique para garantir qualidade.
        """
        results = execution.get("results", [])
        results_text = "\n\n".join(
            f"[{r['agent']} — Step {r['step']}]\n{r['output'][:800]}"
            for r in results
        )

        prompt = (
            f"Objetivo original: {goal}\n\n"
            f"Resultados dos agentes:\n{results_text}\n\n"
            "Produza a síntese executiva consolidada."
        )

        synthesis = self.ask(prompt, system=CONSOLIDATE_SYSTEM)

        # Auto-critique
        critique_obj = SelfCritique()
        critique_prompt = critique_obj.build_critique_prompt(goal, synthesis)
        critique = self.ask(critique_prompt)

        improve_prompt = critique_obj.build_improve_prompt(goal, synthesis, critique)
        final = self.ask(improve_prompt)

        return final

    # ── Run completo ─────────────────────────────────────────────────────

    def run(self, goal: str, context: str = "", use_cot: bool = False,
            save: bool = True) -> dict:
        """
        Pipeline completo: planejar → executar → consolidar.
        """
        self.logger.info(f"META-RUN: {goal[:80]}")
        t0 = time.time()

        # 1. Planejar
        plan = self.plan_with_cot(goal, context) if use_cot else self.plan(goal, context)
        self.logger.info(f"Plano criado: {len(plan.get('steps', []))} steps")

        # 2. Executar
        execution = self.execute_plan(plan)

        # 3. Consolidar
        synthesis = self.consolidate(goal, execution)

        result = {
            "goal": goal,
            "plan": plan,
            "execution": execution,
            "synthesis": synthesis,
            "total_duration_s": round(time.time() - t0, 2),
            "steps_executed": len(execution.get("results", [])),
            "success_rate": sum(
                1 for r in execution.get("results", []) if r.get("success")
            ) / max(1, len(execution.get("results", []))),
        }

        if save:
            self.save_result(result, prefix="meta_run")

        return result


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="META-AGENT — Coordenador autônomo")
    sub = parser.add_subparsers(dest="cmd")

    p_run = sub.add_parser("run", help="Executar objetivo completo")
    p_run.add_argument("goal", help="Objetivo de alto nível")
    p_run.add_argument("--context", default="", help="Contexto adicional")
    p_run.add_argument("--cot", action="store_true", help="Usar Chain-of-Thought no planejamento")
    p_run.add_argument("--no-save", action="store_true")

    p_plan = sub.add_parser("plan", help="Apenas planejar (sem executar)")
    p_plan.add_argument("goal")
    p_plan.add_argument("--context", default="")

    args = parser.parse_args()
    meta = MetaAgent()

    if args.cmd == "run":
        result = meta.run(args.goal, context=args.context, use_cot=args.cot, save=not args.no_save)
        print("\n" + "═" * 60)
        print("SÍNTESE EXECUTIVA")
        print("═" * 60)
        print(result["synthesis"])
        print(f"\nDuração total: {result['total_duration_s']}s")
        print(f"Steps executados: {result['steps_executed']}")
        print(f"Taxa de sucesso: {result['success_rate']:.0%}")

    elif args.cmd == "plan":
        plan = meta.plan(args.goal, context=args.context)
        print(json.dumps(plan, indent=2, ensure_ascii=False))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
