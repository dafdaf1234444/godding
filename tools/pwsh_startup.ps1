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

function Quote-BashArg {
    param([AllowEmptyString()][string]$Text)

    $escapedQuote = "'" + '"' + "'" + '"' + "'"
    return "'" + ($Text -replace "'", $escapedQuote) + "'"
}

function Get-PwshGitRecoveryNotice {
    param(
        [string]$RepoRoot,
        [string[]]$SentinelPaths = @("SWARM.md", "AGENTS.md", "tools/orient.py")
    )

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        return @()
    }

    $gitDir = Join-Path $RepoRoot ".git"
    if (-not (Test-Path $gitDir)) {
        return @()
    }

    $problems = New-Object System.Collections.Generic.List[string]
    $existingSentinels = New-Object System.Collections.Generic.List[string]
    foreach ($sentinel in $SentinelPaths) {
        if (Test-Path (Join-Path $RepoRoot $sentinel)) {
            $existingSentinels.Add($sentinel)
        }
    }

    $indexPath = Join-Path $gitDir "index"
    if (-not (Test-Path $indexPath)) {
        $problems.Add(".git/index is missing")
    } else {
        $indexSize = (Get-Item $indexPath).Length
        if ($indexSize -lt 100) {
            $problems.Add(".git/index is suspiciously small (${indexSize}b)")
        }
    }

    $trackedSentinels = New-Object System.Collections.Generic.List[string]
    $trackedExit = 0
    $trackedArgs = @("-C", $RepoRoot, "ls-files", "--") + $SentinelPaths
    try {
        $trackedLines = @(& git @trackedArgs 2>&1)
        $trackedExit = $LASTEXITCODE
    } catch {
        $trackedLines = @($_.Exception.Message)
        $trackedExit = 1
    }

    if ($trackedExit -ne 0) {
        $problems.Add("PowerShell git ls-files failed")
    } else {
        foreach ($line in $trackedLines) {
            $path = "$line".Trim()
            if (($SentinelPaths -contains $path) -and (-not $trackedSentinels.Contains($path))) {
                $trackedSentinels.Add($path)
            }
        }
    }

    if ($existingSentinels.Count -gt 0 -and $trackedSentinels.Count -eq 0) {
        $problems.Add("PowerShell git tracks 0 sentinel files despite worktree sentinels existing")
    }

    $gitArgs = @("-C", $RepoRoot, "status", "--short", "--untracked-files=all", "--") + $SentinelPaths
    $windowsStatusLines = @()
    $windowsStatusExit = 0
    try {
        $windowsStatusLines = @(& git @gitArgs 2>&1)
        $windowsStatusExit = $LASTEXITCODE
    } catch {
        $windowsStatusLines = @($_.Exception.Message)
        $windowsStatusExit = 1
    }

    if ($windowsStatusExit -ne 0) {
        $problems.Add("PowerShell git status failed")
    }

    $windowsUntracked = New-Object System.Collections.Generic.List[string]
    $windowsDeleted = New-Object System.Collections.Generic.List[string]
    foreach ($line in $windowsStatusLines) {
        $text = "$line"
        if ($text.Length -ge 4) {
            $status = $text.Substring(0, 2)
            $path = $text.Substring(3).Trim()
            if (
                $status.Contains("D") -and
                ($SentinelPaths -contains $path) -and
                ($existingSentinels.Contains($path)) -and
                (-not $windowsDeleted.Contains($path))
            ) {
                $windowsDeleted.Add($path)
            }
        }
        if ($text -match '^\?\?\s+(.+)$') {
            $path = $Matches[1].Trim()
            if (($SentinelPaths -contains $path) -and (-not $windowsUntracked.Contains($path))) {
                $windowsUntracked.Add($path)
            }
        }
    }

    if ($windowsDeleted.Count -gt 0) {
        $problems.Add("PowerShell git reports tracked sentinels as deleted while files exist on disk: $($windowsDeleted -join ', ')")
    }

    $bashCmd = Get-Command bash -ErrorAction SilentlyContinue
    if ($windowsUntracked.Count -gt 0) {
        if ($bashCmd) {
            $bashRoot = Convert-ToBashPath $RepoRoot
            $bashSentinels = ($SentinelPaths | ForEach-Object { Quote-BashArg ($_ -replace "\\", "/") }) -join " "
            $bashCommand = "cd $(Quote-BashArg $bashRoot) && git status --short --untracked-files=all -- $bashSentinels"
            $bashStatusLines = @(& bash -lc $bashCommand 2>&1)
            if ($LASTEXITCODE -eq 0) {
                $bashUntracked = New-Object System.Collections.Generic.List[string]
                foreach ($line in $bashStatusLines) {
                    $text = "$line"
                    if ($text -match '^\?\?\s+(.+)$') {
                        $path = $Matches[1].Trim()
                        if (($SentinelPaths -contains $path) -and (-not $bashUntracked.Contains($path))) {
                            $bashUntracked.Add($path)
                        }
                    }
                }

                $windowsOnly = @($windowsUntracked | Where-Object { -not $bashUntracked.Contains($_) })
                if ($windowsOnly.Count -gt 0) {
                    $problems.Add("PowerShell git reports tracked sentinels as untracked: $($windowsOnly -join ', ')")
                }
            }
        } else {
            $problems.Add("PowerShell git reports tracked sentinels as untracked: $($windowsUntracked -join ', ')")
        }
    }

    if ($problems.Count -eq 0) {
        return @()
    }

    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("[NOTICE] PowerShell git/index state looks inconsistent.")
    foreach ($problem in ($problems | Sort-Object -Unique)) {
        $lines.Add("  - $problem")
    }
    $lines.Add("  - Wrapper will continue with the repo's preferred runtime path so startup can proceed.")

    if ($bashCmd) {
        $bashRoot = Convert-ToBashPath $RepoRoot
        $repairBody = "cd $(Quote-BashArg $bashRoot) && rm -f .git/index .git/index.lock && git read-tree HEAD && git update-index --refresh"
        $lines.Add('  - Recovery: bash -lc "' + $repairBody + '"')
    } else {
        $lines.Add("  - Recovery: remove .git/index/.git/index.lock, then run git read-tree HEAD and git update-index --refresh.")
    }

    $lines.Add("  - Note: this preserves worktree files but rebuilds the index from HEAD; re-stage intentional changes afterward.")
    return $lines
}

