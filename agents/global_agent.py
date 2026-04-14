"""
GLOBAL Agent — ULTIMATE CRONUS
Expansão internacional, entrada em mercados, localização e go-to-market global.

Uso:
    python global_agent.py market-entry --company data/empresa.json --target-market "Europa"
    python global_agent.py localization --content data/conteudo.json --target-lang "en" --market "US"
    python global_agent.py regulatory --product data/produto.json --countries "BR,US,EU"
    python global_agent.py global-gtm --company data/empresa.json --markets data/mercados.json
    python global_agent.py competitor-map --industry "SaaS HR" --regions "LATAM,US,EU"
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from base_agent import BaseAgent

SYSTEM_GLOBAL = """Você é o GLOBAL, agente de Expansão Internacional do ULTIMATE CRONUS.
Você domina estratégias de internacionalização, localização cultural e go-to-market em novos mercados.
Pense como um VP of International Growth que já expandiu para 30+ países.
Equilibre velocidade de expansão com fit cultural e compliance regulatório."""


class GlobalAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="GLOBAL", output_dir="agents/output")

    def market_entry_strategy(self, company: dict, target_market: str) -> dict:
        """Cria estratégia de entrada em novo mercado."""
        self.logger.info(f"Market entry: {target_market}")
        prompt = f"""Crie uma estratégia completa de entrada no mercado: {target_market}

EMPRESA:
{json.dumps(company, indent=2, ensure_ascii=False)[:3000]}

Retorne JSON com:
- atratividade_mercado: score 0-100 e justificativa
- tamanho_mercado:
  - tam: Total Addressable Market em USD
  - sam: Serviceable Addressable Market
  - som: Serviceable Obtainable Market (ano 1)
- analise_competitiva_local: principais concorrentes no mercado alvo
- barreiras_entrada:
  - regulatorias: exigências legais e de compliance
  - culturais: diferenças culturais relevantes
  - tecnologicas: adaptações necessárias
  - financeiras: custo de entrada estimado
- modelo_entrada_recomendado: "direto"|"parceiro_local"|"aquisicao"|"joint_venture"|"franchise"
- parceiros_estrategicos: tipo de parceiro ideal no mercado alvo
- cronograma:
  - mes_1_3: ações de preparação
  - mes_4_6: entrada e validação
  - mes_7_12: escala e crescimento
- investimento_necessario: faixa de investimento para entrar
- kpis_sucesso_ano1: métricas de sucesso no primeiro ano
- riscos_criticos: top 3 riscos e mitigation
- decisao_recomendada: "entrar_agora"|"entrar_em_6m"|"aguardar"|"nao_entrar"
- proximos_passos: ações concretas para as próximas 2 semanas"""

        result = self.ask_json(prompt, system=SYSTEM_GLOBAL)
        score = result.get("atratividade_mercado", {})
        if isinstance(score, dict):
            score_val = score.get("score", 0)
        else:
            score_val = score
        print(f"\n🌍 Market Entry: {target_market} — Atratividade: {score_val}/100")
        print(f"  Modelo: {result.get('modelo_entrada_recomendado', '?')}")
        print(f"  Decisão: {result.get('decisao_recomendada', '?')}")
        self.save_result(result, prefix=f"market_entry_{target_market.replace(' ', '_').lower()}")
        return result

    def localize_content(self, content: dict, target_lang: str, market: str) -> dict:
        """Localiza conteúdo para mercado e idioma alvo."""
        self.logger.info(f"Localization: {target_lang}/{market}")
        content_text = content.get("texto") or content.get("content") or json.dumps(content)
        prompt = f"""Localize este conteúdo para o mercado {market} em {target_lang}:

CONTEÚDO ORIGINAL:
{content_text[:3000]}

Retorne JSON com:
- conteudo_traduzido: versão traduzida e localizada
- adaptacoes_culturais: mudanças feitas por razões culturais (não só tradução)
- referencias_locais: referências culturais locais adicionadas
- tom_ajustado: como o tom foi ajustado para o mercado
- termos_tecnicos_locais: glossário de termos específicos do mercado
- o_que_nao_funciona: elementos do original que não funcionam neste mercado
- sugestoes_adicionais: ideias específicas para engajar este mercado
- nivel_localizacao: "traducao_basica"|"adaptado"|"criado_localmente"
- revisao_necessaria: itens que precisam de revisão por nativo local"""

        result = self.ask_json(prompt, system=SYSTEM_GLOBAL)
        print(f"\n🌐 Localization: {target_lang}/{market}")
        print(f"  Nível: {result.get('nivel_localizacao', '?')}")
        adaptacoes = result.get("adaptacoes_culturais", [])
        print(f"  Adaptações culturais: {len(adaptacoes) if isinstance(adaptacoes, list) else '?'}")
        self.save_result(result, prefix=f"localized_{target_lang}_{market}")
        return result

    def regulatory_analysis(self, product: dict, countries: list) -> dict:
        """Analisa requisitos regulatórios por país."""
        self.logger.info(f"Regulatory: {countries}")
        prompt = f"""Analise os requisitos regulatórios para este produto nos países indicados:

PRODUTO/SERVIÇO:
{json.dumps(product, indent=2, ensure_ascii=False)[:2000]}

PAÍSES: {', '.join(countries)}

