---
name: Convenções do Projeto
description: Padrões de código, nomenclatura, estrutura de agentes e arquivos do ULTIMATE CRONUS
type: project
---

## Agentes Python

Todo agente deve:
1. Herdar de `BaseAgent` em `agents/base_agent.py`
2. Chamar Claude via `self.ask(prompt, system=SYSTEM_XXX)`
3. Usar `self.ask_json()` quando precisar de resposta estruturada
4. Salvar estado com `self.save_state(data)`
5. Salvar resultados com `self.save_result(data, prefix="nome")` ou `self.save_markdown(text)`
6. Ter CLI com `argparse` no bloco `if __name__ == "__main__"`
7. Ter uma constante `SYSTEM_XXX` no topo com o system prompt do agente

```python
class MeuAgente(BaseAgent):
    def __init__(self):
        super().__init__(name="MEU_AGENTE", output_dir="output/meu_agente")
    
    def fazer_algo(self, param: str) -> dict:
        self.logger.info(f"Fazendo algo com: {param}")
        result = self.ask_json(f"Analise: {param}", system=SYSTEM_MEU_AGENTE)
        self.save_result(result, prefix="resultado")
        return result
```

## Missões JSON (Orchestrator)

```json
{
  "name": "Nome da Missão",
  "objective": "O que quer alcançar",
  "success_criteria": { "metrica": "valor_alvo" },
  "steps": [
    {
      "name": "Nome da Etapa",
      "parallel": true,
      "tasks": [
        {
          "id": "id_unico",
          "agent": "swarm",
          "method": "research",
          "params": { "query": "...", "depth": 3 }
        }
      ]
    }
  ]
}
```

## Arquivos Obsidian (.md)

- Nome sempre com emoji no início: `🧠 Nome do Arquivo.md`
- Links internos: padrão wiki do Obsidian
- Canvas para mapas visuais: `Nome.canvas` com JSON de nodes e edges
- MOCs (Map of Content) como índices de categoria

## Estrutura de pastas

```
agents/           → scripts Python dos agentes
automation/       → automações agendadas
integrations/     → integrações externas (Slack, GitHub, etc)
config/           → configurações JSON globais
.claude/          → configurações do Claude Code
.claude/memory/   → memórias persistentes do projeto
output/           → resultados gerados
data/             → dados de entrada
reports/          → relatórios gerados
state/            → estado persistente dos agentes
logs/             → logs de execução
```

## Nomenclatura

- Agentes: `{nome}_agent.py` (ex: `swarm_agent.py`)
- Classes: `{Nome}Agent` (ex: `SwarmAgent`)
- Outputs: `{prefix}_{YYYYMMDD_HHMMSS}.{ext}`
- Relatórios: `{YYYY-MM-DD}.md` (daily) ou `{YYYY-Www}.md` (weekly)
- Missões: `{objetivo}.json` (ex: `revenue_growth.json`)

## How to apply

Sempre que criar novo agente ou missão, seguir estes padrões. Ao editar agentes existentes, manter consistência com a classe BaseAgent.
