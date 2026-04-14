"""
HUNTER Agent — ULTIMATE CRONUS
Sistema de prospecção, qualificação e outreach de leads.

Uso:
    python hunter_agent.py hunt --icp config/icp_template.json --limit 50
    python hunter_agent.py qualify --lead '{"nome":"João","empresa":"Acme","cargo":"CEO"}'
    python hunter_agent.py outreach --lead-file results/leads.json --context "demo gratuita"
    python hunter_agent.py pipeline --icp config/icp_template.json --limit 20
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from base_agent import BaseAgent

SYSTEM_HUNTER = """Você é o HUNTER, agente especialista em prospecção e vendas B2B do ULTIMATE CRONUS.
Você identifica, qualifica e engaja leads com precisão cirúrgica.
Seu foco é qualidade sobre quantidade: leads altamente qualificados que têm dor real, budget e autoridade.
Use frameworks como BANT, MEDDIC e Challenger Sale quando aplicável."""


class HunterAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="HUNTER", output_dir="agents/results")
        Path("agents/results").mkdir(parents=True, exist_ok=True)

    def hunt(self, icp: dict, sources: list | None = None, limit: int = 50) -> list[dict]:
        """Busca leads baseado no ICP (Ideal Customer Profile)."""
        if sources is None:
            sources = ["LinkedIn", "Crunchbase", "Product Hunt", "G2", "Glassdoor"]

        self.logger.info(f"Hunting {limit} leads | ICP: {icp.get('setor','?')} | Sources: {sources}")

        prompt = f"""Você é um especialista em prospecção B2B. Com base no ICP abaixo, gere uma lista de {limit} leads fictícios mas realistas que representam empresas ideais.

ICP (Ideal Customer Profile):
{json.dumps(icp, indent=2, ensure_ascii=False)}

Fontes de pesquisa simuladas: {', '.join(sources)}

Para cada lead, retorne JSON com:
- id: número único
- nome_empresa: nome da empresa
- setor: setor de atuação
- tamanho: número de funcionários
- website: website fictício mas realista
- linkedin_url: URL do LinkedIn
- decisor_nome: nome do decisor (fictício)
- decisor_cargo: cargo do decisor
- decisor_linkedin: LinkedIn do decisor
- dores_identificadas: lista de 2-3 dores específicas
- sinais_de_compra: lista de 1-3 sinais que indicam momento de compra
- score_fit: 0-100 (fit com ICP)
- score_timing: 0-100 (momento de compra)
- score_total: média ponderada (fit 60% + timing 40%)
- fonte: de onde veio o lead
- notas: observação relevante

Retorne array JSON de {limit} leads ordenados por score_total decrescente."""

        result = self.ask_json(prompt, system=SYSTEM_HUNTER)
        leads = result if isinstance(result, list) else result.get("leads", [])

        # Salva resultado
        data = {"icp": icp, "sources": sources, "leads": leads, "total": len(leads)}
        path = self.save_result(data, prefix="hunt")

        print(f"\n🎯 HUNTER — {len(leads)} leads encontrados → {path}\n")
        print(f"  {'Empresa':<30} {'Cargo':<20} {'Score'}")
        print(f"  {'-'*30} {'-'*20} {'-'*5}")
        for lead in leads[:10]:
            print(f"  {lead.get('nome_empresa','?'):<30} {lead.get('decisor_cargo','?'):<20} {lead.get('score_total','?')}")
        if len(leads) > 10:
            print(f"  ... e mais {len(leads)-10} leads")

        self.save_state({"last_hunt": datetime.now().isoformat(), "leads_found": len(leads)})
        return leads

    def qualify(self, lead: dict) -> dict:
        """Qualifica um lead com score detalhado e próximos passos."""
        nome = lead.get("nome_empresa", lead.get("nome", "Lead"))
        self.logger.info(f"Qualificando: {nome}")

        prompt = f"""Qualifique este lead B2B usando o framework BANT + sinais modernos:

LEAD:
{json.dumps(lead, indent=2, ensure_ascii=False)}

