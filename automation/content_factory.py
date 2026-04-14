"""
Content Factory — ULTIMATE CRONUS
Fábrica de conteúdo em escala: blog, social, email, ads, vídeo scripts.

Uso:
    python content_factory.py monthly-plan --brand data/marca.json --topics 20
    python content_factory.py full-pack --topic "IA no RH" --brand data/marca.json
    python content_factory.py repurpose --content data/artigo.json --formats all
    python content_factory.py seo-cluster --keyword "automação empresarial" --articles 10
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))
from base_agent import BaseAgent

SYSTEM_FACTORY = """Você é a Content Factory do ULTIMATE CRONUS — uma máquina de produção de conteúdo.
Você cria conteúdo que educa, engaja e converte em todos os formatos.
Cada peça é otimizada para SEO, plataforma e estágio do funil."""


class ContentFactory(BaseAgent):
    def __init__(self):
        super().__init__(name="CONTENT_FACTORY", output_dir="automation/reports")

    def monthly_content_plan(self, brand: dict, num_topics: int = 20) -> dict:
        """Cria plano de conteúdo mensal completo."""
        self.logger.info(f"Plano mensal: {num_topics} tópicos")
        prompt = f"""Crie um plano de conteúdo mensal completo:

MARCA/EMPRESA:
{json.dumps(brand, indent=2, ensure_ascii=False)[:2000]}

METAS: {num_topics} peças de conteúdo no mês

Retorne JSON com:
- temas_pillar: 4-5 temas principais da marca
- calendario: lista de {num_topics} objetos com:
  - semana: 1-4
  - dia_publicacao: dia da semana recomendado
  - titulo: título do conteúdo
  - formato: "blog"|"linkedin"|"instagram"|"email"|"youtube"|"tiktok"
  - objetivo_funil: "topo"|"meio"|"fundo"
  - keyword_seo: palavra-chave alvo (se blog)
  - angulo: ângulo único do conteúdo
  - cta: call-to-action
  - tempo_producao_horas: estimativa
- distribuicao_por_formato: contagem por tipo
- metricas_alvo: KPIs do plano
- ferramentas_recomendadas: stack de produção"""

        result = self.ask_json(prompt, system=SYSTEM_FACTORY)
        calendario = result.get("calendario",[])
        print(f"\n📅 Content Plan — {len(calendario)} peças planejadas")
        dist = result.get("distribuicao_por_formato",{})
        for fmt, count in dist.items():
            print(f"  {fmt}: {count}")
        self.save_result(result, prefix="content_plan")
        return result

    def full_content_pack(self, topic: str, brand: dict) -> dict:
        """Gera pack completo de conteúdo em todos os formatos para um tópico."""
        self.logger.info(f"Content pack: {topic}")
        prompt = f"""Gere um pack completo de conteúdo sobre "{topic}":

MARCA:
{json.dumps(brand, indent=2, ensure_ascii=False)[:1000]}

Retorne JSON com:
- blog_post: artigo completo em Markdown (800-1200 palavras)
- linkedin_post: post longo para LinkedIn (1500 chars)
- instagram_caption: legenda + hashtags
- email_newsletter: email completo
- twitter_thread: 5-8 tweets em sequência
- youtube_script: roteiro de vídeo (5-8 min)
- tiktok_hook: gancho de 3 segundos + roteiro 60s
- quote_cards: 5 frases impactantes para cards visuais
- meta_description: 150 chars para SEO"""

        result = self.ask_json(prompt, system=SYSTEM_FACTORY)
        md = f"# Content Pack: {topic}\n\n"
        md += f"**Gerado:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n---\n\n"
        md += f"## Blog Post\n{result.get('blog_post','')}\n\n---\n\n"
        md += f"## LinkedIn\n{result.get('linkedin_post','')}\n\n---\n\n"
        md += f"## Email Newsletter\n{result.get('email_newsletter','')}\n\n"
        path = self.save_markdown(md, prefix="content_pack")
        self.save_result(result, prefix="content_pack")
        print(f"\n📦 Content Pack gerado → {path}")
        return result

    def repurpose_content(self, content: dict, formats: list | None = None) -> dict:
        """Repropósita um conteúdo existente para múltiplos formatos."""
        if formats is None:
            formats = ["linkedin", "instagram", "email", "twitter_thread", "video_script"]
        self.logger.info(f"Repurposing para: {formats}")

        content_text = content.get("texto") or content.get("content") or json.dumps(content)
        prompt = f"""Repropósita este conteúdo para os formatos: {', '.join(formats)}

