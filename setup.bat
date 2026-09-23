@echo off
setlocal

set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "FRONTEND=%ROOT%frontend"

echo ============================================
echo   NexFi - Setup (instala e prepara o projeto)
echo ============================================
echo.

REM --- Backend: ambiente virtual ---
if not exist "%BACKEND%\.venv\Scripts\python.exe" (
    echo [Setup] Criando ambiente virtual do backend...
    python -m venv "%BACKEND%\.venv"
    if errorlevel 1 (
        echo [ERRO] Falha ao criar o ambiente virtual. Verifique se o Python esta instalado e no PATH.
        pause
        exit /b 1
    )
)

echo [Setup] Instalando dependencias do backend...
call "%BACKEND%\.venv\Scripts\pip.exe" install -q -r "%BACKEND%\requirements.txt"
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias do backend.
    pause
    exit /b 1
)

REM --- Backend: .env ---
if not exist "%BACKEND%\.env" (
    echo [Setup] Criando backend\.env a partir de .env.example...
    copy "%BACKEND%\.env.example" "%BACKEND%\.env" >nul
)

REM --- Frontend: dependencias ---
if not exist "%FRONTEND%\node_modules" (
    echo [Setup] Instalando dependencias do frontend ^(npm install^)...
    pushd "%FRONTEND%"
    call npm install
    if errorlevel 1 (
        echo [ERRO] Falha ao instalar dependencias do frontend.
        popd
        pause
        exit /b 1
    )
    popd
) else (
    echo [Setup] Dependencias do frontend ja instaladas — pulando npm install.
)

REM --- Frontend: .env ---
if not exist "%FRONTEND%\.env" (
    echo [Setup] Criando frontend\.env ...
    echo VITE_API_URL=http://localhost:8000/api/v1> "%FRONTEND%\.env"
)

REM --- Banco de dados: migrations ---
echo [Setup] Aplicando migrations do banco de dados...
pushd "%BACKEND%"
call .venv\Scripts\alembic.exe upgrade head
if errorlevel 1 (
    echo [ERRO] Falha ao aplicar migrations. Verifique backend\.env ^(DATABASE_URL^) e a conexao com o banco.
    popd
    pause
    exit /b 1
)
popd

REM --- Banco de dados: seed (idempotente - pula se o usuario demo ja existir) ---
echo [Setup] Populando dados de exemplo ^(seed^)...
pushd "%BACKEND%"
call .venv\Scripts\python.exe -m app.seeds.seed
popd

echo.
echo ============================================
echo   Setup concluido!
echo ============================================
echo Usuario demo: demo@abdalanexus.com / demo123
echo.
echo Agora execute start.bat para iniciar a aplicacao.
pause

endlocal
