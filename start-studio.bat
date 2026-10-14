@echo off
title Agy Studio - Agentic AI Workspace
color 0b

echo =================================================================
echo                 AGY STUDIO - AGENTIC WORKSPACE
echo           Vibe Coding ^| Deep Thinking ^| Creative ^| Pedagogie
echo =================================================================
echo.

:: Use the directory of this .bat file as APP_ROOT (portable)
set APP_ROOT=%~dp0
if "%APP_ROOT:~-1%"=="\" set APP_ROOT=%APP_ROOT:~0,-1%

echo [*] Dossier applicatif : %APP_ROOT%

:: Discover uv.exe - search multiple locations, most likely first
set UV_EXE=

:: 1. Check same-folder runtime/ (bundled portable)
if exist "%APP_ROOT%\runtime\uv.exe" set UV_EXE=%APP_ROOT%\runtime\uv.exe

:: 2. Check Hermes bin (common install location on this machine class)
if not defined UV_EXE if exist "%LOCALAPPDATA%\hermes\bin\uv.exe" set UV_EXE=%LOCALAPPDATA%\hermes\bin\uv.exe

:: 3. Check standard uv install location
if not defined UV_EXE if exist "%LOCALAPPDATA%\uv\uv.exe" set UV_EXE=%LOCALAPPDATA%\uv\uv.exe

:: 4. Check Astral uv in Python tools
if not defined UV_EXE if exist "%LOCALAPPDATA%\Programs\astral\uv\uv.exe" set UV_EXE=%LOCALAPPDATA%\Programs\astral\uv\uv.exe

:: 5. Fall back to PATH
if not defined UV_EXE for /f "delims=" %%i in ('where uv 2^>nul') do if not defined UV_EXE set UV_EXE=%%i

if not defined UV_EXE (
    echo [ERREUR] uv.exe introuvable. Installez UV depuis https://docs.astral.sh/uv/
    pause
    exit /b 1
)

echo [*] UV trouve : %UV_EXE%

:: Chrome or Edge discovery (portable app-mode window)
set BROWSER_EXE=
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set BROWSER_EXE=%ProgramFiles%\Google\Chrome\Application\chrome.exe
if not defined BROWSER_EXE if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set BROWSER_EXE=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe
if not defined BROWSER_EXE if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" set BROWSER_EXE=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe
if not defined BROWSER_EXE if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" set BROWSER_EXE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe
if not defined BROWSER_EXE if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" set BROWSER_EXE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe

:: Nettoyer les processus orphelins sur les ports 8000 et 8001
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8001 ^| findstr LISTENING') do taskkill /f /pid %%a >nul 2>&1

:: Lancer le pont natif desktop AgyStudioFolderPicker en arriere-plan
if exist "%APP_ROOT%\AgyStudioFolderPicker.exe" (
    echo [*] Lancement du pont natif AgyStudioFolderPicker (port 8001)...
    start "" /b "%APP_ROOT%\AgyStudioFolderPicker.exe" --bridge 8001
)

:: Lancer le navigateur vers Agy Studio apres 1.5s
if defined BROWSER_EXE (
    echo [*] Lancement du navigateur en mode application...
    start "" powershell -Command "Start-Sleep -Milliseconds 1500; Start-Process '%BROWSER_EXE%' -ArgumentList '--app=http://127.0.0.1:8000'"
) else (
    echo [*] Ouverture du navigateur par defaut...
    start "" powershell -Command "Start-Sleep -Milliseconds 1500; Start-Process 'http://127.0.0.1:8000'"
)

:: Demarrer le serveur FastAPI depuis le dossier de l'application (portable)
cd /d "%APP_ROOT%"
"%UV_EXE%" run --with fastapi --with uvicorn --with websockets --with pydantic --with python-docx --with python-multipart --with pypdf --with openpyxl --with python-pptx --with pillow --with playwright --with httpx --with httpx2 python "backend\server.py"
