"""
Base Agent — ULTIMATE CRONUS
Classe base completa com:
  - Provider plugável (Anthropic, OpenAI, Groq, Gemini, Ollama…)
  - Ferramentas (web search, código, arquivos, calc, scraper)
  - Memória de longo prazo + episódica
  - Raciocínio (CoT, self-critique, Tree-of-Thought)
  - Multi-modal (imagens, documentos)
  - Logging estruturado + persistência de estado
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from agents.providers.factory import ProviderFactory
from agents.providers.base_provider import CompletionRequest, Message


def _setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = logging.Formatter(
            '{"time":"%(asctime)s","agent":"%(name)s","level":"%(levelname)s","msg":"%(message)s"}',
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        handler.setFormatter(fmt)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


class BaseAgent:
    """
    Classe base universal do ULTIMATE CRONUS.
    Todos os agentes herdam desta classe e ganham superpoderes automaticamente.
    """

    MODEL = ""
    MAX_TOKENS = 8096
    MAX_RETRIES = 3
    RETRY_DELAY = 2

    # Ferramentas habilitadas por padrão (sobrescreva no subclasse)
    DEFAULT_TOOLS: list[str] = []  # ex: ["web_search", "calculator", "file_reader"]

    def __init__(
        self,
        name: str,
        state_dir: str = "state",
        output_dir: str = "output",
        provider: str = "",
        model: str = "",
        enable_memory: bool = True,
        enable_tools: bool = True,
        tools: list[str] | None = None,
    ):
        self.name = name
        self.logger = _setup_logger(name)

        # ── Provider de IA ────────────────────────────────────────────────
        self.provider = ProviderFactory.create(
            provider_alias=provider,
            model=model or self.MODEL,
            agent_name=name,
        )
        self.logger.info(f"Provider: {self.provider.name} | Model: {self.provider.default_model}")

        # ── Dirs ──────────────────────────────────────────────────────────
        self.state_dir = Path(state_dir)
        self.output_dir = Path(output_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._state: dict = self._load_state()

        # ── Ferramentas ───────────────────────────────────────────────────
        self._toolkit = None
        if enable_tools:
            self._init_tools(tools or self.DEFAULT_TOOLS)

        # ── Memória ───────────────────────────────────────────────────────
        self._ltm = None
        self._episodic = None
        if enable_memory:
            self._init_memory()

        # ── Raciocínio ────────────────────────────────────────────────────
        self._cot = None
        self._critique = None

    # ── Inicialização lazy ────────────────────────────────────────────────

    def _init_tools(self, tool_names: list[str]):
        try:
            from agents.tools.registry import build_default_registry, ToolKit
            build_default_registry()
            self._toolkit = ToolKit(tool_names if tool_names else None)
            self.logger.info(f"Ferramentas: {list(self._toolkit._tools.keys())}")
        except Exception as e:
            self.logger.warning(f"Ferramentas não inicializadas: {e}")

    def _init_memory(self):
        try:
            from agents.memory.long_term_memory import LongTermMemory
            from agents.memory.episodic import EpisodicMemory
            self._ltm = LongTermMemory(self.name)
            self._episodic = EpisodicMemory(self.name)
        except Exception as e:
            self.logger.warning(f"Memória não inicializada: {e}")

    def _get_cot(self):
        if self._cot is None:
            from agents.reasoning.chain_of_thought import ChainOfThought
            self._cot = ChainOfThought()
        return self._cot

    def _get_critique(self):
        if self._critique is None:
            from agents.reasoning.self_critique import SelfCritique
            self._critique = SelfCritique()
        return self._critique

    # ── IA Core ───────────────────────────────────────────────────────────

    def ask(self, prompt: str, system: str = "", max_tokens: int | None = None) -> str:
        """Envia prompt ao provider com retry automático."""
        request = CompletionRequest(
            messages=[Message(role="user", content=prompt)],
            system=system,
            max_tokens=max_tokens or self.MAX_TOKENS,
            model=self.MODEL or "",
        )
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                resp = self.provider.complete(request)
                self.logger.info(
                    f"tokens in={resp.input_tokens} out={resp.output_tokens} "
                    f"${resp.cost_usd:.6f} {resp.latency_ms}ms"
                )
                return resp.text
            except Exception as e:
                err = str(e)
                if "rate" in err.lower() or "429" in err or "limit" in err.lower():
                    wait = self.RETRY_DELAY * attempt
                    self.logger.warning(f"Rate limit — aguardando {wait}s")
                    time.sleep(wait)
                elif attempt == self.MAX_RETRIES:
                    raise
                else:
                    time.sleep(self.RETRY_DELAY)
        raise RuntimeError("Máximo de tentativas atingido")

    def ask_json(self, prompt: str, system: str = "") -> dict:
        """Pede resposta em JSON e faz parse."""
        sys_ = (system + "\n\n" if system else "") + "Responda APENAS com JSON válido, sem markdown."
        request = CompletionRequest(
            messages=[Message(role="user", content=prompt)],
            system=sys_,
            max_tokens=self.MAX_TOKENS,
            model=self.MODEL or "",
            json_mode=True,
        )
        resp = self.provider.complete(request)
        raw = resp.text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(raw)

    def ask_with_history(self, messages: list[dict], system: str = "",
                         max_tokens: int | None = None) -> str:
        """Conversa multi-turn com histórico."""
        msgs = [Message(role=m["role"], content=m["content"]) for m in messages]
        request = CompletionRequest(
            messages=msgs,
            system=system,
            max_tokens=max_tokens or self.MAX_TOKENS,
            model=self.MODEL or "",
        )
        resp = self.provider.complete(request)
        return resp.text

    # ── Raciocínio avançado ───────────────────────────────────────────────

    def think(self, question: str, context: str = "", deep: bool = False) -> str:
        """
        Chain-of-Thought: pensa passo a passo antes de responder.
        Args:
            question: Pergunta ou problema
            context:  Contexto adicional
            deep:     Se True, usa few-shot CoT com exemplos
        """
        cot = self._get_cot()
        if deep:
            prompt = cot.build_prompt(question, context=context, examples=cot.few_shot_examples())
        else:
            from agents.reasoning.chain_of_thought import ZeroShotCoT
            prompt = ZeroShotCoT.augment(
                cot.build_prompt(question, context=context)
            )
        return self.ask(prompt)

    def think_json(self, question: str, context: str = "") -> dict:
        """CoT com output estruturado em JSON."""
        cot = self._get_cot()
        from agents.reasoning.chain_of_thought import COT_JSON_SYSTEM
        prompt = cot.build_json_prompt(question, context=context)
        return self.ask_json(prompt, system=COT_JSON_SYSTEM)

    def refine(self, question: str, initial_answer: str, iterations: int = 1) -> str:
        """
        Self-critique loop: gera → critica → melhora.
        Args:
            question:       Pergunta original
            initial_answer: Resposta a melhorar
            iterations:     Quantas rodadas de melhoria
        """
        critique = self._get_critique()
        answer = initial_answer

        for i in range(iterations):
            critique_prompt = critique.build_critique_prompt(question, answer)
            feedback = self.ask(critique_prompt, system="Seja um crítico rigoroso e específico.")
            improve_prompt = critique.build_improve_prompt(question, answer, feedback)
            answer = self.ask(improve_prompt)
            self.logger.info(f"Refine iteração {i+1}/{iterations} concluída")

        return answer

    def explore(self, problem: str, context: str = "", breadth: int = 3) -> str:
        """
        Tree-of-Thought: explora múltiplos caminhos e sintetiza o melhor.
        Args:
            problem:  Problema a resolver
            context:  Contexto adicional
            breadth:  Quantas abordagens gerar por nível
        """
        from agents.reasoning.tree_of_thought import TreeOfThought
        tot = TreeOfThought(breadth=breadth)

        # Gerar N abordagens
        gen_prompt = tot.build_generate_prompt(problem, context=context, n=breadth)
        thoughts_text = self.ask(gen_prompt)
        thoughts = tot.parse_thoughts(thoughts_text)

        if not thoughts:
            return self.ask(problem)

        # Avaliar abordagens
        eval_prompt = tot.build_evaluate_prompt(problem, thoughts)
        eval_text = self.ask(eval_prompt)
        scores = tot.parse_scores(eval_text, len(thoughts))

        # Top-2 abordagens
        ranked = sorted(zip(scores, thoughts), reverse=True)
        top = [t for _, t in ranked[:2]]

        # Sintetizar resposta final
        final_prompt = tot.build_final_prompt(problem, [top])
        return self.ask(final_prompt)

    # ── Ferramentas ───────────────────────────────────────────────────────

    def search(self, query: str, max_results: int = 5) -> list[dict]:
        """Busca na web via WebSearchTool."""
        if not self._toolkit:
            raise RuntimeError("Ferramentas não habilitadas. Passe enable_tools=True.")
        result = self._toolkit.run("web_search", query=query, max_results=max_results)
        if result.success:
            return result.output if isinstance(result.output, list) else [{"snippet": str(result.output)}]
        self.logger.warning(f"Busca falhou: {result.error}")
        return []

    def search_and_summarize(self, query: str, n: int = 5) -> str:
        """Busca na web e resume os resultados com IA."""
        results = self.search(query, max_results=n)
        if not results:
            return f"Nenhum resultado encontrado para: {query}"

        results_text = "\n".join(
            f"{i+1}. {r.get('title', '')}: {r.get('snippet', '')}"
            for i, r in enumerate(results)
        )
        return self.ask(
            f"Busca: {query}\n\nResultados:\n{results_text}\n\n"
            "Resuma os achados principais em linguagem clara e direta.",
        )

    def run_code(self, code: str, timeout: int = 30) -> str:
        """Executa código Python e retorna output."""
        if not self._toolkit:
            raise RuntimeError("Ferramentas não habilitadas.")
        result = self._toolkit.run("code_executor", code=code, timeout=timeout)
        return str(result)

    def read_file(self, path: str) -> str:
        """Lê um arquivo (PDF, CSV, DOCX, JSON, TXT)."""
        if not self._toolkit:
            raise RuntimeError("Ferramentas não habilitadas.")
        result = self._toolkit.run("file_reader", path=path)
        return str(result)

    def scrape(self, url: str) -> str:
        """Acessa URL e extrai texto da página."""
        if not self._toolkit:
            raise RuntimeError("Ferramentas não habilitadas.")
        result = self._toolkit.run("scraper", url=url)
        return str(result)

    def calculate(self, expression: str, variables: dict | None = None) -> Any:
        """Avalia expressão matemática."""
        if not self._toolkit:
            raise RuntimeError("Ferramentas não habilitadas.")
        result = self._toolkit.run("calculator", expression=expression, variables=variables or {})
        return result.output if result.success else result.error

    # ── Memória ───────────────────────────────────────────────────────────

    def remember(self, text: str, category: str = "fact", importance: int = 5,
                 tags: list[str] | None = None) -> str | None:
        """Salva informação na memória de longo prazo."""
        if not self._ltm:
            return None
        return self._ltm.remember(text, category=category, importance=importance, tags=tags)

    def recall(self, query: str, n: int = 5, as_context: bool = False) -> Any:
        """
        Busca memórias relevantes por similaridade.
        Args:
            query:      O que buscar
            n:          Máximo de resultados
            as_context: Se True, retorna string formatada para prompt
        """
        if not self._ltm:
            return "" if as_context else []
        if as_context:
            return self._ltm.recall_as_context(query, n=n)
        return self._ltm.recall(query, n=n)

    def ask_with_memory(self, prompt: str, system: str = "", memory_query: str = "") -> str:
        """
        Envia prompt enriquecido com memórias relevantes.
        """
        query = memory_query or prompt[:200]
        memory_ctx = self.recall(query, n=5, as_context=True)
        episodic_ctx = ""
        if self._episodic:
            episodic_ctx = self._episodic.format_for_prompt(n=3)

        enriched_system = system
        if memory_ctx:
            enriched_system += f"\n\n{memory_ctx}"
        if episodic_ctx:
            enriched_system += f"\n\n{episodic_ctx}"

        return self.ask(prompt, system=enriched_system.strip())

    def start_episode(self, task: str, input_summary: str = "") -> str | None:
        """Inicia registro de episódio."""
        if not self._episodic:
            return None
        return self._episodic.start_episode(task, input_summary=input_summary)

    def end_episode(self, ep_id: str, output_summary: str = "", success: bool = True,
                    learnings: list[str] | None = None) -> None:
        """Finaliza registro de episódio."""
        if self._episodic and ep_id:
            self._episodic.end_episode(ep_id, output_summary=output_summary,
                                       success=success, learnings=learnings)

    # ── Multimodal ────────────────────────────────────────────────────────

    def see(self, image_path: str, prompt: str = "") -> str:
        """Analisa uma imagem (vision)."""
        from agents.multimodal.vision import VisionProcessor
        vp = VisionProcessor(provider=self.provider.name)
        result = vp.analyze(image_path, prompt=prompt)
        return result.description

    def read_document(self, path: str, questions: list[str] | None = None) -> dict:
        """Lê e analisa um documento (PDF, DOCX, XLSX…)."""
        from agents.multimodal.document import DocumentProcessor
        dp = DocumentProcessor()
        doc = dp.analyze(path, questions=questions)
        return {
            "path": doc.path,
            "summary": doc.summary,
            "key_points": doc.key_points,
            "entities": doc.entities,
            "text_preview": doc.text[:500],
        }

    # ── Estado persistente ────────────────────────────────────────────────

    def _state_path(self) -> Path:
        return self.state_dir / f"{self.name}_state.json"

    def _load_state(self) -> dict:
        p = self._state_path()
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def save_state(self, data: dict | None = None) -> None:
        if data:
            self._state.update(data)
        self._state["updated_at"] = datetime.now().isoformat()
        self._state_path().write_text(
            json.dumps(self._state, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        self.logger.info("Estado salvo")

    def get_state(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    # ── Output ────────────────────────────────────────────────────────────

    def save_result(self, data: Any, prefix: str = "result", ext: str = "json") -> Path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.output_dir / f"{prefix}_{ts}.{ext}"
        if ext == "json":
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            path.write_text(str(data), encoding="utf-8")
        self.logger.info(f"Resultado salvo em {path}")
        return path

    def save_markdown(self, content: str, prefix: str = "report") -> Path:
        return self.save_result(content, prefix=prefix, ext="md")

    def timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── Info ──────────────────────────────────────────────────────────────

    def info(self) -> dict:
        """Retorna resumo das capacidades do agente."""
        return {
            "name":        self.name,
            "provider":    self.provider.name,
            "model":       self.provider.default_model,
            "tools":       list(self._toolkit._tools.keys()) if self._toolkit else [],
            "memory":      self._ltm.stats() if self._ltm else {},
            "episodes":    self._episodic.stats() if self._episodic else {},
        }