Retorne JSON com:
- score_total: 0-100
- dimensoes:
  - budget: score 0-100 + justificativa
  - authority: score 0-100 + justificativa
  - need: score 0-100 + justificativa
  - timing: score 0-100 + justificativa
  - fit_produto: score 0-100 + justificativa
- classificacao: "hot" | "warm" | "cold" | "disqualified"
- razao_principal: por que este lead vale ou não vale
- proximo_passo: ação recomendada imediata
- prazo_recomendado: quando entrar em contato
- red_flags: lista de alertas (pode ser vazia)
- oportunidade_estimada: valor estimado do contrato em R$"""

        result = self.ask_json(prompt, system=SYSTEM_HUNTER)
        score = result.get("score_total", 0)
        classif = result.get("classificacao", "?")

        icon = {"hot": "🔥", "warm": "🟡", "cold": "🔵", "disqualified": "❌"}.get(classif, "●")
        print(f"\n{icon} {nome} — Score: {score}/100 ({classif.upper()})")
        print(f"  Próximo passo: {result.get('proximo_passo','')}")
        print(f"  Oportunidade: {result.get('oportunidade_estimada','?')}")

        return result

    def enrich(self, lead: dict) -> dict:
        """Enriquece dados de um lead com informações adicionais."""
        nome = lead.get("nome_empresa", "Lead")
        self.logger.info(f"Enriquecendo: {nome}")

        prompt = f"""Enriqueça os dados deste lead com informações de inteligência de mercado:

LEAD ATUAL:
{json.dumps(lead, indent=2, ensure_ascii=False)}

Adicione ao JSON original os seguintes campos:
- tech_stack: tecnologias que provavelmente usam
- ferramentas_concorrentes: ferramentas concorrentes que provavelmente usam
- budget_estimado_anual: em R$ (range)
- crescimento_estimado: "crescendo" | "estável" | "encolhendo"
- maturidade_digital: 1-5 (1=baixa, 5=alta)
- dores_profundas: dores mais profundas baseadas no contexto
- gatilhos_de_compra: eventos que podem acelerar a decisão
- referencias_similares: 2-3 empresas similares que já compraram soluções parecidas
- icebreaker: assunto personalizado para abrir a conversa
- linguagem_do_cliente: como este perfil costuma falar (formal/informal, técnico/executivo)

Retorne o JSON do lead original + estes novos campos."""

        result = self.ask_json(prompt, system=SYSTEM_HUNTER)
        enriched = {**lead, **result}
        self.save_result(enriched, prefix="enriched_lead")
        print(f"\n✨ Lead enriquecido: {nome}")
        print(f"  Tech stack: {', '.join(enriched.get('tech_stack', [])[:3])}")
        print(f"  Icebreaker: {enriched.get('icebreaker','')[:80]}")
        return enriched

    def generate_outreach(self, lead: dict, context: str = "", channel: str = "email") -> dict:
        """Gera mensagem de outreach personalizada para o lead."""
        nome = lead.get("decisor_nome", lead.get("nome_empresa", "Lead"))
        self.logger.info(f"Gerando outreach para: {nome} via {channel}")

        prompt = f"""Crie uma mensagem de outreach B2B altamente personalizada:

LEAD:
{json.dumps(lead, indent=2, ensure_ascii=False)}

CONTEXTO ADICIONAL: {context or 'Demo gratuita de 30 minutos'}
CANAL: {channel}

Gere JSON com:
- subject: assunto (para email, max 50 chars, personalizado)
- mensagem_curta: versão curta (LinkedIn, max 300 chars)
- mensagem_completa: versão completa (email, 150-250 palavras)
- follow_up_1: mensagem de follow-up após 3 dias (se não responder)
- follow_up_2: mensagem de follow-up após 7 dias
- cta: call-to-action claro e específico
- angulo_usado: qual ângulo de persuasão foi usado
- personalizacao_key: o elemento mais personalizado da mensagem

