"""
SEO Automation — ULTIMATE CRONUS
Automação completa de SEO: auditoria, keywords, conteúdo, link building e technical SEO.

Uso:
    python seo_automation.py audit --site data/site.json
    python seo_automation.py keyword-research --niche "software RH" --country "BR"
    python seo_automation.py content-brief --keyword "melhor crm para pequenas empresas"
    python seo_automation.py link-building --site data/site.json --niche "SaaS"
    python seo_automation.py competitor-seo --competitors data/concorrentes.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))
from base_agent import BaseAgent

SYSTEM_SEO = """Você é o especialista em SEO do ULTIMATE CRONUS.
Você domina SEO técnico, content SEO, link building e SEO para SaaS e e-commerce.
Pense como um SEO Lead de agência de resultados com foco em tráfego orgânico que converte.
Priorize intenção de busca, não apenas volume. Foque em páginas que geram receita."""


class SeoAutomation(BaseAgent):
    def __init__(self):
        super().__init__(name="SEO", output_dir="automation/reports")

    def site_audit(self, site: dict) -> dict:
        """Auditoria completa de SEO do site."""
        self.logger.info(f"SEO audit: {site.get('url','?')}")
        prompt = f"""Faça uma auditoria completa de SEO para este site:

SITE:
{json.dumps(site, indent=2, ensure_ascii=False)[:4000]}

Retorne JSON com:
- score_seo: 0-100
- seo_tecnico:
  - velocidade_carregamento: análise e score
  - core_web_vitals: LCP, FID, CLS status
  - mobile_first: compatibilidade mobile
  - https: status e configuração
  - crawlability: robots.txt, sitemap, canonical
  - estrutura_urls: análise de URLs
  - schema_markup: dados estruturados implementados
- on_page:
  - titles_e_metas: análise de title tags e meta descriptions
  - headers: uso de H1, H2, H3
  - conteudo: qualidade e profundidade
  - imagens: alt texts e otimização
  - links_internos: estrutura de links internos
- off_page:
  - backlinks_estimados: quantidade e qualidade estimada
  - domain_authority_estimado: score de autoridade
  - anchor_text_distribution: variedade de anchor texts
- problemas_criticos: erros que prejudicam muito o SEO agora
- quick_wins: melhorias rápidas de alto impacto
- roadmap_seo: plano de 3 meses para crescer organicamente"""

        result = self.ask_json(prompt, system=SYSTEM_SEO)
        score = result.get("score_seo", 0)
        problemas = result.get("problemas_criticos", [])
        print(f"\n🔍 SEO Audit — {site.get('url','?')}: {score}/100")
        print(f"  Problemas críticos: {len(problemas) if isinstance(problemas, list) else '?'}")
        quick = result.get("quick_wins", [])
        if isinstance(quick, list):
            for qw in quick[:3]:
                print(f"  ✓ {str(qw)[:80]}")
        self.save_result(result, prefix="seo_audit")
        return result

    def keyword_research(self, niche: str, country: str = "BR") -> dict:
        """Pesquisa completa de keywords para um nicho."""
        self.logger.info(f"Keyword research: {niche} / {country}")
        prompt = f"""Faça uma pesquisa completa de palavras-chave para o nicho: "{niche}" no {country}

Retorne JSON com:
- keywords_principais: 20 palavras-chave primárias com:
  - keyword: termo
  - volume_mensal_estimado: buscas/mês
  - dificuldade: "baixa"|"media"|"alta"|"muito_alta"
  - intencao: "informacional"|"comercial"|"transacional"|"navegacional"
  - cpc_estimado: R$ (para Google Ads)
  - oportunidade: score 0-100
