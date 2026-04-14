@echo off
chcp 65001 >nul
:: ============================================================
::  CRONUS — Sincronizar notas do Railway/GitHub para Obsidian
::  Baixa automaticamente tudo que o Railway criou na nuvem.
::  Adicione este arquivo ao Agendador de Tarefas para rodar
::  a cada 15 min enquanto o PC estiver ligado.
:: ============================================================

set VAULT=C:\Users\adria\Desktop\claude-code-main\claude-code-main\obsidian-ai-vault
set BASH=C:\Program Files\Git\bin\bash.exe

if not exist "%VAULT%\.git" (
    echo [ERRO] Vault nao inicializado como repositorio git.
    echo Execute o passo 4 do guia DEPLOY_RAILWAY.txt primeiro.
    pause
    exit /b 1
)

echo [CRONUS] Sincronizando notas do GitHub...
"%BASH%" -c "cd '%VAULT%' && git fetch origin && git merge origin/main --no-edit --strategy-option=theirs 2>&1"

if %ERRORLEVEL%==0 (
    echo [OK] Notas sincronizadas com sucesso!
) else (
    echo [AVISO] Nenhuma nota nova ou conflito ignorado.
)

:: Abre o Obsidian depois de sincronizar (opcional)
:: start "" "C:\Users\adria\AppData\Local\Programs\Obsidian\Obsidian.exe"

exit /b 0
