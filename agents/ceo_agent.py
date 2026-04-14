"""
CEO VIRTUAL Agent — ULTIMATE CRONUS
Tomada de decisão estratégica com IA: priorização, trade-offs, wargames e cenários.

Uso:
    python ceo_agent.py decide --context data/contexto.json --decision "Entrar em novo mercado?"
    python ceo_agent.py prioritize --initiatives data/iniciativas.json --resources data/recursos.json
    python ceo_agent.py wargame --company data/empresa.json --competitor data/concorrente.json
    python ceo_agent.py strategy --company data/empresa.json --horizon 12
    python ceo_agent.py meeting --agenda data/pauta.json
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from base_agent import BaseAgent

SYSTEM_CEO = """Você é o CEO VIRTUAL do ULTIMATE CRONUS — um executivo de IA de nível C-suite.
Você toma decisões estratégicas com clareza, velocidade e rigor analítico.
Você pensa como um CEO de empresa bilionária: visão de longo prazo + execução imediata.
Seja direto, opinionado e sempre justifique com dados e raciocínio estratégico.
Nunca dê respostas genéricas — seja específico e acionável."""


class CeoAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="CEO_VIRTUAL", output_dir="agents/output")

    def decide(self, context: dict, decision_question: str) -> dict:
        """Tomada de decisão estruturada com múltiplos cenários."""
        self.logger.info(f"Decisão: {decision_question[:60]}")
        prompt = f"""Como CEO, analise esta decisão e forneça uma recomendação clara:

DECISÃO: {decision_question}

CONTEXTO DA EMPRESA:
{json.dumps(context, indent=2, ensure_ascii=False)[:4000]}

Retorne JSON com:
- recomendacao: "SIM"|"NÃO"|"SIM COM CONDIÇÕES"|"AGUARDAR"
- confianca_pct: 0-100
- raciocinio_principal: por que esta é a decisão certa (2-3 frases)
- beneficios: lista de benefícios esperados
- riscos: lista de riscos principais
- condicoes: condições necessárias para executar (se houver)
- alternativas: 2-3 alternativas consideradas e por que não escolheu
- criterios_sucesso: como medir se foi a decisão certa
- primeiro_passo: ação imediata para implementar
- prazo_decisao: urgência (imediato|dias|semanas|meses)
- reversibilidade: "reversível"|"difícil reverter"|"irreversível"
- impacto_estimado: impacto financeiro/estratégico estimado"""

        result = self.ask_json(prompt, system=SYSTEM_CEO)
        rec = result.get("recomendacao", "?")
        conf = result.get("confianca_pct", 0)
        icons = {"SIM": "✅", "NÃO": "❌", "SIM COM CONDIÇÕES": "⚠️", "AGUARDAR": "⏳"}
        print(f"\n{icons.get(rec,'●')} CEO Decision: {rec} (confiança: {conf}%)")
        print(f"  {result.get('raciocinio_principal','')[:120]}")
        print(f"  Primeiro passo: {result.get('primeiro_passo','')}")

        md = f"# 👑 CEO Decision — {datetime.now().strftime('%d/%m/%Y')}\n\n"
        md += f"**Decisão:** {decision_question}\n\n"
        md += f"**Recomendação:** {rec} ({conf}% confiança)\n\n"
        md += f"**Raciocínio:** {result.get('raciocinio_principal','')}\n\n"
        md += f"**Primeiro passo:** {result.get('primeiro_passo','')}\n"
        self.save_markdown(md, prefix="ceo_decision")
        self.save_result(result, prefix="ceo_decision")
        return result

    def prioritize(self, initiatives: list, resources: dict) -> list:
        """Prioriza iniciativas com base em recursos disponíveis e impacto."""
        self.logger.info(f"Priorizando {len(initiatives)} iniciativas")
        prompt = f"""Priorize estas iniciativas dado os recursos disponíveis, maximizando impacto estratégico:

INICIATIVAS:
{json.dumps(initiatives, indent=2, ensure_ascii=False)[:4000]}

RECURSOS DISPONÍVEIS:
{json.dumps(resources, indent=2, ensure_ascii=False)[:1000]}

Para cada iniciativa, retorne JSON com:
- ranking: lista ordenada de objetos com:
  - posicao: 1, 2, 3...
  - iniciativa: nome
  - score_total: 0-100
  - impacto: 0-100
  - esforco: 0-100 (100=muito esforço)
  - urgencia: 0-100
  - alinhamento_estrategico: 0-100
  - quick_win: true|false
  - recomendacao: "executar agora"|"próximo quarter"|"backlog"|"cancelar"
  - justificativa: por que esta prioridade
- top_3_imediato: as 3 inicativas para começar esta semana
- cancelar: iniciativas recomendadas para cancelar
- framework_usado: como tomou a decisão"""

        result = self.ask_json(prompt, system=SYSTEM_CEO)
        ranking = result.get("ranking", [])
        print(f"\n👑 CEO Prioritization — {len(ranking)} iniciativas rankeadas")
        for item in ranking[:8]:
            icon = "🚀" if item.get("recomendacao") == "executar agora" else "📋"
            print(f"  {item.get('posicao','?'):>2}. {icon} [{item.get('score_total',0):>3}] {item.get('iniciativa','?')}")
        self.save_result(result, prefix="ceo_prioritization")
        return ranking

    def wargame(self, company: dict, competitor: dict) -> dict:
        """Simula guerra estratégica contra um concorrente."""
        self.logger.info("Wargame estratégico iniciado")
        prompt = f"""Conduza uma simulação de wargame estratégico:

