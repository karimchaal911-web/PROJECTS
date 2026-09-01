# PREMIUM ASSET GENERATION — MODEL SELECTION

**Scope:** every generated visual asset considered for the Three.js soutenance
in `final_presentation/web`.
**Mandate:** prioritise **Seedance 2.0** and **Nano Banana Pro**; do not default
to a convenience-tier model; document why each winner won.
**Date of this pass:** 2026-08-28.

---

## 0. STATUS — READ THIS FIRST

**UPDATE — execution pass, 2026-08-28.** A1, A2 and B1 have now been generated
through the Higgsfield **MCP** server. Verdicts, job ids and credits are in §7.
Outcome in one line: **A1 selected AND integrated into the build, A2 rejected on
the §8 truth rule, B1 generated but not shipped on the §4 reliability gate.**

The original blocking report is kept below for provenance. The Higgsfield CLI was
installed, authenticated and working for everything except generation:

| Capability | Result |
|---|---|
| `higgsfield auth token` | ✅ valid (`oat_…`) |
| `higgsfield account status` | ✅ `plus` plan · **106.49 credits** |
| `higgsfield model list / get` | ✅ `nano_banana_pro` (image), `seedance_2_0` (video) both present |
| `higgsfield generate cost` | ✅ priced (see §5) |
| `higgsfield upload create` | ✅ all three reference photographs uploaded (ids in §3) |
| `higgsfield generate create` | ❌ **`{"error_type":"only_mcp_usage_on_trial_is_available"}`** |

The refusal is **account-tier, not credential and not model-specific** — it
reproduces identically on `nano_banana_pro`, `seedance_2_0`, `nano_banana_2_lite`
and `gpt_image_2`. Inspecting the CLI binary shows it sends an
`x-hf-mcp-client-name` header, so the backend permits generation from Higgsfield's
**MCP** client and refuses it from the bare CLI on this tier.

The MCP server has since been registered and authenticated for this repository:

```
higgsfield: https://mcp.higgsfield.ai/mcp (HTTP) - ✔ Connected
```

but **MCP tool schemas are loaded when a Claude Code session starts**, so they were
not callable from the session that registered them.

**That block is now cleared.** From a later session the MCP generation tools were
callable and the §4 shot list was executed in full — A1 and A2 on Nano Banana Pro,
B1 on Seedance 2.0. Total spend **53 credits**, balance **104.49 → 51.49**.

**What was delivered instead, in this pass:** the opening hero was rebuilt from a
**real photograph of the actual rotary dryer this project supervises**
(`web/public/img/rotary_dryer_shell.jpg`), shipped in the bundle since the first
build and never referenced by any code. It is graded in CSS (`.boot__plate`),
not retouched — see §6, which argues this is the *better* answer for the opening
frame regardless of the block.

---

## 1. THE CONSTRAINT THAT SHAPED EVERY DECISION

Section 8 of the brief: *a beautiful but technically false asset is REJECTED.*
Section 58: *do not fabricate evidence.*

This presentation's hero moments are, in order of jury weight:

1. the **Power BI report** — a real capture of the shipped PBIP export, rendered
   from the live PostgreSQL views;
2. the **hold-out evidence chart** — 165 real predictions against real targets;
3. the **rotary dryer** — 3D geometry traced from the site photograph;
4. the **MAP product** — a real photograph of product stored at the site.

Three of those four are evidence. **Generative imagery cannot touch them**, and
"upgrading" them with a model would be the single most damaging thing that could
be done to this deck's credibility. The frames a generative model may legitimately
serve are the ones that assert nothing: the title card, and atmospheric support.

That is why the shot list below is short. Five exceptional assets beat many
mediocre ones (§7 of the brief) — and here, two is closer to the honest number.

### Explicitly ruled out, with reasons

