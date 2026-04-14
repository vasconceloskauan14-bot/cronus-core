"""
Health Agent — ULTIMATE CRONUS
Automações para saúde: clínicas, telemedicina, healthtechs e operadoras.

Uso:
    python health_agent.py clinic-ops --data data/clinica.json
    python health_agent.py patient-journey --patient data/paciente.json
    python health_agent.py health-content --topic "diabetes tipo 2" --audience "pacientes"
    python health_agent.py telemedicine --metrics data/telemed.json
    python health_agent.py population-health --cohort data/cohort.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_agent import BaseAgent

SYSTEM_HEALTH = """Você é especialista em saúde digital do ULTIMATE CRONUS.
Você domina operações clínicas, telemedicina, healthtech e gestão de saúde populacional.
IMPORTANTE: Não faça diagnósticos médicos. Foque em gestão operacional, comunicação e estratégia.
Compliance é crítico — sempre considere LGPD, CFM e regulações da ANS."""


class HealthAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="HEALTH", output_dir="agents/output")

    def clinic_operations(self, data: dict) -> dict:
        """Analisa e otimiza operações de clínica/consultório."""
        self.logger.info(f"Clinic ops: {data.get('nome', '?')}")
        prompt = f"""Analise e otimize as operações desta clínica/serviço de saúde:

DADOS:
{json.dumps(data, indent=2, ensure_ascii=False)[:4000]}

Retorne JSON com:
- score_operacional: 0-100
- metricas_calculadas:
  - taxa_ocupacao_pct: % de slots preenchidos
  - taxa_no_show_pct: % de faltas
  - tempo_espera_medio_min: tempo médio de espera
  - satisfacao_paciente: NPS ou score equivalente
  - receita_por_atendimento: R$
- gargalos_operacionais: onde a clínica perde mais eficiência
- oportunidades_receita: como aumentar faturamento sem aumentar custos
- reducao_no_show: estratégias para reduzir faltas
- otimizacao_agenda: como maximizar slots produtivos
- melhorias_experiencia_paciente: quick wins de experiência
- automacoes_recomendadas: o que automatizar primeiro
- kpis_prioritarios: top 5 métricas a monitorar
- plano_acao_30_dias: ações concretas com responsável e prazo"""

        result = self.ask_json(prompt, system=SYSTEM_HEALTH)
        score = result.get("score_operacional", 0)
        print(f"\n🏥 Clinic Operations — {data.get('nome', '?')}: {score}/100")
        m = result.get("metricas_calculadas", {})
        print(f"  Ocupação: {m.get('taxa_ocupacao_pct', '?')}% | No-show: {m.get('taxa_no_show_pct', '?')}% | Espera: {m.get('tempo_espera_medio_min', '?')}min")
        self.save_result(result, prefix="clinic_ops")
        return result

    def patient_journey(self, patient: dict) -> dict:
        """Mapeia jornada do paciente e cria plano de comunicação."""
        self.logger.info(f"Patient journey: {patient.get('condicao', '?')}")
        prompt = f"""Mapeie a jornada do paciente e crie plano de comunicação personalizado:

PACIENTE (dados anonimizados):
{json.dumps(patient, indent=2, ensure_ascii=False)[:2000]}

Retorne JSON com:
- fases_jornada: lista das fases (busca, primeiro contato, atendimento, tratamento, acompanhamento)
- pontos_de_dor: onde o paciente mais sofre na jornada atual
- momentos_verdade: momentos críticos que determinam a experiência
- comunicacoes_por_fase: para cada fase:
  - fase: nome
  - canal: email|sms|whatsapp|app|ligacao
  - mensagem_modelo: template de mensagem
  - timing: quando enviar
  - objetivo: o que quer alcançar
- educacao_em_saude: conteúdo educativo relevante para este paciente
- follow_up_pos_consulta: sequência de follow-up
- programa_adesao: se tratamento longo, como garantir adesão
- metricas_satisfacao: como medir satisfação em cada ponto
- compliance_lgpd: alertas de conformidade para comunicações"""

        result = self.ask_json(prompt, system=SYSTEM_HEALTH)
        fases = result.get("fases_jornada", [])
        print(f"\n🩺 Patient Journey — {patient.get('condicao', '?')}: {len(fases)} fases")
        dores = result.get("pontos_de_dor", [])
        if dores:
            print(f"  Maior dor: {dores[0] if isinstance(dores[0], str) else str(dores[0])[:80]}")
        self.save_result(result, prefix="patient_journey")
        return result

    def health_content(self, topic: str, audience: str) -> dict:
        """Cria conteúdo de saúde validado e educativo."""
        self.logger.info(f"Health content: {topic} → {audience}")
        prompt = f"""Crie conteúdo de saúde educativo sobre: "{topic}"
Audiência: {audience}

IMPORTANTE: Conteúdo informativo, não diagnóstico. Sempre recomendar consulta médica.

Retorne JSON com:
- artigo_educativo: artigo completo em português (500-800 palavras) com:
  - linguagem acessível para o público-alvo
  - informação médica correta e validada
  - chamada para consultar profissional de saúde
