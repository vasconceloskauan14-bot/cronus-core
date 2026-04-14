"""
Router Agent — ULTIMATE CRONUS
Roteador inteligente: seleciona o melhor modelo/provider por tipo de tarefa.

Estratégias:
  - reasoning  → Claude Opus / o1 (tarefas complexas, análise profunda)
  - speed      → Groq Llama (tempo real, drafts, triagem)
  - cost       → Llama 8B / Haiku (volume alto, tarefas simples)
  - creative   → GPT-4o / Claude Sonnet (conteúdo, copy, criatividade)
  - local      → Ollama (dados sensíveis, offline)
  - search     → Perplexity Sonar (busca web em tempo real)
  - code       → Claude Sonnet / DeepSeek (programação)
  - structured → Claude Sonnet / GPT-4o-mini (JSON, extração, classificação)
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.providers.factory import ProviderFactory, _load_config
from agents.providers.base_provider import CompletionRequest, Message


# Mapa de estratégia → (provider, model)
STRATEGY_DEFAULTS = {
    "reasoning":  ("anthropic",  "claude-opus-4-6"),
    "speed":      ("groq",       "llama-3.3-70b-versatile"),
    "cost":       ("groq",       "llama-3.1-8b-instant"),
    "creative":   ("openai",     "gpt-4o"),
    "local":      ("ollama",     "llama3.2"),
    "search":     ("perplexity", "sonar-pro"),
    "code":       ("anthropic",  "claude-sonnet-4-6"),
    "structured": ("anthropic",  "claude-sonnet-4-6"),
}

# Palavras-chave para auto-detectar estratégia
STRATEGY_KEYWORDS = {
    "reasoning":  ["analise", "estratégia", "decisão", "complexo", "por que", "raciocínio", "reflita"],
    "speed":      ["rápido", "urgente", "agora", "imediato", "resumo", "draft", "rascunho"],
    "cost":       ["classifica", "triagem", "extrai", "simples", "básico", "lista"],
    "creative":   ["crie", "escreva", "conteúdo", "copy", "criativo", "blog", "post", "slogan"],
    "local":      ["local", "offline", "privado", "confidencial", "interno"],
    "search":     ["pesquisa", "busca", "notícias", "atual", "mercado", "tendência", "2024", "2025"],
    "code":       ["código", "python", "javascript", "função", "script", "bug", "debug", "implementa"],
    "structured": ["json", "estruturado", "campos", "extrai dados", "classifica"],
}


class RouterAgent:
    """
    Roteia tarefas para o melhor provider/modelo.
    Pode ser usado como agente standalone ou integrado ao Orchestrator.
    """

    name = "ROUTER"

    def __init__(self):
        self._providers: dict = {}
        self._cfg = _load_config()

    def _get_provider(self, alias: str, model: str):
        key = f"{alias}:{model}"
        if key not in self._providers:
            try:
                p = ProviderFactory.create(provider_alias=alias, model=model)
                if p.is_available():
                    self._providers[key] = p
                else:
                    return None
            except Exception:
                return None
        return self._providers.get(key)

    def detect_strategy(self, prompt: str) -> str:
        """Auto-detecta estratégia baseado em palavras-chave no prompt."""
        prompt_lower = prompt.lower()
        scores = {s: 0 for s in STRATEGY_KEYWORDS}
        for strategy, keywords in STRATEGY_KEYWORDS.items():
            for kw in keywords:
                if kw in prompt_lower:
                    scores[strategy] += 1
        best = max(scores, key=lambda s: scores[s])
        return best if scores[best] > 0 else "reasoning"

    def route(self, prompt: str, strategy: str = "", system: str = "",
              max_tokens: int = 8096, fallback: bool = True) -> dict:
        """
        Roteia prompt para o melhor provider.

        Returns:
            dict com 'text', 'provider', 'model', 'strategy', 'latency_ms', 'cost_usd'
        """
        if not strategy:
            strategy = self.detect_strategy(prompt)

        # Resolver provider/model da estratégia
        routing_cfg = self._cfg.get("routing", {})
        if strategy in routing_cfg:
            provider_alias = routing_cfg[strategy].get("provider", "")
            model = routing_cfg[strategy].get("model", "")
        else:
            provider_alias, model = STRATEGY_DEFAULTS.get(strategy, ("anthropic", "claude-sonnet-4-6"))

        # Tentar provider principal
        provider = self._get_provider(provider_alias, model)

        # Fallback chain se provider indisponível
        if provider is None and fallback:
            fallback_chain = [
                ("anthropic", "claude-sonnet-4-6"),
                ("openai",    "gpt-4o-mini"),
                ("groq",      "llama-3.3-70b-versatile"),
                ("deepseek",  "deepseek-chat"),
                ("ollama",    "llama3.2"),
            ]
            for fb_alias, fb_model in fallback_chain:
                provider = self._get_provider(fb_alias, fb_model)
                if provider:
                    provider_alias, model = fb_alias, fb_model
                    break

        if provider is None:
            raise RuntimeError(f"Nenhum provider disponível para estratégia '{strategy}'")

        request = CompletionRequest(
            messages=[Message(role="user", content=prompt)],
            system=system,
            max_tokens=max_tokens,
            model=model,
        )

        t0 = time.time()
        resp = provider.complete(request)
        latency = int((time.time() - t0) * 1000)

        return {
            "text":       resp.text,
            "provider":   resp.provider,
            "model":      resp.model,
            "strategy":   strategy,
            "latency_ms": latency,
            "cost_usd":   resp.cost_usd,
            "tokens": {
                "input":  resp.input_tokens,
                "output": resp.output_tokens,
            }
        }

    def benchmark(self, prompt: str, strategies: list[str] | None = None) -> list[dict]:
        """Roda o mesmo prompt em múltiplos providers e compara resultados."""
        strategies = strategies or list(STRATEGY_DEFAULTS.keys())
        results = []
        for strategy in strategies:
            try:
                result = self.route(prompt, strategy=strategy, fallback=False)
                result["strategy"] = strategy
                results.append(result)
                print(f"  [{strategy}] {result['provider']}/{result['model']} — "
                      f"{result['latency_ms']}ms | ${result['cost_usd']:.6f}")
            except Exception as e:
                results.append({"strategy": strategy, "error": str(e)})
        return results

    def status(self) -> dict:
        """Retorna status de todos os providers disponíveis."""
        available = ProviderFactory.list_available()
        status = {}
        for alias in available:
            try:
                p = ProviderFactory.create(provider_alias=alias)
                status[alias] = {
                    "available": p.is_available(),
                    "model":     p.default_model,
                    "models":    p.list_models()[:5],  # primeiros 5
                }
            except Exception as e:
                status[alias] = {"available": False, "error": str(e)}
        return status


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="ROUTER — Roteador inteligente de IA")
    sub = parser.add_subparsers(dest="cmd")

    # route
    p_route = sub.add_parser("route", help="Rotear um prompt para o melhor provider")
    p_route.add_argument("prompt", help="Prompt a enviar")
    p_route.add_argument("--strategy", default="", help="Estratégia: reasoning|speed|cost|creative|local|search|code|structured")
    p_route.add_argument("--system", default="", help="System prompt")
    p_route.add_argument("--max-tokens", type=int, default=8096)

    # detect
    p_detect = sub.add_parser("detect", help="Detectar estratégia para um prompt")
    p_detect.add_argument("prompt")

    # benchmark
    p_bench = sub.add_parser("benchmark", help="Rodar prompt em múltiplos providers")
    p_bench.add_argument("prompt")
    p_bench.add_argument("--strategies", nargs="*", help="Estratégias a testar")

    # status
    sub.add_parser("status", help="Status de todos os providers")

    args = parser.parse_args()
    router = RouterAgent()

    if args.cmd == "route":
        result = router.route(args.prompt, strategy=args.strategy,
                              system=args.system, max_tokens=args.max_tokens)
        print(f"\nProvider: {result['provider']} | Model: {result['model']}")
        print(f"Estratégia: {result['strategy']} | Latência: {result['latency_ms']}ms | Custo: ${result['cost_usd']:.6f}\n")
        print(result["text"])

    elif args.cmd == "detect":
        strategy = router.detect_strategy(args.prompt)
        provider, model = STRATEGY_DEFAULTS.get(strategy, ("anthropic", "claude-sonnet-4-6"))
        print(f"Estratégia detectada: {strategy}")
        print(f"Provider recomendado: {provider} / {model}")

    elif args.cmd == "benchmark":
        print(f"\nBenchmark: '{args.prompt[:60]}...'\n")
        results = router.benchmark(args.prompt, strategies=args.strategies)
        out_path = Path("agents/output") / f"benchmark_{int(time.time())}.json"
        out_path.parent.mkdir(exist_ok=True)
        out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nResultados salvos em {out_path}")

    elif args.cmd == "status":
        status = router.status()
        print(json.dumps(status, indent=2, ensure_ascii=False))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