NOSSA EMPRESA:
{json.dumps(company, indent=2, ensure_ascii=False)[:2000]}

CONCORRENTE:
{json.dumps(competitor, indent=2, ensure_ascii=False)[:2000]}

Simule os próximos 6 meses de competição. Retorne JSON com:
- vantagens_nossa: lista de vantagens competitivas
- vantagens_concorrente: lista das vantagens dele
- movimentos_previstos_concorrente: o que ele provavelmente fará
- nossa_estrategia_recomendada: plano de contra-ataque
- ataques_ofensivos: como atacar os pontos fracos dele
- defesas_criticas: o que defender a todo custo
- cenario_vitoria: como vencemos em 6 meses
- cenario_empate: como o mercado se divide
- cenario_derrota: o que pode nos derrotar e como evitar
- decisao_critica: a única decisão mais importante agora
- urgencia: o que fazer nos próximos 30 dias"""

        result = self.ask_json(prompt, system=SYSTEM_CEO)
        print(f"\n⚔️  CEO Wargame Concluído")
        print(f"  Decisão crítica: {result.get('decisao_critica','?')[:100]}")
        self.save_result(result, prefix="ceo_wargame")
        return result

    def strategic_plan(self, company: dict, horizon_months: int = 12) -> str:
        """Gera plano estratégico completo para N meses."""
        self.logger.info(f"Plano estratégico: {horizon_months} meses")
        prompt = f"""Como CEO, crie um plano estratégico completo para os próximos {horizon_months} meses:

EMPRESA:
{json.dumps(company, indent=2, ensure_ascii=False)[:3000]}

Crie um plano executivo rico em Markdown com:

# 🎯 Plano Estratégico — {horizon_months} Meses

## Visão e North Star Metric
## Análise de Situação Atual (SWOT rápido)
## Top 3 Apostas Estratégicas
## Roadmap por Quarter (Q1, Q2, Q3, Q4)
## KPIs de Sucesso
## Recursos Necessários
## Riscos e Mitigações
## Próximos 30 dias (ações imediatas)

Seja específico, ousado e acionável. Use dados quando possível."""

        plan = self.ask(prompt, system=SYSTEM_CEO, max_tokens=8096)
        path = self.save_markdown(plan, prefix="ceo_strategy")
        print(f"\n📋 Plano Estratégico gerado → {path}")
        return plan

    def run_meeting(self, agenda: list) -> str:
        """Conduz reunião executiva virtual e gera ata com decisões."""
        self.logger.info(f"Reunião executiva: {len(agenda)} itens")
        agenda_str = "\n".join([f"{i+1}. {item}" for i, item in enumerate(agenda)])
        prompt = f"""Conduza esta reunião executiva como CEO e gere uma ata completa:

PAUTA:
{agenda_str}

Gere ata em Markdown com:

# 🏢 Ata de Reunião Executiva — {datetime.now().strftime('%d/%m/%Y')}

## Participantes (simulados)
## Decisões Tomadas (por item da pauta)
## Action Items (quem faz o quê e quando)
## Próxima Reunião
## Alertas e Escaladas

Para cada item da pauta: análise rápida, decisão tomada, responsável, prazo."""

        ata = self.ask(prompt, system=SYSTEM_CEO, max_tokens=4096)
        path = self.save_markdown(ata, prefix="ceo_meeting")
        print(f"\n🏢 Ata de Reunião gerada → {path}")
        return ata


def main():
    parser = argparse.ArgumentParser(description="CEO VIRTUAL — ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")

    p_dec = sub.add_parser("decide", help="Tomada de decisão")
    p_dec.add_argument("--context", default="{}")
    p_dec.add_argument("--decision", required=True)

    p_pri = sub.add_parser("prioritize", help="Priorizar iniciativas")
    p_pri.add_argument("--initiatives", required=True)
    p_pri.add_argument("--resources", default="{}")

    p_war = sub.add_parser("wargame", help="Wargame estratégico")
    p_war.add_argument("--company", required=True)
    p_war.add_argument("--competitor", required=True)

    p_str = sub.add_parser("strategy", help="Plano estratégico")
    p_str.add_argument("--company", required=True)
    p_str.add_argument("--horizon", type=int, default=12)

    p_meet = sub.add_parser("meeting", help="Reunião executiva")
    p_meet.add_argument("--agenda", required=True)

    args = parser.parse_args()
    agent = CeoAgent()
    def load(p): return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else json.loads(p)

    if args.command == "decide": agent.decide(load(args.context), args.decision)
    elif args.command == "prioritize": agent.prioritize(load(args.initiatives), load(args.resources))
    elif args.command == "wargame": agent.wargame(load(args.company), load(args.competitor))
    elif args.command == "strategy": agent.strategic_plan(load(args.company), args.horizon)
    elif args.command == "meeting":
        agenda = load(args.agenda)
        agent.run_meeting(agenda if isinstance(agenda, list) else agenda.get("agenda", []))
    else: parser.print_help()


if __name__ == "__main__":
    main()