CONTEÚDO ORIGINAL:
{content_text[:3000]}

Para cada formato, crie uma versão adaptada ao canal e seu público.
Retorne JSON com um campo para cada formato solicitado com o conteúdo adaptado.
Preserve a essência mas adapte tom, tamanho e estrutura de cada plataforma."""

        result = self.ask_json(prompt, system=SYSTEM_FACTORY)
        print(f"\n♻️  Repurposed para {len(formats)} formatos")
        for fmt in formats:
            if fmt in result:
                print(f"  ✅ {fmt}: {len(str(result[fmt]))} chars")
        self.save_result(result, prefix="content_repurposed")
        return result

    def seo_cluster(self, keyword: str, num_articles: int = 10) -> dict:
        """Cria cluster de SEO com artigos pillar e supporting."""
        self.logger.info(f"SEO cluster: '{keyword}' ({num_articles} artigos)")
        prompt = f"""Crie um cluster de conteúdo SEO para a keyword: "{keyword}"

Número de artigos: {num_articles}

Retorne JSON com:
- pillar_page: objeto com:
  - titulo: título do artigo principal
  - keyword_principal: keyword exata
  - outline: estrutura completa do artigo
  - word_count_alvo: número de palavras
- supporting_articles: lista de {num_articles-1} artigos de suporte com:
  - titulo: título
  - keyword: keyword alvo
  - intent: "informacional"|"navegacional"|"transacional"
  - link_para_pillar: como linkear para o artigo principal
  - outline: estrutura em tópicos
- estrategia_link_building: como construir links para este cluster
- internal_linking_map: mapa de links internos
- estimativa_trafego_mensal: visitas/mês esperadas após 6 meses"""

        result = self.ask_json(prompt, system=SYSTEM_FACTORY)
        supporting = result.get("supporting_articles",[])
        print(f"\n🔍 SEO Cluster: '{keyword}' — {len(supporting)+1} artigos")
        print(f"  Tráfego estimado: {result.get('estimativa_trafego_mensal','?')} visitas/mês")
        self.save_result(result, prefix="seo_cluster")
        return result


def main():
    parser = argparse.ArgumentParser(description="Content Factory — ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")
    p_mp = sub.add_parser("monthly-plan"); p_mp.add_argument("--brand", required=True); p_mp.add_argument("--topics", type=int, default=20)
    p_fp = sub.add_parser("full-pack"); p_fp.add_argument("--topic", required=True); p_fp.add_argument("--brand", required=True)
    p_rp = sub.add_parser("repurpose"); p_rp.add_argument("--content", required=True); p_rp.add_argument("--formats", default="linkedin,instagram,email,twitter_thread")
    p_seo = sub.add_parser("seo-cluster"); p_seo.add_argument("--keyword", required=True); p_seo.add_argument("--articles", type=int, default=10)

    args = parser.parse_args()
    agent = ContentFactory()
    def load(p): return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else {}

    if args.command == "monthly-plan": agent.monthly_content_plan(load(args.brand), args.topics)
    elif args.command == "full-pack": agent.full_content_pack(args.topic, load(args.brand))
    elif args.command == "repurpose":
        fmts = [f.strip() for f in args.formats.split(",")]; agent.repurpose_content(load(args.content), fmts)
    elif args.command == "seo-cluster": agent.seo_cluster(args.keyword, args.articles)
    else: parser.print_help()


if __name__ == "__main__":
    main()
