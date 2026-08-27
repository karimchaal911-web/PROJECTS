$ErrorActionPreference = 'Stop'

$packageRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$screensRoot = Join-Path $packageRoot 'exports\screenshots'
$notesPath = Join-Path $packageRoot 'speaker_notes\FULL_SPEAKER_NOTES.md'
$videoPath = Join-Path $packageRoot 'exports\video\FINAL_MAP_Soluble_Digitalization_Soutenance.mp4'
$pptxPath = Join-Path $packageRoot 'FINAL_MAP_Soluble_Digitalization_Soutenance.pptx'
$pdfPath = Join-Path $packageRoot 'FINAL_MAP_Soluble_Digitalization_Soutenance.pdf'

if (-not (Test-Path -LiteralPath $videoPath)) { throw "Missing cinematic film: $videoPath" }

$rawNotes = Get-Content -Raw -LiteralPath $notesPath
$notes = @{}
$matches = [regex]::Matches($rawNotes, '(?ms)^##\s+(\d{2})\s+-\s+.*?\r?\n\r?\n(.*?)(?=^##\s+\d{2}\s+-|\z)')
foreach ($match in $matches) {
    $notes[[int]$match.Groups[1].Value] = $match.Groups[2].Value.Trim()
}

$sceneNames = @(
    'Site awakening', 'Follow the granule', 'Dryer hero', 'Inside the drum', 'Time tunnel',
    'Signal lattice', 'Architecture flight', 'Intelligence split', 'Ridge ribbon', 'Novelty envelope',
    'Validation theatre', 'Control room', 'Operating loop', 'Governed roadmap', 'Closing visibility'
)

$sources = @(
    'Sources: final_report/MAP_Dryer_AI_Internship_Report.pdf; final_report/figures/process_photos/drying_section_structure.jpeg',
    'Sources: final_report/MAP_Dryer_AI_Internship_Report.pdf, Chapter 2',
    'Sources: final_report/MAP_Dryer_AI_Internship_Report.pdf, Chapters 2-3; final_report/figures/process_photos/rotary_dryer_shell.jpeg',
    'Sources: final_report/MAP_Dryer_AI_Internship_Report.pdf, Chapter 3; explanatory mechanism only, not CFD',
    'Sources: models/prototype_manifest.json; data/processed/MAP_Dryer_Canonical_5s.manifest.json; laboratory spacing from project report',
    'Sources: final_report/MAP_Dryer_AI_Internship_Report.pdf, Chapters 2-3; repository preprocessing implementation',
    'Sources: README.md; models/model_registry.json; powerbi dashboard/README.md',
    'Sources: models/model_registry.json; models/model_metadata.json; artifacts/notebook04_anomaly_evaluation.json',
    'Sources: models/5s/training_report.json; models/model_metadata.json',
    'Sources: models/5s/training_report.json; artifacts/notebook04_anomaly_evaluation.json',
    'Sources: models/5s/training_report.json; figures/03_Model1_SoftSensor/05_final_holdout_predictions.png',
    'Sources: powerbi dashboard/preview/preview_page1_overview.png; powerbi dashboard/preview/preview_page2_diagnostics.png; Power BI README.md',
    'Sources: README.md; models/prototype_manifest.json; repository runtime implementation',
    'Sources: artifacts/FINAL_VALIDATION_2026-08-24.md; final_report/MAP_Dryer_AI_Internship_Report.pdf, Conclusion',
    'Sources: final_report/MAP_Dryer_AI_Internship_Report.pdf; verified repository artifacts and implementation'
)

$powerPoint = New-Object -ComObject PowerPoint.Application
$presentation = $null
try {
    $presentation = $powerPoint.Presentations.Add()
    $presentation.PageSetup.SlideWidth = 960
    $presentation.PageSetup.SlideHeight = 540

    for ($index = 1; $index -le 15; $index++) {
        $slide = $presentation.Slides.Add($index, 12)
        $slide.Name = ('Scene ' + $index.ToString('00') + ' - ' + $sceneNames[$index - 1])
        $imagePath = Join-Path $screensRoot ('scene-' + $index.ToString('00') + '.png')
        if (-not (Test-Path -LiteralPath $imagePath)) { throw "Missing screenshot: $imagePath" }
        $picture = $slide.Shapes.AddPicture($imagePath, 0, -1, 0, 0, 960, 540)
        $picture.Name = 'Cinematic scene render'
        $picture.AlternativeText = 'Rendered frame from the continuous 3D scene: ' + $sceneNames[$index - 1]

        $noteText = if ($notes.ContainsKey($index)) { $notes[$index] } else { '' }
        $noteText = $noteText + "`r`n`r`n" + $sources[$index - 1]
        try {
            $slide.NotesPage.Shapes.Placeholders.Item(2).TextFrame.TextRange.Text = $noteText
        }
        catch {
            $noteBox = $slide.NotesPage.Shapes.AddTextbox(1, 48, 390, 620, 240)
            $noteBox.TextFrame.TextRange.Text = $noteText
        }

        try {
            $slide.SlideShowTransition.EntryEffect = 3849
            $slide.SlideShowTransition.AdvanceOnTime = 0
            $slide.SlideShowTransition.AdvanceOnClick = -1
            $slide.SlideShowTransition.Speed = 2
        }
        catch { }
    }

    try {
        $presentation.BuiltInDocumentProperties.Item('Title').Value = 'Soluble MAP - Cinematic Dryer Digitalization Soutenance'
        $presentation.BuiltInDocumentProperties.Item('Subject').Value = 'Industrial digital twin, advisory soft sensing, process novelty, validation, and operator supervision'
        $presentation.BuiltInDocumentProperties.Item('Comments').Value = 'Film-first 15-scene presentation. Slide 1 embeds the complete cinematic tour; slides 2-15 are discussion fallbacks.'
        $presentation.BuiltInDocumentProperties.Item('Keywords').Value = 'OCP, soluble MAP, rotary dryer, digital twin, Ridge, One-Class SVM, PostgreSQL, Power BI'
    }
    catch { }

    # Export the static 15-scene PDF before placing the film on slide 1.
    $presentation.SaveAs($pdfPath, 32)

    $firstSlide = $presentation.Slides.Item(1)
    $media = $null
    try {
        $media = $firstSlide.Shapes.AddMediaObject2($videoPath, 0, -1, 0, 0, 960, 540)
    }
    catch {
        $media = $firstSlide.Shapes.AddMediaObject($videoPath, 0, 0, 960, 540)
    }
    $media.Name = 'Cinematic autoplay - scenes 01 to 15'
    $media.AlternativeText = 'Embedded 83-second cinematic tour through all 15 connected 3D scenes.'
    try {
        $media.AnimationSettings.PlaySettings.PlayOnEntry = -1
        $media.AnimationSettings.PlaySettings.HideWhileNotPlaying = 0
        $media.AnimationSettings.PlaySettings.LoopUntilStopped = 0
        $media.AnimationSettings.PlaySettings.RewindMovie = 0
        $firstSlide.SlideShowTransition.AdvanceOnClick = 0
    }
    catch { }

    $presentation.SaveAs($pptxPath, 24)
}
finally {
    if ($null -ne $presentation) { $presentation.Close() }
    $powerPoint.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($powerPoint) | Out-Null
}

Get-Item -LiteralPath $pptxPath, $pdfPath, $videoPath | Select-Object FullName, Length, LastWriteTime
