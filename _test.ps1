Set-Location "C:\6FBA~1\SCRUM~1\70AA~1\5806~1"
$env:PORT = "8000"
$env:HF_HUB_OFFLINE = "1"
try {
    python -u -c "print('hello from python')" 2>&1 | Write-Host
    Write-Host "---"
    python -u main.py 2>&1 | Select-Object -First 50
} catch {
    Write-Host "CAUGHT: $($_.Exception.Message)"
}
