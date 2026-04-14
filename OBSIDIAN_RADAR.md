# Radar 24h para o Obsidian

Este worker deixa uma IA pesquisando temas continuamente e gravando notas no vault do Obsidian.

## Arquivos principais
- `automation/obsidian_radar_worker.py`
- `config/obsidian_radar.json`
- `state/obsidian_radar_state.json`

## Como iniciar uma rodada
```bash
uv run python run.py auto obsidian-radar --once
```

## Como deixar rodando em loop
```bash
uv run python run.py auto obsidian-radar
```

## Onde as notas entram
- `obsidian-ai-vault/Memoria/Radar/...`

## Temas que ja deixei configurados
- Demanda por editores
- Tipos de edicao mais procurados
- Nichos que mais precisam de edicao
- Faixas de preco e pacotes de edicao

## Como configurar os temas
Edite `config/obsidian_radar.json`.

Campos mais importantes por tema:
- `name`: nome do radar
- `query`: busca usada para encontrar sinais públicos
- `folder`: pasta relativa ao vault
- `notes`: direção editorial
- `cadence_hours`: intervalo ideal daquele tema
- `priority`: prioridade maior roda antes
- `enabled`: ativa ou desativa o tema

## Como funciona
1. O worker escolhe os temas vencidos ou mais prioritários.
2. Busca resultados na web.
3. Usa a IA para sintetizar o que importa.
4. Grava uma nota nova no Obsidian.
5. Guarda estado para evitar repetir sempre as mesmas URLs.
