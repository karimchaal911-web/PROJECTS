<#
.SYNOPSIS
    Launches the final soutenance presentation from the repository root.

.DESCRIPTION
    Alias for final_presentation_claude\RUN_PRESENTATION.ps1, so either name
    works from either folder. All four combinations reach the same script.

    Not to be confused with RUN_FINAL_DEMO.ps1, which starts the PostgreSQL
    replay and opens the live Power BI dashboard. That one is optional; this one
    is the presentation itself.

.EXAMPLE
    .\RUN_PRESENTATION.ps1
    .\RUN_PRESENTATION.ps1 -Safe
#>
[CmdletBinding()]
param(
    [switch]$Safe,
    [int]$Port = 0
)

$ErrorActionPreference = 'Stop'
$target = Join-Path $PSScriptRoot 'final_presentation_claude\RUN_PRESENTATION.ps1'

if (-not (Test-Path $target)) {
    throw "Presentation launcher not found at $target"
}

& $target @PSBoundParameters
