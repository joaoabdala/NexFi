@echo off
setlocal enabledelayedexpansion

set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "FRONTEND=%ROOT%frontend"

echo ============================================
echo   NexFi - Personal Finance by Abdala Nexus
echo ============================================
echo.

echo Encerrando processos antigos nas portas 8000 e 5173...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173 " ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)

set "NEEDS_SETUP=0"

if not exist "%BACKEND%\.venv\Scripts\python.exe" (
    echo [AVISO] Ambiente virtual do backend nao encontrado.
    set "NEEDS_SETUP=1"
)

if not exist "%BACKEND%\.env" (
    echo [AVISO] backend\.env nao encontrado.
    set "NEEDS_SETUP=1"
)

if not exist "%FRONTEND%\node_modules" (
    echo [AVISO] Dependencias do frontend nao instaladas.
    set "NEEDS_SETUP=1"
)

if exist "%BACKEND%\.env" (
    findstr /C:"DATABASE_URL=sqlite" "%BACKEND%\.env" >nul 2>&1
    if not errorlevel 1 (
        if not exist "%BACKEND%\dev.db" (
            echo [AVISO] Banco de dados nao encontrado ^(dev.db^) — migrations/seed provavelmente nao foram executados.
            set "NEEDS_SETUP=1"
        )
    )
)

if "%NEEDS_SETUP%"=="1" (
    echo.
    echo O projeto ainda nao esta totalmente configurado.
    echo Execute setup.bat primeiro.
    echo.
    pause
    exit /b 1
)

echo [NexFi] Iniciando backend ^(FastAPI^) em http://localhost:8000 ...
start "NexFi - Backend" cmd /k "cd /d "%BACKEND%" && .venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --reload"

echo [NexFi] Iniciando frontend ^(Vite^) em http://localhost:5173 ...
start "NexFi - Frontend" cmd /k "cd /d "%FRONTEND%" && npm run dev"

echo.
echo Aguardando os servidores subirem...
timeout /t 4 /nobreak >nul

start "" http://localhost:5173

echo.
echo Backend:  http://localhost:8000/docs
echo Frontend: http://localhost:5173
echo Usuario demo: demo@abdalanexus.com / demo123
echo.
echo Esta janela pode ser fechada. Backend e frontend continuam rodando
echo em suas proprias janelas — feche-as para encerrar a aplicacao.
pause

endlocal
