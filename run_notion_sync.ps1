# --- run_notion_sync.ps1 (fixed) ---
Set-Location "C:\Projects\auto-trader-agent"

# PowerShell 자체 로그(시작/끝 기록)
Start-Transcript -Path "C:\Projects\auto-trader-agent\reports\logs\notion_sync_$(Get-Date -Format yyyy-MM-dd_HH-mm).log" -Append

# (선택) 가상환경
$venvActivate = "C:\Projects\auto-trader-agent\venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) { . $venvActivate }

# 로그 폴더 보장
$logDir = "C:\Projects\auto-trader-agent\reports\logs"
if (!(Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }

# 추가: 30일 지난 로그 자동 삭제
Get-ChildItem $logDir -Filter "notion_sync_*.log" -File | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } | Remove-Item -Force

# 파이썬 실행 (출력을 Transcript로 흘려보냄 + 별도 파일에도 보존)
$python = "python"
$script = "C:\Projects\auto-trader-agent\src\notion_update.py"

Write-Output ">>> Starting Notion Sync Job at $(Get-Date)"
& $python $script 2>&1 | ForEach-Object {
    $_ | Add-Content -Path (Join-Path $logDir "notion_sync_output.log")
    Write-Output $_
}
$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) {
    Write-Output ">>> Job FAILED with code $exitCode at $(Get-Date)"
    Stop-Transcript
    exit 1   # 스케줄러에서 실패로 표시
} else {
    Write-Output ">>> Job SUCCEEDED at $(Get-Date)"
    Stop-Transcript
    exit 0
}