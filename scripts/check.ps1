Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\_common.ps1"

Set-Location (Split-Path -Parent $PSScriptRoot)
Assert-RiceRepoRoot -ScriptName 'check.ps1'
$venvPython = Require-VenvPython
$pytestBaseTemp = Get-PytestBaseTempPath

# line-length: ignore-next-line -- legacy line pending wrap
Invoke-CheckedCommand -FilePath "$PSScriptRoot\lint.ps1" -Arguments @() -Stage 'lint'
# line-length: ignore-next-line -- legacy line pending wrap
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m', 'pytest', '-q', '--basetemp', $pytestBaseTemp) -Stage 'pytest'
# line-length: ignore-next-line -- legacy line pending wrap
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m','rice','count','supports','--max-support-edges','8') -Stage 'count supports'
# line-length: ignore-next-line -- legacy line pending wrap
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m','rice','count','bundle-types') -Stage 'count bundle-types'
# line-length: ignore-next-line -- legacy line pending wrap
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m','rice','count','bundle-sets','--profile','main') -Stage 'count bundle-sets'
# line-length: ignore-next-line -- legacy line pending wrap
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m','rice','count','assignments','--profile','main') -Stage 'count assignments'
# line-length: ignore-next-line -- legacy line pending wrap
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m','rice','count','assigned-supports','--profile','main') -Stage 'count assigned-supports'
# line-length: ignore-next-line -- legacy line pending wrap
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m','rice','count','networks','--profile','golden') -Stage 'count networks'
