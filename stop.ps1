$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
if(!(Test-Path 'data\service.json')){ Write-Output 'No managed background process record. Press Ctrl+C for a foreground server.'; exit }
$record=Get-Content -LiteralPath 'data\service.json' -Raw | ConvertFrom-Json
$proc=Get-Process -Id $record.pid -ErrorAction SilentlyContinue
if($proc){
 $started=$proc.StartTime.ToUniversalTime().ToString('o')
 $info=Get-CimInstance Win32_Process -Filter "ProcessId = $($record.pid)"
 if($started -ne $record.start_time -or !$info.CommandLine.Contains($record.script)){ throw 'Process identity mismatch. Refusing to stop a different process.' }
 Stop-Process -Id $record.pid
}
Remove-Item -LiteralPath 'data\service.json'
Write-Output 'Hub background service stopped. SQLite data preserved.'
