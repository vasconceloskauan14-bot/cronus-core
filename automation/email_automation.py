"""
Email Automation — ULTIMATE CRONUS
Sequências de email, nutrição de leads, reativação e deliverability.

Uso:
    python email_automation.py nurture --icp data/icp.json --product data/produto.json --steps 7
    python email_automation.py reactivate --inactive data/inativos.json
    python email_automation.py cold-outreach --leads data/leads.json --context data/contexto.json
    python email_automation.py deliverability --domain "meudominio.com.br"
    python email_automation.py ab-subject --topic "desconto 30%" --count 10
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))
from base_agent import BaseAgent

SYSTEM_EMAIL = """Você é o especialista em Email Marketing do ULTIMATE CRONUS.
Você domina copywriting de email, sequências de nutrição, deliverability e otimização de taxa de abertura.
Escreva como um copywriter direto ao ponto — sem floreios, máximo valor por linha.
Meta: open rate >30%, click rate >5%, conversão >2%."""


class EmailAutomation(BaseAgent):
    def __init__(self):
        super().__init__(name="EMAIL", output_dir="automation/reports")

    def nurture_sequence(self, icp: dict, product: dict, steps: int = 7) -> dict:
        """Cria sequência de nutrição de leads completa."""
        self.logger.info(f"Nurture sequence: {steps} emails")
        prompt = f"""Crie uma sequência de nutrição de {steps} emails para converter leads em clientes:

PERFIL DO LEAD (ICP):
{json.dumps(icp, indent=2, ensure_ascii=False)[:1500]}

PRODUTO/SERVIÇO:
{json.dumps(product, indent=2, ensure_ascii=False)[:1500]}

Para cada email retorne JSON com:
- sequencia: lista de {steps} emails com:
  - numero: posição na sequência
  - dia_envio: quantos dias após o primeiro contato
  - objetivo: o que este email deve alcançar
  - assunto: linha de assunto (máx 50 chars, curiosidade ou benefício)
  - pre_header: texto do preview (máx 90 chars)
  - abertura: primeira linha que prende (máx 20 palavras)
  - corpo: corpo completo do email (200-400 palavras)
  - cta: call to action principal
  - link_destino: para onde levar o lead
  - gatilho_mental: escassez|autoridade|prova_social|reciprocidade|etc
- logica_sequencia: por que essa ordem e timing
- segmentacao: como bifurcar a sequência (quem abriu vs quem não abriu)
- metricas_alvo: open rate, click rate e conversão esperados por email"""

        result = self.ask_json(prompt, system=SYSTEM_EMAIL)
        seq = result.get("sequencia", [])
        print(f"\n📧 Nurture Sequence — {len(seq)} emails gerados")
        for e in seq:
            print(f"  Dia {e.get('dia_envio','?'):>3} | {e.get('assunto','?')[:60]}")
        self.save_result(result, prefix="nurture_sequence")
        return result

    def reactivation_campaign(self, inactive: list) -> dict:
        """Cria campanha de reativação para leads/clientes inativos."""
        self.logger.info(f"Reactivation: {len(inactive)} inativos")
        prompt = f"""Crie uma campanha de reativação para {len(inactive)} contatos inativos:

CONTATOS INATIVOS (amostra):
{json.dumps(inactive[:10], indent=2, ensure_ascii=False)[:3000]}

Retorne JSON com:
- segmentacao_inativos:
  - inativos_60_dias: estratégia específica
  - inativos_90_dias: estratégia específica
  - inativos_180_dias: estratégia específica
  - mais_de_180_dias: estratégia de win-back ou limpeza de lista
- emails_reativacao: sequência de 3-5 emails com:
  - numero: posição
  - assunto: linha de assunto chamativa (urgência ou nostalgia)
  - corpo: email completo
  - oferta: incentivo específico para reativar
  - cta: próximo passo
- ultima_chance: email final antes de remover da lista
- limpeza_lista: critérios para remover contatos definitivamente
- taxa_reativacao_esperada_pct: % que deve responder
- valor_recuperado_estimado: R$ de receita potencial"""

        result = self.ask_json(prompt, system=SYSTEM_EMAIL)
        seg = result.get("segmentacao_inativos", {})
        print(f"\n🔄 Reactivation Campaign — {len(inactive)} inativos")
        print(f"  Taxa esperada: {result.get('taxa_reativacao_esperada_pct','?')}%")
        print(f"  Valor potencial: R$ {result.get('valor_recuperado_estimado','?')}")
        self.save_result(result, prefix="reactivation_campaign")
        return result

    def cold_outreach(self, leads: list, context: dict) -> dict:
        """Cria emails de cold outreach personalizados para cada lead."""
        self.logger.info(f"Cold outreach: {len(leads)} leads")
        prompt = f"""Crie emails de cold outreach altamente personalizados:

CONTEXTO DA EMPRESA:
{json.dumps(context, indent=2, ensure_ascii=False)[:1500]}

LEADS ({len(leads)} — mostrando primeiros 10):
{json.dumps(leads[:10], indent=2, ensure_ascii=False)[:3000]}

Para cada lead gere um email único. Retorne JSON com:
- emails_personalizados: lista com:
  - lead_id: identificador
  - lead_nome: nome
  - assunto: assunto personalizado (mencionar algo específico deles)
  - email_completo: corpo completo (150-250 palavras máx)
  - personalizacao_usada: o que foi personalizado e por que
  - gatilho: o que os tornaria receptivos agora
  - follow_up_1: mensagem de follow-up 3 dias depois (50 palavras)
  - follow_up_2: mensagem final de follow-up 7 dias depois (30 palavras)
