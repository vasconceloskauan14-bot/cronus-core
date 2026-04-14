"""
Knowledge Graph Agent — ULTIMATE CRONUS
Construção e consulta de grafo de conhecimento empresarial.

Uso:
    python knowledge_graph.py extract --source data/documento.json --type "relatorio"
    python knowledge_graph.py query --graph data/grafo.json --question "quais clientes compram produto X?"
    python knowledge_graph.py build --sources data/ --output data/knowledge_graph.json
    python knowledge_graph.py insights --graph data/grafo.json
    python knowledge_graph.py update --graph data/grafo.json --new-data data/novos_dados.json
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from base_agent import BaseAgent

SYSTEM_KG = """Você é o Knowledge Graph agent do ULTIMATE CRONUS.
Você extrai, estrutura e conecta conhecimento empresarial em grafos de entidades e relações.
Pense como um data scientist + ontologista que transforma dados não-estruturados em conhecimento acionável.
Entidades devem ter tipos claros. Relações devem ser verbos precisos. Tudo deve ser consultável."""


class KnowledgeGraphAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="KNOWLEDGE_GRAPH", output_dir="agents/output")

    def extract_entities(self, source: dict, doc_type: str) -> dict:
        """Extrai entidades e relações de um documento."""
        self.logger.info(f"Extract entities from {doc_type}")
        content = source.get("texto") or source.get("content") or json.dumps(source)
        prompt = f"""Extraia entidades e relações deste documento de negócios:

TIPO: {doc_type}
CONTEÚDO:
{content[:4000]}

Retorne JSON com:
- entidades: lista de objetos com:
  - id: identificador único (slug)
  - tipo: "pessoa"|"empresa"|"produto"|"mercado"|"processo"|"metrica"|"evento"|"local"|"tecnologia"
  - nome: nome canônico
  - atributos: dict de propriedades relevantes
  - mencoes: como é mencionado no documento
- relacoes: lista de objetos com:
  - sujeito_id: id da entidade sujeito
  - verbo: relação (compra, usa, lidera, concorre_com, etc)
  - objeto_id: id da entidade objeto
  - atributos: propriedades da relação (data, valor, etc)
  - confianca: 0-1 (certeza desta relação)
- fatos_chave: afirmações importantes que não se encaixam em relações simples
- contexto_temporal: quando se passam os eventos descritos
- qualidade_extracao: 0-100 (quanto foi possível extrair do documento)"""

        result = self.ask_json(prompt, system=SYSTEM_KG)
        entidades = result.get("entidades", [])
        relacoes = result.get("relacoes", [])
        print(f"\n🧠 Entity Extraction — {doc_type}")
        print(f"  Entidades: {len(entidades)} | Relações: {len(relacoes)}")
        by_type = {}
        for e in entidades:
            t = e.get("tipo", "outro")
            by_type[t] = by_type.get(t, 0) + 1
        for t, c in by_type.items():
            print(f"  {t}: {c}")
        self.save_result(result, prefix="kg_entities")
        return result

    def query_graph(self, graph: dict, question: str) -> dict:
        """Consulta o knowledge graph com uma pergunta em linguagem natural."""
        self.logger.info(f"Query: {question[:60]}")
        prompt = f"""Responda esta pergunta consultando o knowledge graph:

PERGUNTA: {question}

KNOWLEDGE GRAPH:
{json.dumps(graph, indent=2, ensure_ascii=False)[:6000]}

Retorne JSON com:
- resposta: resposta direta em linguagem natural
- confianca: 0-100 (certeza da resposta)
- entidades_envolvidas: quais entidades do grafo respondem à pergunta
- caminho_inferencia: como chegou à resposta (sequência de relações)
- dados_suporte: dados específicos que sustentam a resposta
- lacunas: informações que faltam para responder melhor
- perguntas_relacionadas: 3 perguntas relacionadas que valem explorar
- insights_adicionais: o que mais o grafo revela sobre este tema"""

        result = self.ask_json(prompt, system=SYSTEM_KG)
        resposta = result.get("resposta", "")
        confianca = result.get("confianca", 0)
        print(f"\n🔍 KG Query ({confianca}% confiança)")
        print(f"  Q: {question[:80]}")
        print(f"  A: {resposta[:150]}")
        self.save_result(result, prefix="kg_query")
        return result

    def build_graph(self, sources_dir: str, output_path: str) -> dict:
        """Constrói knowledge graph a partir de múltiplas fontes."""
        self.logger.info(f"Building graph from {sources_dir}")

        sources = []
        sources_path = Path(sources_dir)
        if sources_path.exists():
            for f in sources_path.glob("*.json"):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    sources.append({"file": f.name, "data": data})
                except Exception:
                    pass

        prompt = f"""Construa um knowledge graph unificado a partir destas fontes:

FONTES ({len(sources)} arquivos):
{json.dumps(sources[:5], indent=2, ensure_ascii=False)[:5000]}

Retorne JSON com:
- entidades: lista completa de entidades únicas (deduplicadas)
- relacoes: lista completa de relações únicas
- clusters: grupos de entidades fortemente conectadas
- entidades_centrais: as 10 entidades mais conectadas (hubs do grafo)
- metricas_grafo:
  - total_entidades: número
  - total_relacoes: número
  - densidade: relações por entidade
  - componentes_conectados: número de clusters isolados
