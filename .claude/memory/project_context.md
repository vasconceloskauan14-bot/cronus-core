---
name: ULTIMATE CRONUS — Contexto do Projeto
description: O que é o projeto, seu objetivo, visão e estado atual de implementação
type: project
---

## O que é

O ULTIMATE CRONUS é um meta-framework de IA que usa o Claude Code CLI para construir uma infraestrutura de agentes autônomos capazes de operar uma empresa inteira. É um sistema de 20+ agentes especializados que trabalham em paralelo 24/7.

**Por que:** Quem controla a infraestrutura de IA controla o futuro da empresa. O objetivo é crescimento exponencial com mínima intervenção humana.

## Localização

Projeto em: `C:\Users\adria\Desktop\claude-code-main\claude-code-main`

Obsidian vault com 170+ arquivos .md de documentação e blueprints.
Código executável em: `agents/`, `automation/`, `integrations/`

## Estado atual (Abril 2026)

**Implementado:**
- `agents/base_agent.py` — classe base com Claude API, retry, logging, estado persistente
- `agents/swarm_agent.py` — pesquisa massiva paralela
- `agents/radar_agent.py` — monitoramento 24/7
- `agents/hunter_agent.py` — prospecção e qualificação de leads
- `agents/analyst_agent.py` — dados e BI
- `agents/scribe_agent.py` — geração de conteúdo em escala
- `agents/orchestrator.py` — coordenador multi-agente com missões JSON
- `automation/daily_report.py` — relatório executivo diário
- `automation/weekly_kpis.py` — KPIs semanais com trends e alertas
- `automation/cron_setup.py` — Task Scheduler / crontab
- `automation/event_triggers.py` — file watcher + webhook (GitHub, Stripe, Slack)
- `integrations/slack_notifier.py` — notificações Slack
- `integrations/github_webhook.py` — code review e PR review automáticos
- `setup.py` — setup completo em um comando
- `CLAUDE.md` — contexto automático para o Claude

**Ainda como blueprint (documentação, sem código):**
- CAPITAL — sistema financeiro autônomo
- CEO VIRTUAL — tomada de decisão estratégica
- FUNIS — conversão automatizada
- SCRIBE multimodal — vídeo, áudio, imagem
- Self-improvement loops
- Modo autônomo 24/7 completo

## Missões prontas para rodar

```bash
python agents/orchestrator.py --mission agents/missions/revenue_growth.json
python agents/orchestrator.py --mission agents/missions/market_research.json
```

## How to apply

Quando o usuário pedir para "continuar o projeto", "evoluir" ou "implementar" algo — verificar o estado acima e sugerir implementar os blueprints que ainda não têm código.
