# Generate a production-ready PULSE env file without printing secret values.

[CmdletBinding()]
param(
    [string]$Output = ".env.production.generated",
    [string]$AppBaseUrl = "https://pulse.tenayan.local",
    [string]$OpenRouterApiKey = "",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

if ((Test-Path $Output) -and -not $Force) {
    throw "$Output already exists. Re-run with -Force to overwrite."
}

function New-Secret([int]$Bytes = 48) {
    $buffer = [byte[]]::new($Bytes)
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $rng.GetBytes($buffer)
    } finally {
        $rng.Dispose()
    }
    return [Convert]::ToBase64String($buffer).TrimEnd("=") -replace "\+", "-" -replace "/", "_"
}

$postgresPassword = New-Secret
$adminPassword = New-Secret
$appSecret = New-Secret 64
$jwtSecret = New-Secret 64

$lines = @(
    "# PULSE production env generated $(Get-Date -Format o)",
    "# Keep this file outside Git. Review every value before deployment.",
    "",
    "APP_SECRET_KEY=$appSecret",
    "JWT_SECRET_KEY=$jwtSecret",
    "JWT_ALGORITHM=HS256",
    "JWT_ACCESS_TTL_MIN=60",
    "JWT_REFRESH_TTL_DAYS=14",
    "",
    "POSTGRES_HOST=pulse-db",
    "POSTGRES_PORT=5432",
    "POSTGRES_DB=pulse",
    "POSTGRES_USER=pulse",
    "POSTGRES_PASSWORD=$postgresPassword",
    "",
    "REDIS_URL=redis://pulse-redis:6379/0",
    "",
    "APP_BASE_URL=$AppBaseUrl",
    "APP_HOST_PORT=3399",
    "",
    "OPENROUTER_API_KEY=$OpenRouterApiKey",
    "OPENROUTER_BASE_URL=https://openrouter.ai/api/v1",
    "OPENROUTER_ROUTINE_MODEL=google/gemini-2.5-flash",
    "OPENROUTER_COMPLEX_MODEL=anthropic/claude-sonnet-4",
    "OPENROUTER_TIMEOUT_SECONDS=20",
    "AI_MOCK_MODE=false",
    "AI_MONTHLY_BUDGET_USD=5",
    "",
    "BACKUP_DIR=/var/backups/pulse",
    "BACKUP_RETAIN_DAYS=30",
    "NAS_DEST=/mnt/nas/pulse-backups",
    "",
    "INITIAL_ADMIN_EMAIL=admin@pulse.tenayan.local",
    "INITIAL_ADMIN_PASSWORD=$adminPassword"
)

Set-Content -Path $Output -Value ($lines -join [Environment]::NewLine) -Encoding UTF8
Write-Host "Generated $Output with strong local secrets. OpenRouter key present: $([bool]$OpenRouterApiKey)" -ForegroundColor Green
Write-Host "Next: review values, copy to .env on the production host, then run ./scripts/dev.ps1 prod-check." -ForegroundColor Cyan