- framework_usado: metodologia de cold email (AIDA, PAS, etc)
- o_que_nao_fazer: erros comuns de cold email que você evitou
- metricas_esperadas: open rate, reply rate estimados"""

        result = self.ask_json(prompt, system=SYSTEM_EMAIL)
        emails = result.get("emails_personalizados", [])
        print(f"\n🎯 Cold Outreach — {len(emails)} emails personalizados")
        for e in emails[:3]:
            print(f"  {e.get('lead_nome','?')}: {e.get('assunto','?')[:60]}")
        self.save_result(result, prefix="cold_outreach")
        return result

    def deliverability_audit(self, domain: str) -> dict:
        """Auditoria de deliverabilidade de email."""
        self.logger.info(f"Deliverability audit: {domain}")
        prompt = f"""Crie um guia completo de auditoria de deliverabilidade para o domínio: {domain}

Retorne JSON com:
- checklist_tecnico:
  - spf: o que verificar e como configurar
  - dkim: o que verificar e como configurar
  - dmarc: o que verificar e como configurar (recomendação: policy=quarantine)
  - mx_records: verificação dos registros MX
  - blacklists: como verificar se está em blacklists (MXToolbox, etc)
  - ssl_certificado: importância e como verificar
- reputacao_dominio:
  - como_verificar: ferramentas (Google Postmaster, Sender Score, etc)
  - o_que_afeta: fatores que impactam a reputação
  - como_recuperar: se a reputação está ruim
- boas_praticas_envio:
  - frequencia: com que frequência enviar
  - horarios_otimos: melhores horários por tipo de email
  - aquecimento_ip: como fazer warm-up de novo IP
  - limpeza_lista: manter lista saudável
- conteudo_e_spam:
  - palavras_spam: evitar (lista de palavras que triggeram filtros)
  - ratio_texto_imagem: proporção ideal
  - links: boas práticas de links em emails
- ferramentas_recomendadas: ESPs e ferramentas de teste
- score_estimado_deliverabilidade: 0-100 e o que impacta"""

        result = self.ask_json(prompt, system=SYSTEM_EMAIL)
        score = result.get("score_estimado_deliverabilidade", 0)
        print(f"\n📬 Deliverability Audit — {domain}: {score}/100")
        checklist = result.get("checklist_tecnico", {})
        for item in checklist:
            print(f"  ✓ {item}")
        self.save_result(result, prefix="deliverability_audit")
        return result

    def ab_subject_lines(self, topic: str, count: int = 10) -> dict:
        """Gera variações de subject line para A/B test."""
        self.logger.info(f"AB subjects: {topic} | {count} variações")
        prompt = f"""Gere {count} variações de subject line para A/B test sobre: "{topic}"

Cada subject deve usar um gatilho mental diferente e ser único.

Retorne JSON com:
- subjects: lista de {count} subjects com:
  - numero: sequência
  - texto: o subject (máx 50 chars)
  - pre_header: preview text complementar (máx 90 chars)
  - gatilho: qual gatilho mental usa
  - por_que_abre: psicologia por trás
  - melhor_para: tipo de audiência que responde melhor
- ranking_estimado: ordem do que provavelmente terá maior open rate
- vencedor_recomendado: qual testar como controle e qual como variante
- como_testar: metodologia de A/B test (tamanho de amostra, duração)
- metricas_alvo: open rate esperado para cada variação"""

        result = self.ask_json(prompt, system=SYSTEM_EMAIL)
        subjects = result.get("subjects", [])
        print(f"\n✉️  A/B Subject Lines — {topic}")
        for s in subjects[:5]:
            print(f"  {s.get('numero','?')}. {s.get('texto','?'):<55} [{s.get('gatilho','?')}]")
        self.save_result(result, prefix="ab_subject_lines")
        return result


def main():
    parser = argparse.ArgumentParser(description="Email Automation — ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")

    p_n = sub.add_parser("nurture")
    p_n.add_argument("--icp", required=True)
    p_n.add_argument("--product", required=True)
    p_n.add_argument("--steps", type=int, default=7)

    sub.add_parser("reactivate").add_argument("--inactive", required=True)

    p_co = sub.add_parser("cold-outreach")
    p_co.add_argument("--leads", required=True)
    p_co.add_argument("--context", required=True)

    sub.add_parser("deliverability").add_argument("--domain", required=True)

    p_ab = sub.add_parser("ab-subject")
    p_ab.add_argument("--topic", required=True)
    p_ab.add_argument("--count", type=int, default=10)

    args = parser.parse_args()
    agent = EmailAutomation()
    def load(p): return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else {}

    if args.command == "nurture":
        agent.nurture_sequence(load(args.icp), load(args.product), args.steps)
    elif args.command == "reactivate":
        data = load(args.inactive)
        agent.reactivation_campaign(data if isinstance(data, list) else data.get("contacts",[]))
    elif args.command == "cold-outreach":
        leads = load(args.leads)
        agent.cold_outreach(leads if isinstance(leads, list) else leads.get("leads",[]), load(args.context))
    elif args.command == "deliverability":
        agent.deliverability_audit(args.domain)
    elif args.command == "ab-subject":
        agent.ab_subject_lines(args.topic, args.count)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
