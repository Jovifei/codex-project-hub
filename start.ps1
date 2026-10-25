$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
python owner.py init
python server.py --port 8765
