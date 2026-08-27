$ErrorActionPreference = 'Stop'
$packageRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$pptxPath = Join-Path $packageRoot 'FINAL_MAP_Soluble_Digitalization_Soutenance.pptx'
$videoPath = Join-Path $PSScriptRoot 'FINAL_MAP_Soluble_Digitalization_Soutenance.mp4'

$powerPoint = New-Object -ComObject PowerPoint.Application
$presentation = $null
try {
    $presentation = $powerPoint.Presentations.Open($pptxPath, $true, $false, $false)
    foreach ($slide in $presentation.Slides) {
        $slide.SlideShowTransition.AdvanceOnTime = -1
        $slide.SlideShowTransition.AdvanceTime = 4
        try { $slide.SlideShowTransition.EntryEffect = 3849 } catch { }
    }
    $presentation.CreateVideo($videoPath, $true, 4, 1080, 30, 85)
    $elapsed = 0
    while ($presentation.CreateVideoStatus -in @(1, 2)) {
        Start-Sleep -Seconds 1
        $elapsed++
        if ($elapsed -gt 420) { throw 'PowerPoint video export exceeded seven minutes.' }
    }
    if ($presentation.CreateVideoStatus -ne 3) { throw "PowerPoint video export failed with status $($presentation.CreateVideoStatus)." }
}
finally {
    if ($null -ne $presentation) { $presentation.Close() }
    $powerPoint.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($powerPoint) | Out-Null
}

Get-Item -LiteralPath $videoPath | Select-Object FullName, Length
