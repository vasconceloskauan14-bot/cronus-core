"""
Social Media Automation — ULTIMATE CRONUS
Gestão completa de redes sociais: calendário, criação, análise e crescimento.

Uso:
    python social_media.py calendar --brand data/marca.json --month "Abril 2026"
    python social_media.py create --topic "IA no RH" --platforms instagram,linkedin,twitter
    python social_media.py analyze --metrics data/social_metrics.json
    python social_media.py influencer --niche "tech B2B" --budget 5000
    python social_media.py viral-hooks --product data/produto.json --count 20
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))
from base_agent import BaseAgent

SYSTEM_SOCIAL = """Você é o Social Media Manager do ULTIMATE CRONUS.
Você domina Instagram, LinkedIn, Twitter/X, TikTok, YouTube Shorts e Pinterest.
Pense em engajamento, viralidade, algorithm hacks e crescimento orgânico.
Cada post deve ter um objetivo claro: awareness, engajamento, tráfego ou conversão."""


class SocialMediaAutomation(BaseAgent):
    def __init__(self):
        super().__init__(name="SOCIAL_MEDIA", output_dir="automation/reports")

    def content_calendar(self, brand: dict, month: str) -> dict:
        """Cria calendário editorial completo para o mês."""
        self.logger.info(f"Content calendar: {month}")
        prompt = f"""Crie um calendário editorial completo para {month}:

MARCA:
{json.dumps(brand, indent=2, ensure_ascii=False)[:2000]}

Retorne JSON com:
- estrategia_mes: tema e narrativa do mês
- pilares_conteudo: 3-5 pilares que guiam o conteúdo
- calendario_posts: lista de 30-40 posts com:
  - data: dia do mês
  - plataforma: instagram|linkedin|twitter|tiktok|youtube
  - tipo: "feed"|"stories"|"reels"|"carrossel"|"thread"|"shorts"
  - pilar: qual pilar de conteúdo
  - tema: sobre o que é o post
  - gancho: primeira linha / hook que prende
  - objetivo: awareness|engajamento|tráfego|conversão
  - melhor_horario: hora de publicação recomendada
  - hashtags: 5-10 hashtags para o post
- distribuicao_por_plataforma: quantos posts em cada rede
- conteudos_reutilizaveis: posts que podem ser adaptados para múltiplas plataformas
- campanhas_especiais: datas ou momentos especiais do mês
- meta_crescimento: expectativa de crescimento de seguidores/engajamento"""

        result = self.ask_json(prompt, system=SYSTEM_SOCIAL)
        posts = result.get("calendario_posts", [])
        print(f"\n📅 Content Calendar — {month}: {len(posts)} posts planejados")
        dist = result.get("distribuicao_por_plataforma", {})
        for p, c in dist.items():
            print(f"  {p}: {c} posts")
        self.save_result(result, prefix=f"social_calendar_{month.replace(' ', '_').lower()}")
        return result

    def create_posts(self, topic: str, platforms: list) -> dict:
        """Cria posts completos para múltiplas plataformas."""
        self.logger.info(f"Creating posts: {topic} → {platforms}")
        prompt = f"""Crie posts completos sobre "{topic}" para as plataformas: {', '.join(platforms)}

Para cada plataforma, adapte formato, tom e tamanho.

Retorne JSON com posts para cada plataforma solicitada:
- instagram_feed: legenda completa + 20-30 hashtags + sugestão de visual
- instagram_stories: sequência de 3-5 stories (texto de cada slide)
- instagram_reels: gancho (3s) + roteiro de 30-60s + legenda
- linkedin_post: post profissional longo (1500-2000 chars) com formatting
- twitter_thread: thread de 8-12 tweets em sequência (280 chars cada)
- tiktok_script: gancho + roteiro de 60s + legenda + sons sugeridos
- youtube_shorts: título + roteiro de 60s + descrição + tags
- pinterest_pin: título + descrição + palavras-chave para SEO

Para cada plataforma incluir também:
- melhor_horario_postagem: hora ideal
- objetivo_post: o que quer alcançar
- cta: call to action específico"""

        result = self.ask_json(prompt, system=SYSTEM_SOCIAL)
        print(f"\n📱 Posts Created — {topic}")
        for platform in platforms:
            key = f"{platform}_post" if platform not in ["instagram", "tiktok"] else f"{platform}_feed"
            content = result.get(key, result.get(platform, ""))
            if content:
                print(f"  ✅ {platform}: {len(str(content))} chars")
        self.save_result(result, prefix=f"social_posts_{topic[:30].replace(' ', '_').lower()}")
        return result

    def analyze_performance(self, metrics: dict) -> dict:
        """Analisa performance das redes sociais e otimiza estratégia."""
        self.logger.info("Social media performance analysis")
        prompt = f"""Analise a performance nas redes sociais e crie plano de otimização:

MÉTRICAS:
{json.dumps(metrics, indent=2, ensure_ascii=False)[:5000]}

Retorne JSON com:
- score_social: 0-100
- metricas_consolidadas:
  - seguidores_total: soma de todas as redes
  - crescimento_seguidores_pct: crescimento no período
  - taxa_engajamento_media_pct: engajamento médio
  - alcance_total: pessoas únicas alcançadas
  - impressoes_total: total de visualizações
  - conversoes_social: cliques para site/compras
- analise_por_plataforma: para cada rede:
  - plataforma: nome
  - seguidores: total e crescimento
  - engajamento_pct: taxa de engajamento
  - alcance_por_post: média
  - top_formato: que tipo de conteúdo performa melhor
  - pior_formato: o que não funciona
  - recomendacao: escalar|manter|reduzir esforço
