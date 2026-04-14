"""
Web Search Tool — ULTIMATE CRONUS
Busca web via DuckDuckGo (grátis) ou Brave Search API.
"""

import json
import os
import urllib.parse
import urllib.request
from .base_tool import BaseTool, ToolResult


class WebSearchTool(BaseTool):
    """
    Busca na web em tempo real.
    Usa DuckDuckGo (sem API key) ou Brave Search (com BRAVE_API_KEY).
    """

    name = "web_search"
    description = "Busca informações na web em tempo real. Use para notícias, dados atuais, pesquisas de mercado."

    def __init__(self, max_results: int = 5):
        self.max_results = max_results
        self._brave_key = os.environ.get("BRAVE_API_KEY", "")

    def is_available(self) -> bool:
        return True  # DuckDuckGo sempre disponível

    def run(self, query: str, max_results: int = 0) -> ToolResult:
        """
        Busca na web.
        Args:
            query: Termo de busca
            max_results: Número máximo de resultados (default: self.max_results)
        """
        n = max_results or self.max_results
        if self._brave_key:
            return self._brave_search(query, n)
        return self._ddg_search(query, n)

    def _ddg_search(self, query: str, n: int) -> ToolResult:
        """DuckDuckGo Instant Answer API + HTML scraping fallback."""
        try:
            # Tenta duckduckgo-search package primeiro
            try:
                try:
                    from ddgs import DDGS
                except ImportError:
                    from duckduckgo_search import DDGS
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=n))
                formatted = [
                    {
                        "title": r.get("title", ""),
                        "url":   r.get("href", ""),
                        "snippet": r.get("body", ""),
                    }
                    for r in results
                ]
                return ToolResult(
                    success=True,
                    output=formatted,
                    metadata={"source": "duckduckgo", "query": query, "count": len(formatted)},
                )
            except ImportError:
                pass

            # Fallback: DuckDuckGo Instant Answer API
            encoded = urllib.parse.quote_plus(query)
            url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"
            req = urllib.request.Request(url, headers={"User-Agent": "ULTIMATE-CRONUS/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())

            results = []
            # Abstract
            if data.get("AbstractText"):
                results.append({
                    "title":   data.get("Heading", ""),
                    "url":     data.get("AbstractURL", ""),
                    "snippet": data["AbstractText"],
                })
            # Related topics
            for topic in data.get("RelatedTopics", [])[:n]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append({
                        "title":   topic.get("Text", "")[:80],
                        "url":     topic.get("FirstURL", ""),
                        "snippet": topic.get("Text", ""),
                    })

            return ToolResult(
                success=True,
                output=results[:n],
                metadata={"source": "duckduckgo_api", "query": query, "count": len(results)},
            )
        except Exception as e:
            return ToolResult(success=False, output=[], error=str(e))

    def _brave_search(self, query: str, n: int) -> ToolResult:
        """Brave Search API (requer BRAVE_API_KEY)."""
        try:
            encoded = urllib.parse.quote_plus(query)
            url = f"https://api.search.brave.com/res/v1/web/search?q={encoded}&count={n}"
            req = urllib.request.Request(
                url,
                headers={
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip",
                    "X-Subscription-Token": self._brave_key,
                }
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())

            results = [
                {
                    "title":   r.get("title", ""),
                    "url":     r.get("url", ""),
                    "snippet": r.get("description", ""),
                }
                for r in data.get("web", {}).get("results", [])[:n]
            ]
            return ToolResult(
                success=True,
                output=results,
                metadata={"source": "brave", "query": query, "count": len(results)},
            )
        except Exception as e:
            return ToolResult(success=False, output=[], error=str(e))

    def schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Termo de busca"},
                    "max_results": {"type": "integer", "description": "Máximo de resultados (padrão 5)", "default": 5},
                },
                "required": ["query"],
            },
        }
