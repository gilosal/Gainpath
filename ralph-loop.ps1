param(
    [switch]$Headless,
    [switch]$Verify,
    [string]$Agent,
    [string]$Model
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$statusJson = $null
try {
    $statusJson = ralph-tui status --json --cwd $root | ConvertFrom-Json
} catch {
    $statusJson = $null
}

if ($statusJson -and $statusJson.status -in @('running','paused','interrupted')) {
    $cmd = @('resume', '--cwd', $root)
} else {
    $cmd = @('run', '--cwd', $root, '--prd', '.\tasks\prd.json')
}

if ($Headless) { $cmd += '--headless' }
if ($Verify) { $cmd += '--verify' }
if ($Agent) { $cmd += @('--agent', $Agent) }
if ($Model) { $cmd += @('--model', $Model) }

& ralph-tui @cmd
