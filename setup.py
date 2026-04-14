"""
Setup — ULTIMATE CRONUS
Configura o ambiente completo do sistema em um comando.

Uso:
    python setup.py
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent
REQUIRED_DIRS = [
    "agents/logs", "agents/output/scribe", "agents/missions",
    "agents/state", "agents/results",
    "automation/reports/daily", "automation/reports/weekly",
    "automation/data", "automation/config",
    "integrations", "config", "output", "data", "state",
    ".claude/memory",
]

def check(label: str, ok: bool, fix: str = ""):
    icon = "✅" if ok else "❌"
    print(f"  {icon} {label}")
    if not ok and fix:
        print(f"     → {fix}")
    return ok


def run(cmd: str) -> tuple[bool, str]:
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r.returncode == 0, r.stdout + r.stderr


def main():
    print("\n🚀 ULTIMATE CRONUS — Setup\n")
    issues = []

    # 1. Python
    v = sys.version_info
    ok = v.major == 3 and v.minor >= 10
    if not check(f"Python {v.major}.{v.minor}", ok, "Instale Python 3.10+"):
        issues.append("python")

    # 2. pip packages
    print("\n📦 Instalando dependências Python...")
    ok, out = run(f"{sys.executable} -m pip install -r requirements.txt -q")
    check("requirements.txt instalado", ok, "Rode: pip install -r requirements.txt")
    if not ok:
        issues.append("pip")

    # 3. Pastas
    print("\n📁 Criando estrutura de pastas...")
    for d in REQUIRED_DIRS:
        path = BASE / d
        path.mkdir(parents=True, exist_ok=True)
    check("Estrutura de pastas", True)

    # 4. .env
    print("\n🔐 Verificando variáveis de ambiente...")
    env_file = BASE / ".env"
    if not env_file.exists():
        shutil.copy(BASE / ".env.example", env_file)
        print("  📋 .env criado a partir do .env.example — preencha os valores!")
    ok = bool(os.environ.get("ANTHROPIC_API_KEY") or (env_file.exists() and "sk-ant" in env_file.read_text()))
    check("ANTHROPIC_API_KEY configurado", ok, "Adicione sua API key no arquivo .env")
    if not ok:
        issues.append("api_key")

    # 5. Node / npx (para MCP servers)
    print("\n🟩 Verificando Node.js (para MCP servers)...")
    ok, _ = run("node --version")
    check("Node.js instalado", ok, "Instale em: https://nodejs.org")

    ok, _ = run("npx --version")
    check("npx disponível", ok, "Instale Node.js")

    # 6. Teste da API Anthropic
    print("\n🤖 Testando conexão com Claude API...")
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key and env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                api_key = line.split("=", 1)[1].strip()
                break

    if api_key and not api_key.startswith("sk-ant-..."):
        test_code = (
            "import anthropic; c=anthropic.Anthropic(); "
            "r=c.messages.create(model='claude-haiku-4-5-20251001',max_tokens=10,messages=[{'role':'user','content':'ok'}]); "
            "print('ok')"
        )
        env = {**os.environ, "ANTHROPIC_API_KEY": api_key}
        r = subprocess.run([sys.executable, "-c", test_code], capture_output=True, text=True, env=env, timeout=15)
        ok = "ok" in r.stdout
        check("Claude API respondendo", ok, "Verifique sua ANTHROPIC_API_KEY")
        if not ok:
            issues.append("claude_api")
    else:
        check("Claude API (não testado — configure .env primeiro)", False, "")

    # 7. Resumo
    print("\n" + "="*50)
    if not issues:
        print("✅ Setup completo! ULTIMATE CRONUS pronto para rodar.\n")
        print("  Próximos passos:")
        print("  1. python agents/orchestrator.py --mission agents/missions/revenue_growth.json")
        print("  2. python automation/cron_setup.py --install")
        print("  3. python automation/event_triggers.py --start\n")
    else:
        print(f"⚠️  Setup incompleto. {len(issues)} item(s) pendente(s): {', '.join(issues)}")
        print("  Resolva os itens ❌ acima e rode setup.py novamente.\n")


if __name__ == "__main__":
    main()
