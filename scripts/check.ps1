Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\_common.ps1"

Set-Location (Split-Path -Parent $PSScriptRoot)
Assert-RiceRepoRoot -ScriptName 'check.ps1'
$venvPython = Require-VenvPython

Invoke-CheckedCommand -FilePath "$PSScriptRoot\lint.ps1" -Arguments @() -Stage 'lint'
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m','pytest','-q') -Stage 'pytest'
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m','rice','count','supports','--max-support-edges','8') -Stage 'count supports'
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m','rice','count','bundle-types') -Stage 'count bundle-types'
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m','rice','count','bundle-sets','--profile','main') -Stage 'count bundle-sets'
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m','rice','count','assignments','--profile','main') -Stage 'count assignments'
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m','rice','count','assigned-supports','--profile','main') -Stage 'count assigned-supports'
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m','rice','count','networks','--profile','golden') -Stage 'count networks'
