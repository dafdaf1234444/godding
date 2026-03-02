#!/usr/bin/env pwsh
# Portable swarm check wrapper for PowerShell hosts.

[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$checkSh = Join-Path $PSScriptRoot "check.sh"
$validatePy = Join-Path $PSScriptRoot "validate_beliefs.py"
$maintenancePy = Join-Path $PSScriptRoot "maintenance.py"

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
    $bashScript = Convert-ToBashPath $checkSh
    & bash $bashScript @Args
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

$quick = $Args -contains "--quick"
$pyArgs = @()
if ($quick) {
    $pyArgs += "--quick"
}

Push-Location $repoRoot
try {
    & $pythonCmd @pythonArgs $validatePy @pyArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Error "FAIL: Belief validation failed."
        exit $LASTEXITCODE
    }

    & $pythonCmd @pythonArgs $maintenancePy @pyArgs
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
