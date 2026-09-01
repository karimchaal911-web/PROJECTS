# POWER BI — STATIC BACKUP

If the live demonstration cannot be run in the room, these are the fallbacks.
They are the **same artifacts the presentation itself displays** — scenes 10 and
11 map `powerbi_overview.png` and `powerbi_diagnostics.png` onto the report plane
— so nothing here is a second, prettier version of the deliverable.

| File | What it is |
|---|---|
| `powerbi_overview.png` | Page 1, **3200 × 1800** (the deterministic 1600 × 900 report page at deviceScaleFactor 2) |
| `powerbi_diagnostics.png` | Page 2, same resolution |
| `preview_page1_overview.html` | The page's own source, rendered by `tools/render_dashboard_preview.py` from the live PostgreSQL views. Open it in any browser — it needs no server and no database. |
| `preview_page2_diagnostics.html` | ditto |

## What state this capture is in, and why it matters

The capture is a **live replay state taken inside an injected disturbance**, not
a null state and not a mock-up. Verifiable in the HTML source:

| Claim on screen | Verbatim in the source |
|---|---|
| freshness pill | `LIVE DATA` |
| refresh cadence | `AUTO 60 SEC` |
| latest event | `Latest 2026-07-16 14:42:55` |
| ingestion lag | `ingested 0 min ago` |
| anomaly score | `0.95` · severity `HIGH` |
| subsystem | drying-air and exhaust circuit |
| diagnosis + operator guidance | populated, ranked |

The previous capture announced `DATA · STALE`, `STALE` on every process tile and
`ingested 8525 min ago` — roughly six days — directly beneath an eyebrow about
real-time supervision, and it was taken in the null state (`NORMAL`, "No active
anomaly", "No anomaly-related cause list is generated"), so the diagnosis scene
had nothing to show. That was the single most damaging contradiction in the
presentation and the most likely jury question. It no longer exists.

## Scale reconciliation

Predicted moisture reads `0.0798 %`, laboratory `0.0752 %`, validated absolute
error `0.0013 %` — the **same scale** as the hold-out chart in scene 09
(y-axis 0.065 → 0.080). There is no 10× or 100× discrepancy between the two
scenes to explain away.

## Refresh cadence, stated precisely

Three different five-second things used to be conflated. They are distinct:

* the **replay tick** writes one row every 5 s (`237,600` rows over the held-out
  test period);
* the **report page** auto-refreshes on a 60-second cycle — that is the
  `AUTO 60 SEC` pill, and it is what the screen actually does;
* **no physical instrument sampled at 5 s.** The 5-second grid is the prototype
  historian grid, not a plant sampling rate.

## To regenerate

```
1. run the replay so the views hold a fresh, meaningful state
2. python tools/render_dashboard_preview.py
3. cd final_presentation/web && node scripts/capture-dashboard.mjs
```

Step 3 writes straight into `web/public/img/`, so the presentation picks the new
capture up on the next build. Copy the results back into this folder afterwards.

**A video backup has not been produced.** A deterministic screen recording of the
replay would need PostgreSQL and the Python service running on the capture
machine; the two HTML pages above are self-contained, need neither, and show the
same state — which is the more reliable fallback for a room you do not control.
