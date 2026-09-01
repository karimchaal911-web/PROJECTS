# LIVE DEMONSTRATION — OPERATING PROCEDURE

**The presentation is complete without this.** Scene 10 already shows the real
Power BI report, captured from the shipped PBIP project. Run the live demo only
if the room, the machine and the clock all allow it — and decide *before* you
start speaking, not during.

Budget: **90 seconds** inside the soutenance, plus 10 minutes of setup before
the jury enters.

---

## 0. Decide

| Condition | Do |
|---|---|
| PostgreSQL reachable, Power BI Desktop installed, ≥ 10 min before the session | Run the demo |
| Anything above is uncertain | **Skip it.** Scene 10 carries the point |
| Something fails mid-demo | Press `Alt+Tab` back to the browser, say *"the captured version shows the same thing"*, continue at scene 11 |

Never debug in front of a jury. The decision to abandon costs you five seconds;
troubleshooting costs you the presentation.

---

## 1. Before the session (T − 15 min)

From the repository root, in the `realtime_pipeline` environment:

```powershell
# 1 — database reachable and the view contract intact
python realtime_pipeline/src/verify_powerbi_views.py
```

Expect **five of five view contracts passed** and a row count for each.

* *View missing* → `python realtime_pipeline/src/apply_sql_migration.py`, then re-verify.
* *Zero rows* → normal before the replay starts; the launcher fills them.
* *Cannot connect* → **skip the live demo.** Do not attempt to fix the database.

```powershell
# 2 — full launcher (validates environment, clears runtime tables,
#     starts a fresh 5 s TEST replay, verifies views, opens the dashboard)
.\RUN_FINAL_DEMO.ps1
```

Close any open Power BI Desktop window first — the launcher expects to open it
itself.

To keep existing rows and resume after the newest stored timestamp:

```powershell
.\RUN_FINAL_DEMO.ps1 -Resume
```

The launcher never retrains models, regenerates datasets, executes notebooks or
rebuilds the report.

## 2. Park it

Once the dashboard is populated and refreshing:

1. Leave Power BI Desktop open on **page 1, Operations Overview**.
2. Leave the replay service running in its terminal. It continues while Power BI
   is open and stops when Power BI closes or on `Ctrl+C`.
3. Bring the presentation browser to the front and press `F` for fullscreen.
4. Confirm the browser is on scene 01 (press `1`).

You now have both windows ready and only need `Alt+Tab`.

---

## 3. During the soutenance

Cut to the live dashboard at the **end of scene 10, beat 3** — after the
diagnostics page, before pressing into scene 11.

> *"That is the captured report. It is also running right now — let me show you."*

`Alt+Tab` → Power BI.

**Ninety seconds, three things, in this order:**

1. **The freshness pill and the timestamp are moving.** This is arriving now, not
   a screenshot.
2. **Predicted moisture beside the latest laboratory result**, and the validated
   error between them.
3. **The anomaly risk against the warning and critical lines**, and the
   contributor list on page 2.

Say the guard aloud while it is on screen:

> *"This is a prototype replay of held-out synthetic data, refreshing every five
> seconds. Power BI is only visualising — it never loads a model and never runs
> inference."*

`Alt+Tab` back to the browser. Press `→` to continue into scene 11, which
explains exactly the layers you just saw working.

---

## 4. Recovery

| Symptom | Action |
|---|---|
| Power BI shows a credential prompt | Cancel. Return to the browser. Skip the demo. |
| Visuals blank or "can't display" | Return to the browser; scene 10 shows the same pages. |
| Timestamp frozen | The replay stopped. Do not restart it mid-talk — return to the browser. |
| Power BI unresponsive | `Alt+Tab` away and keep going. Do not wait for it. |
| Wrong monitor / mirrored display | Continue on whatever is projected; do not re-configure displays live. |

After the session: `Ctrl+C` in the replay terminal, then close Power BI.

---

## 5. What the demo is allowed to claim

* The replay is the **held-out chronological TEST partition**, one row every five
  seconds, from a synthetic dataset.
* The service runs the **exact model artifacts exported by notebooks 03 and 04**,
  verified by SHA-256 against `models/model_registry.json`.
* Power BI reads **five semantic SQL views** over DirectQuery and nothing else.
* Everything on screen is **advisory**. There is no write path to the process.

## 6. What it must not be allowed to imply

* That the dashboard is connected to a plant.
* That five seconds is the plant historian's acquisition rate.
* That the anomaly risk is a probability of failure.
* That the diagnosis has identified a confirmed root cause.
* That the laboratory has been replaced or reduced.

If a jury question drifts toward any of these, restate the boundary before
answering. It is a stronger answer than the one they were fishing for.

---

## 7. Reference

| Item | Path |
|---|---|
| Launcher | `RUN_FINAL_DEMO.ps1` (repository root) |
| Replay service | `realtime_pipeline/src/realtime_service.py` |
| View verification | `realtime_pipeline/src/verify_powerbi_views.py` |
| Migration | `realtime_pipeline/src/apply_sql_migration.py` |
| Dashboard project | `powerbi_dashboard/MAP Dryer AI Dashboard.pbip` |
| Connection settings | `realtime_pipeline/.env` (template: `.env.example`) |
| Captured pages | `final_presentation/assets/dashboard/` |

Credentials live only in Power BI Desktop's encrypted credential store on the
presenting machine. Nothing in this repository contains the password, and
nothing should be added that does.
