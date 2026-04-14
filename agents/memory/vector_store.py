"""
Vector Store — ULTIMATE CRONUS
Armazenamento vetorial para memória semântica dos agentes.
Usa ChromaDB se disponível, fallback para busca TF-IDF simples em JSON.
"""

import json
import math
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any


class SimpleVectorStore:
    """
    Fallback: busca por TF-IDF simples em memória/JSON.
    Não requer nenhuma dependência extra.
    """

    def __init__(self, persist_path: Path):
        self.persist_path = persist_path
        self._docs: list[dict] = []
        self._load()

    def _load(self):
        if self.persist_path.exists():
            try:
                self._docs = json.loads(self.persist_path.read_text(encoding="utf-8"))
            except Exception:
                self._docs = []

    def _save(self):
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        self.persist_path.write_text(
            json.dumps(self._docs, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"\w+", text.lower())

    def _tfidf_score(self, query_tokens: list[str], doc_tokens: list[str]) -> float:
        if not doc_tokens:
            return 0.0
        doc_counter = Counter(doc_tokens)
        doc_len = len(doc_tokens)
        score = 0.0
        for token in set(query_tokens):
            tf = doc_counter.get(token, 0) / doc_len
            # IDF simplificado
            docs_with_token = sum(
                1 for d in self._docs
                if token in self._tokenize(d.get("text", ""))
            )
            idf = math.log((len(self._docs) + 1) / (docs_with_token + 1)) + 1
            score += tf * idf
        return score

    def add(self, text: str, metadata: dict | None = None, doc_id: str = "") -> str:
        doc_id = doc_id or f"doc_{int(time.time() * 1000)}_{len(self._docs)}"
        self._docs.append({
            "id": doc_id,
            "text": text,
            "metadata": metadata or {},
            "created_at": time.time(),
        })
        self._save()
        return doc_id

    def search(self, query: str, n: int = 5, filter_meta: dict | None = None) -> list[dict]:
        q_tokens = self._tokenize(query)
        scored = []
        for doc in self._docs:
            # Filtro de metadata
            if filter_meta:
                match = all(doc.get("metadata", {}).get(k) == v for k, v in filter_meta.items())
                if not match:
                    continue
            d_tokens = self._tokenize(doc.get("text", ""))
            score = self._tfidf_score(q_tokens, d_tokens)
            scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {"score": score, "text": doc["text"], "metadata": doc["metadata"], "id": doc["id"]}
            for score, doc in scored[:n]
        ]

    def delete(self, doc_id: str) -> bool:
        before = len(self._docs)
        self._docs = [d for d in self._docs if d["id"] != doc_id]
        self._save()
        return len(self._docs) < before

    def count(self) -> int:
        return len(self._docs)

    def clear(self):
        self._docs = []
        self._save()


class ChromaVectorStore:
    """
    Vector store usando ChromaDB com embeddings reais.
    Requer: pip install chromadb
    """

    def __init__(self, collection_name: str, persist_dir: str):
        import chromadb
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._col = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, text: str, metadata: dict | None = None, doc_id: str = "") -> str:
        doc_id = doc_id or f"doc_{int(time.time() * 1000)}"
        self._col.add(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[doc_id],
        )
        return doc_id

    def search(self, query: str, n: int = 5, filter_meta: dict | None = None) -> list[dict]:
        kwargs: dict = {"query_texts": [query], "n_results": min(n, max(1, self._col.count()))}
        if filter_meta:
            kwargs["where"] = filter_meta
        results = self._col.query(**kwargs)
        output = []
        for i, doc in enumerate(results["documents"][0]):
            output.append({
                "score":    1 - results["distances"][0][i],
                "text":     doc,
                "metadata": results["metadatas"][0][i],
                "id":       results["ids"][0][i],
            })
        return output

    def delete(self, doc_id: str) -> bool:
        try:
            self._col.delete(ids=[doc_id])
            return True
        except Exception:
            return False

    def count(self) -> int:
        return self._col.count()

    def clear(self):
        self._col.delete(where={"_ne": "___none___"})


def create_vector_store(
    name: str,
    persist_dir: str = "agents/memory/db",
    use_chroma: bool = True,
):
    """
    Cria o melhor vector store disponível.
    Tenta ChromaDB primeiro, fallback para SimpleVectorStore.
    """
    if use_chroma:
        try:
            store = ChromaVectorStore(
                collection_name=name,
                persist_dir=persist_dir,
            )
            return store
        except ImportError:
            pass
        except Exception:
            pass

    # Fallback JSON
    path = Path(persist_dir) / f"{name}.json"
    return SimpleVectorStore(persist_path=path)
