Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\_common.ps1"

Assert-RiceRepoRoot -ScriptName 'test.ps1'
$venvPython = Require-VenvPython
$pytestBaseTemp = Get-PytestBaseTempPath

# line-length: ignore-next-line -- legacy line pending wrap
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m', 'pytest', '-q', '--basetemp', $pytestBaseTemp) -Stage 'pytest'
