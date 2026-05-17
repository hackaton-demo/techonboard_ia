param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

$ErrorActionPreference = "Stop"

function Set-EnvFile {
    param([string]$Source)
    if (-not (Test-Path $Source)) {
        Write-Host "No se encontro $Source" -ForegroundColor Red
        exit 1
    }
    Copy-Item -Path $Source -Destination ".env" -Force
    Write-Host "Usando $Source como .env" -ForegroundColor DarkGray
}

function Invoke-Mock {
    Write-Host ""
    Write-Host "Modo MOCK - sin APIs externas requeridas" -ForegroundColor Magenta
    Write-Host "Gemini / GitHub / Jira / Slack retornan datos simulados" -ForegroundColor DarkGray
    Write-Host ""
    Set-EnvFile ".env.mock"
    docker compose up -d db redis
    Write-Host "Esperando base de datos..." -ForegroundColor DarkGray
    Start-Sleep -Seconds 5
    docker compose up -d backend celery_worker frontend
    Write-Host ""
    Write-Host "Listo en http://localhost:3000" -ForegroundColor Green
    Write-Host "API docs en http://localhost:8000/docs" -ForegroundColor Green
}

function Invoke-Full {
    Write-Host ""
    Write-Host "Modo FULL - con APIs reales" -ForegroundColor Cyan
    if (-not (Test-Path ".env")) {
        Write-Host ".env no encontrado - copia .env.example y agrega tus credenciales" -ForegroundColor Red
        exit 1
    }
    $key = (Get-Content ".env" | Where-Object { $_ -match "^GOOGLE_API_KEY=" }) -replace "^GOOGLE_API_KEY=", ""
    if ([string]::IsNullOrWhiteSpace($key)) {
        Write-Host "GOOGLE_API_KEY vacio en .env - agrega tu key de Google AI Studio" -ForegroundColor Red
        exit 1
    }
    docker compose up -d
    Write-Host ""
    Write-Host "Listo en http://localhost:3000" -ForegroundColor Green
    Write-Host "API docs en http://localhost:8000/docs" -ForegroundColor Green
}

function Invoke-Up {
    Write-Host "Levantando servicios..." -ForegroundColor Cyan
    docker compose up -d
}

function Invoke-Down {
    Write-Host "Deteniendo servicios..." -ForegroundColor Yellow
    docker compose down
}

function Invoke-Logs {
    docker compose logs -f
}

function Invoke-Migrate {
    Write-Host "Corriendo migraciones..." -ForegroundColor Cyan
    docker compose exec backend alembic upgrade head
}

function Invoke-Seed {
    Write-Host "Cargando datos de demo..." -ForegroundColor Cyan
    docker compose exec backend python scripts/seed_demo_data.py
}

function Invoke-Shell {
    docker compose exec backend bash
}

function Invoke-Test {
    docker compose exec backend pytest
}

function Invoke-Build {
    Write-Host "Construyendo imagenes..." -ForegroundColor Cyan
    docker compose build --no-cache
}

function Invoke-Reset {
    Write-Host "Reset completo..." -ForegroundColor Red
    docker compose down -v
    Invoke-Up
    Start-Sleep -Seconds 5
    Invoke-Migrate
    Invoke-Seed
}

function Invoke-FrontendDev {
    Set-Location frontend
    npm run dev
}

function Invoke-BackendDev {
    uvicorn main:app --reload --port 8000
}

function Invoke-Help {
    Write-Host ""
    Write-Host "TechOnboard - Comandos disponibles" -ForegroundColor Green
    Write-Host "Uso: .\run.ps1 [comando]" -ForegroundColor White
    Write-Host ""
    Write-Host "  MODOS DE ARRANQUE:" -ForegroundColor Cyan
    Write-Host "  mock          Sin APIs externas, todo simulado, solo necesitas Docker" -ForegroundColor Magenta
    Write-Host "  full          Con APIs reales, requiere .env con GOOGLE_API_KEY" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  OPERACIONES:" -ForegroundColor Cyan
    Write-Host "  up            Levanta todos los servicios Docker" -ForegroundColor Yellow
    Write-Host "  down          Detiene todos los servicios" -ForegroundColor Yellow
    Write-Host "  logs          Ver logs en tiempo real" -ForegroundColor Yellow
    Write-Host "  migrate       Corre migraciones de Alembic" -ForegroundColor Yellow
    Write-Host "  seed          Carga datos de demo" -ForegroundColor Yellow
    Write-Host "  shell         Abre bash en el backend" -ForegroundColor Yellow
    Write-Host "  test          Corre los tests" -ForegroundColor Yellow
    Write-Host "  build         Reconstruye las imagenes Docker" -ForegroundColor Yellow
    Write-Host "  reset         Borra todo y vuelve a empezar" -ForegroundColor Yellow
    Write-Host "  frontend-dev  Inicia el frontend en modo dev" -ForegroundColor Yellow
    Write-Host "  backend-dev   Inicia el backend directamente sin Docker" -ForegroundColor Yellow
    Write-Host ""
}

switch ($Command.ToLower()) {
    "mock"         { Invoke-Mock }
    "full"         { Invoke-Full }
    "up"           { Invoke-Up }
    "down"         { Invoke-Down }
    "logs"         { Invoke-Logs }
    "migrate"      { Invoke-Migrate }
    "seed"         { Invoke-Seed }
    "shell"        { Invoke-Shell }
    "test"         { Invoke-Test }
    "build"        { Invoke-Build }
    "reset"        { Invoke-Reset }
    "frontend-dev" { Invoke-FrontendDev }
    "backend-dev"  { Invoke-BackendDev }
    default        { Invoke-Help }
}
