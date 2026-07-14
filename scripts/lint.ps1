Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\_common.ps1"

Assert-RiceRepoRoot -ScriptName 'lint.ps1'
$venvPython = Require-VenvPython

Invoke-CheckedCommand -FilePath 'git' -Arguments @(
    'diff',
    '--check'
) -Stage 'git diff --check'
Invoke-CheckedCommand -FilePath $venvPython -Arguments @(
    'scripts/check_line_lengths.py'
) -Stage 'line-length check'

Write-Host ''
Write-Host '==> syntax compile tracked Python files under src/ and tests/'
$pythonFiles = @(git ls-files 'src/*.py' 'tests/*.py')
if ($LASTEXITCODE -ne 0) {
    throw 'Stage failed: list tracked Python files'
}

if ($pythonFiles.Count -eq 0) {
    Write-Host 'No tracked Python files found under src/ or tests/.'
} else {
    $compileScript = @'
import pathlib
import sys

failed = False
for raw_path in sys.argv[1:]:
    path = pathlib.Path(raw_path)
    try:
        source = path.read_text(encoding="utf-8")
        compile(source, raw_path, "exec")
    except SyntaxError as exc:
        failed = True
        location = f"{raw_path}:{exc.lineno}:{exc.offset or 0}"
        print(f"Syntax error in {location}: {exc.msg}", file=sys.stderr)
    except OSError as exc:
        failed = True
        print(f"Could not read {raw_path}: {exc}", file=sys.stderr)

if failed:
    raise SystemExit(1)

print(f"Compiled {len(sys.argv) - 1} Python files without writing bytecode.")
'@

    & $venvPython -c $compileScript @pythonFiles
    if ($LASTEXITCODE -ne 0) {
        throw 'Stage failed: Python syntax compile'
    }
}
