# Upwork OS — Windows Task Scheduler Setup
# Registers all Tier 3 daemon tasks for always-on autonomous operation.
# Run ONCE as Administrator. Re-run at any time to update trigger intervals.
#
# Tasks registered:
#   UpworkOS_EmailWatcher   — every 30 minutes (detect job alerts + client replies)
#   UpworkOS_ProcessApprovals — every 15 minutes (check Telegram for button taps)
#   UpworkOS_FollowUp       — every 6 hours (scan proposals, send follow-up requests)
#   UpworkOS_Heartbeat      — on login + daily 8AM (surface top priority action)
#
# Usage:
#   1. Open PowerShell as Administrator
#   2. cd "c:\Users\HomePC\Documents\Upwork OS"
#   3. .\scripts\setup_scheduler.ps1
#
# To remove all tasks:
#   .\scripts\setup_scheduler.ps1 -Uninstall
#
# To check task status:
#   Get-ScheduledTask -TaskPath "\UpworkOS\" | Select-Object TaskName, State

param(
    [switch]$Uninstall
)

# ─── Config ──────────────────────────────────────────────────────────────────

$OS_ROOT   = "c:\Users\HomePC\Documents\Upwork OS"
$PYTHON    = (Get-Command python -ErrorAction SilentlyContinue).Source
$LOG_DIR   = "$OS_ROOT\logs"
$TASK_PATH = "\UpworkOS\"

if (-not $PYTHON) {
    Write-Error "Python not found in PATH. Install Python and add it to PATH first."
    exit 1
}

# Ensure log directory exists
if (-not (Test-Path $LOG_DIR)) {
    New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null
}

# ─── Uninstall mode ───────────────────────────────────────────────────────────

if ($Uninstall) {
    Write-Host "Removing all UpworkOS scheduled tasks..." -ForegroundColor Yellow
    $tasks = @(
        "UpworkOS_EmailWatcher",
        "UpworkOS_ProcessApprovals",
        "UpworkOS_ProcessFollowUpApprovals",
        "UpworkOS_FollowUp",
        "UpworkOS_Heartbeat",
        "UpworkOS_OutreachAuto",
        "UpworkOS_OutreachFollowUp"
    )
    foreach ($task in $tasks) {
        if (Get-ScheduledTask -TaskName $task -TaskPath $TASK_PATH -ErrorAction SilentlyContinue) {
            Unregister-ScheduledTask -TaskName $task -TaskPath $TASK_PATH -Confirm:$false
            Write-Host "  Removed: $task" -ForegroundColor Green
        } else {
            Write-Host "  Not found: $task" -ForegroundColor Gray
        }
    }
    Write-Host "Done." -ForegroundColor Green
    exit 0
}

# ─── Helper: register a task ──────────────────────────────────────────────────

function Register-OSTask {
    param(
        [string]$TaskName,
        [string]$Script,
        [string]$Args,
        [object]$Trigger,
        [string]$Description
    )

    $LogFile = "$LOG_DIR\$($TaskName.Replace('UpworkOS_','').ToLower()).log"

    # Build command that logs stdout+stderr to file
    $Command = $PYTHON
    $Arguments = "`"$OS_ROOT\scripts\$Script`" $Args >> `"$LogFile`" 2>&1"
    $FullAction = "/c `"$Command $Arguments`""

    $Action = New-ScheduledTaskAction `
        -Execute "cmd.exe" `
        -Argument $FullAction `
        -WorkingDirectory $OS_ROOT

    $Settings = New-ScheduledTaskSettingsSet `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
        -MultipleInstances IgnoreNew `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable

    # Remove existing task if present
    if (Get-ScheduledTask -TaskName $TaskName -TaskPath $TASK_PATH -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -TaskPath $TASK_PATH -Confirm:$false
    }

    Register-ScheduledTask `
        -TaskName    $TaskName `
        -TaskPath    $TASK_PATH `
        -Action      $Action `
        -Trigger     $Trigger `
        -Settings    $Settings `
        -Description $Description `
        -RunLevel    Limited `
        -Force | Out-Null

    Write-Host "  Registered: $TaskName" -ForegroundColor Green
}

# ─── Task definitions ─────────────────────────────────────────────────────────

Write-Host ""
Write-Host "Upwork OS — Task Scheduler Setup" -ForegroundColor Cyan
Write-Host "Python: $PYTHON" -ForegroundColor Gray
Write-Host "OS root: $OS_ROOT" -ForegroundColor Gray
Write-Host ""
Write-Host "Registering tasks..." -ForegroundColor White

# 1. Email Watcher — every 30 minutes
$TriggerEmail = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 30) -Once -At (Get-Date)
Register-OSTask `
    -TaskName    "UpworkOS_EmailWatcher" `
    -Script      "email_watcher.py" `
    -Args        "--since 1h" `
    -Trigger     $TriggerEmail `
    -Description "Scans Gmail for Upwork job alerts and client replies every 30 minutes"

# 2. Process Approvals — every 15 minutes
# Checks Telegram for button taps (job bid approvals + follow-up approvals)
$TriggerApprovals = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 15) -Once -At (Get-Date)
Register-OSTask `
    -TaskName    "UpworkOS_ProcessApprovals" `
    -Script      "job_watcher.py" `
    -Args        "--process-approvals" `
    -Trigger     $TriggerApprovals `
    -Description "Polls Telegram for approved/rejected job bids every 15 minutes"