| Candidate | Verdict | Why |
|---|---|---|
| Generated "MAP product hero" for scene 02 | **REJECTED** | Would replace a real photograph of the actual product with a synthetic one, on the slide whose note says *"Photographed on product stored at the site."* Straight contradiction. |
| Generated control room behind the dashboard (scenes 10–11) | **REJECTED** | §8 names "fake control-room tech" as an auto-reject. The project has no control room; inventing one asserts deployment it does not have. |
| Generated dryer internals / CFD-looking transfer imagery | **REJECTED** | Scene 04b is captioned `SCHEMATIC — NOT A CFD RESULT`. Photoreal internals would make that caption a lie. |
| Generated plant establishing shots for scenes 01 / 03 | **REJECTED** | The persistent Three.js world is a protected architecture (§2 F). Cutting to a plate breaks the one-continuous-world claim the whole film rests on. |
| Generated "future digital twin" closing frame | **REJECTED** | Scene 13 states closed-loop control does not exist in this project. A polished future-state image two scenes earlier undermines it. |

---

## 2. MODEL ROLES

| Model | Type | Role here |
|---|---|---|
| **Nano Banana Pro** (`nano_banana_pro`) | image | Reference-faithful regrade of real project photographs. Chosen over Seedance for stills because it takes up to 14 image references and is an image model — grading a real photograph is an image-to-image task, not a synthesis task. |
| **Seedance 2.0** (`seedance_2_0`) | video | Candidate for a slow, cinematic move on the title-card plate. Chosen over Seedance 1.5 Pro / 2.0 Mini / 2.5 because 2.0 at `mode std` is the only one of the four that reaches 1080p with the `start_image` fidelity this needs. |
| GPT Image 2, Nano Banana 2 / 2 Lite, Z Image | — | **Not used.** Convenience tier; the brief forbids defaulting to them, and nothing here is rough ideation. |

---

## 3. REFERENCES (uploaded, ids valid)

All three are **real project photographs**, already shipped in `web/public/img/`.

| Asset | Upload id | Used by |
|---|---|---|
| `rotary_dryer_shell.jpg` — the actual dryer, riding rings, green steel, grating | `718a70a4-a75a-403a-9f5e-03c1dd650781` | A1, A2, B1 |
| `drying_section_structure.jpg` — the drying-section structural bay | `03e98731-9bb3-4075-a1a9-d1e5ccce1783` | A2 (secondary) |
| `soluble_map_storage.jpg` — MAP in storage at the site | `5f04e68d-40ac-4729-a4b2-bcec86d2d7e8` | reference only; **not** to be regenerated |

Additional grounding available and to be respected: `assets/process/pcs7_*.jpeg`
(PCS7 screens), `final_report/` diagrams, `assets/dashboard/powerbi_*.png`.

---

## 4. SHOT LIST — READY TO EXECUTE

### A1 — OPENING HERO PLATE · Nano Banana Pro · **primary candidate**

* **Scene:** boot gate / title card (`.boot__plate`), the first frame anybody sees.
* **Purpose:** §7 Priority A — expensive, industrial, cinematic, OCP-compatible.
* **Why Nano Banana Pro:** the job is *grade this exact photograph*, not *invent an
  industrial scene*. Reference fidelity is the whole requirement; an image model
  with strong reference adherence is the correct tool, and Seedance would be
  synthesising motion nobody asked for.
* **Acceptance test:** hold it beside `rotary_dryer_shell.jpg`. Every pipe, ring,
  handrail and column must be traceable to the original. Any invented equipment,
  any added person, any signage → **reject**.

```bash
higgsfield generate create nano_banana_pro \
  --image 718a70a4-a75a-403a-9f5e-03c1dd650781 \
  --aspect-ratio 16:9 --resolution 4k --wait --wait-timeout 12m \
  --prompt "Cinematic industrial photography grade of THIS EXACT rotary dryer installation. Preserve the equipment, its geometry and its framing exactly as photographed: the inclined rotary dryer shell with its welded seams and riding rings, the lagged overhead ducts, the green painted structural steel columns, the galvanised handrail and the grating platform. Do NOT add, remove, relocate or invent any equipment, pipe, vessel, machine, person, sign or logo. Recompose to a 16:9 landscape frame with the dryer shell running from lower left into depth on the right. Relight as a restrained industrial night interior: deep near-black background, one soft cool key raking along the top of the shell, a faint warm rim on the discharge side, the structural steel reading as deep forest green. Remove the harsh on-camera flash blowout; keep the real surface texture, weld lines and product dust deposits. Muted desaturated palette of near-black, cool grey steel and deep green with one restrained warm accent. No text, no graphics, no people. Photoreal, large-format, high dynamic range, quiet, expensive, engineered."
```

