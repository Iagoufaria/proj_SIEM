@echo off
REM Script de build do SIEM TCC. Execute no Windows, dentro da pasta do projeto.
REM Requisito: Python 3.11+ instalado e no PATH.

echo ==========================================
echo   SIEM TCC - Build do executavel (.exe)
echo ==========================================

if not exist ".venv" (
    echo [*] Criando ambiente virtual...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo [*] Instalando dependencias...
pip install --upgrade pip >nul
pip install -r requirements.txt

echo [*] Limpando builds anteriores...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

echo [*] Gerando executavel com PyInstaller...
pyinstaller siem.spec

echo.
echo ==========================================
echo   Build concluido!
echo   Executavel em: dist\SIEM_TCC.exe
echo ==========================================
pause
