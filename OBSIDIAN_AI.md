# IA com memoria no Obsidian

Esta base cria uma IA local simples cuja memoria fica guardada em um vault do Obsidian.

## O que foi criado
- Servidor web: `automation/obsidian_memory_ai.py`
- Busca e persistencia em Markdown: `automation/obsidian_memory_store.py`
- Interface web: `automation/static/obsidian_memory_ai.html`
- Vault inicial: `obsidian-ai-vault/`

## Como iniciar
```bash
uv run python run.py auto obsidian-ai
```

Depois abra no navegador:

```text
http://127.0.0.1:8787
```

## Companion por voz
Para deixar o Zeus sempre ouvindo com uma bolinha flutuante na lateral da tela:

```bash
uv run python run.py auto zeus-companion
```

Detalhes de uso e controles: `ZEUS_COMPANION.md`

## Variaveis uteis
- `OPENAI_API_KEY`: chave da OpenAI
- `CRONUS_PROVIDER`: provider padrao, por exemplo `openai` ou `ollama`
- `OBSIDIAN_AI_PROVIDER`: provider especifico desta IA
- `OBSIDIAN_AI_MODEL`: modelo desejado
- `OBSIDIAN_AI_PORT`: porta do servidor
- `OBSIDIAN_AI_VAULT`: caminho do vault

## Memoria
- Conversas: `obsidian-ai-vault/Memoria/Conversas/`
- Diario resumido: `obsidian-ai-vault/Memoria/Diario/`
- Memoria manual: `obsidian-ai-vault/Inbox/` e `obsidian-ai-vault/Memoria/`
- Cerebro Zeus: `obsidian-ai-vault/01 - Zeus.md` e `obsidian-ai-vault/Memoria/Zeus/`

## Uso recomendado
1. Abra `obsidian-ai-vault/` no Obsidian.
2. Edite `Memoria/Identidade.md` e `Memoria/Fatos Importantes.md`.
3. Abra `01 - Zeus.md` para navegar pelo cerebro do Zeus.
4. Suba o servidor.
5. Converse pela interface web e use o formulario "Ensinar o Zeus" para guardar comandos, falas, regras e preferencias.
