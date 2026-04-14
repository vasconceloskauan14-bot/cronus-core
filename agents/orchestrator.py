"""
Orchestrator — ULTIMATE CRONUS
Coordena múltiplos agentes em missões complexas com execução paralela.

Uso:
    python orchestrator.py --mission missions/revenue_growth.json
    python orchestrator.py --mission missions/market_research.json
    python orchestrator.py --list-agents
"""

import argparse
import json
import logging
import sys
import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).parent))
from base_agent import BaseAgent

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / f"orchestrator_{datetime.now().strftime('%Y%m%d')}.log",
    level=logging.INFO,
    format='{"time":"%(asctime)s","component":"orchestrator","level":"%(levelname)s","msg":"%(message)s"}',
    datefmt="%Y-%m-%dT%H:%M:%S",
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger().addHandler(console)
logger = logging.getLogger("ORCHESTRATOR")


# ── Registry de agentes disponíveis ─────────────────────────────────────────

def _load_agent(agent_type: str) -> BaseAgent:
    """Importa e instancia um agente pelo tipo."""
    mapping = {
        "swarm":          ("swarm_agent",       "SwarmAgent"),
        "radar":          ("radar_agent",        "RadarAgent"),
        "hunter":         ("hunter_agent",       "HunterAgent"),
        "analyst":        ("analyst_agent",      "AnalystAgent"),
        "scribe":         ("scribe_agent",       "ScribeAgent"),
        "capital":        ("capital_agent",      "CapitalAgent"),
        "ceo":            ("ceo_agent",          "CeoAgent"),
        "funis":          ("funis_agent",        "FunisAgent"),
        "atendimento":    ("atendimento_agent",  "AtendimentoAgent"),
        "vision":         ("vision_agent",       "VisionAgent"),
        "global":         ("global_agent",       "GlobalAgent"),
        "innovation":     ("innovation_agent",   "InnovationAgent"),
        "moat":           ("moat_agent",         "MoatAgent"),
        "self_improve":   ("self_improvement",   "SelfImprovementAgent"),
        "knowledge_graph":("knowledge_graph",    "KnowledgeGraphAgent"),
    }
    # Also accept uppercase keys
    agent_lower = agent_type.lower()
    if agent_lower not in mapping:
        raise ValueError(f"Agente desconhecido: {agent_type}. Disponíveis: {list(mapping)}")
    module_name, class_name = mapping[agent_lower]
    module = __import__(module_name)
    cls = getattr(module, class_name)
    return cls()


# ── Orchestrator ─────────────────────────────────────────────────────────────