# We need a second action for follow-up approvals in the same 15-minute tick
# Since Register-OSTask only handles one script, we register a separate task
$TriggerFollowUpApprovals = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 15) -Once -At ((Get-Date).AddSeconds(30))
Register-OSTask `
    -TaskName    "UpworkOS_ProcessFollowUpApprovals" `
    -Script      "follow_up.py" `
    -Args        "--process-approvals" `
    -Trigger     $TriggerFollowUpApprovals `
    -Description "Polls Telegram for approved follow-up messages every 15 minutes"

# 3. Follow-up Engine — every 6 hours
$TriggerFollowUp = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Hours 6) -Once -At (Get-Date)
Register-OSTask `
    -TaskName    "UpworkOS_FollowUp" `
    -Script      "follow_up.py" `
    -Args        "" `
    -Trigger     $TriggerFollowUp `
    -Description "Scans proposals for 72h no-reply and sends follow-up approval requests"

# 4. Heartbeat — on login AND daily at 8:00 AM WAT (= 7:00 AM UTC)
$TriggerHeartbeatLogon = New-ScheduledTaskTrigger -AtLogOn
$TriggerHeartbeatDaily = New-ScheduledTaskTrigger -Daily -At "07:00AM"

# Register logon trigger
$LogFile = "$LOG_DIR\heartbeat.log"
$HeartbeatAction = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$PYTHON `"$OS_ROOT\scripts\heartbeat.py`" >> `"$LogFile`" 2>&1`"" `
    -WorkingDirectory $OS_ROOT

$HeartbeatSettings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5) `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable

if (Get-ScheduledTask -TaskName "UpworkOS_Heartbeat" -TaskPath $TASK_PATH -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName "UpworkOS_Heartbeat" -TaskPath $TASK_PATH -Confirm:$false
}

Register-ScheduledTask `
    -TaskName    "UpworkOS_Heartbeat" `
    -TaskPath    $TASK_PATH `
    -Action      $HeartbeatAction `
    -Trigger     @($TriggerHeartbeatLogon, $TriggerHeartbeatDaily) `
    -Settings    $HeartbeatSettings `
    -Description "Runs heartbeat.py on login and daily at 8AM WAT to surface top priority action" `
    -RunLevel    Limited `
    -Force | Out-Null

Write-Host "  Registered: UpworkOS_Heartbeat (logon + daily 8AM WAT)" -ForegroundColor Green

# 5. Outreach Auto — every 6 hours (auto-send to all 'prospect' nodes)
$TriggerOutreachAuto = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Hours 6) -Once -At ((Get-Date).AddMinutes(5))
Register-OSTask `
    -TaskName    "UpworkOS_OutreachAuto" `
    -Script      "outreach.py" `
    -Args        "--auto" `
    -Trigger     $TriggerOutreachAuto `
    -Description "Auto-sends personalized emails to all prospect-status nodes every 6 hours"

# 6. Outreach Follow-Up — every 12 hours (follow-up to non-responders after 5 days)
$TriggerOutreachFollowUp = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Hours 12) -Once -At ((Get-Date).AddMinutes(10))
Register-OSTask `
    -TaskName    "UpworkOS_OutreachFollowUp" `
    -Script      "outreach.py" `
    -Args        "--follow-up --auto" `
    -Trigger     $TriggerOutreachFollowUp `
    -Description "Auto-sends follow-up emails to non-responders (5+ days) every 12 hours"

# ─── Summary ─────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "Setup complete. Tasks registered:" -ForegroundColor Cyan
Write-Host ""
Get-ScheduledTask -TaskPath $TASK_PATH | Format-Table TaskName, State -AutoSize
Write-Host ""
Write-Host "Logs will appear in: $LOG_DIR" -ForegroundColor Gray
Write-Host ""
Write-Host "Before the daemons can run, complete these steps:" -ForegroundColor Yellow
Write-Host "  1. Set TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID in config.py" -ForegroundColor White
Write-Host "     → Create bot: open @BotFather on Telegram → /newbot" -ForegroundColor Gray
Write-Host "     → Run: python scripts\notify.py --get-chat-id" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Set up Gmail API credentials" -ForegroundColor White
Write-Host "     → console.cloud.google.com → Create project → Gmail API → OAuth → Desktop → Download JSON → save as credentials.json" -ForegroundColor Gray
Write-Host "     → First run: python scripts\email_watcher.py --since 1h  (opens browser for auth)" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Test the stack:" -ForegroundColor White
Write-Host "     → python scripts\notify.py --test" -ForegroundColor Gray
Write-Host "     → python scripts\heartbeat.py" -ForegroundColor Gray
Write-Host "     → python scripts\email_watcher.py --dry-run --since 24h" -ForegroundColor Gray
Write-Host ""
Write-Host "Tasks run automatically after that. No other action needed." -ForegroundColor Green
Write-Host ""
