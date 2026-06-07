$ErrorActionPreference = "Continue"
Set-Location "C:\6FBA~1\SCRUM~1\70AA~1\5806~1"
$env:PORT = "8000"
$env:HF_HUB_OFFLINE = "1"
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
$proc = Start-Process -FilePath "python" -ArgumentList "-u","main.py" -WorkingDirectory "C:\6FBA~1\SCRUM~1\70AA~1\5806~1" -PassThru -RedirectStandardError "C:\6FBA~1\SCRUM~1\70AA~1\5806~1\_stderr.log" -RedirectStandardOutput "C:\6FBA~1\SCRUM~1\70AA~1\5806~1\_stdout.log"
Write-Host "STARTED PID=$($proc.Id)"
