"""
Web Scraper Tool — ULTIMATE CRONUS
Acessa URLs e extrai conteúdo de páginas web.
"""

import re
import urllib.request
import urllib.error
from .base_tool import BaseTool, ToolResult

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}


def _strip_html(html: str) -> str:
    """Remove tags HTML e retorna texto limpo."""
    # Remove scripts e styles
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Remove tags
    html = re.sub(r"<[^>]+>", " ", html)
    # Limpar espaços
    html = re.sub(r"&nbsp;", " ", html)
    html = re.sub(r"&amp;", "&", html)
    html = re.sub(r"&lt;", "<", html)
    html = re.sub(r"&gt;", ">", html)
    html = re.sub(r"&#\d+;", "", html)
    html = re.sub(r"\s+", " ", html)
    return html.strip()


class ScraperTool(BaseTool):
    """
    Acessa uma URL e extrai o texto da página.
    Útil para ler artigos, páginas de produto, documentações.
    """

    name = "scraper"
    description = "Acessa uma URL e retorna o conteúdo da página como texto. Use para ler artigos, sites, documentações."

    def __init__(self, timeout: int = 15, max_chars: int = 20_000):
        self.timeout = timeout
        self.max_chars = max_chars

    def run(self, url: str, extract_links: bool = False) -> ToolResult:
        """
        Acessa e extrai conteúdo de uma URL.
        Args:
            url:           URL a acessar
            extract_links: Se True, também retorna links encontrados
        """
        try:
            req = urllib.request.Request(url, headers=_HEADERS)
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                content_type = resp.headers.get("Content-Type", "")
                raw = resp.read()
                # Detectar encoding
                encoding = "utf-8"
                if "charset=" in content_type:
                    encoding = content_type.split("charset=")[-1].split(";")[0].strip()
                html = raw.decode(encoding, errors="replace")

            text = _strip_html(html)
            text = text[:self.max_chars]

            metadata = {"url": url, "chars": len(text), "content_type": content_type}

            if extract_links:
                links = re.findall(r'href=["\']([^"\']+)["\']', html)
                # Filtrar links absolutos
                abs_links = [l for l in links if l.startswith("http")][:20]
                metadata["links"] = abs_links

            return ToolResult(success=True, output=text, metadata=metadata)

        except urllib.error.HTTPError as e:
            return ToolResult(success=False, output="", error=f"HTTP {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            return ToolResult(success=False, output="", error=f"URL Error: {e.reason}")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "url":  {"type": "string", "description": "URL a acessar"},
                    "extract_links": {"type": "boolean", "description": "Extrair links da página", "default": False},
                },
                "required": ["url"],
            },
        }
