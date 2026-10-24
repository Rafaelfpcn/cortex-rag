$backendDir = Join-Path $PSScriptRoot "backend"
$venvPython = Join-Path $backendDir ".venv\Scripts\python.exe"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  CortexRAG -- Enterprise Document Intelligence Engine    " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

if (-not (Test-Path $venvPython)) {
    Write-Host "[*] Ambiente virtual nao encontrado. Criando em $backendDir\.venv..." -ForegroundColor Yellow
    python -m venv (Join-Path $backendDir ".venv")
    & $venvPython -m pip install -r (Join-Path $backendDir "requirements.txt")
}

$port = 8000
$portBusy = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portBusy) {
    Write-Host "[*] Porta 8000 ocupada. Alternando para a porta 8080..." -ForegroundColor Yellow
    $port = 8080
}

Write-Host ""
Write-Host " [OK] Servidor iniciando com sucesso!" -ForegroundColor Green
Write-Host " Web App Dark Mode: http://localhost:$port" -ForegroundColor Cyan
Write-Host " Swagger OpenAPI:   http://localhost:$port/docs" -ForegroundColor Cyan
Write-Host " Dica: Clique no botao 'Acessar Demo (1-Clique)' na interface para testar." -ForegroundColor Gray
Write-Host ""
Write-Host "Pressione CTRL+C para encerrar o servidor a qualquer momento." -ForegroundColor DarkGray
Write-Host ""

Set-Location $backendDir
& $venvPython -m uvicorn app.main:app --port $port
