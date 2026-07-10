Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\_common.ps1"

Assert-RiceRepoRoot -ScriptName 'check.ps1'
$venvPython = Require-VenvPython

Invoke-CheckedCommand -FilePath (Join-Path (Get-Location) 'scripts\lint.ps1') -Stage 'lint.ps1'
Invoke-CheckedCommand -FilePath (Join-Path (Get-Location) 'scripts\test.ps1') -Stage 'test.ps1'
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m', 'rice', 'supports', '--max-edges', '8') -Stage 'rice supports'
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m', 'rice', 'bundles', '--max-r', '3', '--max-reactive', '5') -Stage 'rice bundles'
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m', 'rice', 'labelings', '--max-r', '3', '--max-reactive', '5') -Stage 'rice labelings'
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m', 'rice', 'reduced', '--max-r', '2', '--max-reactive', '3') -Stage 'rice reduced'
