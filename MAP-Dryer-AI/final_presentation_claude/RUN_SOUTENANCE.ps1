<#
.SYNOPSIS
    Alias for RUN_PRESENTATION.ps1, so either name works from either folder.

.DESCRIPTION
    The launcher can be started as RUN_SOUTENANCE.ps1 or RUN_PRESENTATION.ps1,
    from the repository root or from final_presentation_claude. All four
    combinations reach the same script. On the day you should not have to
    remember which name belongs to which directory.

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
& (Join-Path $PSScriptRoot 'RUN_PRESENTATION.ps1') @PSBoundParameters
