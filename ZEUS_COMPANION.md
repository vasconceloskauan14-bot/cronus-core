# Zeus Companion

O Zeus Companion e uma bolinha flutuante para Windows que fica sempre visivel na lateral da tela, escuta a wake word `Zeus` e responde por voz.

## Como iniciar
```bash
uv run python run.py auto zeus-companion
```

Se preferir, no diretorio acima do projeto existe o atalho `Iniciar Zeus Companion.cmd`.

## Como usar
- Diga `Zeus` e espere o aviso falado: `Sim? Pode falar.`
- Ou diga tudo de uma vez, por exemplo: `Zeus, registra esse comando`.
- A bolinha muda de cor para mostrar o estado:
- `on`: escutando a wake word
- `ouvindo`: esperando a sua frase depois de `Zeus`
- `pensando`: enviando a pergunta
- `falando`: respondendo por voz
- `erro`: algum problema com microfone, servidor ou resposta

## Controles
- Arrastar com o mouse esquerdo: move a bolinha pela tela
- Clique duplo com o mouse esquerdo: ativa o Zeus manualmente
- Clique direito: fecha o companion

## Variaveis uteis
- `ZEUS_WAKE_WORD`: muda a palavra de ativacao
- `ZEUS_SERVER_URL`: muda o endereco do servidor do Zeus

## Requisitos
- Windows
- Microfone padrao configurado no sistema
- `System.Speech` disponivel no PowerShell do Windows

## Fallback de escuta
Se o reconhecimento nativo do Windows nao estiver configurado, o Zeus tenta usar transcricao via Groq com captura local do microfone.

- Chave usada: `GROQ_API_KEY`
- Modelo padrao: `whisper-large-v3-turbo`
- Captura local: pacote Python `sounddevice`
