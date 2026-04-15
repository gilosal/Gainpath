param(
    [ValidateSet("backend", "frontend", "all")]
    [string]$Service = "all"
)

$ErrorActionPreference = "Stop"

function Deploy-Service {
    param(
        [string]$Name,
        [string]$Path
    )

    Push-Location $Path
    try {
        Write-Host "Deploying $Name from $Path" -ForegroundColor Cyan
        railway up -d
    }
    finally {
        Pop-Location
    }
}

switch ($Service) {
    "backend" {
        Deploy-Service -Name "backend" -Path (Join-Path $PSScriptRoot "backend")
    }
    "frontend" {
        Deploy-Service -Name "frontend" -Path (Join-Path $PSScriptRoot "frontend")
    }
    "all" {
        Deploy-Service -Name "backend" -Path (Join-Path $PSScriptRoot "backend")
        Deploy-Service -Name "frontend" -Path (Join-Path $PSScriptRoot "frontend")
    }
}