### A2 — OPENING HERO PLATE, ALTERNATE DIRECTION · Nano Banana Pro

* **Purpose:** controlled comparison against A1, as §6 of the brief requires for
  hero assets. Wider, more graphic, more negative space for the title column.
* **Selection criterion:** whichever leaves a cleaner, darker left third for the
  headline **without** flattening the machine into a silhouette.

```bash
higgsfield generate create nano_banana_pro \
  --image 718a70a4-a75a-403a-9f5e-03c1dd650781 \
  --image 03e98731-9bb3-4075-a1a9-d1e5ccce1783 \
  --aspect-ratio 21:9 --resolution 4k --wait --wait-timeout 12m \
  --prompt "Wide anamorphic industrial plate built from THESE EXACT photographs of one rotary dryer and its structural bay. Preserve every real element — shell, riding rings, lagged ducts, green steel columns, grating, handrail — in their real relationship. Invent nothing: no added machinery, no people, no signage, no text. Compose 21:9 with the machine held to the right two-thirds and the left third falling into clean darkness for typography. Low-key industrial night lighting, a single cool grazing key along the shell, deep forest-green steel, near-black ground, one restrained warm accent far in depth. Remove flash blowout and airborne dust glare; retain weld seams, surface wear and dust deposits. Restrained, documentary, expensive. Photoreal, no stylisation, no lens flare, no volumetric god rays."
```

### B1 — TITLE-CARD MOTION PLATE · Seedance 2.0 · **evaluate, then decide**

* **Purpose:** §6 — a moving version of the opening hero, from the selected still.
* **Why Seedance 2.0:** the only video model in the roster that holds 1080p from a
  `start_image` at `mode std`; 2.0 Mini and 1.5 Pro both degrade reference fidelity.
* **Direction:** a *held shot*, not a camera move. 5 s, almost imperceptible drift,
  dust settling. Anything more becomes a product trailer and fights the deck's
  restraint.
* **`--generate-audio false` is mandatory.** §52: the presentation has no audio and
  must keep none.

```bash
# start_image = the A1/A2 winner's job id
higgsfield generate create seedance_2_0 \
  --start-image <WINNING_JOB_ID> \
  --prompt "A locked-off cinematic hold on this industrial interior. Almost no camera movement: a barely perceptible 2 percent push and a slow settling of suspended dust in the light. The machine does not move. No cuts, no zoom, no rack focus, no lens flare, no people entering frame, no text. Quiet, restrained, documentary, expensive." \
  --duration 5 --resolution 1080p --mode std --aspect-ratio 16:9 \
  --generate-audio false --wait --wait-timeout 20m
```

**Ship / do-not-ship rule for B1.** It goes into the build **only if** it costs
nothing in live reliability. The boot gate is where shader pre-warm happens
(`Prewarm.jsx`, eight frames behind the panel) and where the 677 ms scene-11 stall
was eliminated. A video decode competing with that window trades a Priority-1
guarantee for a Priority-5 flourish. Concretely: ship only if the file is
≤ 4 MB, the first `Prewarm` frame is unaffected, and `qa-perf` still reports zero
frames > 30 ms. **Otherwise keep the still.** That is a legitimate, documented
model-selection outcome, not a failure to try.

---

## 5. COST

| Asset | Model | Params | Credits |
|---|---|---|---|
| A1 | `nano_banana_pro` | 16:9 · 2k | **2** (measured) |
| A1 at 4k | `nano_banana_pro` | 16:9 · 4k | ~2–4 |
| A2 | `nano_banana_pro` | 21:9 · 4k | ~2–4 |
| B1 | `seedance_2_0` | 5 s · 1080p · std | **45** (measured) |

Balance at time of writing: **106.49**. The whole list fits with ~55 in reserve for
a second Seedance take if the first is too animated.

---

## 6. WHAT IS SHIPPED FOR THE OPENING HERO

**A1 is in the build.** `web/public/img/dryer_hero_plate.jpg` — the Nano Banana Pro
relight of `rotary_dryer_shell.jpg`, resampled to 2400 x 1340 and saved as
progressive JPEG at quality 88 (**534 KB**, down from the 24.9 MB 4k PNG, which is
archived in `selected/`). `App.jsx` points `.boot__plate` at it and `styles.css`
now trims exposure only (`brightness(0.86) saturate(0.92)`), because the plate
arrives already graded.

