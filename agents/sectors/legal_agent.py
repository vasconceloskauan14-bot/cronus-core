"""
Legal Agent — ULTIMATE CRONUS
Automações jurídicas: contratos, compliance, LGPD, due diligence e riscos legais.

AVISO: Este agente fornece análise jurídica preliminar e informações gerais.
NÃO substitui consulta com advogado habilitado. Sempre validar com profissional jurídico.

Uso:
    python legal_agent.py contract-review --contract data/contrato.json
    python legal_agent.py lgpd-audit --company data/empresa.json
    python legal_agent.py risk-assessment --situation data/situacao.json
    python legal_agent.py terms-generator --product data/produto.json --type "SaaS"
    python legal_agent.py due-diligence --target data/empresa_alvo.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_agent import BaseAgent

SYSTEM_LEGAL = """Você é o Legal advisor do ULTIMATE CRONUS — análise jurídica empresarial.
Você cobre contratos, compliance, LGPD, regulações e gestão de riscos legais.
IMPORTANTE: Sempre incluir disclaimer que não substitui consultoria jurídica profissional.
Foque em direito empresarial brasileiro: Código Civil, CLT, LGPD, Lei das SA, Marco Civil da Internet."""


LEGAL_DISCLAIMER = "\n\n⚠️ AVISO: Esta análise é informativa. Consulte um advogado habilitado antes de tomar decisões jurídicas."


class LegalAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="LEGAL", output_dir="agents/output")

    def review_contract(self, contract: dict) -> dict:
        """Analisa contrato e identifica riscos."""
        self.logger.info(f"Contract review: {contract.get('tipo', '?')}")
        contract_text = contract.get("texto") or contract.get("content") or json.dumps(contract)
        prompt = f"""Analise este contrato e identifique riscos e pontos de atenção:

CONTRATO:
{contract_text[:5000]}

Retorne JSON com:
- tipo_contrato: classificação do contrato
- partes_identificadas: quem são as partes
- pontos_positivos: cláusulas favoráveis ao contratante
- riscos_identificados: lista de riscos ordenados por severidade:
  - clausula: referência à cláusula
  - risco: descrição do risco
  - severidade: "baixo"|"médio"|"alto"|"crítico"
  - recomendacao: o que fazer
- clausulas_ausentes: o que deveria estar no contrato e não está
- clausulas_abusivas: cláusulas potencialmente abusivas ou leoninas
- prazo_e_renovacao: análise de vigência e renovação automática
- penalidades: multas e penalidades previstas
- foro: jurisdição e resolução de conflitos
- score_favorabilidade: 0-100 (100 = totalmente favorável)
- negociacoes_recomendadas: o que pedir para alterar antes de assinar
- parecer_geral: recomendação final (assinar|negociar|recusar)
- disclaimer: aviso que esta análise não substitui consulta jurídica"""

        result = self.ask_json(prompt, system=SYSTEM_LEGAL)
        score = result.get("score_favorabilidade", 0)
        parecer = result.get("parecer_geral", "?")
        riscos = [r for r in result.get("riscos_identificados", []) if isinstance(r, dict) and r.get("severidade") in ["alto", "crítico"]]
        print(f"\n⚖️  Contract Review — Score: {score}/100 | Parecer: {parecer}")
        print(f"  Riscos altos/críticos: {len(riscos)}")
        print(LEGAL_DISCLAIMER)
        self.save_result(result, prefix="contract_review")
        return result

    def lgpd_audit(self, company: dict) -> dict:
        """Auditoria de conformidade com LGPD."""
        self.logger.info(f"LGPD audit: {company.get('nome', '?')}")
        prompt = f"""Realize uma auditoria de conformidade com a LGPD para esta empresa:

EMPRESA:
{json.dumps(company, indent=2, ensure_ascii=False)[:3000]}