class Orchestrator:
    def __init__(self, max_workers: int = 6):
        self.max_workers = max_workers
        self.results: dict[str, Any] = {}
        self.errors: dict[str, str] = {}

    def run_mission(self, mission: dict) -> dict:
        """Executa missão completa conforme definição JSON."""
        name = mission.get("name", "Missão Sem Nome")
        objective = mission.get("objective", "")
        steps = mission.get("steps", [])

        logger.info(f"🚀 MISSÃO INICIADA: {name}")
        logger.info(f"   Objetivo: {objective}")
        logger.info(f"   Etapas: {len(steps)}")

        start_time = time.time()
        mission_log: list[dict] = []

        for i, step in enumerate(steps, 1):
            step_name = step.get("name", f"Etapa {i}")
            parallel = step.get("parallel", False)
            tasks = step.get("tasks", [])

            logger.info(f"\n📋 ETAPA {i}/{len(steps)}: {step_name} ({'paralela' if parallel else 'sequencial'})")

            if parallel:
                step_results = self._run_parallel(tasks)
            else:
                step_results = self._run_sequential(tasks)

            self.results.update(step_results)
            mission_log.append({"step": step_name, "results": step_results})

        elapsed = round(time.time() - start_time, 1)
        summary = self._generate_summary(name, objective, mission_log, elapsed)

        output = {
            "mission": name,
            "objective": objective,
            "status": "completed" if not self.errors else "completed_with_errors",
            "elapsed_seconds": elapsed,
            "results": self.results,
            "errors": self.errors,
            "summary": summary,
        }

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = Path("output") / f"mission_{ts}.json"
        out_path.parent.mkdir(exist_ok=True)
        out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

        logger.info(f"\n✅ MISSÃO CONCLUÍDA em {elapsed}s → {out_path}")
        return output

    def spawn_agents(self, agent_types: list[str], task: str) -> dict[str, Any]:
        """Spawna múltiplos agentes em paralelo para uma mesma tarefa genérica."""
        logger.info(f"Spawnando {len(agent_types)} agentes para: {task}")
        tasks = [{"agent": t, "method": "ask", "params": {"prompt": task}} for t in agent_types]
        return self._run_parallel(tasks)

    def route_task(self, task: str) -> str:
        """Decide qual agente é mais adequado para uma tarefa."""
        keywords = {
            "swarm":   ["pesquisa", "buscar", "encontrar", "listar", "mapear"],
            "radar":   ["monitorar", "acompanhar", "vigiar", "alerta", "mudança"],
            "hunter":  ["lead", "prospect", "cliente", "outreach", "contato"],
            "analyst": ["analisar", "dados", "métrica", "kpi", "relatório", "trend"],
            "scribe":  ["escrever", "copy", "conteúdo", "email", "post", "artigo"],
        }
        task_lower = task.lower()
        scores = {agent: sum(1 for kw in kws if kw in task_lower) for agent, kws in keywords.items()}
        best = max(scores, key=lambda k: scores[k])
        logger.info(f"Tarefa roteada para: {best} (score: {scores[best]})")
        return best

    # ── Execução interna ─────────────────────────────────────────────────────

    def _run_parallel(self, tasks: list[dict]) -> dict[str, Any]:
        results: dict[str, Any] = {}
        futures: dict[Future, str] = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for task in tasks:
                task_id = task.get("id", task.get("agent", "task"))
                future = executor.submit(self._execute_task, task)
                futures[future] = task_id

            for future in as_completed(futures):
                task_id = futures[future]
                try:
                    results[task_id] = future.result()
                    logger.info(f"  ✓ {task_id} concluído")
                except Exception as e:
                    self.errors[task_id] = str(e)
                    logger.error(f"  ✗ {task_id} falhou: {e}")

        return results

    def _run_sequential(self, tasks: list[dict]) -> dict[str, Any]:
        results: dict[str, Any] = {}
        for task in tasks:
            task_id = task.get("id", task.get("agent", "task"))
            try:
                results[task_id] = self._execute_task(task)
                logger.info(f"  ✓ {task_id} concluído")
            except Exception as e:
                self.errors[task_id] = str(e)
                logger.error(f"  ✗ {task_id} falhou: {e}")
        return results

    def _execute_task(self, task: dict) -> Any:
        """Executa uma task individual — chama método do agente ou função customizada."""
        agent_type = task.get("agent")
        method_name = task.get("method", "ask")
        params = task.get("params", {})
        raw_prompt = task.get("prompt")

        # Task direta com prompt
        if raw_prompt and not agent_type:
            agent = BaseAgent(name="inline")
            return agent.ask(raw_prompt)

        if not agent_type:
            raise ValueError("Task deve ter 'agent' ou 'prompt'")

        agent = _load_agent(agent_type)
        method: Callable = getattr(agent, method_name)
        return method(**params)

    def _generate_summary(self, name: str, objective: str, log: list, elapsed: float) -> str:
        """Usa Claude para gerar resumo executivo da missão."""
        try:
            agent = BaseAgent(name="orchestrator_summary")
            log_str = json.dumps(log, ensure_ascii=False, indent=2)[:4000]
            prompt = f"""Gere um resumo executivo em Markdown para esta missão de IA:

MISSÃO: {name}
OBJETIVO: {objective}
TEMPO: {elapsed}s
ERROS: {len(self.errors)}

LOG DE EXECUÇÃO:
{log_str}

Inclua: o que foi alcançado, principais resultados, próximos passos recomendados. Máximo 300 palavras."""
            return agent.ask(prompt)
        except Exception:
            return f"Missão '{name}' concluída em {elapsed}s."

    def list_agents(self):
        agents = {
            "swarm":          "Motor de Pesquisa Massiva — busca paralela em escala",
            "radar":          "Monitoramento Contínuo 24/7 — sinais de mercado",
            "hunter":         "Sistema de Prospecção — identificação e qualificação de leads",
            "analyst":        "Dados e Business Intelligence — análise e insights",
            "scribe":         "Geração de Conteúdo — copy, emails, posts, artigos em escala",
            "capital":        "CFO Virtual — finanças, runway, forecast, orçamento",
            "ceo":            "CEO Virtual — decisões estratégicas, wargames, OKRs",
            "funis":          "Funis de Conversão — otimização de funil e A/B tests",
            "atendimento":    "Customer Success — suporte, churn, retenção, onboarding",
            "vision":         "Brand Strategy — posicionamento, identidade, messaging",
            "global":         "Expansão Internacional — market entry, localização",
            "innovation":     "P&D e Inovação — ideação, experimentos, tech radar",
            "moat":           "Vantagem Competitiva — construção e defesa do moat",
            "self_improve":   "Auto-Evolução — auditoria e melhoria do próprio sistema",
            "knowledge_graph":"Grafo de Conhecimento — extração e consulta de insights",
        }
        print("\n🤖 AGENTES DISPONÍVEIS NO ULTIMATE CRONUS\n")
        for name, desc in agents.items():
            print(f"  {name:<18} — {desc}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Orchestrator — ULTIMATE CRONUS")
    parser.add_argument("--mission", help="Caminho para arquivo JSON de missão")
    parser.add_argument("--list-agents", action="store_true", help="Lista agentes disponíveis")
    parser.add_argument("--task", help="Tarefa rápida (sem arquivo de missão)")
    parser.add_argument("--agents", help="Agentes para tarefa rápida (ex: swarm,analyst)")
    parser.add_argument("--workers", type=int, default=6, help="Máximo de workers paralelos")

    args = parser.parse_args()
    orch = Orchestrator(max_workers=args.workers)

    if args.list_agents:
        orch.list_agents()
    elif args.mission:
        mission_path = Path(args.mission)
        if not mission_path.exists():
            print(f"❌ Arquivo não encontrado: {args.mission}")
            sys.exit(1)
        mission = json.loads(mission_path.read_text(encoding="utf-8"))
        orch.run_mission(mission)
    elif args.task:
        if args.agents:
            agent_list = [a.strip() for a in args.agents.split(",")]
        else:
            routed = orch.route_task(args.task)
            agent_list = [routed]
        results = orch.spawn_agents(agent_list, args.task)
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
