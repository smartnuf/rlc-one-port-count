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

# line-length: ignore-next-line -- legacy line pending wrap
    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ([System.IO.Path]::GetRandomFileName())
    New-Item -ItemType Directory -Path $tempRoot | Out-Null
    try {
        & $FilePath @Arguments -m venv (Join-Path $tempRoot 'venv') *> $null
        if ($LASTEXITCODE -ne 0) {
            return $null
        }
    } finally {
# line-length: ignore-next-line -- legacy line pending wrap
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }

    return [pscustomobject]@{
        FilePath = $FilePath
        Arguments = $Arguments
        Executable = [string]$output[0]
        Version = [string]$output[1]
    }
}

function Find-BasePython {
# line-length: ignore-next-line -- legacy line pending wrap
    $seen = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    $candidates = @()

    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($null -ne $py) {
        $candidates += ,@($py.Source, @('-3'))
        $candidates += ,@($py.Source, @('-3.14'))
        $candidates += ,@($py.Source, @('-3.13'))
        $candidates += ,@($py.Source, @('-3.12'))
        $candidates += ,@($py.Source, @('-3.11'))
    }

    $python = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($null -ne $python) {
        $candidates += ,@($python.Source, @())
    }

    foreach ($entry in $candidates) {
        $filePath = [string]$entry[0]
        $arguments = [string[]]$entry[1]
        $key = $filePath + ' ' + ($arguments -join ' ')
        if (-not $seen.Add($key)) { continue }
# line-length: ignore-next-line -- legacy line pending wrap
        $candidate = Test-PythonCandidate -FilePath $filePath -Arguments $arguments
        if ($null -ne $candidate) {
            return $candidate
        }
    }

    return $null
}

Write-Host 'Setting up RICE development environment'

$basePython = Find-BasePython
if ($null -eq $basePython) {
# line-length: ignore-next-line -- legacy line pending wrap
    throw 'Error: Python 3.11 or newer with working venv support is required, but no suitable Windows interpreter was found.'
}

Write-Host 'Selected base Python:'
Write-Host ("  executable: {0}" -f $basePython.Executable)
Write-Host ("  version: {0}" -f $basePython.Version)

# line-length: ignore-next-line -- legacy line pending wrap
Invoke-CheckedCommand -FilePath $basePython.FilePath -Arguments ($basePython.Arguments + @('-m', 'venv', '.venv')) -Stage 'create virtual environment'

$venvPython = Get-VenvPythonPath
# line-length: ignore-next-line -- legacy line pending wrap
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m', 'pip', 'install', '--upgrade', 'pip', 'setuptools', 'wheel') -Stage 'upgrade packaging tools'
# line-length: ignore-next-line -- legacy line pending wrap
Invoke-CheckedCommand -FilePath $venvPython -Arguments @('-m', 'pip', 'install', '-e', '.[dev]') -Stage 'install editable project with dev dependencies'

Write-Host ''
Write-Host 'Virtual environment Python:'
# line-length: ignore-next-line -- legacy line pending wrap
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