Retorne JSON com:
- score_conformidade_lgpd: 0-100
- nivel_risco: "baixo"|"médio"|"alto"|"crítico"
- checklist_lgpd: lista de itens com status:
  - item: nome do requisito LGPD
  - status: "conforme"|"parcial"|"nao_conforme"|"nao_aplicavel"
  - prioridade: "urgente"|"importante"|"recomendado"
  - acao_necessaria: o que fazer para regularizar
- dados_tratados: categorias de dados pessoais identificadas
- bases_legais_utilizadas: fundamentos legais para cada tratamento
- dpo_status: se tem DPO nomeado e situação
- politica_privacidade: avaliação da política de privacidade
- cookies_e_consentimento: situação do consentimento digital
- incidentes_procedimento: se tem processo para incidentes de segurança
- penalidades_em_risco: multas potenciais com ANPD (até 2% faturamento, máx 50M)
- plano_adequacao:
  - urgente_0_30_dias: ações críticas imediatas
  - curto_prazo_30_90_dias: adequações importantes
  - medio_prazo_3_6_meses: melhorias complementares
- disclaimer: esta auditoria não substitui DPO ou consultoria jurídica especializada"""

        result = self.ask_json(prompt, system=SYSTEM_LEGAL)
        score = result.get("score_conformidade_lgpd", 0)
        nivel = result.get("nivel_risco", "?")
        icons = {"crítico": "🚨", "alto": "🔴", "médio": "🟡", "baixo": "🟢"}
        print(f"\n{icons.get(nivel, '●')} LGPD Audit — {company.get('nome', '?')}: {score}/100 ({nivel})")
        print(LEGAL_DISCLAIMER)
        self.save_result(result, prefix="lgpd_audit")
        return result

    def legal_risk_assessment(self, situation: dict) -> dict:
        """Avalia risco legal de uma situação específica."""
        self.logger.info("Legal risk assessment")
        prompt = f"""Avalie os riscos legais desta situação empresarial:

SITUAÇÃO:
{json.dumps(situation, indent=2, ensure_ascii=False)[:3000]}

Retorne JSON com:
- resumo_situacao: descrição objetiva do que está acontecendo
- riscos_legais: lista de riscos por área do direito:
  - area: cível|trabalhista|tributário|consumidor|concorrencial|digital
  - risco: descrição do risco
  - probabilidade: "baixa"|"média"|"alta"
  - impacto: "baixo"|"médio"|"alto"|"catastrófico"
  - score_risco: 0-100
  - legislacao_aplicavel: leis e normas relevantes
  - precedentes: se há jurisprudência relevante
- acoes_preventivas: o que fazer agora para reduzir riscos
- acoes_se_demandado: como agir se surgir processo ou notificação
- prazo_prescricional: prazos prescricionais relevantes
- especialistas_necessarios: que tipo de advogado contratar
- provisoes_necessarias: se deve provisionar para contingências (valor estimado)
- disclaimer: sempre consultar advogado habilitado"""

        result = self.ask_json(prompt, system=SYSTEM_LEGAL)
        riscos = result.get("riscos_legais", [])
        altos = [r for r in riscos if isinstance(r, dict) and r.get("probabilidade") in ["alta"] and r.get("impacto") in ["alto", "catastrófico"]]
        print(f"\n⚠️  Legal Risk Assessment — {len(riscos)} riscos mapeados")
        print(f"  Alta probabilidade + alto impacto: {len(altos)}")
        print(LEGAL_DISCLAIMER)
        self.save_result(result, prefix="legal_risk")
        return result

    def generate_terms(self, product: dict, service_type: str) -> dict:
        """Gera termos de uso e política de privacidade."""
        self.logger.info(f"Terms generator: {service_type}")
        prompt = f"""Gere Termos de Uso e Política de Privacidade para este produto/serviço:

PRODUTO:
{json.dumps(product, indent=2, ensure_ascii=False)[:2000]}

TIPO DE SERVIÇO: {service_type}