### Why it ships, having been checked rather than assumed

Held side by side with `rotary_dryer_shell.jpg` at native resolution, every element
is traceable: the same elevated viewpoint past the dust-caked handrail, the same
inclined shell running lower-left into the wall penetration, the same riding-ring
band, the same lagged overhead ducts with their right-hand elbow, the same green
structural columns, the same grating below. Nothing is added — no equipment, no
person, no signage, no text. The flash blowout is gone and the surface texture and
product-dust deposits survive, which is exactly what an image model was chosen for
over a synthesis model.

The §7.2 caveat about A1's left third turned out not to bind: the boot gate's
existing three-layer scrim (a left-to-right gradient clearing the type column, a
radial vignette, and a 20 % OCP-green wash) already darkens that region, so the
headline sits cleanly over it while the machine reads at full detail on the right.
Verified in a captured boot frame at 1920 x 1080, not assumed.

### The interim answer, kept for the record

While generation was blocked, the title card stood on `rotary_dryer_shell.jpg`
itself, graded entirely in CSS. That was the right call under the constraint — the
audit had noted 787 KB of plant photographs shipping unreferenced, and this used
one truthfully at zero cost. A1 clears the bar §6 set for it
(*"visibly better than the graded original, with every real element intact"*): it is
a genuine relight with retained micro-texture rather than a filter over a phone
photograph. The original file is untouched on disk and remains the reference the
generated plate is judged against.

---

## 7. LOG

| Date | Asset | Seedance 2.0 tested? | Nano Banana Pro tested? | Selected | Note |
|---|---|---|---|---|---|
| 2026-08-28 | A1 opening hero | n/a | **yes** — `74bb6f03`, 4 cr | ✅ **SELECTED** | passes the §4 test on every element |
| 2026-08-28 | A2 alternate | n/a | **yes** — `0840ee7a`, 4 cr | ❌ **REJECTED — §8 truth rule** | invents equipment and a location that do not exist |
| 2026-08-28 | B1 motion plate | **yes** — `3d654b93`, 45 cr | n/a | ⛔ **GENERATED, NOT SHIPPED** | good take; fails the §4 size gate at 5.76 MB |
| 2026-08-28 | Opening hero **as shipped** | n/a | n/a | **A1 — `dryer_hero_plate.jpg`** | integrated and verified in a captured boot frame; see §6 |
| 2026-08-28 | Scene 02 product hero | n/a | n/a | **real photograph, unmodified** | regenerating it would contradict the slide's own note |
| 2026-08-28 | Power BI hero | n/a | n/a | **real capture of the shipped report** | evidence — never generative |

### 7.1 Execution record

Run 2026-08-28 via the Higgsfield MCP server. Balance **104.49 → 51.49 = 53 credits**.

| Asset | Job id | Model requested | Params | Credits | Output |
|---|---|---|---|---|---|
| A1 | `74bb6f03-49b2-49d0-8da4-42f7d16d52a0` | `nano_banana_pro` | 16:9 · 4k · 1 ref | 4 | 5504×3072 PNG |
| A2 | `0840ee7a-22ac-429b-9dd8-29905328c431` | `nano_banana_pro` | 21:9 · 4k · 2 refs | 4 | 6336×2688 PNG |
| B1 | `3d654b93-a96f-4cc3-b70e-65926230ac18` | `seedance_2_0` | 5 s · 1080p · std · 16:9 · no audio | 45 | 1920×1080, 24 fps, 121 f, 5.04 s, 5.76 MB |

**Model-identity note.** Both image jobs come back from the API labelled
`model: nano_banana_2`, not `nano_banana_pro`. This is an **alias artifact, not a
downgrade**, and the billing proves it: `nano_banana_pro` is priced at 4 credits for
these params and `nano_banana_2` at 3, and the observed balance delta for A1 + A2 was
exactly **8 credits (4 + 4)**. Both are catalogued as distinct models and both accept
4k and 21:9, so output specs alone do not disambiguate — only price does. The §2
mandate was honoured.

### 7.2 A1 — SELECTED

