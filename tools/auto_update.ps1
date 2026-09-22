# Refresh the data and publish, unattended.
#
#   powershell -ExecutionPolicy Bypass -File tools\auto_update.ps1
#
# Install it as a weekly task (run this once, from an elevated PowerShell):
#
#   powershell -ExecutionPolicy Bypass -File tools\auto_update.ps1 -Install
#
# This runs locally rather than in GitHub Actions for two reasons. Actions is
# blocked on this account ("the job was not started because your account is
# locked due to a billing issue"), and even unblocked it would be the wrong
# place: the Sofascore extractor impersonates a browser, which works from a home
# connection and is routinely refused from a datacentre IP. The published
# pages.yml stays in place for the day that changes.
#
# Every step is gated. A failed test, a failed quality check or a broken link
# stops the run before anything is pushed — an unattended job that publishes bad
# data is worse than one that does nothing.

param(
    [switch]$Install,
    [string]$At = "07:00",
    [string]$Day = "Monday"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
$log = Join-Path $root "auto_update.log"

function Write-Log($message) {
    $line = "{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $message
    Write-Output $line
    Add-Content -Path $log -Value $line
}

if ($Install) {
    $action = New-ScheduledTaskAction -Execute "powershell.exe" `
        -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$PSCommandPath`"" `
        -WorkingDirectory $root
    $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $Day -At $At
    # skip a run rather than queue it if the machine was asleep, and give up
    # after two hours rather than leaving a wedged job holding the repo
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
        -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 2)
    Register-ScheduledTask -TaskName "Etalons Analytics refresh" -Action $action `
        -Trigger $trigger -Settings $settings -Description `
        "Refresh Etalons Analytics data and publish the site." -Force | Out-Null
    Write-Host "Installed: runs every $Day at $At."
    Write-Host "Check it with:  Get-ScheduledTask -TaskName 'Etalons Analytics refresh'"
    Write-Host "Run it now with: Start-ScheduledTask -TaskName 'Etalons Analytics refresh'"
    exit 0
}

Set-Location $root
Write-Log "=== refresh started ==="

try {
    # A played match never changes, so this pulls only what is new: results,
    # fixtures, squad lists, and any profile older than 30 days.
    & $python -m etl all
    if ($LASTEXITCODE -ne 0) { throw "etl all failed ($LASTEXITCODE)" }

    & $python tools/build_site.py
    if ($LASTEXITCODE -ne 0) { throw "build_site failed" }

    foreach ($check in @("-m pytest -q", "tools/check_links.py", "tools/check_seo.py")) {
        & $python $check.Split(" ")
        if ($LASTEXITCODE -ne 0) { throw "gate failed: $check" }
    }

    $changed = (git status --porcelain).Trim()
    if (-not $changed) {
        Write-Log "nothing changed; nothing published"
        exit 0
    }

    git add -A
    git commit -m ("Refresh data ({0})" -f (Get-Date -Format "yyyy-MM-dd")) | Out-Null
    git push origin main
    if ($LASTEXITCODE -ne 0) { throw "push to main failed" }
    git subtree push --prefix site origin gh-pages
    if ($LASTEXITCODE -ne 0) { throw "publish to gh-pages failed" }

    Write-Log "published"
}
catch {
    Write-Log ("FAILED: {0}" -f $_.Exception.Message)
    Write-Log "nothing was published"
    exit 1
}
