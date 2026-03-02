<#
.SYNOPSIS
  Emit README snapshot numbers without Python.
#>
[CmdletBinding()]
param(
  [string]$Session,
  [switch]$SkipLines,
  [switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$invariant = [System.Globalization.CultureInfo]::InvariantCulture

function Format-Int {
  param([long]$Value)
  return $Value.ToString("N0", $invariant)
}

function Format-Decimal {
  param([double]$Value, [int]$Places = 1)
  $format = "N$Places"
  return $Value.ToString($format, $invariant)
}

function Resolve-RepoRoot {
  $root = Resolve-Path (Join-Path $PSScriptRoot "..")
  return $root.Path
}

$repoRoot = Resolve-RepoRoot

function Invoke-Git {
  param([Parameter(Mandatory = $true)][string[]]$Args)
  & git -C $repoRoot @Args
}

function Get-SessionNumber {
  $sessionLog = Join-Path $repoRoot "memory" "SESSION-LOG.md"
  $logNums = @()
  if (Test-Path -LiteralPath $sessionLog) {
    foreach ($line in Get-Content -Path $sessionLog) {
      if ($line -match '^S(\d+)') {
        $logNums += [int]$matches[1]
      }
    }
  }
  $logMax = if ($logNums.Count -gt 0) { ($logNums | Measure-Object -Maximum).Maximum } else { 0 }
  $gitNums = @()
  foreach ($line in Invoke-Git -Args @("log", "--oneline", "-50")) {
    if ($line -match '\[S(\d+)\]') {
      $gitNums += [int]$matches[1]
    }
  }
  $gitMax = if ($gitNums.Count -gt 0) { ($gitNums | Measure-Object -Maximum).Maximum } else { 0 }
  return [Math]::Max($logMax, $gitMax)
}

function Get-IndexCounts {
  $indexPath = Join-Path $repoRoot "memory" "INDEX.md"
  $counts = [ordered]@{ lessons = 0; principles = 0; beliefs = 0; frontiers = 0 }
  if (Test-Path -LiteralPath $indexPath) {
    $text = Get-Content -Path $indexPath -Raw
    $m = [regex]::Match($text, '\*\*(\d+)\s+lessons\*\*')
    if ($m.Success) { $counts.lessons = [int]$m.Groups[1].Value }
    $m = [regex]::Match($text, '\*\*(\d+)\s+principles\*\*')
    if ($m.Success) { $counts.principles = [int]$m.Groups[1].Value }
    $m = [regex]::Match($text, '\*\*(\d+)\s+beliefs\*\*')
    if ($m.Success) { $counts.beliefs = [int]$m.Groups[1].Value }
    $m = [regex]::Match($text, '\*\*(\d+)\s+frontier questions\*\*')
    if ($m.Success) { $counts.frontiers = [int]$m.Groups[1].Value }
  }
  return $counts
}

function Get-LineCount {
  param([byte[]]$Bytes)
  if (-not $Bytes) { return 0 }
  $count = 0
  foreach ($b in $Bytes) {
    if ($b -eq 10) { $count++ }
  }
  if ($Bytes.Length -gt 0 -and $Bytes[$Bytes.Length - 1] -ne 10) {
    $count++
  }
  return $count
}

$session = if ($Session) { $Session.Trim() } else { (Get-SessionNumber).ToString() }
if ($session -match '^S(\d+)$') { $session = $matches[1] }
$date = Get-Date -Format "yyyy-MM-dd"
$indexCounts = Get-IndexCounts

$paths = @(Invoke-Git -Args @("ls-files") | Where-Object { $_ -ne "" })
if (-not $paths -or $paths.Count -eq 0) {
  throw "git ls-files returned no files."
}

$trackedFiles = $paths.Count
$trackedBytes = 0
$totalLines = 0
$md = 0
$py = 0
$jsonCount = 0
$sh = 0
$exp = 0
$mem = 0
$tools = 0
$domains = 0

foreach ($path in $paths) {
  $normalized = $path -replace "\\", "/"
  if ($normalized.StartsWith("experiments/")) { $exp++ }
  elseif ($normalized.StartsWith("memory/")) { $mem++ }
  elseif ($normalized.StartsWith("tools/")) { $tools++ }
  elseif ($normalized.StartsWith("domains/")) { $domains++ }

  if ($normalized -match '\.md$') { $md++ }
  elseif ($normalized -match '\.py$') { $py++ }
  elseif ($normalized -match '\.json$') { $jsonCount++ }
  elseif ($normalized -match '\.sh$') { $sh++ }

  $fullPath = [System.IO.Path]::Combine($repoRoot, $path)
  if (-not (Test-Path -LiteralPath $fullPath)) { continue }

  try {
    $info = Get-Item -LiteralPath $fullPath -ErrorAction Stop
    $trackedBytes += $info.Length
    if (-not $SkipLines) {
      $bytes = [System.IO.File]::ReadAllBytes($fullPath)
      $totalLines += (Get-LineCount -Bytes $bytes)
    }
  } catch {
    continue
  }
}

$commitCountRaw = Invoke-Git -Args @("rev-list", "--count", "HEAD")
$commitCount = if ($commitCountRaw) { [int]$commitCountRaw } else { 0 }

$size = 0.0
$sizePack = 0.0
foreach ($line in Invoke-Git -Args @("count-objects", "-v")) {
  if ($line -match '^size:\s+(\d+)') { $size = [double]$matches[1] }
  elseif ($line -match '^size-pack:\s+(\d+)') { $sizePack = [double]$matches[1] }
}

$trackedMiB = $trackedBytes / 1MB
$objectTotalMiB = ($size + $sizePack) / 1024
$objectLooseMiB = $size / 1024

if ($Json) {
  $payload = [ordered]@{
    date = $date
    session = $session
    lessons = $indexCounts.lessons
    principles = $indexCounts.principles
    beliefs = $indexCounts.beliefs
    frontiers = $indexCounts.frontiers
    tracked = [ordered]@{
      files = $trackedFiles
      lines = $totalLines
      bytes = $trackedBytes
      mib = [Math]::Round($trackedMiB, 2)
      commits = $commitCount
    }
    file_mix = [ordered]@{ md = $md; py = $py; json = $jsonCount; sh = $sh }
    top_dirs = [ordered]@{ experiments = $exp; memory = $mem; tools = $tools; domains = $domains }
    git_objects = [ordered]@{
      total_mib = [Math]::Round($objectTotalMiB, 2)
      loose_mib = [Math]::Round($objectLooseMiB, 2)
      size_kib = [int]$size
      size_pack_kib = [int]$sizePack
    }
  }
  $payload | ConvertTo-Json -Depth 4
  exit 0
}

$filesDisplay = Format-Int $trackedFiles
$linesDisplay = if ($SkipLines) { "n/a" } else { Format-Int $totalLines }
$trackedMiBDisplay = Format-Decimal $trackedMiB 1
$commitsDisplay = Format-Int $commitCount
$objectTotalDisplay = Format-Decimal $objectTotalMiB 1
$objectLooseDisplay = Format-Decimal $objectLooseMiB 1

Write-Output "## Current State Snapshot ($date, S$session)"
Write-Output ""
Write-Output ("- Swarm scale: {0} lessons, {1} principles, {2} beliefs, {3} active frontier questions." -f `
  (Format-Int $indexCounts.lessons), (Format-Int $indexCounts.principles), (Format-Int $indexCounts.beliefs), (Format-Int $indexCounts.frontiers))
if ($SkipLines) {
  Write-Output "- Project footprint (tracked): $filesDisplay files, lines: n/a, ~$trackedMiBDisplay MiB tracked content, $commitsDisplay commits."
} else {
  Write-Output "- Project footprint (tracked): $filesDisplay files, ~$linesDisplay estimated lines, ~$trackedMiBDisplay MiB tracked content, $commitsDisplay commits."
}
Write-Output ("- File mix (tracked): {0} Markdown, {1} Python, {2} JSON, {3} shell scripts." -f `
  (Format-Int $md), (Format-Int $py), (Format-Int $jsonCount), (Format-Int $sh))
Write-Output ('- Largest tracked areas by file count: `experiments/` {0}, `memory/` {1}, `tools/` {2}, `domains/` {3}.' -f `
  (Format-Int $exp), (Format-Int $mem), (Format-Int $tools), (Format-Int $domains))
Write-Output ('- Git object store: ~{0} MiB total (packed + loose objects). Run `git gc` - loose objects currently ~{1} MiB.' -f `
  $objectTotalDisplay, $objectLooseDisplay)
