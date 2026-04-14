"""
VISION Agent — ULTIMATE CRONUS
Branding, posicionamento, identidade visual e brand strategy.

Uso:
    python vision_agent.py audit --brand data/marca.json
    python vision_agent.py positioning --market data/mercado.json --company data/empresa.json
    python vision_agent.py identity --brief data/brief.json
    python vision_agent.py messaging --brand data/marca.json --audience data/audiencia.json
    python vision_agent.py rebranding --current data/marca_atual.json --goals data/objetivos.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from base_agent import BaseAgent

SYSTEM_VISION = """Você é o VISION, agente de Brand Strategy do ULTIMATE CRONUS.
Você constrói marcas que vendem, posicionamentos que dominam mercados.
Pense como um Chief Brand Officer de uma marca global com 20 anos de experiência.
Combine estética, psicologia e negócios para criar identidades inesquecíveis."""


class VisionAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="VISION", output_dir="agents/output")

    def brand_audit(self, brand: dict) -> dict:
        """Auditoria completa da marca atual."""
        self.logger.info(f"Brand audit: {brand.get('nome', '?')}")
        prompt = f"""Faça uma auditoria completa desta marca:

MARCA:
{json.dumps(brand, indent=2, ensure_ascii=False)[:4000]}

Retorne JSON com:
- score_brand_saude: 0-100
- identidade_atual:
  - pontos_fortes: o que está funcionando
  - pontos_fracos: o que está prejudicando
  - inconsistencias: onde a marca é incoerente
- brand_perception: como o mercado provavelmente percebe a marca
- gap_desejado_vs_real: diferença entre posicionamento desejado e real
- arquetipos_marca: qual arquétipo Jungiano representa a marca
- tom_de_voz_atual: como a marca se comunica hoje
- recomendacoes_criticas: top 5 ações urgentes
- oportunidades_branding: onde crescer a percepção de valor
- score_por_dimensao:
  - clareza: 0-10
  - diferenciacao: 0-10
  - autenticidade: 0-10
  - consistencia: 0-10
  - emocionalidade: 0-10"""

        result = self.ask_json(prompt, system=SYSTEM_VISION)
        score = result.get("score_brand_saude", 0)
        print(f"\n🎨 Brand Audit — {brand.get('nome', '?')}: {score}/100")
        dims = result.get("score_por_dimensao", {})
        for d, v in dims.items():
            bar = "█" * v + "░" * (10 - v)
            print(f"  {d:<18} {bar} {v}/10")
        self.save_result(result, prefix="brand_audit")
        return result

    def positioning_strategy(self, market: dict, company: dict) -> dict:
        """Cria estratégia de posicionamento competitivo."""
        self.logger.info(f"Positioning: {company.get('nome', '?')}")
        prompt = f"""Crie uma estratégia de posicionamento competitivo:

EMPRESA:
{json.dumps(company, indent=2, ensure_ascii=False)[:2000]}

MERCADO/CONCORRENTES:
{json.dumps(market, indent=2, ensure_ascii=False)[:2000]}

Retorne JSON com:
- posicionamento_recomendado: declaração de posicionamento completa (30 palavras)
- category_design: como redefinir a categoria para ganhar
- diferenciacao_principal: o que torna único e por que importa
- claim_central: tagline/slogan principal
- claims_suporte: 3 claims de suporte
- territorio_da_marca: espaço emocional e racional que a marca ocupa
- mapa_perceptual: descrição do mapa perceptual vs concorrentes
- proposta_valor: proposta de valor estruturada (quem, o que, por que, para quem)
- pilares_marca: 4-5 pilares que sustentam o posicionamento
- prova_social: que tipo de evidência usar para cada pilar
- messaging_hierarchy: ordem de comunicação dos benefícios"""

        result = self.ask_json(prompt, system=SYSTEM_VISION)
        print(f"\n🎯 Positioning — {company.get('nome', '?')}")
        print(f"  Posicionamento: {result.get('posicionamento_recomendado', '')[:100]}")
        print(f"  Claim: {result.get('claim_central', '')}")
        self.save_result(result, prefix="brand_positioning")
        return result

    def visual_identity(self, brief: dict) -> dict:
        """Cria brief completo de identidade visual."""
        self.logger.info(f"Visual identity: {brief.get('marca', '?')}")
        prompt = f"""Crie um brief completo de identidade visual para esta marca:

BRIEF:
{json.dumps(brief, indent=2, ensure_ascii=False)[:3000]}

Retorne JSON com:
- conceito_visual: ideia central que guia toda a identidade
- paleta_cores:
  - cor_primaria: hex + nome + psicologia
  - cor_secundaria: hex + nome + psicologia
  - cor_acento: hex + nome + uso
  - cor_neutra: hex + nome
  - razao_paleta: por que estas cores para esta marca
- tipografia:
  - fonte_principal: nome + estilo + uso + alternativa Google Fonts
  - fonte_secundaria: nome + estilo + uso
  - escala_tipografica: h1, h2, h3, body, caption
- logo_brief:
  - conceito: ideia do logo
  - estilo: "wordmark"|"lettermark"|"emblem"|"combination"
  - elementos_graficos: formas e simbolos a explorar
  - o_que_evitar: estilos e elementos proibidos