- tipos_entidade_distribuicao: contagem por tipo
- qualidade_geral: score de qualidade do grafo 0-100
- recomendacoes: o que adicionar para enriquecer o grafo"""

        result = self.ask_json(prompt, system=SYSTEM_KG)
        metricas = result.get("metricas_grafo", {})
        print(f"\n🕸️  Knowledge Graph Built")
        print(f"  Entidades: {metricas.get('total_entidades', '?')} | Relações: {metricas.get('total_relacoes', '?')}")
        print(f"  Densidade: {metricas.get('densidade', '?')}")

        # Save the graph to output path
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  Grafo salvo → {output_path}")

        self.save_result(result, prefix="knowledge_graph")
        return result

    def generate_insights(self, graph: dict) -> dict:
        """Gera insights automáticos a partir do knowledge graph."""
        self.logger.info("Generating insights from graph")
        prompt = f"""Analise este knowledge graph e gere insights de negócio:

KNOWLEDGE GRAPH:
{json.dumps(graph, indent=2, ensure_ascii=False)[:6000]}

Retorne JSON com:
- insights_estrategicos: 5-10 insights não óbvios descobertos no grafo
- padroes_detectados: padrões e tendências visíveis nas relações
- anomalias: relações ou entidades inesperadas
- oportunidades: oportunidades de negócio reveladas pelas conexões
- riscos: riscos identificados pelas relações no grafo
- recomendacoes_acao: ações concretas baseadas nos insights
- perguntas_investigar: questões que merecem investigação mais profunda
- entidades_monitorar: entidades que devem ser monitoradas por serem críticas
- projecoes: o que o grafo sugere sobre o futuro"""

        result = self.ask_json(prompt, system=SYSTEM_KG)
        insights = result.get("insights_estrategicos", [])
        print(f"\n💡 KG Insights — {len(insights) if isinstance(insights, list) else '?'} insights gerados")
        for i, insight in enumerate(insights[:3] if isinstance(insights, list) else [], 1):
            print(f"  {i}. {str(insight)[:100]}")
        self.save_result(result, prefix="kg_insights")
        return result

    def update_graph(self, graph: dict, new_data: dict) -> dict:
        """Atualiza o knowledge graph com novos dados."""
        self.logger.info("Updating knowledge graph")
        prompt = f"""Atualize este knowledge graph com novos dados, resolvendo conflitos e deduplicando:

GRAFO ATUAL:
Entidades: {len(graph.get('entidades', []))} | Relações: {len(graph.get('relacoes', []))}
{json.dumps({'entidades': graph.get('entidades', [])[:20], 'relacoes': graph.get('relacoes', [])[:20]}, indent=2, ensure_ascii=False)[:3000]}

NOVOS DADOS:
{json.dumps(new_data, indent=2, ensure_ascii=False)[:3000]}

Retorne JSON com:
- entidades_adicionadas: novas entidades inseridas
- entidades_atualizadas: entidades existentes com novos atributos
- relacoes_adicionadas: novas relações
- relacoes_removidas: relações contraditadas pelos novos dados
- conflitos_resolvidos: como resolveu dados conflitantes
- grafo_atualizado: o grafo completo atualizado
- changelog: resumo das mudanças feitas"""

        result = self.ask_json(prompt, system=SYSTEM_KG)
        adicionadas = result.get("entidades_adicionadas", [])
        atualizadas = result.get("entidades_atualizadas", [])
        print(f"\n🔄 Graph Update — +{len(adicionadas) if isinstance(adicionadas, list) else '?'} entidades, ~{len(atualizadas) if isinstance(atualizadas, list) else '?'} atualizadas")
        self.save_result(result, prefix="kg_updated")
        return result.get("grafo_atualizado", graph)


def main():
    parser = argparse.ArgumentParser(description="Knowledge Graph Agent — ULTIMATE CRONUS")
    sub = parser.add_subparsers(dest="command")

    p_e = sub.add_parser("extract")
    p_e.add_argument("--source", required=True)
    p_e.add_argument("--type", default="documento", dest="doc_type")

    p_q = sub.add_parser("query")
    p_q.add_argument("--graph", required=True)
    p_q.add_argument("--question", required=True)

    p_b = sub.add_parser("build")
    p_b.add_argument("--sources", required=True)
    p_b.add_argument("--output", default="data/knowledge_graph.json")

    sub.add_parser("insights").add_argument("--graph", required=True)

    p_u = sub.add_parser("update")
    p_u.add_argument("--graph", required=True)
    p_u.add_argument("--new-data", required=True)

    args = parser.parse_args()
    agent = KnowledgeGraphAgent()
    def load(p): return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else {}

    if args.command == "extract":
        agent.extract_entities(load(args.source), args.doc_type)
    elif args.command == "query":
        agent.query_graph(load(args.graph), args.question)
    elif args.command == "build":
        agent.build_graph(args.sources, args.output)
    elif args.command == "insights":
        agent.generate_insights(load(args.graph))
    elif args.command == "update":
        agent.update_graph(load(args.graph), load(args.new_data))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
