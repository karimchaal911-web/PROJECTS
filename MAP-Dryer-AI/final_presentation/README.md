# Soluble MAP Dryer Digitalization - Cinematic Soutenance

This package contains a 15-scene, film-first presentation built as one persistent Three.js industrial-digital world. The camera travels from the OCP process line to the rotary dryer, inside the drum, through the laboratory-delay tunnel, preprocessing, architecture, model intelligence, validation, operator supervision, roadmap, and back to the still-moving dryer.

## Start here

- Best live experience: `web/run_presentation.ps1`
- Lower-GPU live experience: `web/run_presentation_safe.ps1`
- PowerPoint with embedded 83-second cinematic film on slide 1: `FINAL_MAP_Soluble_Digitalization_Soutenance.pptx`
- Static 15-scene handout: `FINAL_MAP_Soluble_Digitalization_Soutenance.pdf`
- Standalone cinematic film: `exports/video/FINAL_MAP_Soluble_Digitalization_Soutenance.mp4`
- Full presenter notes: `speaker_notes/FULL_SPEAKER_NOTES.md`
- One-line cues: `speaker_notes/QUICK_CUES.md`

The live version autoplays. Camera movement does not require clicks. Press Space only when you want to pause or resume for explanation. The PowerPoint begins with the complete film; slides 2-15 remain available for discussion and Q&A.

## Controls

- Space: play or pause the automatic director
- Left/Right: manual scene selection for Q&A
- R: restart the automatic tour
- P: presenter cue panel
- S: restart in safe mode
- F: fullscreen
- Home/End: first or final scene

## Visual systems

- Persistent rotating dryer with lifters, particle cascade, heat field, vapor, and sensor pulses
- Granule-follow process journey
- Spatial two-hour laboratory gap versus five-second prototype replay
- Signal-to-structure preprocessing lattice
- Sensors -> Python -> models -> PostgreSQL -> Power BI pipeline
- Separate Ridge quality ribbon and One-Class SVM novelty envelope
- Chronological evidence theatre using the authentic held-out plot
- Curved control room using authentic Power BI project previews
- Governed read-only/shadow-validation roadmap
- Camera arcs, push-ins, orbit moves, portal travel, parallax, focus shifts, lighting changes, and reduced-motion behavior

## Truth boundary

- The prototype is advisory, not autonomous control.
- Power BI visualizes PostgreSQL outputs; it does not run models.
- Five seconds is the deterministic prototype replay/visualization cadence, not a confirmed plant historian frequency.
- The 92-day dataset is deterministic synthetic data for reproducibility, not evidence of live-plant generalization.
- Laboratory moisture remains the quality reference.
- There is no live PCS7 connection, actuator write-back, or closed-loop control in the current project.

## Rebuild

From `web/`: `npm install`, then `npm run build`.

Scene exports: `npm run capture:scenes` while the local `dist` folder is served on port 8765.

PowerPoint/PDF: run `pptx_build/build_fallback.ps1` after the scene frames and cinematic MP4 are present.
