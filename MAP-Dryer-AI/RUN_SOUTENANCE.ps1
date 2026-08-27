<#
.SYNOPSIS
    Launches the final soutenance presentation from the repository root.

.DESCRIPTION
    A thin forwarder to final_presentation_claude\RUN_PRESENTATION.ps1, so the
    presentation starts from wherever the terminal happens to be sitting.

    Not to be confused with RUN_FINAL_DEMO.ps1, which starts the PostgreSQL
    replay and opens the live Power BI dashboard. That one is optional; this one
    is the presentation itself.

.PARAMETER Safe
    Start in reduced-performance mode.

.EXAMPLE
    .\RUN_SOUTENANCE.ps1
    .\RUN_SOUTENANCE.ps1 -Safe
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
