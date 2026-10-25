$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
if(Test-Path 'data\service.json'){ throw 'Service record exists. Run stop.ps1 or inspect the process first.' }
python owner.py init
$pythonPath=(python -c "import sys; print(sys.executable)").Trim()
if($LASTEXITCODE -ne 0 -or !(Test-Path -LiteralPath $pythonPath)){ throw "Cannot resolve Python executable" }
$serverPath=Join-Path $PSScriptRoot 'server.py'
$serverArgs='"' + $serverPath + '" --port 8765'
$proc=Start-Process -FilePath $pythonPath -ArgumentList $serverArgs -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput 'data\service.out' -RedirectStandardError 'data\service.err'
@{pid=$proc.Id;start_time=$proc.StartTime.ToUniversalTime().ToString('o');script=$serverPath} | ConvertTo-Json | Set-Content -LiteralPath 'data\service.json' -Encoding utf8
Write-Output 'http://127.0.0.1:8765 - use stop.ps1 to stop this service'
