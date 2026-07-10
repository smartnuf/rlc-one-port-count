Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\_common.ps1"

Assert-RiceRepoRoot -ScriptName 'clean.ps1'

$script:RemovedAny = $false

function Remove-GeneratedPath {
    param(
        [Parameter(Mandatory = $true)]
        [string] $RelativePath
    )

    $fullPath = Resolve-PathUnderRepo -RelativePath $RelativePath
    if (Test-Path -LiteralPath $fullPath) {
        Write-Host ("Removing {0}" -f $RelativePath)
        Remove-Item -LiteralPath $fullPath -Recurse -Force
        $script:RemovedAny = $true
    }
}

function Remove-GeneratedFullPath {
    param(
        [Parameter(Mandatory = $true)]
        [string] $FullPath
    )

    $repoRoot = Get-RepoRootPath
    $resolved = [System.IO.Path]::GetFullPath($FullPath)
    $relative = $resolved.Substring($repoRoot.Length).TrimStart('\', '/')
    $null = Resolve-PathUnderRepo -RelativePath $relative

    if (Test-Path -LiteralPath $resolved) {
        Write-Host ("Removing {0}" -f $relative)
        Remove-Item -LiteralPath $resolved -Recurse -Force
        $script:RemovedAny = $true
    }
}

function Remove-PycacheDirectories {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Directory
    )

    foreach ($child in Get-ChildItem -LiteralPath $Directory -Force -Directory) {
        if ($child.Name -eq '.git' -or $child.Name -eq '.venv') {
            continue
        }

        if ($child.Name -eq '__pycache__') {
            Remove-GeneratedFullPath -FullPath $child.FullName
            continue
        }

        Remove-PycacheDirectories -Directory $child.FullName
    }
}

Remove-GeneratedPath -RelativePath '.venv'
Remove-GeneratedPath -RelativePath '.pytest_cache'
Remove-GeneratedPath -RelativePath 'build'
Remove-GeneratedPath -RelativePath 'dist'

$repoRoot = Get-RepoRootPath
foreach ($eggInfo in @(Get-ChildItem -LiteralPath $repoRoot -Force -Filter '*.egg-info' -ErrorAction SilentlyContinue)) {
    Remove-GeneratedFullPath -FullPath $eggInfo.FullName
}

$srcDir = Resolve-PathUnderRepo -RelativePath 'src'
if (Test-Path -LiteralPath $srcDir -PathType Container) {
    foreach ($eggInfo in @(Get-ChildItem -LiteralPath $srcDir -Force -Filter '*.egg-info' -ErrorAction SilentlyContinue)) {
        Remove-GeneratedFullPath -FullPath $eggInfo.FullName
    }
}

Remove-PycacheDirectories -Directory $repoRoot

if (-not $script:RemovedAny) {
    Write-Host 'Development artefacts already clean.'
}
