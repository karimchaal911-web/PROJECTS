# Three.js Scene Plan

## Runtime architecture

One renderer, one scene, one camera, and one persistent world are created in `src/main.js` and `src/world.js`. Scene records in `src/scenes.js` describe camera, lens, light, hold duration, and visibility-channel targets. No chapter replaces the canvas.

`CinematicDirector` behavior in `main.js`:

- interpolates from current live camera/target values;
- uses curved paths with intentional lateral or vertical waypoints;
- updates FOV, roll, fog, exposure, key/green/warm/blue lights, bloom, and focus;
- schedules the next chapter automatically after its hold;
- pauses/resumes without rebuilding state;
- exposes `window.__director` for QA and film capture.

## Persistent world systems

- Industrial site frame, vessels, centrifuge, conveyors, cooler, and warehouse
- Rotary dryer shell, bands, supports, rollers, lifters, inlet/exhaust, internal particles, heat volumes, vapor, and twin wireframe
- Process product curve and hero granule
- Sensor nodes and pulses
- Time tunnel with dense replay packets and three lab anchors
- Preprocessing strands, four gates, and structured data lattice
- Architecture portals and sensor/Python/model/PostgreSQL/Power BI nodes
- Ridge ribbon with laboratory anchors
- One-Class SVM normal envelope, novelty point, and contributor bars
- Chronological validation theatre with authentic project plot
- Curved control room with authentic overview/diagnostics previews
- Solid-to-outlined roadmap nodes
- Visibility ribbon returning from supervision to the physical dryer

## Visibility channels

`atmosphere`, `structure`, `process`, `dryer`, `interior`, `product`, `heat`, `vapor`, `sensors`, `twin`, `time`, `preprocessing`, `pipeline`, `ridge`, `novelty`, `validation`, `controlRoom`, `roadmap`, `visibility`.

Each material stores its base opacity. A scene supplies a normalized value per channel. GSAP interpolates opacity and keeps the material alive until it is visually negligible, preventing transition pops.

## Post-processing

Standard mode: ACES tone mapping, soft shadows, Bokeh depth of field, and thresholded Unreal bloom.

Safe mode: direct renderer, reduced particles, no shadows, pixel ratio 1, no post-processing.

## Deterministic exports

- `?shot=N&capture=1` resolves scene N immediately and hides transport controls.
- `?safe=1` selects the low-GPU path.
- `?film=1&auto=0&pace=.52` allows the recorder to start the director after screencast capture begins.
- `window.__PRESENTATION_READY__` is set only after 3D textures and DOM images resolve.
- Standard frames: 1920x1080 PNG.
- Film capture: 1920x1080 full-page JPEG frames, encoded to H.264 30 fps.

Current world complexity: about 303 objects and 115 tracked materials in standard and safe modes; particle density and rendering features differ by mode.
