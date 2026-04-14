"""
SCRIBE Agent — ULTIMATE CRONUS
Geração de conteúdo de marketing, copy e documentação em escala.

Uso:
    python scribe_agent.py copy --product "SaaS de RH" --audience "RH de PMEs" --format email --variations 5
    python scribe_agent.py email-sequence --goal "converter trial em pago" --steps 7
    python scribe_agent.py social-posts --topic "lançamento de produto" --platforms linkedin,instagram --count 10
    python scribe_agent.py blog-post --topic "IA no RH" --keywords "automação,contratação" --words 1500
    python scribe_agent.py score --file output/scribe/copy_20260408.md
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from base_agent import BaseAgent


SYSTEM_SCRIBE = """Você é o SCRIBE, agente especialista em copywriting e marketing de conteúdo do ULTIMATE CRONUS.
Você escreve copy que converte: direto, persuasivo, orientado a benefícios, sem jargão desnecessário.
Seu conteúdo é sempre adaptado ao público-alvo e ao objetivo de negócio específico.
Use frameworks como AIDA, PAS, StoryBrand quando aplicável."""


class ScribeAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="SCRIBE",
            output_dir="output/scribe",
        )

    def generate_copy(self, product: str, audience: str, format: str, variations: int = 5) -> list[dict]:
        """Gera N variações de copy para um produto/serviço."""
        self.logger.info(f"Gerando {variations} variações de copy para '{product}'")
        prompt = f"""Gere {variations} variações de copy para:

PRODUTO/SERVIÇO: {product}
PÚBLICO-ALVO: {audience}
FORMATO: {format}

Para cada variação, retorne JSON com:
- id: número da variação
- headline: título principal (max 10 palavras)
- subheadline: subtítulo (max 20 palavras)
- body: corpo do texto (adequado ao formato)
- cta: call-to-action (max 5 palavras)
- angle: ângulo usado (ex: "medo de perder", "transformação", "prova social")
- score_estimado: 0-100 (sua estimativa de conversão)

Responda com array JSON de {variations} objetos."""

        result = self.ask_json(prompt, system=SYSTEM_SCRIBE)
        variations_list = result if isinstance(result, list) else result.get("variations", [result])

        path = self.save_result(
            {"product": product, "audience": audience, "format": format, "variations": variations_list},
            prefix="copy",
        )
        print(f"\n✍️  {len(variations_list)} variações de copy geradas → {path}\n")
        for v in variations_list:
            print(f"  [{v.get('id','')}] {v.get('headline','')} (score: {v.get('score_estimado','')})")
        return variations_list

    def write_email_sequence(self, goal: str, steps: int = 5) -> list[dict]:
        """Gera sequência completa de emails de nurturing."""
        self.logger.info(f"Gerando sequência de {steps} emails para: {goal}")
        prompt = f"""Crie uma sequência de {steps} emails de nurturing para:
OBJETIVO: {goal}

Para cada email, retorne JSON com:
- step: número do email (1 a {steps})
- day: dia do envio (ex: 0, 1, 3, 7, 14)
- subject: assunto (max 50 chars, inclua [número] no início ex: [1/5])
- preview_text: preview do email (max 90 chars)
- body: corpo completo do email em Markdown
- cta_text: texto do botão CTA
- cta_url_placeholder: placeholder da URL (ex: {{{{link_checkout}}}})
- objetivo_do_email: o que este email específico deve alcançar

Responda com array JSON de {steps} objetos."""

        result = self.ask_json(prompt, system=SYSTEM_SCRIBE)
        emails = result if isinstance(result, list) else result.get("emails", [result])

        md = f"# Sequência de Emails — {goal}\n\n"
        for e in emails:
            md += f"## Email {e.get('step','?')} — Dia {e.get('day','?')}\n"
            md += f"**Assunto:** {e.get('subject','')}\n"
            md += f"**Preview:** {e.get('preview_text','')}\n\n"
            md += f"{e.get('body','')}\n\n"
            md += f"**CTA:** {e.get('cta_text','')}\n\n---\n\n"

        path = self.save_markdown(md, prefix="email_sequence")
        self.save_result({"goal": goal, "steps": steps, "emails": emails}, prefix="email_sequence")
        print(f"\n📧  Sequência de {len(emails)} emails gerada → {path}\n")
        for e in emails:
            print(f"  Dia {e.get('day','?'):>2}: {e.get('subject','')}")
        return emails

    def create_social_posts(self, topic: str, platforms: list[str], count: int = 10) -> dict:
        """Gera posts para múltiplas redes sociais."""
        self.logger.info(f"Gerando {count} posts sobre '{topic}' para {platforms}")
        prompt = f"""Crie {count} posts sobre "{topic}" para as plataformas: {', '.join(platforms)}.

