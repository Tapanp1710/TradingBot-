# UTF-8 Encoding for Emoji Support
$OutputEncoding = [console]::InputEncoding = [console]::OutputEncoding = New-Object System.Text.UTF8Encoding
chcp 65001 > $null

# Set Python encoding
$env:PYTHONIOENCODING="utf-8"

# Start bot
Write-Host "Starting Trading Bot with Online Learning..." -ForegroundColor Green
python run_bot_watchdog.py