- iconografia: estilo de ícones (outlined, filled, custom)
- fotografia: direção fotográfica (estilo, tom, composição)
- ilustracao: se usar, qual estilo
- motion: princípios de animação da marca
- aplicacoes_prioritarias: onde aplicar primeiro"""

        result = self.ask_json(prompt, system=SYSTEM_VISION)
        print(f"\n🎨 Visual Identity Brief — {brief.get('marca', '?')}")
        paleta = result.get("paleta_cores", {})
        if paleta:
            print(f"  Primária: {paleta.get('cor_primaria', {}).get('hex', '?')} | Secundária: {paleta.get('cor_secundaria', {}).get('hex', '?')}")
        self.save_result(result, prefix="visual_identity")
        return result

    def brand_messaging(self, brand: dict, audience: dict) -> dict:
        """Cria sistema completo de mensagens da marca."""
        self.logger.info(f"Messaging: {brand.get('nome', '?')}")
        prompt = f"""Crie um sistema completo de mensagens da marca:

MARCA:
{json.dumps(brand, indent=2, ensure_ascii=False)[:2000]}

AUDIÊNCIA:
{json.dumps(audience, indent=2, ensure_ascii=False)[:2000]}

Retorne JSON com:
- mensagem_central: o coração da comunicação da marca (1 frase impactante)
- tom_de_voz:
  - personalidade: 4 adjetivos que definem como a marca fala
  - como_falar: guidelines de tom
  - como_nao_falar: o que evitar
  - exemplos_corretos: 3 exemplos de mensagens no tom certo
  - exemplos_errados: 3 exemplos do tom errado
- mensagens_por_audiencia: para cada segmento de audiência:
  - segmento: nome
  - dor_principal: maior problema
  - mensagem_chave: mensagem específica para este segmento
  - prova: como provar para este segmento
- narrativa_marca: story brand canvas completo
- elevator_pitch: 30 segundos, 2 minutos, 5 minutos
- perguntas_frequentes: 10 respostas no tom de marca
- manifesto_marca: texto de manifesto para uso interno e externo"""

        result = self.ask_json(prompt, system=SYSTEM_VISION)
        print(f"\n📣 Brand Messaging — {brand.get('nome', '?')}")
        print(f"  Central: {result.get('mensagem_central', '')[:100]}")
        self.save_result(result, prefix="brand_messaging")
        return result

    def rebranding_plan(self, current: dict, goals: dict) -> dict:
        """Plano completo de rebranding."""
        self.logger.info("Rebranding plan")
        prompt = f"""Crie um plano de rebranding estratégico:

MARCA ATUAL:
{json.dumps(current, indent=2, ensure_ascii=False)[:2000]}

OBJETIVOS DO REBRANDING:
{json.dumps(goals, indent=2, ensure_ascii=False)[:1000]}

Retorne JSON com:
- diagnostico: por que o rebranding é necessário
- o_que_manter: elementos da marca atual que preservar
- o_que_mudar: o que precisa evoluir
- o_que_eliminar: o que descartar completamente
- novo_posicionamento: para onde a marca vai
- fases_rebranding:
  - fase_1_estrategia: semanas 1-4
  - fase_2_identidade: semanas 5-12
  - fase_3_lancamento: semanas 13-16
  - fase_4_rollout: semanas 17-24
- comunicacao_mudanca:
  - para_clientes: como comunicar
  - para_equipe: como engajar internamente
  - para_mercado: como anunciar
- riscos: o que pode dar errado e como mitigar
- kpis_sucesso: como medir se o rebranding funcionou
- orcamento_estimado: faixas por porte de empresa
- checklist_execucao: lista de tarefas por fase"""

        result = self.ask_json(prompt, system=SYSTEM_VISION)
        fases = [k for k in result.get("fases_rebranding", {}).keys()]
        print(f"\n🔄 Rebranding Plan — {len(fases)} fases")
        print(f"  Diagnóstico: {result.get('diagnostico', '')[:100]}")
        self.save_result(result, prefix="rebranding_plan")
        return result


def main():
    parser = argparse.ArgumentParser(description="VISION Agent — ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("audit").add_argument("--brand", required=True)
    p_pos = sub.add_parser("positioning")
    p_pos.add_argument("--market", required=True)
    p_pos.add_argument("--company", required=True)
    sub.add_parser("identity").add_argument("--brief", required=True)
    p_msg = sub.add_parser("messaging")
    p_msg.add_argument("--brand", required=True)
    p_msg.add_argument("--audience", required=True)
    p_rb = sub.add_parser("rebranding")
    p_rb.add_argument("--current", required=True)
    p_rb.add_argument("--goals", required=True)

    args = parser.parse_args()
    agent = VisionAgent()
    def load(p): return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else {}

    if args.command == "audit":
        agent.brand_audit(load(args.brand))
    elif args.command == "positioning":
        agent.positioning_strategy(load(args.market), load(args.company))
    elif args.command == "identity":
        agent.visual_identity(load(args.brief))
    elif args.command == "messaging":
        agent.brand_messaging(load(args.brand), load(args.audience))
    elif args.command == "rebranding":
        agent.rebranding_plan(load(args.current), load(args.goals))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
