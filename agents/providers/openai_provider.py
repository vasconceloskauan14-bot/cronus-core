"""
OpenAI-Compatible Provider — ULTIMATE CRONUS
Suporta: OpenAI, Groq, Together AI, Ollama, Mistral, DeepSeek, Perplexity,
         LM Studio, vLLM, Anyscale — qualquer API OpenAI-compatible.

Configurar via env vars ou config/ai_providers.json.
"""

import os
import time

from .base_provider import BaseProvider, CompletionRequest, CompletionResponse

# Pricing por 1M tokens (USD) — principais modelos
OPENAI_PRICING = {
    # OpenAI
    "gpt-4o":                {"input":  2.50, "output": 10.00},
    "gpt-4o-mini":           {"input":  0.15, "output":  0.60},
    "gpt-4-turbo":           {"input": 10.00, "output": 30.00},
    "o1":                    {"input": 15.00, "output": 60.00},
    "o1-mini":               {"input":  3.00, "output": 12.00},
    "o3-mini":               {"input":  1.10, "output":  4.40},
    # Groq (ultra-rápido)
    "llama-3.3-70b-versatile":     {"input": 0.59, "output": 0.79},
    "llama-3.1-8b-instant":        {"input": 0.05, "output": 0.08},
    "mixtral-8x7b-32768":          {"input": 0.24, "output": 0.24},
    "gemma2-9b-it":                {"input": 0.20, "output": 0.20},
    # Together AI
    "meta-llama/Llama-3.3-70B-Instruct-Turbo": {"input": 0.88, "output": 0.88},
    "mistralai/Mixtral-8x22B-Instruct-v0.1":   {"input": 1.20, "output": 1.20},
    "deepseek-ai/DeepSeek-V3":                  {"input": 1.25, "output": 1.25},
    # Mistral
    "mistral-large-latest":  {"input":  2.00, "output":  6.00},
    "mistral-small-latest":  {"input":  0.20, "output":  0.60},
    # DeepSeek
    "deepseek-chat":         {"input":  0.14, "output":  0.28},
    "deepseek-reasoner":     {"input":  0.55, "output":  2.19},
    # Perplexity
    "sonar-pro":             {"input":  3.00, "output": 15.00},
    "sonar":                 {"input":  1.00, "output":  1.00},
}


class OpenAICompatibleProvider(BaseProvider):
    """
    Provider universal para qualquer API compatível com OpenAI.
    Troca o base_url para usar Groq, Together, Ollama, Mistral, etc.
    """

    name = "openai"
    default_model = "gpt-4o-mini"

    # Endpoints conhecidos (base_url por provider alias)
    ENDPOINTS = {
        "openai":      "https://api.openai.com/v1",
        "groq":        "https://api.groq.com/openai/v1",
        "together":    "https://api.together.xyz/v1",
        "mistral":     "https://api.mistral.ai/v1",
        "deepseek":    "https://api.deepseek.com/v1",
        "perplexity":  "https://api.perplexity.ai",
        "ollama":      "http://localhost:11434/v1",
        "lmstudio":    "http://localhost:1234/v1",
        "anyscale":    "https://api.endpoints.anyscale.com/v1",
    }

    # Modelos padrão por provider alias
    DEFAULT_MODELS = {
        "openai":     "gpt-4o-mini",
        "groq":       "llama-3.3-70b-versatile",
        "together":   "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "mistral":    "mistral-small-latest",
        "deepseek":   "deepseek-chat",
        "perplexity": "sonar",
        "ollama":     "llama3.2",
        "lmstudio":   "local-model",
    }

    def __init__(self, provider_alias: str = "openai", api_key: str = "", model: str = "",
                 base_url: str = ""):
        self.provider_alias = provider_alias
        self.name = provider_alias

        # API key — tenta env var padrão por alias
        env_map = {
            "openai":     "OPENAI_API_KEY",
            "groq":       "GROQ_API_KEY",
            "together":   "TOGETHER_API_KEY",
            "mistral":    "MISTRAL_API_KEY",
            "deepseek":   "DEEPSEEK_API_KEY",
            "perplexity": "PERPLEXITY_API_KEY",
            "ollama":     "OLLAMA_API_KEY",      # geralmente "ollama" ou vazio
            "lmstudio":   "LMSTUDIO_API_KEY",    # geralmente "lm-studio" ou vazio
        }
        self._api_key = api_key or os.environ.get(env_map.get(provider_alias, ""), "")
        if provider_alias in ("ollama", "lmstudio") and not self._api_key:
            self._api_key = "local"  # APIs locais aceitam qualquer key

        # Base URL
        self._base_url = base_url or self.ENDPOINTS.get(provider_alias, self.ENDPOINTS["openai"])

        # Model
        self.default_model = model or self.DEFAULT_MODELS.get(provider_alias, "gpt-4o-mini")

        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
                max_retries=0,
            )
        return self._client

    def is_available(self) -> bool:
        return bool(self._api_key)

    def list_models(self) -> list[str]:
        try:
            client = self._get_client()
            return [m.id for m in client.models.list().data]
        except Exception:
            return list(OPENAI_PRICING.keys())

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str = "") -> float:
        m = model or self.default_model
        pricing = OPENAI_PRICING.get(m, {"input": 1.0, "output": 3.0})
        return (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        client = self._get_client()
        model = request.model or self.default_model

        # Construir messages no formato OpenAI
        messages = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        for m in request.messages:
            if m.role != "system":
                messages.append({"role": m.role, "content": m.content})

        kwargs: dict = {
            "model": model,
            "max_tokens": request.max_tokens,
            "messages": messages,
            "temperature": request.temperature,
        }
        if request.json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        t0 = time.time()
        for attempt in range(1, 4):
            try:
                resp = client.chat.completions.create(**kwargs)
                latency = int((time.time() - t0) * 1000)
                text = resp.choices[0].message.content or ""
                in_tok = resp.usage.prompt_tokens if resp.usage else 0
                out_tok = resp.usage.completion_tokens if resp.usage else 0
                return CompletionResponse(
                    text=text,
                    model=model,
                    provider=self.name,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    cost_usd=self.estimate_cost(in_tok, out_tok, model),
                    latency_ms=latency,
                )
            except Exception as e:
                err = str(e)
                err_lower = err.lower()
                if "insufficient_quota" in err_lower or "quota" in err_lower:
                    raise RuntimeError(f"{self.provider_alias}: quota insuficiente")
                if "rate" in err_lower or "429" in err:
                    # Groq reseta a cada 60s — espera o suficiente antes de tentar de novo
                    wait = 65 if attempt == 1 else 30
                    print(f"[{self.provider_alias}] 429 rate limit, aguardando {wait}s (tentativa {attempt}/3)...")
                    time.sleep(wait)
                elif attempt == 3:
                    raise
                else:
                    time.sleep(1)

        raise RuntimeError(f"{self.provider_alias}: máximo de tentativas atingido")
