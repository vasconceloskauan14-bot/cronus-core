"""
ATENDIMENTO Agent — ULTIMATE CRONUS
Resposta autônoma a clientes: suporte, CS, retenção e churn prevention.

Uso:
    python atendimento_agent.py respond --ticket data/ticket.json
    python atendimento_agent.py churn-risk --customer data/cliente.json
    python atendimento_agent.py retention --at-risk data/clientes_risco.json
    python atendimento_agent.py onboarding --customer data/novo_cliente.json
    python atendimento_agent.py nps-follow --response data/nps.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from base_agent import BaseAgent

SYSTEM_ATENDIMENTO = """Você é o ATENDIMENTO, agente de Customer Success Autônomo do ULTIMATE CRONUS.
Você resolve problemas de clientes com empatia, velocidade e eficácia.
Seu objetivo: cliente satisfeito, problema resolvido, churn evitado.
Sempre seja humano, direto e ofereça soluções concretas."""


class AtendimentoAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="ATENDIMENTO", output_dir="agents/output")

    def respond_ticket(self, ticket: dict) -> dict:
        """Responde ticket de suporte com solução completa."""
        self.logger.info(f"Respondendo ticket: {ticket.get('titulo','?')[:50]}")
        prompt = f"""Responda este ticket de suporte como especialista em Customer Success:

TICKET:
{json.dumps(ticket, indent=2, ensure_ascii=False)[:3000]}

Retorne JSON com:
- categoria: "bug"|"dúvida"|"reclamação"|"feature_request"|"cobrança"|"cancelamento"
- prioridade: "baixa"|"média"|"alta"|"crítica"
- sentimento_cliente: "neutro"|"frustrado"|"muito_frustrado"|"satisfeito"
- solucao_imediata: o que fazer agora para resolver
- resposta_email: email completo de resposta (em português, tom humano e empático)
- passos_resolucao: lista de passos técnicos se necessário
- escalacao_necessaria: true|false
- para_quem_escalar: se escalar, para quem
- follow_up_24h: mensagem de follow-up em 24h
- risco_churn: "baixo"|"médio"|"alto"
- acao_preventiva: o que fazer para evitar que isso volte a acontecer
- tempo_resolucao_estimado: em horas"""

        result = self.ask_json(prompt, system=SYSTEM_ATENDIMENTO)
        prioridade = result.get("prioridade","?")
        icons = {"crítica":"🚨","alta":"🔴","média":"🟡","baixa":"🟢"}
        print(f"\n{icons.get(prioridade,'●')} Ticket [{prioridade.upper()}] — Churn risk: {result.get('risco_churn','?')}")
        print(f"  Categoria: {result.get('categoria','?')}")
        print(f"  Sentimento: {result.get('sentimento_cliente','?')}")
        self.save_result(result, prefix="ticket_response")
        return result

    def analyze_churn_risk(self, customer: dict) -> dict:
        """Analisa risco de churn de um cliente e gera plano de retenção."""
        self.logger.info(f"Análise de churn: {customer.get('nome','?')}")
        prompt = f"""Analise o risco de churn deste cliente e crie um plano de retenção:

CLIENTE:
{json.dumps(customer, indent=2, ensure_ascii=False)[:3000]}

Retorne JSON com:
- score_churn: 0-100 (100 = certeza de churn)
- nivel_risco: "baixo"|"médio"|"alto"|"crítico"
- sinais_detectados: lista de sinais de churn identificados
- causa_raiz_provavel: principal motivo do risco
- valor_em_risco: MRR em risco em R$
- plano_retencao:
  - acao_imediata: o que fazer nas próximas 24h
  - sequencia_contatos: lista de contatos com timing e mensagem
  - oferta_retencao: desconto ou benefício para oferecer se necessário
  - sucesso_esperado_pct: probabilidade de reter
- mensagem_personalizda: email/WhatsApp personalizado para este cliente
- se_nao_retido: plano B (downsell, pause, etc)"""

        result = self.ask_json(prompt, system=SYSTEM_ATENDIMENTO)
        score = result.get("score_churn",0)
        nivel = result.get("nivel_risco","?")
        icons = {"crítico":"🚨","alto":"🔴","médio":"🟡","baixo":"🟢"}
        print(f"\n{icons.get(nivel,'●')} Churn Risk: {score}/100 ({nivel.upper()})")
        print(f"  Causa: {result.get('causa_raiz_provavel','')[:80]}")
        self.save_result(result, prefix="churn_risk")
        return result

    def retention_campaign(self, at_risk_customers: list) -> dict:
        """Cria campanha de retenção para lista de clientes em risco."""
        self.logger.info(f"Campanha de retenção: {len(at_risk_customers)} clientes")
        prompt = f"""Crie uma campanha de retenção para estes clientes em risco de churn:

CLIENTES EM RISCO:
{json.dumps(at_risk_customers[:20], indent=2, ensure_ascii=False)[:4000]}