Retorne JSON com:
- analise_por_pais: para cada país:
  - pais: nome
  - complexidade_regulatoria: "baixa"|"media"|"alta"|"muito_alta"
  - requisitos_principais: lista dos principais requisitos
  - licencas_necessarias: licenças e registros obrigatórios
  - protecao_dados: requisitos de privacidade (LGPD, GDPR, etc)
  - restricoes_produto: o que pode/não pode fazer
  - tempo_estimado_compliance: meses para estar em conformidade
  - custo_estimado_compliance: faixa em USD
- pais_mais_facil: qual país tem menor barreira regulatória
- pais_mais_dificil: qual tem maior barreira
- estrategia_compliance: como abordar o compliance em paralelo
- riscos_regulatorios: principais riscos e penalidades
- parceiros_juridicos_recomendados: tipo de expertise legal necessária"""

        result = self.ask_json(prompt, system=SYSTEM_GLOBAL)
        print(f"\n⚖️  Regulatory Analysis — {len(countries)} países")
        mais_facil = result.get("pais_mais_facil", "?")
        mais_dificil = result.get("pais_mais_dificil", "?")
        print(f"  Mais fácil: {mais_facil} | Mais difícil: {mais_dificil}")
        self.save_result(result, prefix="regulatory_analysis")
        return result

    def global_gtm(self, company: dict, markets: list) -> dict:
        """Cria go-to-market global para múltiplos mercados."""
        self.logger.info(f"Global GTM: {len(markets)} mercados")
        prompt = f"""Crie uma estratégia de go-to-market global:

EMPRESA:
{json.dumps(company, indent=2, ensure_ascii=False)[:2000]}

MERCADOS ALVO:
{json.dumps(markets, indent=2, ensure_ascii=False)[:2000]}

Retorne JSON com:
- sequencia_entrada: ordem recomendada para entrar nos mercados e por quê
- estrategia_global: abordagem geral (standardized vs localized)
- playbook_por_mercado: para cada mercado:
  - mercado: nome
  - prioridade: 1-5
  - modelo_gtm: como entrar
  - icp_local: perfil do cliente ideal local
  - canais_aquisicao: canais mais efetivos neste mercado
  - parceiros_locais: tipo de parceiro ideal
  - meta_ano1: revenue e clientes esperados
- estrutura_time_global: como organizar o time para suportar expansão
- budget_global: distribuição orçamentária por mercado e trimestre
- metricas_globais: KPIs unificados para acompanhar expansão
- riscos_expansao: riscos sistêmicos de expandir muito rápido"""

        result = self.ask_json(prompt, system=SYSTEM_GLOBAL)
        seq = result.get("sequencia_entrada", [])
        print(f"\n🌏 Global GTM — {len(markets)} mercados, sequência: {seq}")
        self.save_result(result, prefix="global_gtm")
        return result

    def competitor_map(self, industry: str, regions: list) -> dict:
        """Mapeia competição global por região."""
        self.logger.info(f"Competitor map: {industry} in {regions}")
        prompt = f"""Mapeie o panorama competitivo global:

INDÚSTRIA: {industry}
REGIÕES: {', '.join(regions)}

Retorne JSON com:
- lideres_globais: top players mundiais com descrição
- players_por_regiao: para cada região:
  - regiao: nome
  - lider_local: principal player local
  - diferenciais_locais: o que os players locais fazem diferente
  - oportunidade_gap: espaço não coberto no mercado
- tendencias_globais: trends que afetam a indústria globalmente
- diferenciacoes_por_mercado: como os players adaptam oferta por mercado
- white_spaces: mercados/regiões sem player forte
- ameacas_emergentes: startups ou disruptors que podem mudar o jogo
- implicacoes_estrategicas: o que isso significa para expansão"""

        result = self.ask_json(prompt, system=SYSTEM_GLOBAL)
        white_spaces = result.get("white_spaces", [])
        print(f"\n🗺️  Competitor Map — {industry}")
        print(f"  White spaces: {len(white_spaces) if isinstance(white_spaces, list) else '?'} oportunidades")
        self.save_result(result, prefix="competitor_map_global")
        return result


def main():
    parser = argparse.ArgumentParser(description="GLOBAL Agent — ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")

    p_me = sub.add_parser("market-entry")
    p_me.add_argument("--company", required=True)
    p_me.add_argument("--target-market", required=True)

    p_loc = sub.add_parser("localization")
    p_loc.add_argument("--content", required=True)
    p_loc.add_argument("--target-lang", required=True)
    p_loc.add_argument("--market", required=True)

    p_reg = sub.add_parser("regulatory")
    p_reg.add_argument("--product", required=True)
    p_reg.add_argument("--countries", required=True)

    p_gtm = sub.add_parser("global-gtm")
    p_gtm.add_argument("--company", required=True)
    p_gtm.add_argument("--markets", required=True)

    p_cm = sub.add_parser("competitor-map")
    p_cm.add_argument("--industry", required=True)
    p_cm.add_argument("--regions", required=True)

    args = parser.parse_args()
    agent = GlobalAgent()
    def load(p): return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else {}

    if args.command == "market-entry":
        agent.market_entry_strategy(load(args.company), args.target_market)
    elif args.command == "localization":
        agent.localize_content(load(args.content), args.target_lang, args.market)
    elif args.command == "regulatory":
        countries = [c.strip() for c in args.countries.split(",")]
        agent.regulatory_analysis(load(args.product), countries)
    elif args.command == "global-gtm":
        markets_data = load(args.markets)
        agent.global_gtm(load(args.company), markets_data if isinstance(markets_data, list) else [])
    elif args.command == "competitor-map":
        regions = [r.strip() for r in args.regions.split(",")]
        agent.competitor_map(args.industry, regions)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