- perguntas_frequentes: 8 FAQs sobre o tema com respostas
- mitos_e_verdades: 5 mitos comuns e a realidade
- quando_buscar_medico: sinais de alerta para consultar imediatamente
- dicas_prevencao: 5 dicas práticas de prevenção/manejo
- post_redes_sociais: versão para Instagram e LinkedIn
- newsletter_saude: email informativo para pacientes
- disclaimer_medico: aviso legal adequado para conteúdo de saúde"""

        result = self.ask_json(prompt, system=SYSTEM_HEALTH)
        print(f"\n📋 Health Content — {topic}")
        print(f"  Audiência: {audience}")
        print(f"  FAQs: {len(result.get('perguntas_frequentes', []))}")
        self.save_result(result, prefix="health_content")
        return result

    def telemedicine_analytics(self, metrics: dict) -> dict:
        """Analisa performance de operação de telemedicina."""
        self.logger.info("Telemedicine analytics")
        prompt = f"""Analise a performance desta operação de telemedicina:

MÉTRICAS:
{json.dumps(metrics, indent=2, ensure_ascii=False)[:4000]}

Retorne JSON com:
- score_telemed: 0-100
- metricas_chave:
  - taxa_resolucao_primeira_consulta_pct: % resolvidos sem retorno
  - tempo_medio_consulta_min: duração média
  - nps_telemed: satisfação do paciente
  - taxa_conversao_telemed_presencial: quando precisam ir à clínica
  - custo_por_atendimento: R$
- comparacao_presencial: telemed vs presencial em custo, NPS e efetividade
- especialidades_mais_adequadas: para quais especialidades funciona melhor
- gargalos_tecnicos: problemas de plataforma e conectividade
- oportunidades_expansao: como crescer a operação
- modelo_hibrido: como integrar telemed com presencial
- regulatorio_cfm: status de compliance com regulações do CFM
- roi_telemedicina: retorno estimado sobre investimento"""

        result = self.ask_json(prompt, system=SYSTEM_HEALTH)
        score = result.get("score_telemed", 0)
        print(f"\n💻 Telemedicine Analytics — Score: {score}/100")
        m = result.get("metricas_chave", {})
        print(f"  Resolução 1a consulta: {m.get('taxa_resolucao_primeira_consulta_pct', '?')}%")
        print(f"  NPS: {m.get('nps_telemed', '?')}")
        self.save_result(result, prefix="telemedicine_analytics")
        return result

    def population_health(self, cohort: dict) -> dict:
        """Analisa saúde populacional de um grupo/cohort."""
        self.logger.info("Population health analysis")
        prompt = f"""Analise a saúde desta população/cohort e crie programa de intervenção:

COHORT:
{json.dumps(cohort, indent=2, ensure_ascii=False)[:4000]}

Retorne JSON com:
- perfil_epidemiologico: principais condições e fatores de risco
- estratificacao_risco: distribuição da população por nível de risco (baixo/médio/alto)
- doencas_prevalentes: top 5 condições mais comuns
- custos_estimados:
  - custo_atual_por_membro: R$/mês
  - custo_alta_complexidade: % do custo total
  - custo_emergencia_evitavel: R$ evitáveis com prevenção
- programa_gestao_saude:
  - acoes_prevencao: campanhas de prevenção prioritárias
  - gestao_doencas_cronicas: programa para crônicos de alto risco
  - incentivos_saude: como engajar população em cuidados preventivos
- roi_prevencao: economia estimada com programa preventivo
- kpis_saude_populacional: métricas para monitorar evolução
- cronograma_intervencao: quando implementar cada ação"""

        result = self.ask_json(prompt, system=SYSTEM_HEALTH)
        perfil = result.get("perfil_epidemiologico", "")
        print(f"\n👥 Population Health Analysis")
        print(f"  {str(perfil)[:100]}")
        roi = result.get("roi_prevencao", "?")
        print(f"  ROI prevenção: {roi}")
        self.save_result(result, prefix="population_health")
        return result


def main():
    parser = argparse.ArgumentParser(description="Health Agent — ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("clinic-ops").add_argument("--data", required=True)
    sub.add_parser("patient-journey").add_argument("--patient", required=True)

    p_hc = sub.add_parser("health-content")
    p_hc.add_argument("--topic", required=True)
    p_hc.add_argument("--audience", default="pacientes")

    sub.add_parser("telemedicine").add_argument("--metrics", required=True)
    sub.add_parser("population-health").add_argument("--cohort", required=True)

    args = parser.parse_args()
    agent = HealthAgent()
    def load(p): return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else {}

    if args.command == "clinic-ops":
        agent.clinic_operations(load(args.data))
    elif args.command == "patient-journey":
        agent.patient_journey(load(args.patient))
    elif args.command == "health-content":
        agent.health_content(args.topic, args.audience)
    elif args.command == "telemedicine":
        agent.telemedicine_analytics(load(args.metrics))
    elif args.command == "population-health":
        agent.population_health(load(args.cohort))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
