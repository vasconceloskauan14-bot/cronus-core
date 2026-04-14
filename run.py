#!/usr/bin/env python3
"""
ULTIMATE CRONUS — Master Runner
Ponto de entrada único para todos os agentes e automações.

Uso:
    python run.py                          # Menu interativo
    python run.py agent SWARM "query"      # Rodar agente diretamente
    python run.py mission revenue_growth   # Executar missão
    python run.py auto daily               # Executar automação
    python run.py status                   # Status do sistema
    python run.py list                     # Listar todos os agentes

No Windows desta máquina, também funciona via:
    .\run.ps1 auto obsidian expand
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent

# ── REGISTRY COMPLETO ─────────────────────────────────────────────────────────

AGENTS = {
    # Core
    "SWARM":          ("agents/swarm_agent.py",              "SwarmAgent"),
    "RADAR":          ("agents/radar_agent.py",              "RadarAgent"),
    "HUNTER":         ("agents/hunter_agent.py",             "HunterAgent"),
    "ANALYST":        ("agents/analyst_agent.py",            "AnalystAgent"),
    "SCRIBE":         ("agents/scribe_agent.py",             "ScribeAgent"),
    "CAPITAL":        ("agents/capital_agent.py",            "CapitalAgent"),
    "CEO":            ("agents/ceo_agent.py",                "CeoAgent"),
    "FUNIS":          ("agents/funis_agent.py",              "FunisAgent"),
    "ATENDIMENTO":    ("agents/atendimento_agent.py",        "AtendimentoAgent"),
    # Strategy
    "VISION":         ("agents/vision_agent.py",             "VisionAgent"),
    "GLOBAL":         ("agents/global_agent.py",             "GlobalAgent"),
    "INNOVATION":     ("agents/innovation_agent.py",         "InnovationAgent"),
    "MOAT":           ("agents/moat_agent.py",               "MoatAgent"),
    # Intelligence
    "SELF_IMPROVE":   ("agents/self_improvement.py",         "SelfImprovementAgent"),
    "KNOWLEDGE_GRAPH":("agents/knowledge_graph.py",          "KnowledgeGraphAgent"),
    "ROUTER":         ("agents/router_agent.py",             "RouterAgent"),
    # Sectors
    "SAAS":           ("agents/sectors/saas_agent.py",       "SaasAgent"),
    "ECOMMERCE":      ("agents/sectors/ecommerce_agent.py",  "EcommerceAgent"),
    "HEALTH":         ("agents/sectors/health_agent.py",     "HealthAgent"),
    "REALESTATE":     ("agents/sectors/realestate_agent.py", "RealEstateAgent"),
    "LEGAL":          ("agents/sectors/legal_agent.py",      "LegalAgent"),
    "EDUCATION":      ("agents/sectors/education_agent.py",  "EducationAgent"),
    "FINTECH":        ("agents/sectors/fintech_agent.py",    "FintechAgent"),
    "LOGISTICS":      ("agents/sectors/logistics_agent.py",  "LogisticsAgent"),
    "RESTAURANT":     ("agents/sectors/restaurant_agent.py", "RestaurantAgent"),
    "AGRO":           ("agents/sectors/agro_agent.py",       "AgroAgent"),
}

AUTOMATIONS = {
    "daily":       "automation/daily_report.py",
    "weekly":      "automation/weekly_kpis.py",
    "obsidian-ai": "automation/obsidian_memory_ai.py",
    "zeus-companion": "automation/zeus_companion.py",
    "obsidian-calendar": "automation/obsidian_calendar_worker.py",
    "obsidian-radar": "automation/obsidian_radar_worker.py",
    "obsidian-synthesis": "automation/obsidian_synthesis_worker.py",
    "obsidian-news": "automation/obsidian_news_worker.py",
    "crm":         "automation/crm_automation.py",
    "content":     "automation/content_factory.py",
    "hr":          "automation/hr_automation.py",
    "finance":     "automation/financial_ops.py",
    "marketing":   "automation/marketing_automation.py",
    "social":      "automation/social_media.py",
    "competitor":  "automation/competitor_intelligence.py",
    "observe":     "automation/observability.py",
    "email":       "automation/email_automation.py",
    "seo":         "automation/seo_automation.py",
    "product":     "automation/product_analytics.py",
    "events":      "automation/event_triggers.py",
    "cron":        "automation/cron_setup.py",
}

MISSIONS = {
    "revenue":    "agents/missions/revenue_growth.json",
    "market":     "agents/missions/market_research.json",
    "audit":      "agents/missions/full_business_audit.json",
    "saas":       "agents/missions/saas_growth.json",
    "ecommerce":  "agents/missions/ecommerce_boost.json",
    "global":     "agents/missions/global_expansion.json",
    "startup":    "agents/missions/startup_launch.json",
}

AGENT_DESCRIPTIONS = {
    "SWARM":          "🔍 Pesquisa massiva paralela (50+ fontes)",
    "RADAR":          "📡 Monitoramento de mercado 24/7",
    "HUNTER":         "🎯 Prospecção e qualificação de leads",
    "ANALYST":        "📊 Business Intelligence e análise de dados",
    "SCRIBE":         "✍️  Geração de conteúdo em escala",
    "CAPITAL":        "🏦 CFO Virtual — finanças e investimento",
    "CEO":            "👑 CEO Virtual — decisão estratégica",
    "FUNIS":          "🌊 Funis de conversão e A/B tests",
    "ATENDIMENTO":    "🤝 Customer Success autônomo",
    "VISION":         "🎨 Brand strategy e identidade visual",
    "GLOBAL":         "🌍 Expansão internacional",
    "INNOVATION":     "💡 P&D, experimentos, tech radar",
    "MOAT":           "🏰 Vantagem competitiva",
    "SELF_IMPROVE":   "🧬 Auto-evolução do sistema",
    "KNOWLEDGE_GRAPH":"🕸️  Grafo de conhecimento empresarial",
    "SAAS":           "💻 SaaS (MRR, NRR, churn, pricing)",
    "ECOMMERCE":      "🛒 E-commerce (conversão, cart recovery)",
    "HEALTH":         "🏥 Saúde digital e telemedicina",
    "REALESTATE":     "🏠 Mercado imobiliário",
    "LEGAL":          "⚖️  Jurídico e compliance",
    "EDUCATION":      "🎓 EdTech e design instrucional",
    "FINTECH":        "💳 Fintech, crédito e pagamentos",
    "LOGISTICS":      "🚚 Logística e supply chain",
    "RESTAURANT":     "🍽️  Restaurantes e food service",
    "AGRO":           "🌱 Agronegócio e commodities",
}


# ── UTILITIES ─────────────────────────────────────────────────────────────────

def _run(cmd: list[str], cwd: Path = ROOT) -> int:
    """Executa comando e retorna exit code."""
    import platform
    kwargs: dict = {"cwd": str(cwd)}
    if platform.system() == "Windows":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    result = subprocess.run(cmd, **kwargs)
    return result.returncode


def _check_env() -> bool:
    """Verifica se pelo menos um provider de IA está configurado."""
    providers = {
        "ANTHROPIC_API_KEY": "Anthropic",
        "OPENAI_API_KEY":    "OpenAI",
        "GROQ_API_KEY":      "Groq",
        "GOOGLE_API_KEY":    "Gemini",
        "TOGETHER_API_KEY":  "Together AI",
        "MISTRAL_API_KEY":   "Mistral",
        "DEEPSEEK_API_KEY":  "DeepSeek",
        "PERPLEXITY_API_KEY":"Perplexity",
    }
    for env in providers:
        if os.environ.get(env, ""):
            return True
    # Locais (Ollama/LM Studio) sempre OK
    cronus = os.environ.get("CRONUS_PROVIDER", "")
    if cronus in ("ollama", "lmstudio", "vllm"):
        return True
    print("⚠️  Nenhum provider de IA configurado.")
    print("   Configure pelo menos uma das variáveis:")
    for env in providers:
        print(f"     {env}")
    print("   Ou use Ollama local: CRONUS_PROVIDER=ollama")
    return False


def _load_dotenv():
    """Carrega .env se existir."""
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())


# ── COMMANDS ──────────────────────────────────────────────────────────────────

def cmd_list():
    """Lista todos os agentes disponíveis."""
    print("\n" + "═" * 60)
    print("    🤖 ULTIMATE CRONUS — AGENTES DISPONÍVEIS")
    print("═" * 60)

    print("\n── CORE AGENTS ─────────────────────────────────────────────")
    core = ["SWARM","RADAR","HUNTER","ANALYST","SCRIBE","CAPITAL","CEO","FUNIS","ATENDIMENTO"]
    for name in core:
        print(f"  {name:<18} {AGENT_DESCRIPTIONS.get(name,'')}")

    print("\n── STRATEGY AGENTS ─────────────────────────────────────────")
    strategy = ["VISION","GLOBAL","INNOVATION","MOAT"]
    for name in strategy:
        print(f"  {name:<18} {AGENT_DESCRIPTIONS.get(name,'')}")

    print("\n── INTELLIGENCE AGENTS ─────────────────────────────────────")
    intel = ["SELF_IMPROVE","KNOWLEDGE_GRAPH"]
    for name in intel:
        print(f"  {name:<18} {AGENT_DESCRIPTIONS.get(name,'')}")

    print("\n── SECTOR AGENTS ────────────────────────────────────────────")
    sectors = ["SAAS","ECOMMERCE","HEALTH","REALESTATE","LEGAL","EDUCATION","FINTECH","LOGISTICS"]
    for name in sectors:
        print(f"  {name:<18} {AGENT_DESCRIPTIONS.get(name,'')}")

    print("\n── AUTOMATIONS ──────────────────────────────────────────────")
    for name, path in AUTOMATIONS.items():
        print(f"  {name:<18} {path}")

    print("\n── MISSIONS ─────────────────────────────────────────────────")
    for name, path in MISSIONS.items():
        print(f"  {name:<18} {path}")

    print(f"\n  Total: {len(AGENTS)} agentes + {len(AUTOMATIONS)} automações + {len(MISSIONS)} missões")
    print("═" * 60 + "\n")


def cmd_status():
    """Verifica status do sistema."""
    print("\n🔭 ULTIMATE CRONUS — STATUS DO SISTEMA\n")

    # Check API key
    provider_keys = [
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "GROQ_API_KEY",
        "GOOGLE_API_KEY",
        "TOGETHER_API_KEY",
        "MISTRAL_API_KEY",
        "DEEPSEEK_API_KEY",
        "PERPLEXITY_API_KEY",
    ]
    key = next((os.environ.get(name, "") for name in provider_keys if os.environ.get(name, "")), "")
    local_provider = os.environ.get("CRONUS_PROVIDER", "") in ("ollama", "lmstudio", "vllm")
    api_ok = (key.startswith("sk-") if key else False) or local_provider
    print(f"  API Key:      {'✅ Configurada' if api_ok else '❌ Não configurada'}")

    # Check agent files
    total = 0
    missing = []
    for name, (path, _) in AGENTS.items():
        fp = ROOT / path
        if fp.exists():
            total += 1
        else:
            missing.append(name)
    print(f"  Agentes:      ✅ {total}/{len(AGENTS)} disponíveis" + (f" | ❌ Faltam: {missing}" if missing else ""))

    # Check automation files
    auto_ok = sum(1 for p in AUTOMATIONS.values() if (ROOT / p).exists())
    print(f"  Automações:   ✅ {auto_ok}/{len(AUTOMATIONS)} disponíveis")

    # Check output dirs
    for d in ["agents/output", "automation/reports", "agents/logs", "agents/state"]:
        dp = ROOT / d
        if dp.exists():
            files = list(dp.glob("*.*"))
            print(f"  {d:<25} {len(files)} arquivos")
        else:
            print(f"  {d:<25} ⚠️  Diretório não existe")

    # Check missions
    miss_ok = sum(1 for p in MISSIONS.values() if (ROOT / p).exists())
    print(f"  Missões:      ✅ {miss_ok}/{len(MISSIONS)} disponíveis")

    print()


def cmd_agent(agent_name: str, args_rest: list):
    """Executa um agente específico."""
    agent_name = agent_name.upper()
    if agent_name not in AGENTS:
        print(f"❌ Agente '{agent_name}' não encontrado.")
        print(f"   Agentes disponíveis: {', '.join(AGENTS.keys())}")
        return 1
    path, _ = AGENTS[agent_name]
    script = ROOT / path
    if not script.exists():
        print(f"❌ Script não encontrado: {path}")
        return 1
    return _run([sys.executable, str(script)] + args_rest)


def cmd_auto(automation_name: str, args_rest: list):
    """Executa uma automação."""
    if automation_name not in AUTOMATIONS:
        print(f"❌ Automação '{automation_name}' não encontrada.")
        print(f"   Disponíveis: {', '.join(AUTOMATIONS.keys())}")
        return 1
    script = ROOT / AUTOMATIONS[automation_name]
    if not script.exists():
        print(f"❌ Script não encontrado: {AUTOMATIONS[automation_name]}")
        return 1
    return _run([sys.executable, str(script)] + args_rest)


def cmd_mission(mission_name: str):
    """Executa uma missão no orchestrator."""
    if mission_name not in MISSIONS:
        print(f"❌ Missão '{mission_name}' não encontrada.")
        print(f"   Disponíveis: {', '.join(MISSIONS.keys())}")
        return 1
    mission_path = ROOT / MISSIONS[mission_name]
    orchestrator = ROOT / "agents" / "orchestrator.py"
    return _run([sys.executable, str(orchestrator), "--mission", str(mission_path)])


def cmd_interactive():
    """Menu interativo."""
    print("\n" + "═" * 50)
    print("  🤖 ULTIMATE CRONUS")
    print("═" * 50)
    print("  1. Listar agentes")
    print("  2. Rodar agente")
    print("  3. Executar missão")
    print("  4. Executar automação")
    print("  5. Status do sistema")
    print("  6. Sair")
    print("═" * 50)

    choice = input("\nEscolha: ").strip()

    if choice == "1":
        cmd_list()
    elif choice == "2":
        agent = input("Nome do agente (ex: SWARM): ").strip().upper()
        extra = input("Argumentos (ex: --help): ").strip().split()
        cmd_agent(agent, extra)
    elif choice == "3":
        print(f"Missões: {', '.join(MISSIONS.keys())}")
        mission = input("Nome da missão: ").strip().lower()
        cmd_mission(mission)
    elif choice == "4":
        print(f"Automações: {', '.join(AUTOMATIONS.keys())}")
        auto = input("Nome da automação: ").strip().lower()
        extra = input("Argumentos (ex: --help): ").strip().split()
        cmd_auto(auto, extra)
    elif choice == "5":
        cmd_status()
    elif choice == "6":
        print("Até logo! 🚀")
    else:
        print("Opção inválida.")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    _load_dotenv()

    parser = argparse.ArgumentParser(
        description="ULTIMATE CRONUS — Master Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python run.py list
  python run.py status
  python run.py agent SWARM --help
  python run.py agent HUNTER pipeline --icp data/icp.json --limit 20
  python run.py mission revenue
  python run.py auto daily
  python run.py auto obsidian-ai
  python run.py auto zeus-companion
  python run.py auto obsidian-calendar
  python run.py auto obsidian-radar --once
  python run.py auto social calendar --brand data/marca.json --month "Abril 2026"
        """
    )
    parser.add_argument("command", nargs="?", choices=["list","status","agent","mission","auto"],
                        help="Comando a executar")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Argumentos do comando")

    args = parser.parse_args()

    if not args.command:
        cmd_interactive()
        return

    if args.command == "list":
        cmd_list()
    elif args.command == "status":
        cmd_status()
    elif args.command == "agent":
        if not args.args:
            print("❌ Especifique o nome do agente. Ex: python run.py agent SWARM --help")
            return
        if not _check_env():
            return
        cmd_agent(args.args[0], args.args[1:])
    elif args.command == "auto":
        if not args.args:
            print("❌ Especifique a automação. Ex: python run.py auto daily")
            return
        if args.args[0] not in ("obsidian-ai", "zeus-companion") and not _check_env():
            return
        cmd_auto(args.args[0], args.args[1:])
    elif args.command == "mission":
        if not args.args:
            print("❌ Especifique a missão. Ex: python run.py mission revenue")
            return
        if not _check_env():
            return
        cmd_mission(args.args[0])


if __name__ == "__main__":
    main()
