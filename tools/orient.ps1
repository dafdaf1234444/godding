#!/usr/bin/env pwsh
# Portable orient wrapper for PowerShell hosts.

[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$orientPy = Join-Path $PSScriptRoot "orient.py"

function Convert-ToBashPath {
    param([string]$PathText)
    $p = ($PathText -replace "\\", "/")
    if ($p -match "^[A-Za-z]:") {
        $drive = $p.Substring(0, 1).ToLower()
        $rest = $p.Substring(2)
        return "/mnt/$drive$rest"
    }
    return $p
}

if (Get-Command bash -ErrorAction SilentlyContinue) {
    $bashRoot = Convert-ToBashPath $repoRoot
    $argCount = if ($null -eq $Args) { 0 } else { @($Args).Count }
    $argText = if ($argCount -gt 0) { " " + (@($Args) -join " ") } else { "" }
    & bash -lc "cd '$bashRoot' && python3 tools/orient.py$argText"
    exit $LASTEXITCODE
}

$pythonCmd = $null
$pythonArgs = @()

if (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py"
    $pythonArgs = @("-3")
}

if (-not $pythonCmd) {
    Write-Error "FAIL: No runnable runtime found (bash/python3/python/py -3)."
    exit 1
}

Push-Location $repoRoot
try {
    & $pythonCmd @pythonArgs $orientPy @Args
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