Regras:
- Não use "Espero que este email te encontre bem"
- Comece com algo específico sobre a empresa/pessoa
- Seja direto: problema → solução → CTA
- Máximo 3 parágrafos no email completo"""

        result = self.ask_json(prompt, system=SYSTEM_HUNTER)

        path = self.save_result(
            {"lead": lead, "channel": channel, "outreach": result},
            prefix="outreach"
        )
        print(f"\n📧 Outreach gerado → {path}")
        print(f"  Assunto: {result.get('subject','')}")
        print(f"  Ângulo: {result.get('angulo_usado','')}")
        return result

    def pipeline(self, icp: dict, limit: int = 20) -> dict:
        """Pipeline completo: hunt → qualify → enrich → outreach."""
        self.logger.info(f"Pipeline completo para {limit} leads")
        print(f"\n🚀 HUNTER Pipeline — {limit} leads\n")

        # 1. Hunt
        print("1/4 🔍 Buscando leads...")
        leads = self.hunt(icp, limit=limit)

        # 2. Qualify (top 50%)
        top_leads = leads[:max(1, limit // 2)]
        print(f"\n2/4 ✅ Qualificando top {len(top_leads)} leads...")
        qualified = []
        for lead in top_leads[:5]:  # limita para não gastar muita API
            qual = self.qualify(lead)
            if qual.get("score_total", 0) >= 60:
                lead["qualification"] = qual
                qualified.append(lead)

        # 3. Enrich top 3
        print(f"\n3/4 ✨ Enriquecendo top {min(3, len(qualified))} leads...")
        enriched = []
        for lead in qualified[:3]:
            enriched.append(self.enrich(lead))

        # 4. Outreach para top 3
        print(f"\n4/4 📧 Gerando outreach para {len(enriched)} leads...")
        final = []
        for lead in enriched:
            outreach = self.generate_outreach(lead)
            lead["outreach"] = outreach
            final.append(lead)

        result = {"icp": icp, "total_hunted": len(leads), "qualified": len(qualified), "pipeline": final}
        path = self.save_result(result, prefix="pipeline")
        print(f"\n✅ Pipeline concluído! {len(final)} leads prontos para outreach → {path}")
        return result


def main():
    parser = argparse.ArgumentParser(description="HUNTER — Sistema de Prospecção ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")

    p_hunt = sub.add_parser("hunt", help="Buscar leads")
    p_hunt.add_argument("--icp", help="Arquivo JSON com ICP")
    p_hunt.add_argument("--limit", type=int, default=50)

    p_qual = sub.add_parser("qualify", help="Qualificar lead")
    p_qual.add_argument("--lead", help="JSON do lead ou caminho para arquivo")

    p_enrich = sub.add_parser("enrich", help="Enriquecer lead")
    p_enrich.add_argument("--lead", help="JSON do lead ou caminho para arquivo")

    p_out = sub.add_parser("outreach", help="Gerar outreach")
    p_out.add_argument("--lead", help="JSON do lead ou caminho para arquivo")
    p_out.add_argument("--context", default="")
    p_out.add_argument("--channel", default="email", choices=["email", "linkedin", "whatsapp"])

    p_pipe = sub.add_parser("pipeline", help="Pipeline completo")
    p_pipe.add_argument("--icp", help="Arquivo JSON com ICP")
    p_pipe.add_argument("--limit", type=int, default=20)

    args = parser.parse_args()
    agent = HunterAgent()

    def load_icp(path: str) -> dict:
        return json.loads(Path(path).read_text(encoding="utf-8")) if path else {
            "setor": "SaaS B2B", "tamanho": "50-500 funcionários",
            "cargo_decisor": "CEO, CTO", "dores": ["escalar sem contratar", "automatizar processos"],
            "budget_estimado": "R$5.000-50.000/mês"
        }

    def load_lead(val: str) -> dict:
        if val and Path(val).exists():
            return json.loads(Path(val).read_text(encoding="utf-8"))
        return json.loads(val) if val else {}

    if args.command == "hunt":
        agent.hunt(load_icp(args.icp), limit=args.limit)
    elif args.command == "qualify":
        agent.qualify(load_lead(args.lead))
    elif args.command == "enrich":
        agent.enrich(load_lead(args.lead))
    elif args.command == "outreach":
        agent.generate_outreach(load_lead(args.lead), args.context, args.channel)
    elif args.command == "pipeline":
        agent.pipeline(load_icp(args.icp), args.limit)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
