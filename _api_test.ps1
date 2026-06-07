$urls = @(
    "http://127.0.0.1:8000/api/stats",
    "http://127.0.0.1:8000/api/joke/random",
    "http://127.0.0.1:8000/api/categories"
)
$out = ""
foreach ($url in $urls) {
    try {
        $r = (New-Object Net.WebClient).DownloadString($url)
        $out += "$url`n$r`n---`n"
    } catch {
        $out += "$url`nERROR: $($_.Exception.Message)`n---`n"
    }
}
$out | Out-File "C:\6FBA~1\SCRUM~1\70AA~1\5806~1\_api_result.txt" -Encoding UTF8
Write-Host "DONE"
