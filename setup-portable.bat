@echo off
setlocal
title Agy Studio Portable - Setup Windows 11
color 0b

set "APP_ROOT=%~dp0"
if "%APP_ROOT:~-1%"=="\" set "APP_ROOT=%APP_ROOT:~0,-1%"

cd /d "%APP_ROOT%"

set "UV_EXE=%APP_ROOT%\runtime\uv.exe"
if not exist "%UV_EXE%" (
    where uv >nul 2>&1
    if %errorlevel% equ 0 (
        for /f "delims=" %%i in ('where uv') do set "UV_EXE=%%i"
    )
)

if not exist "%UV_EXE%" (
    echo [ERREUR] uv.exe est introuvable dans runtime\uv.exe ni sur le systeme.
    pause
    exit /b 1
)

"%UV_EXE%" run python "scripts\setup_portable.py"

echo.
set /p "LAUNCH=Voulez-vous lancer Agy Studio maintenant ? (O/N, defaut O) : "
if /i "%LAUNCH%"=="" set "LAUNCH=O"
if /i "%LAUNCH%"=="O" (
    echo [*] Lancement de Agy Studio...
    start "" "%APP_ROOT%\AgyStudio.exe"
)

exit /b 0
