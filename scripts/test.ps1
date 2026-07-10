Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\_common.ps1"

Assert-RiceRepoRoot -ScriptName 'test.ps1'
$venvPython = Require-VenvPython

Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m', 'pytest', '-q') -Stage 'pytest'