Para cada post, retorne JSON com:
- id: número do post
- platform: plataforma (uma de: {', '.join(platforms)})
- content: texto completo do post (respeitando limite de caracteres da plataforma)
- hashtags: lista de hashtags relevantes (só para Instagram/Twitter/LinkedIn)
- hook: primeiras palavras que param o scroll
- format: tipo de post (carrossel, reels, texto, artigo, etc)
- best_time: melhor horário de publicação (ex: "Ter-Qui 18h-20h")

Distribua os {count} posts entre as plataformas de forma equilibrada.
Responda com array JSON de {count} objetos."""

        result = self.ask_json(prompt, system=SYSTEM_SCRIBE)
        posts = result if isinstance(result, list) else result.get("posts", [result])

        path = self.save_result({"topic": topic, "platforms": platforms, "posts": posts}, prefix="social_posts")
        print(f"\n📱  {len(posts)} posts gerados → {path}\n")
        for p in posts:
            print(f"  [{p.get('platform','?'):10}] {str(p.get('hook',''))[:60]}...")
        return {"posts": posts, "path": str(path)}

    def write_blog_post(self, topic: str, keywords: list[str], word_count: int = 1500) -> str:
        """Gera artigo de blog completo e otimizado para SEO."""
        self.logger.info(f"Gerando artigo sobre '{topic}' ({word_count} palavras)")
        prompt = f"""Escreva um artigo de blog completo sobre "{topic}".

PALAVRAS-CHAVE: {', '.join(keywords)}
TAMANHO ALVO: {word_count} palavras
FORMATO: Markdown com H1, H2, H3, listas, negrito

ESTRUTURA OBRIGATÓRIA:
1. H1: Título principal (com keyword principal)
2. Introdução: 150 palavras — hook + problema + o que o leitor vai aprender
3. 4-6 seções H2 com conteúdo substantivo
4. Conclusão com CTA claro
5. Meta description (150-160 chars) ao final

Escreva o artigo completo em Markdown, pronto para publicar."""

        article = self.ask(prompt, system=SYSTEM_SCRIBE, max_tokens=16000)
        path = self.save_markdown(article, prefix="blog_post")
        words = len(article.split())
        print(f"\n📝  Artigo gerado ({words} palavras) → {path}\n")
        print(f"  Tópico: {topic}")
        print(f"  Keywords: {', '.join(keywords)}")
        return article

    def generate_ad_creatives(self, product: str, audience: str, budget_level: str = "medio") -> list[dict]:
        """Gera criativos de anúncios para diferentes formatos."""
        self.logger.info(f"Gerando criativos de ads para '{product}'")
        prompt = f"""Crie 8 criativos de anúncio para:
PRODUTO: {product}
PÚBLICO: {audience}
NÍVEL DE BUDGET: {budget_level} (baixo/medio/alto)

Para cada criativo, retorne JSON com:
- id: número
- platform: plataforma (Meta/Google/LinkedIn/TikTok)
- format: formato (Feed/Stories/Search/Display/Video)
- headline: título principal
- description: descrição
- cta: botão de ação
- visual_concept: descrição do visual/imagem ideal
- hook_type: tipo de hook (dor, curiosidade, prova social, oferta, autoridade)
- objetivo: awareness/consideracao/conversao