function Show-PwshGitRecoveryNotice {
    param([string]$RepoRoot)

    foreach ($line in Get-PwshGitRecoveryNotice -RepoRoot $RepoRoot) {
        Write-Host $line
    }
}

function Invoke-NativeCapturePassthrough {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [string[]]$CommandArgs = @()
    )

    $output = @(& $FilePath @CommandArgs 2>&1)
    $exitCode = $LASTEXITCODE
    foreach ($line in $output) {
        $text = if ($line -is [System.Management.Automation.ErrorRecord]) {
            $line.ToString()
        } else {
            "$line"
        }
        [Console]::Out.WriteLine($text)
    }

    return [pscustomobject]@{
        ExitCode = if ($null -eq $exitCode) { 0 } else { [int]$exitCode }
        Output = ($output | Out-String)
    }
}

function Invoke-BashPythonTool {
    param(
        [string]$RepoRoot,
        [string]$ToolPath,
        [string[]]$ToolArgs
    )

    $bashRoot = Convert-ToBashPath $RepoRoot
    $commandParts = @(
        "cd $(Quote-BashArg $bashRoot)",
        "&&",
        "python3",
        (Quote-BashArg ($ToolPath -replace "\\", "/"))
    )

    foreach ($arg in @($ToolArgs)) {
        if ($null -eq $arg -or $arg -eq "") {
            continue
        }
        $commandParts += Quote-BashArg $arg
    }

    $result = Invoke-NativeCapturePassthrough -FilePath "bash" -CommandArgs @("-lc", ($commandParts -join " "))
    return $result.ExitCode
}
