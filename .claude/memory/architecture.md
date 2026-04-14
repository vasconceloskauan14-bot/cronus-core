---
name: Arquitetura dos 20 Sistemas
description: Os 20 sistemas do ULTIMATE CRONUS, suas relações, scripts e status de implementação
type: project
---

## Camadas da Arquitetura

### 🔴 Camada Executiva (topo)
- **CÉREBRO CENTRAL** — orquestra tudo. Script: `agents/orchestrator.py` ✅
- **REDE NEURAL** — topologia de comunicação entre agentes. Blueprint 📋
- **CONFIG GLOBAL** — settings, permissões. Script: `.claude/settings.json` ✅
- **DNA DA EMPRESA** — contexto base. Arquivo: `🧬 DNA da Empresa.md` 📋

### 🔵 Camada Intel & Campo
- **SWARM** — pesquisa massiva paralela (50+ fontes simultâneas). Script: `agents/swarm_agent.py` ✅
- **RADAR** — monitoramento contínuo 24/7, detecção de sinais. Script: `agents/radar_agent.py` ✅
- **HUNTER** — prospecção, qualificação de leads, outreach. Script: `agents/hunter_agent.py` ✅

### 🟢 Camada Business
- **ANALYST** — dados, BI, forecast, anomalias. Script: `agents/analyst_agent.py` ✅
- **CAPITAL** — sistema financeiro autônomo, caixa, margem. Blueprint 📋
- **CEO VIRTUAL** — tomada de decisão estratégica. Blueprint 📋
- **GLOBAL** — expansão internacional. Blueprint 📋

### 🟣 Camada de Geração
- **SCRIBE** — copy, emails, posts, artigos. Script: `agents/scribe_agent.py` ✅
- **FUNIS** — conversão automatizada. Blueprint 📋
- **ATENDIMENTO** — resposta autônoma a clientes. Blueprint 📋
- **VISION** — branding e posicionamento. Blueprint 📋

### 📚 Fundação Técnica
- **MEMÓRIA** — conhecimento persistente. `.claude/memory/` ✅
- **MCP** — extensões e integrações. `config/mcp_servers.json` ✅
- **SKILLS** — automações modulares. `src/skills/` (Claude Code) ✅
- **PLUGINS** — arquitetura extensível. Blueprint 📋
- **BRIDGE IDE** — integração VS Code/JetBrains. `src/bridge/` ✅

## Missões Disponíveis

| Missão | Arquivo | Agentes Envolvidos |
|--------|---------|-------------------|
| Revenue Growth 3x | `agents/missions/revenue_growth.json` | SWARM + RADAR + HUNTER + ANALYST + SCRIBE |
| Market Research | `agents/missions/market_research.json` | SWARM + RADAR + ANALYST |

## Fluxo de uma Missão Típica

```
Orchestrator recebe missão JSON
    ↓
Etapa 1 (paralela): SWARM pesquisa + RADAR monitora
    ↓
Etapa 2 (paralela): ANALYST analisa + HUNTER qualifica leads
    ↓
Etapa 3 (paralela): SCRIBE gera conteúdo + SCRIBE gera ads
    ↓
Orchestrator consolida com Claude → relatório executivo
```

## How to apply

Ao implementar novos agentes, seguir o padrão da `BaseAgent`. Ao criar missões, seguir o schema JSON de `revenue_growth.json`. Priorizar implementação dos blueprints (CAPITAL, CEO VIRTUAL, FUNIS) nas próximas sessões.