**Why it won.** It is the only candidate that kept the *photograph's own viewpoint*:
the elevated platform looking down past the dust-caked handrail at the inclined shell
running lower-left into the wall penetration. Applying the §4 test element by element
— shell and weld seams, riding-ring band, lagged overhead ducts with their right-hand
elbow, green structural columns, galvanised handrail, grating below — every one is
traceable to `rotary_dryer_shell.jpg`. Inspected at native 4k in the left third and the
right depth: **no invented equipment, no added people, no signage, no text.** The flash
blowout is gone, and the real surface texture and product-dust deposits survive, which
was the whole point of choosing an image model over a synthesis model.

**One honest caveat.** A1's left third is *not* the clean dark type column §4 hoped for
— it carries ducts and green steel at full detail. Its usable negative space is the
mid-left background and lower-left. A2 was the candidate designed to solve that, and
A2 is disqualified, so the typography must work against A1 or against the §6 CSS-graded
original.

**Bar from §6 — "visibly better than the graded original":** met. It is a genuine relight
with retained micro-texture, not a filter over a phone photograph.

### 7.3 A2 — REJECTED on the §8 truth rule (not on quality)

A2 is the more cinematic image of the two. That is precisely the trap §8 names, and it
is rejected on **truth, not quality.** It does not regrade the photograph; it invents a
new scene:

* **Invented equipment** — concrete foundation plinths, a trunnion/support-roller
  assembly with bearing housings on a blue-painted baseplate, and a drive coupling with
  a gearbox-like housing. None of this appears in either reference.
  Evidence: `rejected/A2_evidence_invented_plinths_and_trunnion.jpg`.
* **Invented location and viewpoint** — the camera drops to ground level in an open
  exterior night yard with an asphalt floor and a lit lamp standard in the distance.
  The real photograph is a confined *interior* shot from a grating platform with **no
  ground plane visible at all**. The handrail and grating — both named as required
  elements — are gone.
* **Root cause.** The A2 brief fuses two photographs of *different places*: an interior
  dryer floor and an **exterior daylight** structural bay. Composing them into one
  continuous night interior produces a space that does not exist. The direction was
  flawed as written, independently of the model.

**Correction to an earlier read of mine:** at review resolution the dark blotches on the
drum end look like painted lettering, which would have been a separate "no text"
violation. At native 4k they are corrosion and paint wear. **There is no invented text
in A2** — the rejection rests solely on the invented equipment and location above.

### 7.4 B1 — GENERATED, NOT SHIPPED (§4 reliability gate)

Generated from the A1 winner as `start_image`, `generate_audio false`. **The absence of
audio was verified in the container, not assumed**: the MP4 carries zero `mp4a`,
`soun` and `SoundHandler` boxes, video track only. §52 satisfied.

**The take is good.** Decoded frames show a restrained push that holds A1's geometry —
handrail, shell, ducts and green columns all stable, no people, no text, nothing
invented entering frame, no rotation of the machine. The push is slightly stronger than
the "2 percent" the direction asked for, but it stays the right side of restrained.

**It still does not ship.** §4's rule is ship *only if* the file is ≤ 4 MB. It is
**5.76 MB**. The gate fails on the first condition, so the Priority-1 boot-window
guarantee wins over a Priority-5 flourish and **the still is kept** — the outcome §4
explicitly anticipates. Because the size gate already decides it, the `Prewarm` and
`qa-perf` conditions were not run; they could not have rescued it.

The asset is retained at `video/B1_3d654b93_1080p_5s.mp4`. Re-encoding it under 4 MB is
a legitimate follow-up, but it is a new decision and was not taken here.

### 7.5 Files

```
higgsfield/selected/  A1_opening_hero_16x9_4k.png        ← the winner (24.9 MB, 4k)
                      A1_opening_hero_review.jpg
higgsfield/rejected/  A2_0840ee7a_21x9_4k_REJECTED_truth_rule.png
                      A2_review_REJECTED_truth_rule.jpg
                      A2_evidence_invented_plinths_and_trunnion.jpg
higgsfield/video/     B1_3d654b93_1080p_5s.mp4           ← not shipped, retained
                      B1_contactsheet.jpg
higgsfield/candidates/ review crops kept only where they are not byte-identical
                      to their copy under selected/ or rejected/ (the two 4k
                      originals live under their outcome name, not twice)
web/public/img/    dryer_hero_plate.jpg               <- A1, resampled, IN THE BUILD
                   soluble_map_storage.jpg            <- NOT generated; a resample of
                                                         assets/process/soluble_map_storage.jpeg,
                                                         see 7.6
```

