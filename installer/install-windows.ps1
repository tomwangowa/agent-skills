# Run normally; execution policy and organization restrictions are not bypassed.
$ErrorActionPreference = 'Stop'
$base = $PSScriptRoot
if (-not (Get-Command claude -ErrorAction SilentlyContinue) -and -not (Get-Command codex -ErrorAction SilentlyContinue)) {
    Write-Output 'Install Claude Code or Codex CLI and configure model access, then rerun. Neither host is installed automatically.'
    exit 1
}
function Find-RealPython {
    # Do not execute python/py aliases: the Python manager can download runtimes.
    $registryRoots = @('HKCU:\Software\Python\PythonCore\*\InstallPath', 'HKLM:\Software\Python\PythonCore\*\InstallPath', 'HKLM:\Software\WOW6432Node\Python\PythonCore\*\InstallPath')
    foreach ($registryRoot in $registryRoots) {
        $items = Get-ItemProperty -Path $registryRoot -ErrorAction SilentlyContinue
        foreach ($item in $items) {
            $candidate = $item.ExecutablePath
            if (-not $candidate -and $item.'(default)') { $candidate = Join-Path $item.'(default)' 'python.exe' }
            if (-not $candidate -or $candidate -match '(?i)WindowsApps|PythonManager' -or -not (Test-Path -LiteralPath $candidate -PathType Leaf)) { continue }
            $file = Get-Item -LiteralPath $candidate
            if ($file.Name -ne 'python.exe' -or ($file.Attributes -band [IO.FileAttributes]::ReparsePoint)) { continue }
            & $candidate -I -c 'import sys; raise SystemExit(sys.version_info < (3, 11))' *> $null
            if ($LASTEXITCODE -eq 0) { return $candidate }
        }
    }
    return $null
}
$python = Find-RealPython
if (-not $python) {
    Write-Output 'Python 3.11+ is required. Only registered real interpreters are probed; python/py download aliases are not executed.'
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Output 'Install Python 3.11+ manually. WinGet is not installed automatically.'
        exit 1
    }
    Write-Output 'Proposed: winget install --exact --id @@PYTHON_PACKAGE@@ --source winget'
    Write-Output 'Source: existing WinGet community source. Downloads, transitive dependencies, system/PATH changes and administrator approval may occur.'
    $answer = Read-Host 'Install Python with the existing manager? [y/N]'
    if ($answer -notmatch '^[yY]$') { Write-Output 'Declined. Install Python manually, then rerun.'; exit 130 }
    $env:AGENT_SKILLS_BOOTSTRAP_RESULT = 'Python installation was attempted; earlier system writes may remain.'
    & winget install --exact --id '@@PYTHON_PACKAGE@@' --source winget
    if ($LASTEXITCODE -eq 130) { Write-Output 'Cancelled during Python installation; earlier writes may remain.'; exit 130 }
    if ($LASTEXITCODE -ne 0) { Write-Output 'Python installation failed. Earlier writes may remain; no retry or rollback.'; exit 1 }
    $python = Find-RealPython
    if (-not $python) { Write-Output 'No usable registered interpreter found after installation. Check PATH/registration and rerun; prior writes remain.'; exit 1 }
}
& $python -I (Join-Path $base 'install.py') @args
exit $LASTEXITCODE
