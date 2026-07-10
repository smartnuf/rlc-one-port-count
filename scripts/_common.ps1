Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-RepoRootError {
    param(
        [Parameter(Mandatory = $true)]
        [string] $ScriptName
    )

    [Console]::Error.WriteLine("Error: this script must be run from the RICE repository root.")
    [Console]::Error.WriteLine("Expected invocation: .\scripts\$ScriptName")
}

function Get-ProjectName {
    param(
        [Parameter(Mandatory = $true)]
        [string] $PyprojectPath
    )

    $inProject = $false
    foreach ($line in [System.IO.File]::ReadLines($PyprojectPath)) {
        $trimmed = $line.Trim()
        if ($trimmed -eq '[project]') {
            $inProject = $true
            continue
        }
        if ($trimmed.StartsWith('[')) {
            $inProject = $false
        }
        if ($inProject -and $trimmed -match '^name\s*=\s*["'']([^"'']+)["'']\s*$') {
            return $Matches[1]
        }
    }

    return $null
}

function Assert-RiceRepoRoot {
    param(
        [Parameter(Mandatory = $true)]
        [string] $ScriptName
    )

    $pyproject = Join-Path (Get-Location) 'pyproject.toml'
    $readme = Join-Path (Get-Location) 'README.md'
    $packageDir = Join-Path (Get-Location) 'src\rice'

    if (-not (Test-Path -LiteralPath $pyproject -PathType Leaf) -or
        -not (Test-Path -LiteralPath $readme -PathType Leaf) -or
        -not (Test-Path -LiteralPath $packageDir -PathType Container)) {
        Write-RepoRootError -ScriptName $ScriptName
        exit 1
    }

    $projectName = Get-ProjectName -PyprojectPath $pyproject
    if ($projectName -ne 'rice') {
        Write-RepoRootError -ScriptName $ScriptName
        exit 1
    }
}

function Get-VenvPythonPath {
    return (Join-Path (Get-Location) '.venv\Scripts\python.exe')
}

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string] $FilePath,

        [string[]] $Arguments = @(),

        [string] $Stage = ''
    )

    Write-Host ''
    if ($Arguments.Count -gt 0) {
        Write-Host ("==> {0} {1}" -f $FilePath, ($Arguments -join ' '))
    } else {
        Write-Host ("==> {0}" -f $FilePath)
    }

    & $FilePath @Arguments
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        if ([string]::IsNullOrWhiteSpace($Stage)) {
            throw "Command failed with exit code ${exitCode}: $FilePath"
        }
        throw "Stage failed with exit code ${exitCode}: $Stage"
    }
}

function Require-VenvPython {
    param(
        [string] $SetupHint = '.\scripts\setup.ps1'
    )

    $venvPython = Get-VenvPythonPath
    if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
        throw "Error: missing or unusable .venv\Scripts\python.exe. Run $SetupHint first."
    }

    $pythonInfo = & $venvPython -c 'import sys; print("Using Python:", sys.executable); print("Python version:", sys.version.split()[0])'
    if ($LASTEXITCODE -ne 0) {
        throw "Error: .venv\Scripts\python.exe exists but could not run. Run $SetupHint to recreate it."
    }
    foreach ($line in $pythonInfo) {
        Write-Host $line
    }

    return $venvPython
}

function Get-RepoRootPath {
    return ([System.IO.Path]::GetFullPath((Get-Location).Path).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar))
}

function Resolve-PathUnderRepo {
    param(
        [Parameter(Mandatory = $true)]
        [string] $RelativePath
    )

    if ([System.IO.Path]::IsPathRooted($RelativePath)) {
        throw "Refusing absolute cleanup path: $RelativePath"
    }

    $repoRoot = Get-RepoRootPath
    $fullPath = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $RelativePath))
    $repoPrefix = $repoRoot + [System.IO.Path]::DirectorySeparatorChar

    if ($fullPath -ne $repoRoot -and -not $fullPath.StartsWith($repoPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing path outside repository: $RelativePath"
    }

    return $fullPath
}
