"""
Document Processor — ULTIMATE CRONUS
Processa PDFs, DOCX, planilhas e extrai insights via IA.
"""

import json
import os
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class DocumentResult:
    path: str
    format: str
    page_count: int
    text: str
    summary: str = ""
    key_points: list[str] = field(default_factory=list)
    entities: dict = field(default_factory=dict)
    tables: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class DocumentProcessor:
    """
    Processa documentos complexos e extrai insights via IA.
    Suporta: PDF, DOCX, XLSX, CSV, TXT, MD.
    """

    def __init__(self, chunk_size: int = 8000):
        self.chunk_size = chunk_size

    # ── Extração de texto ─────────────────────────────────────────────────

    def extract_text(self, path: str) -> DocumentResult:
        """Extrai texto bruto do documento."""
        p = Path(path)
        ext = p.suffix.lower()

        if ext == ".pdf":
            return self._extract_pdf(p)
        elif ext in (".docx", ".doc"):
            return self._extract_docx(p)
        elif ext in (".xlsx", ".xls"):
            return self._extract_excel(p)
        elif ext == ".csv":
            return self._extract_csv(p)
        else:
            text = p.read_text(encoding="utf-8", errors="replace")
            return DocumentResult(path=str(p), format=ext, page_count=1, text=text)

    def _extract_pdf(self, p: Path) -> DocumentResult:
        pages = []
        try:
            import pdfplumber
            with pdfplumber.open(str(p)) as pdf:
                for page in pdf.pages:
                    pages.append(page.extract_text() or "")
        except ImportError:
            try:
                import PyPDF2
                with open(p, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        pages.append(page.extract_text() or "")
            except ImportError:
                return DocumentResult(str(p), "pdf", 0, "", metadata={"error": "Instale pdfplumber"})
        return DocumentResult(
            path=str(p), format="pdf", page_count=len(pages),
            text="\n\n".join(pages),
        )

    def _extract_docx(self, p: Path) -> DocumentResult:
        try:
            import docx
            doc = docx.Document(str(p))
            text = "\n".join(para.text for para in doc.paragraphs)
            return DocumentResult(path=str(p), format="docx", page_count=1, text=text)
        except ImportError:
            return DocumentResult(str(p), "docx", 0, "", metadata={"error": "Instale python-docx"})

    def _extract_excel(self, p: Path) -> DocumentResult:
        try:
            import openpyxl
            wb = openpyxl.load_workbook(str(p), read_only=True, data_only=True)
            all_text = []
            tables = []
            for sheet in wb.worksheets:
                rows = list(sheet.iter_rows(values_only=True))
                if not rows:
                    continue
                headers = [str(c or "") for c in rows[0]]
                data_rows = []
                for row in rows[1:]:
                    r = {headers[i]: str(v or "") for i, v in enumerate(row) if i < len(headers)}
                    data_rows.append(r)
                tables.append({"sheet": sheet.title, "headers": headers, "rows": data_rows[:100]})
                all_text.append(f"[Aba: {sheet.title}]\n" + "\n".join(
                    ", ".join(str(c or "") for c in row) for row in rows
                ))
            return DocumentResult(
                path=str(p), format="xlsx", page_count=len(wb.worksheets),
                text="\n\n".join(all_text), tables=tables,
            )
        except ImportError:
            return DocumentResult(str(p), "xlsx", 0, "", metadata={"error": "Instale openpyxl"})

    def _extract_csv(self, p: Path) -> DocumentResult:
        import csv
        rows = []
        with open(p, encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
        text = "\n".join(", ".join(r) for r in rows)
        headers = rows[0] if rows else []
        data = [dict(zip(headers, r)) for r in rows[1:100]]
        return DocumentResult(
            path=str(p), format="csv", page_count=1, text=text,
            tables=[{"headers": headers, "rows": data}],
        )

    # ── Análise via IA ────────────────────────────────────────────────────

    def analyze(self, path: str, questions: list[str] | None = None) -> DocumentResult:
        """
        Extrai texto e enriquece com IA: resumo, pontos-chave, entidades.
        """
        doc = self.extract_text(path)
        if not doc.text.strip():
            return doc

        from agents.providers.factory import ProviderFactory
        from agents.providers.base_provider import CompletionRequest, Message

        provider = ProviderFactory.create()

        # Chunking para documentos longos
        text = doc.text[:self.chunk_size]

        # Resumo + pontos-chave
        summary_prompt = (
            f"Documento: {Path(path).name}\n\n{text}\n\n"
            "Produza em JSON:\n"
            '{"summary": "resumo em 3 frases", '
            '"key_points": ["ponto1", "ponto2", ...], '
            '"entities": {"pessoas": [], "empresas": [], "valores": [], "datas": []}}'
        )
        req = CompletionRequest(
            messages=[Message(role="user", content=summary_prompt)],
            system="Analise documentos e extraia informações estruturadas. Responda APENAS em JSON.",
            max_tokens=2048,
            json_mode=True,
        )
        try:
            resp = provider.complete(req)
            raw = resp.text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            data = json.loads(raw)
            doc.summary = data.get("summary", "")
            doc.key_points = data.get("key_points", [])
            doc.entities = data.get("entities", {})
        except Exception:
            pass

        # Perguntas específicas
        if questions:
            answers = {}
            for q in questions:
                q_prompt = f"Documento:\n{text}\n\nPergunta: {q}\nResponda de forma concisa e direta."
                req = CompletionRequest(
                    messages=[Message(role="user", content=q_prompt)],
                    max_tokens=1024,
                )
                try:
                    ans = provider.complete(req).text
                    answers[q] = ans
                except Exception:
                    answers[q] = "Erro ao processar"
            doc.metadata["qa"] = answers

        return doc

    def compare_documents(self, path1: str, path2: str) -> dict:
        """Compara dois documentos e identifica diferenças e semelhanças."""
        doc1 = self.extract_text(path1)
        doc2 = self.extract_text(path2)

        from agents.providers.factory import ProviderFactory
        from agents.providers.base_provider import CompletionRequest, Message

        provider = ProviderFactory.create()
        prompt = (
            f"Documento 1 ({Path(path1).name}):\n{doc1.text[:4000]}\n\n"
            f"Documento 2 ({Path(path2).name}):\n{doc2.text[:4000]}\n\n"
            "Compare os dois documentos. Identifique: "
            "1) Pontos em comum, 2) Diferenças principais, 3) Qual é mais completo e por quê."
        )
        req = CompletionRequest(
            messages=[Message(role="user", content=prompt)],
            max_tokens=2048,
        )
        analysis = provider.complete(req).text
        return {
            "doc1": path1, "doc2": path2,
            "comparison": analysis,
        }

    def batch_summarize(self, paths: list[str]) -> list[dict]:
        """Resume múltiplos documentos em paralelo."""
        from concurrent.futures import ThreadPoolExecutor
        results = []

        def process(p):
            try:
                doc = self.analyze(p)
                return {"path": p, "summary": doc.summary, "key_points": doc.key_points}
            except Exception as e:
                return {"path": p, "error": str(e)}

        with ThreadPoolExecutor(max_workers=4) as ex:
            results = list(ex.map(process, paths))
        return results
