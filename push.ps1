# godding push helper - run from PowerShell or right-click "Run with PowerShell".
# No clever quoting that markdown might mangle.

$ErrorActionPreference = 'Continue'
Set-Location $PSScriptRoot

Write-Host "godding push helper" -ForegroundColor Cyan
Write-Host "directory: $PSScriptRoot"
Write-Host ""

# 1. clear any stale .git/index.lock
if (Test-Path '.git\index.lock') {
    Write-Host "removing stale .git\index.lock" -ForegroundColor Yellow
    try { Remove-Item -Force '.git\index.lock' } catch { }
}

# 2. restore any HTML file that does not end with </html> from HEAD
Write-Host "checking for truncated pages..." -ForegroundColor Yellow
$bad = @()
$targets = @()
$targets += Get-ChildItem 'pages' -Filter '*.html' -ErrorAction SilentlyContinue
$targets += Get-ChildItem 'index.html' -ErrorAction SilentlyContinue
foreach ($f in $targets) {
    $text = Get-Content $f.FullName -Raw -ErrorAction SilentlyContinue
    if ($text -and -not $text.TrimEnd().EndsWith('</html>')) {
        $bad += $f.FullName
    }
}
if ($bad.Count -gt 0) {
    Write-Host "restoring $($bad.Count) truncated files from git HEAD" -ForegroundColor Red
    foreach ($f in $bad) {
        $rel = Resolve-Path -Relative $f
        git checkout HEAD -- $rel 2>$null
    }
} else {
    Write-Host "no truncations found" -ForegroundColor Green
}

# 3. strip NUL bytes
Write-Host "stripping NUL bytes..." -ForegroundColor Yellow
$scan = @()
$scan += Get-ChildItem 'pages' -Filter '*.html' -ErrorAction SilentlyContinue
$scan += Get-ChildItem 'index.html' -ErrorAction SilentlyContinue
$scan += Get-ChildItem 'assets' -Filter '*.css' -ErrorAction SilentlyContinue
$scan += Get-ChildItem 'assets' -Filter '*.js' -ErrorAction SilentlyContinue
$scan += Get-ChildItem 'swarm' -Filter '*.py' -ErrorAction SilentlyContinue
foreach ($f in $scan) {
    $bytes = [System.IO.File]::ReadAllBytes($f.FullName)
    if ($bytes -contains 0) {
        $clean = $bytes | Where-Object { $_ -ne 0 }
        [System.IO.File]::WriteAllBytes($f.FullName, [byte[]]$clean)
        Write-Host "  cleaned $($f.Name)"
    }
}

# 4. consistency repair (also restores from HEAD as a second layer)
Write-Host "running swarm/repair.py..." -ForegroundColor Yellow
python "swarm\repair.py"

# 5. rebuild links.json so /graph stays current
Write-Host "rebuilding data/links.json..." -ForegroundColor Yellow
python "swarm\linker.py"

# 6. commit + push
Write-Host ""
Write-Host "committing..." -ForegroundColor Cyan
git add -A
$staged = git diff --cached --name-only
if (-not $staged) {
    Write-Host "nothing to commit." -ForegroundColor Green
} else {
    $stamp = Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ'
    git commit -m "godding: push from helper $stamp"
    Write-Host "pushing to origin/main..." -ForegroundColor Cyan
    git push origin HEAD:main
    Write-Host "DONE." -ForegroundColor Green
}

Write-Host ""
Write-Host "press Enter to close"
[void](Read-Host)