- conteudos_top: os 5 posts com melhor performance e por que
- conteudos_flop: os 5 posts com pior performance e por que
- insights_algoritmo: o que o algoritmo de cada rede favorece
- calendario_otimizado: melhores dias e horários para postar
- plano_crescimento: como dobrar o engajamento nos próximos 30 dias"""

        result = self.ask_json(prompt, system=SYSTEM_SOCIAL)
        score = result.get("score_social", 0)
        print(f"\n📊 Social Media Performance — Score: {score}/100")
        m = result.get("metricas_consolidadas", {})
        print(f"  Seguidores: {m.get('seguidores_total', '?')} | Engajamento: {m.get('taxa_engajamento_media_pct', '?')}%")
        self.save_result(result, prefix="social_performance")
        return result

    def influencer_strategy(self, niche: str, budget: float) -> dict:
        """Cria estratégia de marketing com influenciadores."""
        self.logger.info(f"Influencer strategy: {niche} | R$ {budget:,.0f}")
        prompt = f"""Crie uma estratégia completa de marketing com influenciadores:

NICHO: {niche}
BUDGET: R$ {budget:,.2f}

Retorne JSON com:
- estrategia_geral: abordagem recomendada
- tiers_influenciadores:
  - mega: 1M+ seguidores — quando usar e quanto pagar
  - macro: 100K-1M — quando usar e quanto pagar
  - micro: 10K-100K — quando usar e quanto pagar
  - nano: 1K-10K — quando usar e quanto pagar
- mix_recomendado: como distribuir o budget entre tiers
- perfil_ideal_influenciador: características a buscar
- plataformas_prioritarias: onde focar para este nicho
- formato_campanhas:
  - unboxing: como estruturar
  - review: como estruturar
  - collab: como co-criar conteúdo
  - takeover: quando usar
- contrato_e_brief: o que deve constar no contrato e brief
- metricas_sucesso: como avaliar ROI de influenciadores
- como_encontrar: onde e como prospectar influenciadores do nicho
- red_flags: o que evitar na escolha de influenciadores
- cronograma_campanha: como estruturar uma campanha de 30 dias"""

        result = self.ask_json(prompt, system=SYSTEM_SOCIAL)
        print(f"\n🤳 Influencer Strategy — {niche} | R$ {budget:,.0f}")
        mix = result.get("mix_recomendado", {})
        for tier, info in mix.items():
            print(f"  {tier}: {info}")
        self.save_result(result, prefix="influencer_strategy")
        return result

    def viral_hooks(self, product: dict, count: int = 20) -> dict:
        """Gera ganchos virais para aumentar alcance orgânico."""
        self.logger.info(f"Viral hooks: {count} ganchos")
        prompt = f"""Gere {count} ganchos virais para este produto/marca:

PRODUTO/MARCA:
{json.dumps(product, indent=2, ensure_ascii=False)[:2000]}

Um gancho é a primeira frase/imagem que para o scroll e força a pessoa a consumir o conteúdo.

Retorne JSON com:
- ganchos_gerados: lista de {count} ganchos com:
  - numero: sequência
  - gancho: texto do gancho (máx 15 palavras)
  - formato: onde funciona melhor (reels|tiktok|thread|post)
  - tipo: "pergunta"|"controversia"|"numero"|"segredo"|"antes_depois"|"lista"|"historia"
  - por_que_funciona: psicologia por trás deste gancho
  - exemplo_post: como usar este gancho em um post completo
- ganchos_top5: os 5 com maior potencial viral
- padroes_virais: padrões que mais funcionam para este nicho
- timing_certo: quando estes ganchos funcionam melhor
- a_b_test: como testar qual gancho funciona melhor"""

        result = self.ask_json(prompt, system=SYSTEM_SOCIAL)
        ganchos = result.get("ganchos_gerados", [])
        top5 = result.get("ganchos_top5", [])
        print(f"\n🎣 Viral Hooks — {len(ganchos)} ganchos gerados")
        print(f"  Top 5:")
        for g in (top5 if isinstance(top5, list) else [])[:5]:
            print(f"  → {str(g)[:80]}")
        self.save_result(result, prefix="viral_hooks")
        return result


def main():
    parser = argparse.ArgumentParser(description="Social Media Automation — ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")

    p_cal = sub.add_parser("calendar")
    p_cal.add_argument("--brand", required=True)
    p_cal.add_argument("--month", default="Próximo mês")

    p_cr = sub.add_parser("create")
    p_cr.add_argument("--topic", required=True)
    p_cr.add_argument("--platforms", default="instagram,linkedin,twitter")

    sub.add_parser("analyze").add_argument("--metrics", required=True)

    p_inf = sub.add_parser("influencer")
    p_inf.add_argument("--niche", required=True)
    p_inf.add_argument("--budget", type=float, default=5000)

    p_vh = sub.add_parser("viral-hooks")
    p_vh.add_argument("--product", required=True)
    p_vh.add_argument("--count", type=int, default=20)

    args = parser.parse_args()
    agent = SocialMediaAutomation()
    def load(p): return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else {}

    if args.command == "calendar":
        agent.content_calendar(load(args.brand), args.month)
    elif args.command == "create":
        platforms = [p.strip() for p in args.platforms.split(",")]
        agent.create_posts(args.topic, platforms)
    elif args.command == "analyze":
        agent.analyze_performance(load(args.metrics))
    elif args.command == "influencer":
        agent.influencer_strategy(args.niche, args.budget)
    elif args.command == "viral-hooks":
        agent.viral_hooks(load(args.product), args.count)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
