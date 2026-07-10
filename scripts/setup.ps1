Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\_common.ps1"

Assert-RiceRepoRoot -ScriptName 'setup.ps1'

function Test-PythonCandidate {
    param(
        [Parameter(Mandatory = $true)]
        [string] $FilePath,

        [string[]] $Arguments = @()
    )

    $repoVenv = Resolve-PathUnderRepo -RelativePath '.venv'
    $script = @'
import os
import sys
exe = os.path.abspath(sys.executable)
venv = os.path.abspath(sys.argv[1])
if exe.lower().startswith((venv + os.sep).lower()):
    raise SystemExit(2)
if sys.version_info < (3, 11):
    raise SystemExit(1)
print(sys.executable)
print(sys.version.split()[0])
'@

    $output = & $FilePath @Arguments -c $script $repoVenv 2>$null
    if ($LASTEXITCODE -ne 0 -or $null -eq $output -or $output.Count -lt 2) {
        return $null
    }

    return [pscustomobject]@{
        FilePath = $FilePath
        Arguments = $Arguments
        Executable = [string]$output[0]
        Version = [string]$output[1]
    }
}

function Find-BasePython {
    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($null -ne $py) {
        foreach ($versionArg in @('-3.12', '-3.11')) {
            $candidate = Test-PythonCandidate -FilePath $py.Source -Arguments @($versionArg)
            if ($null -ne $candidate) {
                return $candidate
            }
        }
    }

    $python = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($null -ne $python) {
        $candidate = Test-PythonCandidate -FilePath $python.Source
        if ($null -ne $candidate) {
            return $candidate
        }
    }

    return $null
}

Write-Host 'Setting up RICE development environment'

$basePython = Find-BasePython
if ($null -eq $basePython) {
    throw 'Error: Python 3.11 or newer is required, but no suitable Windows interpreter was found.'
}

Write-Host 'Selected base Python:'
Write-Host ("  executable: {0}" -f $basePython.Executable)
Write-Host ("  version: {0}" -f $basePython.Version)

Invoke-CheckedCommand -FilePath $basePython.FilePath -Arguments ($basePython.Arguments + @('-m', 'venv', '.venv')) -Stage 'create virtual environment'

$venvPython = Get-VenvPythonPath
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m', 'pip', 'install', '--upgrade', 'pip', 'setuptools', 'wheel') -Stage 'upgrade packaging tools'
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m', 'pip', 'install', '-e', '.[dev]') -Stage 'install editable project with dev dependencies'

Write-Host ''
Write-Host 'Virtual environment Python:'
& $venvPython -c 'import sys; print("  executable:", sys.executable); print("  version:", sys.version.split()[0])'
if ($LASTEXITCODE -ne 0) {
    throw 'Venv Python version check failed.'
}

Write-Host ''
Write-Host 'Import smoke test:'
$smoke = @'
import sys

import networkx
import pytest
import rice

print("python", sys.executable)
print("networkx", networkx.__version__)
print("pytest", pytest.__version__)
print("rice", rice.__file__)
'@
& $venvPython -c $smoke
if ($LASTEXITCODE -ne 0) {
    throw 'Import smoke test failed.'
}

Write-Host ''
Write-Host 'Setup complete.'
