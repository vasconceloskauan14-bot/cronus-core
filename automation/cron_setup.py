"""
Cron Setup — ULTIMATE CRONUS
Configura todas as automações agendadas (Windows Task Scheduler ou crontab Linux/Mac).

Uso:
    python cron_setup.py --install    # instala todos os schedules
    python cron_setup.py --uninstall  # remove todos os schedules
    python cron_setup.py --list       # lista schedules configurados
    python cron_setup.py --test       # testa execução imediata de cada script
"""

import argparse
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.resolve()
AUTO_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = AUTO_DIR / "config" / "schedule.json"

SCHEDULES = [
    {
        "name": "CRONUS_DailyReport",
        "description": "Relatório executivo diário do ULTIMATE CRONUS",
        "script": str(AUTO_DIR / "daily_report.py"),
        "schedule_win": "/SC DAILY /ST 08:00",
        "cron_linux": "0 8 * * *",
        "enabled": True,
    },
    {
        "name": "CRONUS_WeeklyKPIs",
        "description": "Relatório semanal de KPIs",
        "script": str(AUTO_DIR / "weekly_kpis.py"),
        "schedule_win": "/SC WEEKLY /D MON /ST 09:00",
        "cron_linux": "0 9 * * 1",
        "enabled": True,
    },
    {
        "name": "CRONUS_RadarScan",
        "description": "RADAR — scan horário de mercado e concorrentes",
        "script": str(BASE_DIR / "agents" / "radar_agent.py"),
        "schedule_win": "/SC HOURLY /MO 1",
        "cron_linux": "0 * * * *",
        "enabled": True,
    },
    {
        "name": "CRONUS_SwarmTrends",
        "description": "SWARM — pesquisa de tendências a cada 4 horas",
        "script": str(BASE_DIR / "agents" / "swarm_agent.py"),
        "schedule_win": "/SC HOURLY /MO 4",
        "cron_linux": "0 */4 * * *",
        "enabled": False,  # desabilitado por padrão (custo de API)
    },
]


def install_windows():
    python = sys.executable
    installed = []
    failed = []

    for s in SCHEDULES:
        if not s["enabled"]:
            print(f"  ⏭️  {s['name']} — desabilitado (skipped)")
            continue
        cmd = (
            f'schtasks /Create /TN "{s["name"]}" /TR "{python} {s["script"]}" '
            f'{s["schedule_win"]} /F /RL HIGHEST '
            f'/SD {_today_str()} /ED 12/31/2099'
        )
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ {s['name']} instalado")
            installed.append(s["name"])
        else:
            print(f"  ❌ {s['name']} falhou: {result.stderr.strip()}")
            failed.append(s["name"])

    print(f"\n  Instalados: {len(installed)} | Falhas: {len(failed)}")
    return len(failed) == 0


def uninstall_windows():
    for s in SCHEDULES:
        cmd = f'schtasks /Delete /TN "{s["name"]}" /F'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ {s['name']} removido")
        else:
            print(f"  ⚠️  {s['name']} não encontrado (já removido?)")


def list_windows():
    for s in SCHEDULES:
        cmd = f'schtasks /Query /TN "{s["name"]}" /FO LIST 2>nul'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        status = "✅ ATIVO" if result.returncode == 0 else "❌ NÃO INSTALADO"
        enabled = "habilitado" if s["enabled"] else "desabilitado"
        print(f"  {status}  {s['name']} ({enabled})")
        print(f"           {s['description']}")
        print(f"           Schedule: {s['schedule_win']}\n")


def install_unix():
    python = sys.executable
    new_crons = []
    for s in SCHEDULES:
        if not s["enabled"]:
            continue
        new_crons.append(f"{s['cron_linux']} {python} {s['script']}  # {s['name']}")

    # Lê crontab atual
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    current = result.stdout if result.returncode == 0 else ""

    # Remove entradas antigas do CRONUS
    lines = [l for l in current.splitlines() if "CRONUS_" not in l]
    lines.extend(new_crons)

    new_crontab = "\n".join(lines) + "\n"
    proc = subprocess.run(["crontab", "-"], input=new_crontab, text=True)
    if proc.returncode == 0:
        print(f"  ✅ {len(new_crons)} crons instalados")
    else:
        print("  ❌ Erro ao instalar crontab")


def uninstall_unix():
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    if result.returncode != 0:
        print("  Nenhum crontab encontrado")
        return
    lines = [l for l in result.stdout.splitlines() if "CRONUS_" not in l]
    subprocess.run(["crontab", "-"], input="\n".join(lines) + "\n", text=True)
    print("  ✅ Crons do ULTIMATE CRONUS removidos")


def test_scripts():
    python = sys.executable
    print("\n🧪 Testando scripts (execução rápida)...\n")
    for s in SCHEDULES:
        if not Path(s["script"]).exists():
            print(f"  ⚠️  {s['name']} — arquivo não encontrado: {s['script']}")
            continue
        result = subprocess.run([python, s["script"], "--help"], capture_output=True, text=True, timeout=10)
        ok = result.returncode == 0
        print(f"  {'✅' if ok else '❌'} {s['name']}")


def _today_str() -> str:
    from datetime import date
    return date.today().strftime("%m/%d/%Y")


def main():
    parser = argparse.ArgumentParser(description="Cron Setup — ULTIMATE CRONUS")
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--uninstall", action="store_true")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    is_windows = platform.system() == "Windows"

    print(f"\n⚙️  ULTIMATE CRONUS — Cron Setup ({platform.system()})\n")

    if args.install:
        print("📅 Instalando automações agendadas...\n")
        install_windows() if is_windows else install_unix()
    elif args.uninstall:
        print("🗑️  Removendo automações agendadas...\n")
        uninstall_windows() if is_windows else uninstall_unix()
    elif args.list:
        print("📋 Status das automações:\n")
        list_windows() if is_windows else print("  Use 'crontab -l | grep CRONUS' no Linux/Mac")
    elif args.test:
        test_scripts()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