Responda com array JSON de 8 objetos."""

        result = self.ask_json(prompt, system=SYSTEM_SCRIBE)
        creatives = result if isinstance(result, list) else result.get("creatives", [result])

        path = self.save_result({"product": product, "audience": audience, "creatives": creatives}, prefix="ad_creatives")
        print(f"\n🎯  {len(creatives)} criativos gerados → {path}\n")
        for c in creatives:
            print(f"  [{c.get('platform','?'):8}/{c.get('format','?'):10}] {c.get('headline','')}")
        return creatives

    def score_content(self, content: str, criteria: dict | None = None) -> dict:
        """Avalia qualidade de um conteúdo de 0 a 100."""
        if criteria is None:
            criteria = {
                "clareza": "O texto é claro e fácil de entender?",
                "persuasao": "O texto é persuasivo e convincente?",
                "cta": "O call-to-action é claro e forte?",
                "publico": "O tom está adequado ao público?",
                "seo": "O conteúdo está otimizado para SEO?",
            }

        criteria_text = "\n".join([f"- {k}: {v}" for k, v in criteria.items()])
        prompt = f"""Avalie este conteúdo de marketing segundo os critérios abaixo.

CONTEÚDO:
{content[:3000]}

CRITÉRIOS:
{criteria_text}

Retorne JSON com:
- score_total: nota geral de 0-100
- criterios: objeto com nota 0-100 para cada critério
- pontos_fortes: lista de 3 pontos fortes
- melhorias: lista de 3 sugestões de melhoria prioritárias
- versao_melhorada: reescreva o título/headline principal melhorado"""

        result = self.ask_json(prompt, system=SYSTEM_SCRIBE)
        print(f"\n🏆  Score: {result.get('score_total', '?')}/100")
        for k, v in result.get("criterios", {}).items():
            bar = "█" * (v // 10) + "░" * (10 - v // 10)
            print(f"  {k:12} {bar} {v}")
        return result


def main():
    parser = argparse.ArgumentParser(description="SCRIBE — Geração de Conteúdo em Escala")
    sub = parser.add_subparsers(dest="command")

    # copy
    p_copy = sub.add_parser("copy", help="Gerar variações de copy")
    p_copy.add_argument("--product", required=True)
    p_copy.add_argument("--audience", required=True)
    p_copy.add_argument("--format", default="email")
    p_copy.add_argument("--variations", type=int, default=5)

    # email-sequence
    p_email = sub.add_parser("email-sequence", help="Sequência de emails")
    p_email.add_argument("--goal", required=True)
    p_email.add_argument("--steps", type=int, default=5)

    # social-posts
    p_social = sub.add_parser("social-posts", help="Posts para redes sociais")
    p_social.add_argument("--topic", required=True)
    p_social.add_argument("--platforms", default="linkedin,instagram")
    p_social.add_argument("--count", type=int, default=10)

    # blog-post
    p_blog = sub.add_parser("blog-post", help="Artigo de blog")
    p_blog.add_argument("--topic", required=True)
    p_blog.add_argument("--keywords", default="")
    p_blog.add_argument("--words", type=int, default=1500)

    # ads
    p_ads = sub.add_parser("ads", help="Criativos de anúncios")
    p_ads.add_argument("--product", required=True)
    p_ads.add_argument("--audience", required=True)
    p_ads.add_argument("--budget", default="medio")

    # score
    p_score = sub.add_parser("score", help="Avaliar conteúdo")
    p_score.add_argument("--file", required=True)

    args = parser.parse_args()
    agent = ScribeAgent()

    if args.command == "copy":
        agent.generate_copy(args.product, args.audience, args.format, args.variations)
    elif args.command == "email-sequence":
        agent.write_email_sequence(args.goal, args.steps)
    elif args.command == "social-posts":
        platforms = [p.strip() for p in args.platforms.split(",")]
        agent.create_social_posts(args.topic, platforms, args.count)
    elif args.command == "blog-post":
        keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
        agent.write_blog_post(args.topic, keywords, args.words)
    elif args.command == "ads":
        agent.generate_ad_creatives(args.product, args.audience, args.budget)
    elif args.command == "score":
        content = Path(args.file).read_text(encoding="utf-8")
        agent.score_content(content)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
