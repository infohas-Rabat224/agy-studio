# Agy Studio - Portable PowerShell Launcher
# Uses $PSScriptRoot for portability - works from any location

$APP_ROOT = $PSScriptRoot

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "         AGY STUDIO - AGENTIC DESKTOP WORKSPACE" -ForegroundColor White
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "[*] Dossier applicatif : $APP_ROOT" -ForegroundColor Green

# Discover uv.exe - portable multi-location search
$uv = $null
$uvCandidates = @(
    "$APP_ROOT\runtime\uv.exe",                                                 # Bundled portable
    "$env:LOCALAPPDATA\hermes\bin\uv.exe",                                      # Hermes install
    "$env:LOCALAPPDATA\uv\uv.exe",                                              # Standard uv location
    "$env:LOCALAPPDATA\Programs\astral\uv\uv.exe",                              # Astral Programs
    (& where.exe uv 2>$null | Select-Object -First 1)                          # PATH fallback
)

foreach ($candidate in $uvCandidates) {
    if ($candidate -and (Test-Path $candidate -ErrorAction SilentlyContinue)) {
        $uv = $candidate
        break
    }
}

if (-not $uv) {
    Write-Error "uv.exe introuvable. Installez UV depuis https://docs.astral.sh/uv/"
    Read-Host "Appuyez sur Entree pour quitter"
    exit 1
}

Write-Host "[*] UV trouve : $uv" -ForegroundColor Green

# Discover Chrome - portable
$chrome = $null
$chromeCandidates = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
)
foreach ($c in $chromeCandidates) {
    if (Test-Path $c -ErrorAction SilentlyContinue) { $chrome = $c; break }
}

# Nettoyer les ports residuels
$proc8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($proc8000) {
    Stop-Process -Id $proc8000.OwningProcess -Force -ErrorAction SilentlyContinue
    Write-Host "[*] Port 8000 libere" -ForegroundColor Yellow
}
$proc8001 = Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue
if ($proc8001) {
    Stop-Process -Id $proc8001.OwningProcess -Force -ErrorAction SilentlyContinue
    Write-Host "[*] Port 8001 libere" -ForegroundColor Yellow
}

# Lancer le pont desktop natif pour FolderPicker
$pickerExe = "$APP_ROOT\AgyStudioFolderPicker.exe"
if (Test-Path $pickerExe) {
    Write-Host "[*] Lancement du pont natif AgyStudioFolderPicker (port 8001)..." -ForegroundColor Cyan
    Start-Process -FilePath $pickerExe -ArgumentList "--bridge 8001" -WindowStyle Hidden
}

# Lancer le navigateur
Start-Job -ScriptBlock {
    param($c)
    Start-Sleep -Milliseconds 1500
    if ($c -and (Test-Path $c)) {
        Start-Process $c -ArgumentList "--app=http://127.0.0.1:8000"
    } else {
        Start-Process "http://127.0.0.1:8000"
    }
} -ArgumentList $chrome | Out-Null

Write-Host "[*] Demarrage du serveur backend..." -ForegroundColor Green
Set-Location $APP_ROOT
& $uv run --with fastapi --with uvicorn --with websockets --with pydantic --with python-docx --with python-multipart --with pypdf --with openpyxl --with python-pptx --with pillow --with playwright --with httpx --with httpx2 python "backend\server.py"