- keywords_cauda_longa: 30 long-tail keywords com menor competição
- keywords_pergunta: "como fazer", "o que é", "por que" — para featured snippets
- keywords_comparacao: "X vs Y", "melhor X para Y" — alta intenção comercial
- keywords_locais: variações com localização se relevante
- clusters_tematicos: agrupamento por tema para estrutura de conteúdo
- keywords_evitar: termos com alta competição e baixo retorno
- estrategia_prioridade: por onde começar (menor esforço, maior impacto)
- oportunidades_featured_snippets: keywords onde pode rankear na posição 0"""

        result = self.ask_json(prompt, system=SYSTEM_SEO)
        principais = result.get("keywords_principais", [])
        cauda = result.get("keywords_cauda_longa", [])
        print(f"\n🔑 Keyword Research — {niche}")
        print(f"  Principais: {len(principais)} | Long-tail: {len(cauda)}")
        # Show top 5 opportunities
        if isinstance(principais, list):
            sorted_kw = sorted([k for k in principais if isinstance(k, dict)], key=lambda x: x.get("oportunidade",0), reverse=True)
            for kw in sorted_kw[:5]:
                print(f"  ⭐ {kw.get('keyword','?'):<40} vol:{kw.get('volume_mensal_estimado','?')} dif:{kw.get('dificuldade','?')}")
        self.save_result(result, prefix=f"keyword_research_{niche.replace(' ','_').lower()[:25]}")
        return result

    def content_brief(self, keyword: str) -> dict:
        """Cria brief completo de conteúdo para uma keyword."""
        self.logger.info(f"Content brief: {keyword}")
        prompt = f"""Crie um brief completo de conteúdo para rankear na keyword: "{keyword}"

Retorne JSON com:
- analise_serp: o que aparece atualmente no Google para esta keyword
- intencao_busca: o que o usuário realmente quer ao pesquisar isso
- tipo_conteudo_ideal: blog post|landing page|pillar page|comparison|etc
- titulo_otimizado: título principal com a keyword (máx 60 chars)
- titulos_alternativos: 5 variações de título para testar
- estrutura_artigo:
  - introducao: o que cobrir nos primeiros parágrafos
  - h2s: lista de H2 com subtópicos para cada um
  - h3s: H3s relevantes por seção
  - conclusao: o que incluir
- palavra_chave_primaria: keyword principal e densidade ideal
- keywords_semanticas: LSI keywords e variações a incluir naturalmente
- comprimento_ideal_palavras: quantas palavras o artigo deve ter
- elementos_obrigatorios: imagens, tabelas, listas, exemplos, dados
- links_internos: páginas do próprio site para linkar
- links_externos: tipo de fontes a citar para autoridade
- meta_description: meta description otimizada (150-160 chars)
- cta_interno: como converter o leitor em lead
- tempo_estimado_producao_horas: para produzir este conteúdo"""

        result = self.ask_json(prompt, system=SYSTEM_SEO)
        titulo = result.get("titulo_otimizado","?")
        palavras = result.get("comprimento_ideal_palavras","?")
        print(f"\n📝 Content Brief — {keyword}")
        print(f"  Título: {titulo}")
        print(f"  Tamanho ideal: {palavras} palavras")
        h2s = result.get("estrutura_artigo",{}).get("h2s",[])
        if isinstance(h2s, list):
            for h2 in h2s[:5]:
                print(f"  H2: {str(h2)[:70]}")
        self.save_result(result, prefix=f"content_brief_{keyword[:30].replace(' ','_').lower()}")
        return result

    def link_building_strategy(self, site: dict, niche: str) -> dict:
        """Cria estratégia de link building para o site."""
        self.logger.info(f"Link building: {niche}")
        prompt = f"""Crie uma estratégia completa de link building:

SITE:
{json.dumps(site, indent=2, ensure_ascii=False)[:2000]}

NICHO: {niche}

Retorne JSON com:
- estrategias_link_building:
  - guest_posts: como conseguir posts em outros sites do nicho
  - digital_pr: como gerar backlinks por meio de relações públicas digitais
  - broken_link_building: metodologia para encontrar links quebrados e substituir
  - resource_pages: como entrar em páginas de recursos do nicho
  - skyscraper: criar conteúdo melhor que o que já rankeia
  - linkable_assets: que tipo de conteúdo naturalmente atrai links
  - link_insercao: como fazer link insertion em artigos existentes
