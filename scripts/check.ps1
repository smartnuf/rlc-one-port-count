Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
$venvPython = Join-Path (Get-Location) '.venv\Scripts\python.exe'
function Invoke-CheckedCommand { param([string]$FilePath, [string[]]$Arguments, [string]$Stage) Write-Host "+ $Stage"; & $FilePath @Arguments; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m','ruff','check','.') -Stage 'ruff'
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m','pytest','-q') -Stage 'pytest'
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m','rice','count','supports','--max-support-edges','8') -Stage 'count supports'
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m','rice','count','bundle-types') -Stage 'count bundle-types'
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m','rice','count','bundle-sets','--profile','main') -Stage 'count bundle-sets'
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m','rice','count','assignments','--profile','main') -Stage 'count assignments'
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m','rice','count','assigned-supports','--profile','main') -Stage 'count assigned-supports'
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m','rice','count','networks','--profile','golden') -Stage 'count networks'
