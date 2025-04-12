@echo off
setlocal

REM Verifica se o .env existe
if not exist ".env" (
    echo [ERRO] Arquivo .env nao encontrado!
    echo Certifique-se de que o arquivo .env esta na mesma pasta que este .bat.
    pause
    exit /b 1
)

REM Carrega variáveis do .env
for /f "tokens=1,* delims==" %%A in (".env") do (
    set "%%A=%%B"
)

REM Executa o main.py
python application\src\main.py

pause