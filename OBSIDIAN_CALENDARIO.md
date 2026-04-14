# Calendario + Pesquisa no Obsidian

Agora a IA pode ler um calendario em formato ICS e transformar eventos do dia em pesquisas salvas no Obsidian.

## Como funciona
- Eventos com prefixo `Pesquisa:` viram consultas.
- Exemplo: `Pesquisa: qual tipo de editor mais esta sendo procurado no Brasil`
- A IA pesquisa, resume e salva em `obsidian-ai-vault/Memoria/Calendario/...`

## Formas de conectar
- Arquivo local `.ics`
- URL ICS privada do Google Calendar ou outro calendario compativel

## Configuracao no .env
```env
OBSIDIAN_CALENDAR_SOURCE=data/pesquisas_agendadas.ics
OBSIDIAN_CALENDAR_WINDOW_DAYS=1
OBSIDIAN_CALENDAR_STATE=state/obsidian_calendar_state.json
```

## Exemplo de uso manual
```bash
uv run python run.py auto obsidian-calendar
```

## Pela interface
- Abra a IA web
- Clique em `Ler calendario`

## Regras para o evento
- Coloque `Pesquisa:` no comeco do titulo
- O resto do titulo vira a pergunta de pesquisa
- Se quiser, tambem pode colocar a pergunta na descricao com `Pesquisa:`
