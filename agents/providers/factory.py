"""
Provider Factory — ULTIMATE CRONUS
Cria o provider certo baseado em config/env vars.
Suporte: Anthropic, OpenAI, Groq, Together, Mistral, DeepSeek,
         Perplexity, Ollama, LM Studio, Gemini, vLLM, Anyscale.
"""

import json
import os
from pathlib import Path

from .base_provider import BaseProvider


# Mapa de alias → classe provider (lazy import para não exigir todos os SDKs)
_PROVIDER_MAP = {
    "anthropic": "agents.providers.anthropic_provider.AnthropicProvider",
    "openai":    "agents.providers.openai_provider.OpenAICompatibleProvider",
    "groq":      "agents.providers.openai_provider.OpenAICompatibleProvider",
    "together":  "agents.providers.openai_provider.OpenAICompatibleProvider",
    "mistral":   "agents.providers.openai_provider.OpenAICompatibleProvider",
    "deepseek":  "agents.providers.openai_provider.OpenAICompatibleProvider",
    "perplexity":"agents.providers.openai_provider.OpenAICompatibleProvider",
    "ollama":    "agents.providers.openai_provider.OpenAICompatibleProvider",
    "lmstudio":  "agents.providers.openai_provider.OpenAICompatibleProvider",
    "anyscale":  "agents.providers.openai_provider.OpenAICompatibleProvider",
    "vllm":      "agents.providers.openai_provider.OpenAICompatibleProvider",
    "gemini":    "agents.providers.gemini_provider.GeminiProvider",
}

# Providers que usam a classe OpenAICompatibleProvider com alias
_OPENAI_COMPATIBLE = {"openai", "groq", "together", "mistral", "deepseek",
                      "perplexity", "ollama", "lmstudio", "anyscale", "vllm"}

_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "ai_providers.json"
_config_cache: dict | None = None


def _load_config() -> dict:
    global _config_cache
    if _config_cache is not None:
        return _config_cache
    if _CONFIG_PATH.exists():
        try:
            _config_cache = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
            return _config_cache
        except Exception:
            pass
    _config_cache = {}
    return _config_cache


def _import_class(dotted_path: str):
    """Importa classe por string ex: 'agents.providers.anthropic_provider.AnthropicProvider'"""
    module_path, class_name = dotted_path.rsplit(".", 1)
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


class ProviderFactory:
    """
    Fábrica de providers de IA.

    Ordem de resolução do provider:
      1. Argumento explícito `provider_alias`
      2. Env var CRONUS_PROVIDER
      3. Config `config/ai_providers.json` → campo "default"
      4. Fallback: anthropic (se ANTHROPIC_API_KEY presente) ou groq
    """

    @staticmethod
    def create(
        provider_alias: str = "",
        model: str = "",
        api_key: str = "",
        base_url: str = "",
        agent_name: str = "",
    ) -> BaseProvider:
        """
        Cria e retorna um provider configurado.

        Args:
            provider_alias: Nome do provider (anthropic, openai, groq, gemini, ollama…)
            model:          Modelo a usar (overrides default do provider)
            api_key:        API key (overrides env var)
            base_url:       URL base custom (para vLLM/self-hosted)
            agent_name:     Nome do agente — permite override por agente no config
        """
        cfg = _load_config()
        providers_cfg = cfg.get("providers", {})

        # Resolver alias
        alias = (
            provider_alias
            or _agent_override(cfg, agent_name)
            or os.environ.get("CRONUS_PROVIDER", "")
            or cfg.get("default", "")
            or _auto_detect()
        )
        alias = alias.lower().strip()

        # Resolver model (prioridade: argumento > config por agente > config global)
        resolved_model = (
            model
            or _agent_model_override(cfg, agent_name)
            or providers_cfg.get(alias, {}).get("default_model", "")
        )

        # Resolver api_key
        resolved_key = (
            api_key
            or providers_cfg.get(alias, {}).get("api_key", "")
        )

        # Resolver base_url (para self-hosted)
        resolved_url = (
            base_url
            or providers_cfg.get(alias, {}).get("base_url", "")
        )

        # Instanciar provider
        if alias == "anthropic":
            cls = _import_class(_PROVIDER_MAP["anthropic"])
            return cls(api_key=resolved_key, model=resolved_model)

        if alias == "gemini":
            cls = _import_class(_PROVIDER_MAP["gemini"])
            return cls(api_key=resolved_key, model=resolved_model)

        if alias in _OPENAI_COMPATIBLE:
            cls = _import_class(_PROVIDER_MAP["openai"])
            return cls(
                provider_alias=alias,
                api_key=resolved_key,
                model=resolved_model,
                base_url=resolved_url,
            )

        # Fallback: tenta como OpenAI-compatible com base_url custom
        cls = _import_class(_PROVIDER_MAP["openai"])
        return cls(
            provider_alias=alias,
            api_key=resolved_key,
            model=resolved_model,
            base_url=resolved_url or "https://api.openai.com/v1",
        )

    @staticmethod
    def list_available() -> list[str]:
        """Retorna providers com credenciais configuradas."""
        available = []
        checks = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai":    "OPENAI_API_KEY",
            "groq":      "GROQ_API_KEY",
            "together":  "TOGETHER_API_KEY",
            "mistral":   "MISTRAL_API_KEY",
            "deepseek":  "DEEPSEEK_API_KEY",
            "perplexity":"PERPLEXITY_API_KEY",
            "gemini":    "GOOGLE_API_KEY",
        }
        for alias, env in checks.items():
            if os.environ.get(env):
                available.append(alias)
        # Locais sempre disponíveis
        available += ["ollama", "lmstudio"]
        return available

    @staticmethod
    def create_all_available() -> dict[str, BaseProvider]:
        """Cria instâncias de todos os providers disponíveis."""
        result = {}
        for alias in ProviderFactory.list_available():
            try:
                p = ProviderFactory.create(provider_alias=alias)
                if p.is_available():
                    result[alias] = p
            except Exception:
                pass
        return result


def _agent_override(cfg: dict, agent_name: str) -> str:
    """Retorna provider override para um agente específico."""
    if not agent_name:
        return ""
    return cfg.get("agents", {}).get(agent_name, {}).get("provider", "")


def _agent_model_override(cfg: dict, agent_name: str) -> str:
    """Retorna model override para um agente específico."""
    if not agent_name:
        return ""
    return cfg.get("agents", {}).get(agent_name, {}).get("model", "")


def _auto_detect() -> str:
    """Detecta automaticamente o melhor provider disponível."""
    priority = [
        ("ANTHROPIC_API_KEY", "anthropic"),
        ("OPENAI_API_KEY",    "openai"),
        ("GROQ_API_KEY",      "groq"),
        ("GOOGLE_API_KEY",    "gemini"),
        ("TOGETHER_API_KEY",  "together"),
        ("MISTRAL_API_KEY",   "mistral"),
        ("DEEPSEEK_API_KEY",  "deepseek"),
    ]
    for env, alias in priority:
        if os.environ.get(env):
            return alias
    return "anthropic"  # default mesmo sem key (vai falhar com erro claro)
