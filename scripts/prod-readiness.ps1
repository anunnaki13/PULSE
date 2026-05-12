# PULSE production readiness checker.
# Validates go-live gates without printing secret values.

[CmdletBinding()]
param(
    [string]$EnvFile = ".env",
    [switch]$SkipDocker
)

$ErrorActionPreference = "Stop"
$failures = New-Object System.Collections.Generic.List[string]
$warnings = New-Object System.Collections.Generic.List[string]

function Add-Fail([string]$Message) { $script:failures.Add($Message) | Out-Null }
function Add-Warn([string]$Message) { $script:warnings.Add($Message) | Out-Null }

function Read-EnvFile([string]$Path) {
    $data = @{}
    if (-not (Test-Path $Path)) {
        Add-Fail "Missing env file: $Path"
        return $data
    }
    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) { return }
        $idx = $line.IndexOf("=")
        $key = $line.Substring(0, $idx)
        $value = $line.Substring($idx + 1)
        $data[$key] = $value
    }
    return $data
}

function Test-Secret([hashtable]$Env, [string]$Name, [int]$MinLength = 32) {
    $value = [string]($Env[$Name])
    if (-not $value) {
        Add-Fail "$Name is missing"
        return
    }
    if ($value.Length -lt $MinLength) {
        Add-Fail "$Name must be at least $MinLength characters"
    }
    if ($value -match "(?i)replace|change|dev|default|password|pulse-.*-dev") {
        Add-Fail "$Name still looks like a placeholder or dev secret"
    }
}

$envData = Read-EnvFile $EnvFile

Test-Secret $envData "APP_SECRET_KEY"
Test-Secret $envData "JWT_SECRET_KEY"
Test-Secret $envData "POSTGRES_PASSWORD"
Test-Secret $envData "INITIAL_ADMIN_PASSWORD"

if (-not [string]($envData["OPENROUTER_API_KEY"])) {
    Add-Fail "OPENROUTER_API_KEY is missing"
}
if ([string]($envData["AI_MOCK_MODE"]) -ne "false") {
    Add-Fail "AI_MOCK_MODE must be false for production"
}
if ([string]($envData["APP_BASE_URL"]) -notmatch "^https://") {
    Add-Fail "APP_BASE_URL must use https:// in production"
}

if (-not (Test-Path "infra/production/host-nginx-pulse.conf")) {
    Add-Fail "Missing host nginx TLS template"
}
if (-not (Test-Path "infra/production/apply-firewall.sh")) {
    Add-Fail "Missing production firewall script"
}
if (-not (Test-Path "infra/production/uptimerobot-monitor.example.json")) {
    Add-Fail "Missing external monitor example"
}

if (-not $SkipDocker) {
    docker compose -f docker-compose.yml config --quiet
    if ($LASTEXITCODE -ne 0) { Add-Fail "docker compose config failed" }

    $dbPorts = docker inspect pulse-db --format '{{json .NetworkSettings.Ports}}' 2>$null
    if ($LASTEXITCODE -eq 0 -and $dbPorts -notmatch '"5432/tcp":null') {
        Add-Fail "pulse-db appears to expose port 5432 to the host"
    }

    $nginxPorts = docker inspect pulse-nginx --format '{{json .NetworkSettings.Ports}}' 2>$null
    if ($LASTEXITCODE -eq 0 -and $nginxPorts -notmatch '"80/tcp"') {
        Add-Fail "pulse-nginx does not expose the app port"
    }

    $logConfig = docker inspect pulse-nginx --format '{{json .HostConfig.LogConfig}}' 2>$null
    if ($LASTEXITCODE -eq 0 -and $logConfig -notmatch '"max-size":"10m"') {
        Add-Warn "Docker log rotation is not visible on pulse-nginx; recreate stack with docker compose -f docker-compose.yml up -d --wait"
    }
}

Write-Host "PULSE production readiness" -ForegroundColor Cyan
if ($warnings.Count -gt 0) {
    Write-Host "Warnings:" -ForegroundColor Yellow
    $warnings | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
}
if ($failures.Count -gt 0) {
    Write-Host "Failures:" -ForegroundColor Red
    $failures | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    exit 1
}

Write-Host "PASS: production readiness checks passed" -ForegroundColor Green
