"""
Anthropic Provider — ULTIMATE CRONUS
Claude Opus, Sonnet, Haiku via Anthropic SDK.
"""

import os
import time

from .base_provider import BaseProvider, CompletionRequest, CompletionResponse

# Pricing por 1M tokens (USD) — atualizar conforme Anthropic atualizar
ANTHROPIC_PRICING = {
    "claude-opus-4-6":       {"input": 15.00, "output": 75.00},
    "claude-sonnet-4-6":     {"input":  3.00, "output": 15.00},
    "claude-haiku-4-5-20251001": {"input":  0.80, "output":  4.00},
    "claude-3-5-sonnet-20241022": {"input":  3.00, "output": 15.00},
    "claude-3-5-haiku-20241022":  {"input":  0.80, "output":  4.00},
}


class AnthropicProvider(BaseProvider):
    name = "anthropic"
    default_model = "claude-sonnet-4-6"

    def __init__(self, api_key: str = "", model: str = ""):
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if model:
            self.default_model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    def is_available(self) -> bool:
        return bool(self._api_key and self._api_key.startswith("sk-"))

    def list_models(self) -> list[str]:
        return list(ANTHROPIC_PRICING.keys())

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str = "") -> float:
        m = model or self.default_model
        pricing = ANTHROPIC_PRICING.get(m, {"input": 3.0, "output": 15.0})
        return (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        import anthropic

        client = self._get_client()
        model = request.model or self.default_model

        # Build messages
        messages = [{"role": m.role, "content": m.content} for m in request.messages if m.role != "system"]

        kwargs: dict = {
            "model": model,
            "max_tokens": request.max_tokens,
            "messages": messages,
        }
        if request.system:
            kwargs["system"] = request.system

        t0 = time.time()
        for attempt in range(1, 4):
            try:
                resp = client.messages.create(**kwargs)
                latency = int((time.time() - t0) * 1000)
                text = resp.content[0].text
                in_tok = resp.usage.input_tokens
                out_tok = resp.usage.output_tokens
                return CompletionResponse(
                    text=text,
                    model=model,
                    provider=self.name,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    cost_usd=self.estimate_cost(in_tok, out_tok, model),
                    latency_ms=latency,
                )
            except anthropic.RateLimitError:
                time.sleep(2 * attempt)
            except anthropic.APIError as e:
                if attempt == 3:
                    raise
                time.sleep(2)

        raise RuntimeError("Anthropic: máximo de tentativas atingido")
