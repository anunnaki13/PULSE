# PULSE production smoke test.
# Required params: BaseUrl, Email, Password
# Optional: PeriodeId

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$BaseUrl,

    [Parameter(Mandatory = $true)]
    [string]$Email,

    [Parameter(Mandatory = $true)]
    [string]$Password,

    [string]$PeriodeId
)

$ErrorActionPreference = "Stop"

$health = Invoke-RestMethod -Uri "$BaseUrl/api/v1/health" -Method Get
$loginBody = @{ email = $Email; password = $Password } | ConvertTo-Json
$login = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/login" -Method Post -ContentType "application/json" -Body $loginBody
$headers = @{ Authorization = "Bearer $($login.access_token)" }
$me = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/me" -Headers $headers
$detail = Invoke-RestMethod -Uri "$BaseUrl/api/v1/health/detail" -Headers $headers
$ai = Invoke-RestMethod -Uri "$BaseUrl/api/v1/ai/status" -Headers $headers

$result = [ordered]@{
    user = $me.email
    health_status = $health.status
    health_detail_status = $detail.status
    ai_mode = $ai.mode
}

if ($PeriodeId) {
    $dashboard = Invoke-RestMethod -Uri "$BaseUrl/api/v1/dashboard/executive?periode_id=$PeriodeId" -Headers $headers
    $pdfPath = Join-Path $env:TEMP "pulse-prod-smoke-nko.pdf"
    Invoke-WebRequest -Uri "$BaseUrl/api/v1/reports/nko-semester?periode_id=$PeriodeId&format=pdf" -Headers $headers -OutFile $pdfPath | Out-Null
    $result["periode_id"] = $PeriodeId
    $result["dashboard_nko"] = $dashboard.snapshot.nko_total
    $result["report_pdf_bytes"] = (Get-Item $pdfPath).Length
    Remove-Item $pdfPath -Force
}

Write-Host "PULSE production smoke" -ForegroundColor Cyan
$result.GetEnumerator() | ForEach-Object {
    Write-Host "$($_.Key)=$($_.Value)"
}
