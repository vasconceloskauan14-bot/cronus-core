"""
Google Gemini Provider — ULTIMATE CRONUS
Suporta: Gemini 2.0 Flash, Gemini 1.5 Pro/Flash via google-generativeai SDK.
"""

import os
import time

from .base_provider import BaseProvider, CompletionRequest, CompletionResponse

GEMINI_PRICING = {
    "gemini-2.0-flash":         {"input": 0.10,  "output": 0.40},
    "gemini-2.0-flash-lite":    {"input": 0.075, "output": 0.30},
    "gemini-1.5-pro":           {"input": 1.25,  "output": 5.00},
    "gemini-1.5-flash":         {"input": 0.075, "output": 0.30},
    "gemini-1.5-flash-8b":      {"input": 0.0375,"output": 0.15},
}


class GeminiProvider(BaseProvider):
    """Provider para Google Gemini via google-generativeai SDK."""

    name = "gemini"
    default_model = "gemini-2.0-flash"

    def __init__(self, api_key: str = "", model: str = ""):
        self._api_key = api_key or os.environ.get("GOOGLE_API_KEY", "") or os.environ.get("GEMINI_API_KEY", "")
        if model:
            self.default_model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            import google.generativeai as genai
            genai.configure(api_key=self._api_key)
            self._client = genai
        return self._client

    def is_available(self) -> bool:
        return bool(self._api_key)

    def list_models(self) -> list[str]:
        return list(GEMINI_PRICING.keys())

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str = "") -> float:
        m = model or self.default_model
        pricing = GEMINI_PRICING.get(m, {"input": 1.25, "output": 5.00})
        return (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        genai = self._get_client()
        model_name = request.model or self.default_model

        # Montar histórico + system instruction
        import google.generativeai as google_genai

        gen_config = google_genai.types.GenerationConfig(
            max_output_tokens=request.max_tokens,
            temperature=request.temperature,
        )
        if request.json_mode:
            gen_config = google_genai.types.GenerationConfig(
                max_output_tokens=request.max_tokens,
                temperature=request.temperature,
                response_mime_type="application/json",
            )

        model = google_genai.GenerativeModel(
            model_name=model_name,
            system_instruction=request.system or None,
            generation_config=gen_config,
        )

        # Converter messages para formato Gemini
        history = []
        last_user = None
        for m in request.messages:
            if m.role == "system":
                continue
            gemini_role = "user" if m.role == "user" else "model"
            if gemini_role == "user":
                last_user = m.content
                history.append({"role": "user", "parts": [m.content]})
            else:
                history.append({"role": "model", "parts": [m.content]})

        # Separar último user message do histórico
        if history and history[-1]["role"] == "user":
            last_msg = history.pop()["parts"][0]
        else:
            last_msg = last_user or ""

        t0 = time.time()
        for attempt in range(1, 4):
            try:
                if history:
                    chat = model.start_chat(history=history)
                    resp = chat.send_message(last_msg)
                else:
                    resp = model.generate_content(last_msg)

                latency = int((time.time() - t0) * 1000)
                text = resp.text or ""
                in_tok = getattr(resp.usage_metadata, "prompt_token_count", 0) or 0
                out_tok = getattr(resp.usage_metadata, "candidates_token_count", 0) or 0

                return CompletionResponse(
                    text=text,
                    model=model_name,
                    provider=self.name,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    cost_usd=self.estimate_cost(in_tok, out_tok, model_name),
                    latency_ms=latency,
                )
            except Exception as e:
                err = str(e)
                if "quota" in err.lower() or "429" in err or "rate" in err.lower():
                    time.sleep(2 * attempt)
                elif attempt == 3:
                    raise
                else:
                    time.sleep(1)

        raise RuntimeError("Gemini: máximo de tentativas atingido")
