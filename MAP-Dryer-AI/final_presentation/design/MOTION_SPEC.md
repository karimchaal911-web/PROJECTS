# Motion Specification

## Purpose

Motion explains process continuity, hidden residence history, the laboratory-delay gap, data transformation, model separation, and governance. It is not decorative slide animation.

## Director

- Autoplay is the default. No click is required to move between chapters.
- Scene travel uses interruptible Catmull-Rom camera curves retargeted from the camera's live position.
- Major travel uses `power4.inOut`; text and glass layers materialize with `power4.out`.
- Each destination adds subtle camera drift only after travel completes.
- Space pauses or resumes. Arrow navigation is retained only for Q&A.
- The final scene does not loop; the dryer, particles, and visibility ribbon continue moving.

## Spatial continuity

- 01->02: aerial-to-low dolly; the granule becomes the guide.
- 02->03: the guide terminates at the dryer; the camera orbits the hero asset.
- 03->04: the shell becomes translucent and the lens moves to the cutaway.
- 04->05: drum rings align with time-tunnel rings.
- 05->06: replay pulses detach into signal strands and gates.
- 06->07: gates compress into the first architecture node; the camera travels through portals.
- 07->08: the model hub becomes a spatial bifurcation.
- 08->09/10: parallax selects the quality and process branches without rebuilding the world.
- 10->11: model geometry recedes behind the held-out evidence plane.
- 11->12: the evidence surface becomes the left screen of the curved control room.
- 12->13: camera pulls behind supervision to reveal the complete operating loop.
- 13->14: current objects dim; solid and outlined roadmap nodes appear in depth.
- 14->15: a long return arc lands on the same physical dryer introduced in scene 3.

## Continuous object motion

- Dryer rotation: constant, slow, physically calm.
- Product stream: particles follow the process curve; one hero granule is emphasized.
- Drum interior: lifters rotate; granules lift/cascade; vapor rises from the exhaust.
- Sensor rings: phase-offset pulses, never synchronized blinking.
- Data packets: directionally consistent movement toward Python, PostgreSQL, and Power BI.
- Ridge: continuous advisory ribbon through sparse lab anchors.
- One-Class SVM: slowly rotating envelope with one amber escape point.
- Control room: screen wall is fixed; only subtle environmental drift remains.

## Lens and lighting

- Depth of field is applied in the cinematic renderer with scene-specific focus distance.
- Bloom is restrained and limited to emissive product, sensor, portal, and evidence accents.
- Fog density changes by scene to create depth without hiding the technical object.
- Warm light belongs to heat/novelty; green belongs to process/quality; cyan belongs to architecture/supervision.

## Reduced motion and safe mode

- `prefers-reduced-motion` resolves camera travel immediately, stops drift, and freezes particles at deterministic positions.
- Safe mode disables post-processing, shadows, high particle counts, and high pixel ratio while preserving all chapters and claims.
- No `transition: all`; UI motion uses transform and opacity only.
