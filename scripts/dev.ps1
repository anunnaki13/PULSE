# PULSE — PowerShell developer verbs
# Use this when GNU make is not on PATH (default on Windows hosts).
# Mirrors the targets in Makefile so behavior is identical across shells.
#
# Usage:
#   ./scripts/dev.ps1 up
#   ./scripts/dev.ps1 seed
#   ./scripts/dev.ps1 restore -File backup.sql.gz

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('help','up','down','build','seed','migrate','test','backup','restore','logs','lint','prod-env','prod-check','prod-smoke')]
    [string]$Verb = 'help',

    [Parameter()]
    [string]$File,

    [Parameter()]
    [string]$BaseUrl,

    [Parameter()]
    [string]$Email,

    [Parameter()]
    [string]$Password,

    [Parameter()]
    [string]$PeriodeId
)

function Show-Help {
    Write-Host "PULSE — Developer verbs (PowerShell)" -ForegroundColor Cyan
    Write-Host "  ./scripts/dev.ps1 up              Start all services"
    Write-Host "  ./scripts/dev.ps1 down            Stop and remove all services"
    Write-Host "  ./scripts/dev.ps1 build           Build all images"
    Write-Host "  ./scripts/dev.ps1 seed            Seed bidang + Konkin 2026 master data"
    Write-Host "  ./scripts/dev.ps1 migrate         Run Alembic migrations to head"
    Write-Host "  ./scripts/dev.ps1 test            Run backend pytest + frontend vitest"
    Write-Host "  ./scripts/dev.ps1 backup          Trigger backup script in pulse-backup sidecar"
    Write-Host "  ./scripts/dev.ps1 restore -File … Restore from a backup file"
    Write-Host "  ./scripts/dev.ps1 logs            Tail logs from all services"
    Write-Host "  ./scripts/dev.ps1 lint            Run ruff + eslint"
    Write-Host "  ./scripts/dev.ps1 prod-env        Generate .env.production.generated"
    Write-Host "  ./scripts/dev.ps1 prod-check      Validate production readiness gates"
    Write-Host "  ./scripts/dev.ps1 prod-smoke -BaseUrl … -Email … -Password … [-PeriodeId …]"
}

function Invoke-Cmd {
    param([string]$Cmd)
    Write-Host ">> $Cmd" -ForegroundColor DarkGray
    Invoke-Expression $Cmd
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed (exit $LASTEXITCODE): $Cmd"
    }
}

switch ($Verb) {
    'help'    { Show-Help }
    'up'      { Invoke-Cmd 'docker compose up -d --wait' }
    'down'    { Invoke-Cmd 'docker compose down' }
    'build'   { Invoke-Cmd 'docker compose build' }
    'seed'    { Invoke-Cmd 'docker compose exec pulse-backend python -m app.seed' }
    'migrate' { Invoke-Cmd 'docker compose exec pulse-backend alembic upgrade head' }
    'test'    {
        Invoke-Cmd 'docker compose exec pulse-backend pytest -x -q'
        Push-Location frontend
        try { Invoke-Cmd 'pnpm exec vitest run --reporter=basic' } finally { Pop-Location }
    }
    'backup'  { Invoke-Cmd 'docker compose exec pulse-backup /scripts/backup.sh' }
    'restore' {
        if (-not $File) { throw 'Usage: ./scripts/dev.ps1 restore -File <backup.sql.gz>' }
        Invoke-Cmd "docker compose exec -T pulse-backup /scripts/restore.sh `"$File`""
    }
    'logs'    { Invoke-Cmd 'docker compose logs -f --tail=200' }
    'lint'    {
        Push-Location backend
        try { Invoke-Cmd 'ruff check .' } finally { Pop-Location }
        Push-Location frontend
        try { Invoke-Cmd 'pnpm run lint' } finally { Pop-Location }
    }
    'prod-env'   { Invoke-Cmd './scripts/generate-prod-env.ps1' }
    'prod-check' { Invoke-Cmd './scripts/prod-readiness.ps1' }
    'prod-smoke' {
        if (-not $BaseUrl -or -not $Email -or -not $Password) {
            throw 'Usage: ./scripts/dev.ps1 prod-smoke -BaseUrl <url> -Email <email> -Password <password> [-PeriodeId <uuid>]'
        }
        $cmd = "./scripts/prod-smoke.ps1 -BaseUrl `"$BaseUrl`" -Email `"$Email`" -Password `"$Password`""
        if ($PeriodeId) { $cmd += " -PeriodeId `"$PeriodeId`"" }
        Invoke-Cmd $cmd
    }
    default   { Show-Help }
}