**Shipped:** `web/public/img/dryer_hero_plate.jpg` — A1 resampled to 2400 x 1340,
progressive JPEG q88, **534 KB** (from 24.9 MB). `App.jsx` points `.boot__plate` at it
and `styles.css` trims exposure only. The §7.2 caveat about the type column was checked
against a captured boot frame at 1920 x 1080 before the swap and did not bind: the boot
gate's existing left-to-right scrim already clears that region, so the headline sits
over darkness while the machine reads at full detail on the right. The 4k original stays
in `selected/` and `rotary_dryer_shell.jpg` — the reference A1 is judged against — is
untouched.

---

### 7.6 Follow-up pass, 2026-08-28 (second) — NO GENERATION RAN

This section exists because the pass that produced it was asked to fix a *blurry
full-screen hero* and was pointed at §4 Option B — a Nano Banana Pro restoration —
as one way to do it. Neither happened, and both facts belong on the record.

**The account was not in a state to generate.** The first thing this pass ran was:

```
$ higgsfield account status
karimchaal911@gmail.com — free plan, 0 credits
```

That is a **different account and a different tier** from the one §7.1 records
(`plus` plan, balance 104.49 → 51.49 after the A1/A2/B1 run). No generation was
attempted, no credits were spent, and the Higgsfield MCP server was not available in
this session either. Anything in this document that implies spendable balance is
scoped to §7.1's account at §7.1's date — in particular §9's "~51 credits remain" in
`qa/PRESENTATION_REMEDIATION_REPORT.md`, which is corrected there.

**Option B would have been the wrong call anyway.** The blurry asset was scene 02's
soluble-MAP hero, `soluble_map_storage.jpg`. Look at what is actually in that frame:
handwriting in marker across two bulk bags, printed bag text reading
`MAP Monoammonium Phosphate 12-61-00`, and rack labels reading `R 09`, `R 10`, `R 11`.
Constrained image-to-image on a dense warehouse rack rewrites exactly those things —
handwriting becomes plausible-looking nonsense, bag counts drift, rack numbering
changes. §4 Option B's own prohibitions ("do not add extra bags, change shelving,
alter pallet geometry, invent branding") are the failure modes this specific
photograph invites most. It would have come back a **truth-rule reject**, and the
right answer under §4 Option C is the original photograph, better framed.

**What actually fixed it — measurement, not generation.** The photograph is
1280 × 960 and there is no larger copy anywhere in the project (checked: `assets/`,
`resources/`, both presentation trees, the report resources). It was being drawn
25.5 world units wide at a camera distance of 18 on a 30 mm lens, which is about
**2 860 screen pixels across a 1920-wide frame — a 2.2× bilinear magnification**.
That is the entire defect. Two changes:

1. `three/layers/Material.jsx` draws the plate as an editorial print at a size the
   source can carry — about 1 000 screen pixels at the closest beat, a
   **minification at every beat**, with the copy column beside it rather than on top
   of it.
2. `data_build/restore_plates.py` writes the delivered file: one Lanczos resample to
   2048 × 1536 with a measured unsharp pass either side, 4:4:4 progressive JPEG
   (875 KB). This is **resampling and sharpening of the real photograph** — no
   content is generated, replaced or invented. Held against
   `assets/process/soluble_map_storage.jpeg` at native resolution, every bag,
   pallet, rack label and marker stroke is the same one.

| Asset | Model | Credits | Verdict | Reason |
|---|---|---|---|---|
| Scene 02 soluble-MAP hero | **none — not generated** | 0 | ✅ **real photograph, resampled** | Truthful enhancement could not be guaranteed on handwriting and bag counts (§4 Option B prohibitions), and the account had no credits. §4 Option C applied: original source, better framing. |

`web/public/img/soluble_map_storage.jpg` is therefore a **derivative of a
photograph, not a generation**, and must not be listed among generated assets.