Retorne JSON com:
- termos_de_uso: texto completo dos Termos de Uso (estruturado em seções)
- politica_de_privacidade: texto completo da Política de Privacidade (LGPD compliant)
- cookies_policy: política de cookies (se aplicável)
- sla: acordo de nível de serviço simplificado (se aplicável)
- pontos_criticos_incluidos:
  - limitacao_responsabilidade: como foi estruturada
  - foro_eleito: qual jurisdição
  - lei_aplicavel: direito brasileiro
  - cancelamento: processo definido
  - reembolso: política clara
- recomendacoes_adicionais: o que customizar conforme o negócio específico
- disclaimer: gerar documentos jurídicos requer revisão por advogado especializado"""

        result = self.ask_json(prompt, system=SYSTEM_LEGAL)
        print(f"\n📜 Terms Generator — {service_type}")
        print(f"  Termos de Uso: {len(result.get('termos_de_uso', ''))} chars")
        print(f"  Política de Privacidade: {len(result.get('politica_de_privacidade', ''))} chars")
        print(LEGAL_DISCLAIMER)
        self.save_result(result, prefix="legal_terms")
        return result

    def due_diligence(self, target: dict) -> dict:
        """Checklist de due diligence jurídica para M&A ou parceria."""
        self.logger.info(f"Due diligence: {target.get('nome', '?')}")
        prompt = f"""Crie checklist de due diligence jurídica para esta empresa:

EMPRESA ALVO:
{json.dumps(target, indent=2, ensure_ascii=False)[:3000]}

Retorne JSON com:
- areas_due_diligence:
  - corporativo: documentos societários, atas, cap table
  - contratos: contratos relevantes em vigor
  - trabalhista: situação CLT, terceiros, passivos
  - tributario: status fiscal, débitos, parcelamentos
  - propriedade_intelectual: marcas, patentes, software
  - regulatorio: licenças, autorizações, compliance setorial
  - litigios: processos em andamento e passivos judiciais
  - lgpd_digital: compliance de dados e digital
- documentos_solicitar: lista completa de documentos a pedir
- red_flags_buscar: o que investigar como sinal de problema
- perguntas_chave: perguntas para fazer à gestão
- riscos_comuns_desta_industria: riscos jurídicos típicos do setor
- score_complexidade_dd: 0-100 (100 = muito complexo)
- prazo_estimado_dd: semanas para completar
- especialistas_necessarios: áreas jurídicas que precisam de expertise específica
- disclaimer: due diligence requer equipe jurídica especializada"""

        result = self.ask_json(prompt, system=SYSTEM_LEGAL)
        score = result.get("score_complexidade_dd", 0)
        prazo = result.get("prazo_estimado_dd", "?")
        print(f"\n🔍 Due Diligence — {target.get('nome', '?')}: complexidade {score}/100")
        print(f"  Prazo estimado: {prazo} semanas")
        print(LEGAL_DISCLAIMER)
        self.save_result(result, prefix="due_diligence")
        return result


def main():
    parser = argparse.ArgumentParser(description="Legal Agent — ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("contract-review").add_argument("--contract", required=True)
    sub.add_parser("lgpd-audit").add_argument("--company", required=True)
    sub.add_parser("risk-assessment").add_argument("--situation", required=True)

    p_t = sub.add_parser("terms-generator")
    p_t.add_argument("--product", required=True)
    p_t.add_argument("--type", default="SaaS", dest="service_type")

    sub.add_parser("due-diligence").add_argument("--target", required=True)

    args = parser.parse_args()
    agent = LegalAgent()
    def load(p): return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else {}

    if args.command == "contract-review":
        agent.review_contract(load(args.contract))
    elif args.command == "lgpd-audit":
        agent.lgpd_audit(load(args.company))
    elif args.command == "risk-assessment":
        agent.legal_risk_assessment(load(args.situation))
    elif args.command == "terms-generator":
        agent.generate_terms(load(args.product), args.service_type)
    elif args.command == "due-diligence":
        agent.due_diligence(load(args.target))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
