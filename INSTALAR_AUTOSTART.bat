@echo off
chcp 65001 >nul
echo ============================================================
echo  CRONUS - Instalar Auto-Start no Agendador de Tarefas
echo ============================================================
echo.

set UV=C:\Users\adria\.local\bin\uv.exe
set PROJ=C:\Users\adria\Desktop\claude-code-main\claude-code-main
set TASK=CRONUS_AutoStart

:: Remove tarefa antiga
schtasks /delete /tn "%TASK%" /f >nul 2>&1

:: Cria XML da tarefa
set XML=%TEMP%\cronus_task.xml
(
echo ^<?xml version="1.0" encoding="UTF-16"?^>
echo ^<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task"^>
echo   ^<Triggers^>
echo     ^<LogonTrigger^>^<Enabled^>true^</Enabled^>^</LogonTrigger^>
echo   ^</Triggers^>
echo   ^<Settings^>
echo     ^<MultipleInstancesPolicy^>IgnoreNew^</MultipleInstancesPolicy^>
echo     ^<RestartOnFailure^>^<Count^>999^</Count^>^<Interval^>PT2M^</Interval^>^</RestartOnFailure^>
echo     ^<ExecutionTimeLimit^>PT0S^</ExecutionTimeLimit^>
echo   ^</Settings^>
echo   ^<Actions^>
echo     ^<Exec^>
echo       ^<Command^>%UV%^</Command^>
echo       ^<Arguments^>run --directory "%PROJ%" python start_local.py^</Arguments^>
echo       ^<WorkingDirectory^>%PROJ%^</WorkingDirectory^>
echo     ^</Exec^>
echo   ^</Actions^>
echo ^</Task^>
) > "%XML%"

schtasks /create /tn "%TASK%" /xml "%XML%" /f
del "%XML%" >nul 2>&1

if %ERRORLEVEL%==0 (
    echo.
    echo [OK] CRONUS vai iniciar automaticamente ao ligar o PC!
    echo      E reiniciar sozinho se cair ^(a cada 2 min^).
) else (
    echo.
    echo [ERRO] Nao foi possivel criar a tarefa.
    echo        Tente rodar este arquivo como Administrador.
)

echo.
echo Iniciando CRONUS agora...
start "" /b "%UV%" run --directory "%PROJ%" python start_local.py

echo Aguardando servidor subir...
timeout /t 8 >nul
start http://127.0.0.1:8787
echo.
pause
