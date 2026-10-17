# Setup & Start Karai Metrics Exporter and Persist Startup Entries
$ErrorActionPreference = "Continue"

$py = "C:\Users\Bryan\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\pythonw.exe"
if (-not (Test-Path $py)) {
    $py = "C:\Users\Bryan\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\python.exe"
}

# Stop any existing karai_metrics_exporter.py process
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "karai_metrics_exporter\.py" } | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}

$expCmd = "`"$py`" C:\Users\Bryan\karai_metrics_exporter.py"
$res = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine=$expCmd}
Write-Host "Started Karai Metrics Exporter PID: $($res.ProcessId)"

$llamaCmd = '"C:\Users\Bryan\AppData\Local\Microsoft\WindowsApps\llama.exe" serve --model C:\Users\Bryan\huggingface\models--ggml-org--gemma-4-E4B-it-GGUF\snapshots\b8093469224f83f5c38f691eb906c380e9e63114\gemma-4-E4B-it-Q8_0.gguf --mmproj C:\Users\Bryan\huggingface\models--ggml-org--gemma-4-E4B-it-GGUF\snapshots\b8093469224f83f5c38f691eb906c380e9e63114\mmproj-gemma-4-E4B-it-Q8_0.gguf --host 0.0.0.0 --port 9931 --ctx-size 16384 --jinja --reasoning off --metrics --slots --api-key-file C:\Users\Bryan\AppData\Local\Packages\4e440e29-8151-4465-b20f-fb3acb283925_et8rgxdxvrbdj\LocalCache\Local\Llama\.llama.apikey'

Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "KaraiLlamaServer" -Value $llamaCmd
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "KaraiMetricsExporter" -Value $expCmd

# Ensure Windows Firewall allows port 9835 (or pythonw.exe) if admin, or check connectivity
New-NetFirewallRule -DisplayName "Karai Prometheus Exporter (Port 9835)" -Direction Inbound -LocalPort 9835 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue | Out-Null

Start-Sleep -Seconds 2

# Warm up Llama.cpp metrics with a quick inference request
$key = (Get-Content "C:\Users\Bryan\AppData\Local\Packages\4e440e29-8151-4465-b20f-fb3acb283925_et8rgxdxvrbdj\LocalCache\Local\Llama\.llama.apikey" -Raw).Trim()
$body = @{
    model = "gemma-4-E4B-it-Q8_0.gguf"
    messages = @(
        @{ role = "system"; content = "You are Captain Jean-Luc Picard. Reply in one short sentence." },
        @{ role = "user"; content = "Status report, Captain." }
    )
    max_tokens = 40
} | ConvertTo-Json -Compress

$chatResp = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:9931/v1/chat/completions" -Headers @{Authorization="Bearer $key"; "Content-Type"="application/json"} -Body $body
Write-Host "Picard Test Response: $($chatResp.choices[0].message.content)"

Write-Host "=== Sample Exporter Output (127.0.0.1:9835/metrics) ==="
(Invoke-WebRequest -Uri "http://127.0.0.1:9835/metrics" -UseBasicParsing).Content