- tipos_sites_alvo: perfil de sites de onde buscar links
- sites_blacklist: tipos de sites a evitar (penalização)
- anchor_text_strategy: como variar os anchor texts naturalmente
- ritmo_aquisicao: quantos links por mês para crescer sem riscos
- ferramentas_necessarias: Ahrefs, Semrush, Hunter.io, etc
- template_outreach: email para solicitar link building
- metricas_link_building: como medir qualidade dos links obtidos
- plano_3_meses: quantos e que tipo de links buscar por mês"""

        result = self.ask_json(prompt, system=SYSTEM_SEO)
        print(f"\n🔗 Link Building — {niche}")
        ritmo = result.get("ritmo_aquisicao","?")
        print(f"  Ritmo: {ritmo} links/mês")
        estrategias = result.get("estrategias_link_building",{})
        for e in list(estrategias.keys())[:4]:
            print(f"  ✓ {e}")
        self.save_result(result, prefix="link_building_strategy")
        return result

    def competitor_seo(self, competitors: list) -> dict:
        """Análise de SEO dos concorrentes para identificar oportunidades."""
        self.logger.info(f"Competitor SEO: {len(competitors)} concorrentes")
        prompt = f"""Analise o SEO dos concorrentes e identifique oportunidades:

CONCORRENTES ({len(competitors)}):
{json.dumps(competitors, indent=2, ensure_ascii=False)[:4000]}

Retorne JSON com:
- analise_por_concorrente: para cada concorrente:
  - nome: nome
  - domain_authority_estimado: score de autoridade
  - trafego_organico_estimado: visitas/mês
  - keywords_rankeando: estimativa de palavras-chave
  - top_pages: páginas com mais tráfego estimado
  - pontos_fortes_seo: onde são bons
  - pontos_fracos_seo: onde têm gaps
- keywords_gap: keywords que concorrentes rankeiam mas nós não
- conteudo_gap: tipos de conteúdo que concorrentes têm mas nós não
- oportunidades_rapidas: keywords fáceis de roubar posição
- baclinks_gap: sites que linkam para concorrentes mas não para nós
- estrategia_baseada_na_analise: como superar cada concorrente organicamente"""

        result = self.ask_json(prompt, system=SYSTEM_SEO)
        print(f"\n🕵️  Competitor SEO — {len(competitors)} concorrentes")
        gaps = result.get("keywords_gap",[])
        print(f"  Keyword gaps: {len(gaps) if isinstance(gaps, list) else '?'} oportunidades")
        self.save_result(result, prefix="competitor_seo")
        return result


def main():
    parser = argparse.ArgumentParser(description="SEO Automation — ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("audit").add_argument("--site", required=True)

    p_kr = sub.add_parser("keyword-research")
    p_kr.add_argument("--niche", required=True)
    p_kr.add_argument("--country", default="BR")

    sub.add_parser("content-brief").add_argument("--keyword", required=True)

    p_lb = sub.add_parser("link-building")
    p_lb.add_argument("--site", required=True)
    p_lb.add_argument("--niche", required=True)

    sub.add_parser("competitor-seo").add_argument("--competitors", required=True)

    args = parser.parse_args()
    agent = SeoAutomation()
    def load(p): return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else {}

    if args.command == "audit":
        agent.site_audit(load(args.site))
    elif args.command == "keyword-research":
        agent.keyword_research(args.niche, args.country)
    elif args.command == "content-brief":
        agent.content_brief(args.keyword)
    elif args.command == "link-building":
        agent.link_building_strategy(load(args.site), args.niche)
    elif args.command == "competitor-seo":
        data = load(args.competitors)
        agent.competitor_seo(data if isinstance(data, list) else data.get("competitors",[]))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