Retorne JSON com:
- segmentos: como segmentar estes clientes (por risco, produto, valor, etc)
- estrategia_geral: abordagem da campanha
- sequencias_por_segmento: para cada segmento:
  - segmento: nome
  - clientes: quantos
  - emails: lista de emails com timing e copy
  - ligacoes: quando ligar e script
  - ofertas: o que oferecer
- mrr_total_em_risco: soma do MRR em risco
- resultado_esperado: MRR retido esperado
- taxa_retencao_esperada_pct: % de clientes que vão ficar
- kpis_campanha: como medir sucesso"""

        result = self.ask_json(prompt, system=SYSTEM_ATENDIMENTO)
        print(f"\n🛟 Retention Campaign — {len(at_risk_customers)} clientes")
        print(f"  MRR em risco: R$ {result.get('mrr_total_em_risco',0):,.0f}")
        print(f"  Retenção esperada: {result.get('taxa_retencao_esperada_pct','?')}%")
        self.save_result(result, prefix="retention_campaign")
        return result

    def onboarding_plan(self, customer: dict) -> dict:
        """Cria plano de onboarding personalizado para novo cliente."""
        self.logger.info(f"Onboarding: {customer.get('nome','?')}")
        prompt = f"""Crie um plano de onboarding personalizado para este novo cliente:

CLIENTE:
{json.dumps(customer, indent=2, ensure_ascii=False)[:3000]}

Retorne JSON com:
- objetivo_onboarding: o que o cliente precisa alcançar para ter sucesso
- tempo_estimado_dias: duração do onboarding
- marcos: lista de milestones com:
  - dia: dia do onboarding
  - marco: o que deve ser alcançado
  - acao_cliente: o que o cliente faz
  - acao_cs: o que o CS/sistema faz
  - validacao: como confirmar que foi alcançado
- emails_onboarding: sequência de emails (dia, assunto, corpo resumido)
- riscos_onboarding: o que pode dar errado e como prevenir
- definicao_sucesso: quando o onboarding está completo
- proximo_check_in: quando fazer o primeiro check-in de saúde"""

        result = self.ask_json(prompt, system=SYSTEM_ATENDIMENTO)
        marcos = result.get("marcos",[])
        print(f"\n🚀 Onboarding Plan — {len(marcos)} marcos em {result.get('tempo_estimado_dias','?')} dias")
        for m in marcos[:5]:
            print(f"  Dia {m.get('dia','?'):>2}: {m.get('marco','?')}")
        self.save_result(result, prefix="onboarding_plan")
        return result

    def nps_follow_up(self, nps_response: dict) -> dict:
        """Gera follow-up personalizado baseado na resposta de NPS."""
        score = nps_response.get("score", 5)
        tipo = "promoter" if score >= 9 else "passive" if score >= 7 else "detractor"
        self.logger.info(f"NPS follow-up: score={score} ({tipo})")
        prompt = f"""Gere um follow-up personalizado para esta resposta de NPS:

NPS RESPONSE:
{json.dumps(nps_response, indent=2, ensure_ascii=False)[:2000]}

Tipo: {tipo} (score: {score}/10)

Retorne JSON com:
- tipo: "{tipo}"
- acao_imediata: o que fazer nas próximas 2h
- mensagem_followup: mensagem personalizada de resposta
- se_promoter: como transformar em referência/case/review
- se_passive: como elevar para promoter
- se_detractor: como resolver o problema e evitar churn
- oferta_especial: se aplicável
- prazo_resolucao: quando resolver completamente
- aprendizado: insight para melhorar o produto/serviço"""

        result = self.ask_json(prompt, system=SYSTEM_ATENDIMENTO)
        print(f"\n⭐ NPS Follow-up — {tipo.upper()} (score: {score})")
        print(f"  Ação: {result.get('acao_imediata','')[:80]}")
        self.save_result(result, prefix="nps_followup")
        return result


def main():
    parser = argparse.ArgumentParser(description="ATENDIMENTO — Customer Success ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("respond").add_argument("--ticket", required=True)
    sub.add_parser("churn-risk").add_argument("--customer", required=True)
    sub.add_parser("retention").add_argument("--at-risk", required=True)
    sub.add_parser("onboarding").add_argument("--customer", required=True)
    sub.add_parser("nps-follow").add_argument("--response", required=True)

    args = parser.parse_args()
    agent = AtendimentoAgent()
    def load(p): return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else json.loads(p)

    if args.command == "respond": agent.respond_ticket(load(args.ticket))
    elif args.command == "churn-risk": agent.analyze_churn_risk(load(args.customer))
    elif args.command == "retention":
        data = load(args.at_risk); agent.retention_campaign(data if isinstance(data, list) else data.get("customers",[]))
    elif args.command == "onboarding": agent.onboarding_plan(load(args.customer))
    elif args.command == "nps-follow": agent.nps_follow_up(load(args.response))
    else: parser.print_help()


if __name__ == "__main__":
    main()
