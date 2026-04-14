"""
Vision — ULTIMATE CRONUS
Processamento de imagens via Claude Vision, GPT-4o Vision ou Gemini.
"""

import base64
import os
from pathlib import Path
from dataclasses import dataclass


@dataclass
class VisionResult:
    description: str
    extracted_text: str = ""
    objects: list[str] = None
    data: dict = None
    model: str = ""
    provider: str = ""

    def __post_init__(self):
        if self.objects is None:
            self.objects = []
        if self.data is None:
            self.data = {}


def _encode_image(path: str) -> tuple[str, str]:
    """Codifica imagem em base64 e detecta mime type."""
    p = Path(path)
    ext = p.suffix.lower()
    mime_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".gif": "image/gif",
        ".webp": "image/webp",
    }
    mime = mime_map.get(ext, "image/jpeg")
    with open(path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return data, mime


class VisionProcessor:
    """
    Processa imagens usando o provider configurado.
    Suporta: análise, OCR, extração de dados, classificação.
    """

    def __init__(self, provider: str = ""):
        self._provider = provider or os.environ.get("CRONUS_PROVIDER", "anthropic")

    def analyze(self, image_path: str, prompt: str = "", json_output: bool = False) -> VisionResult:
        """
        Analisa uma imagem.
        Args:
            image_path: Caminho local ou URL da imagem
            prompt:     Instrução específica (ex: "extraia todos os dados desta tabela")
            json_output: Se True, tenta retornar JSON estruturado
        """
        if not prompt:
            prompt = (
                "Descreva detalhadamente esta imagem. "
                "Se houver texto, extraia-o completo. "
                "Se houver dados/tabelas/gráficos, estruture-os."
            )

        is_url = image_path.startswith("http://") or image_path.startswith("https://")

        if self._provider == "anthropic":
            return self._analyze_anthropic(image_path, prompt, is_url, json_output)
        elif self._provider in ("openai", "groq"):
            return self._analyze_openai(image_path, prompt, is_url, json_output)
        elif self._provider == "gemini":
            return self._analyze_gemini(image_path, prompt, is_url, json_output)
        else:
            return self._analyze_anthropic(image_path, prompt, is_url, json_output)

    def _analyze_anthropic(self, path: str, prompt: str, is_url: bool, json_output: bool) -> VisionResult:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

        if is_url:
            content = [
                {"type": "image", "source": {"type": "url", "url": path}},
                {"type": "text", "text": prompt + ("\n\nResponda em JSON." if json_output else "")},
            ]
        else:
            data, mime = _encode_image(path)
            content = [
                {"type": "image", "source": {"type": "base64", "media_type": mime, "data": data}},
                {"type": "text", "text": prompt + ("\n\nResponda em JSON." if json_output else "")},
            ]

        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": content}],
        )
        text = resp.content[0].text

        result = VisionResult(description=text, model="claude-sonnet-4-6", provider="anthropic")
        if json_output:
            import json, re
            raw = re.sub(r"```json|```", "", text).strip()
            try:
                result.data = json.loads(raw)
            except Exception:
                pass
        return result

    def _analyze_openai(self, path: str, prompt: str, is_url: bool, json_output: bool) -> VisionResult:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

        if is_url:
            image_content = {"type": "image_url", "image_url": {"url": path}}
        else:
            data, mime = _encode_image(path)
            image_content = {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{data}"}}

        messages = [{"role": "user", "content": [
            image_content,
            {"type": "text", "text": prompt + ("\n\nResponda em JSON." if json_output else "")},
        ]}]

        kwargs = {"model": "gpt-4o", "max_tokens": 4096, "messages": messages}
        if json_output:
            kwargs["response_format"] = {"type": "json_object"}

        resp = client.chat.completions.create(**kwargs)
        text = resp.choices[0].message.content

        result = VisionResult(description=text, model="gpt-4o", provider="openai")
        if json_output:
            import json
            try:
                result.data = json.loads(text)
            except Exception:
                pass
        return result

    def _analyze_gemini(self, path: str, prompt: str, is_url: bool, json_output: bool) -> VisionResult:
        import google.generativeai as genai
        genai.configure(api_key=os.environ.get("GOOGLE_API_KEY", ""))
        model = genai.GenerativeModel("gemini-2.0-flash")

        if is_url:
            import urllib.request
            with urllib.request.urlopen(path) as resp:
                img_data = resp.read()
            import PIL.Image, io
            img = PIL.Image.open(io.BytesIO(img_data))
        else:
            import PIL.Image
            img = PIL.Image.open(path)

        full_prompt = prompt + ("\n\nResponda em JSON." if json_output else "")
        resp = model.generate_content([full_prompt, img])
        text = resp.text

        result = VisionResult(description=text, model="gemini-2.0-flash", provider="gemini")
        if json_output:
            import json, re
            raw = re.sub(r"```json|```", "", text).strip()
            try:
                result.data = json.loads(raw)
            except Exception:
                pass
        return result

    def extract_text(self, image_path: str) -> str:
        """OCR: extrai texto de uma imagem."""
        result = self.analyze(
            image_path,
            prompt="Extraia TODO o texto desta imagem exatamente como aparece, preservando formatação.",
        )
        return result.description

    def extract_table(self, image_path: str) -> dict:
        """Extrai tabela de uma imagem como JSON."""
        result = self.analyze(
            image_path,
            prompt="Esta imagem contém uma tabela ou dados estruturados. Extraia-os como JSON com headers e rows.",
            json_output=True,
        )
        return result.data or {"raw": result.description}

    def classify(self, image_path: str, categories: list[str]) -> str:
        """Classifica uma imagem em categorias."""
        cats = ", ".join(categories)
        result = self.analyze(
            image_path,
            prompt=f"Classifique esta imagem em UMA das categorias: {cats}. Responda APENAS com o nome da categoria.",
        )
        return result.description.strip()

    def compare(self, image_path1: str, image_path2: str, aspect: str = "") -> str:
        """Compara duas imagens."""
        # Para dois images, processa sequencialmente e compara
        desc1 = self.analyze(image_path1, "Descreva esta imagem detalhadamente.").description
        desc2 = self.analyze(image_path2, "Descreva esta imagem detalhadamente.").description

        aspect_text = f" com foco em: {aspect}" if aspect else ""
        from agents.providers.factory import ProviderFactory
        from agents.providers.base_provider import CompletionRequest, Message

        provider = ProviderFactory.create()
        req = CompletionRequest(
            messages=[Message(role="user", content=(
                f"Compare estas duas imagens{aspect_text}:\n\n"
                f"Imagem 1: {desc1}\n\nImagem 2: {desc2}\n\n"
                "Quais são as principais diferenças e semelhanças?"
            ))],
            max_tokens=2048,
        )
        return provider.complete(req).text
