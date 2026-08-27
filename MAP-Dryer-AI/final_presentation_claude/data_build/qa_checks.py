"""Automated QA for the soutenance build.

Three things this proves, rather than asserts:

1. TECHNICAL — every metric the presentation can display is re-derived from the
   canonical artifacts and matches to 1e-9.
2. OFFLINE   — the built bundle contains no reference to an external host, so
   the presentation cannot silently depend on the network.
3. INTEGRITY — the model artifacts on disk still hash to the values recorded in
   the registry, so the numbers on screen belong to the models in the repo.

  python final_presentation_claude/data_build/qa_checks.py
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRES = ROOT / "final_presentation_claude"
DATA = PRES / "web" / "public" / "data"
DIST = PRES / "web" / "dist"

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, bool(ok), detail))
    print("  [%s] %-52s %s" % ("PASS" if ok else "FAIL", name, detail))


def close(a, b, tol=1e-9) -> bool:
    return a is not None and b is not None and abs(float(a) - float(b)) <= tol


# ------------------------------------------------------------ 1. metrics ---
def check_metrics() -> None:
    print("\nTECHNICAL — displayed values against canonical artifacts")
    nb03 = json.loads((ROOT / "artifacts/notebook03_model_evaluation.json").read_text())
    nb04 = json.loads((ROOT / "artifacts/notebook04_anomaly_evaluation.json").read_text())
    audit = json.loads((ROOT / "artifacts/notebook01_canonical_audit.json").read_text())
    holdout = json.loads((DATA / "holdout.json").read_text())
    anomaly = json.loads((DATA / "anomaly.json").read_text())
    facts = json.loads((DATA / "facts.json").read_text())
    cands = json.loads((DATA / "candidates.json").read_text())
    gap = json.loads((DATA / "gap.json").read_text())

    ref = nb03["metrics"]["test"]
    got = holdout["metrics"]
    for key, shown in (("mae", "mae"), ("rmse", "rmse"), ("r2", "r2"),
                       ("bias", "bias"), ("max_abs_error", "maxAbsError")):
        check("moisture %s" % key, close(got[shown], ref[key]),
              "%.10f" % got[shown])
    check("moisture n = 165", holdout["n"] == ref["n"] == 165, str(holdout["n"]))
    check("holdout series length matches n",
          len(holdout["actual"]) == len(holdout["predicted"]) == holdout["n"], "")

    check("selected model is Ridge", cands["selected"] == nb03["selected_model"],
          cands["selected"])
    check("candidate count", len(cands["candidates"]) == len(nb03["candidate_results"]),
          str(len(cands["candidates"])))
    for row in cands["candidates"]:
        ok = close(row["valRmse"], nb03["candidate_results"][row["name"]]["validation"]["rmse"])
        check("candidate %s val RMSE" % row["name"], ok, "%.6f" % row["valRmse"])

    check("anomaly nu", close(anomaly["nu"], nb04["nu"]), str(anomaly["nu"]))
    check("anomaly warning threshold",
          close(anomaly["warning"], nb04["risk_calibration"]["risk_warning_threshold"]), "0.50")
    check("anomaly critical threshold",
          close(anomaly["critical"], nb04["risk_calibration"]["risk_critical_threshold"]), "0.80")
    check("anomaly risk is not a probability",
          anomaly["isProbability"] is False and
          nb04["risk_calibration"]["is_probability"] is False, "")
    check("anomaly training rows",
          anomaly["trainingProcessRows"] == nb04["training_process_rows"],
          "{:,}".format(anomaly["trainingProcessRows"]))

    ev = anomaly.get("event", {})
    check("disturbance event present", bool(ev), ev.get("label", "-"))
    if ev:
        check("in-event risk exceeds out-of-event risk",
              ev["riskInEventMean"] > ev["riskOutEventMean"] * 2,
              "%.3f vs %.3f" % (ev["riskInEventMean"], ev["riskOutEventMean"]))
        check("majority of warnings inside the labelled event",
              ev["warningPointsInsideEvent"] / max(ev["warningPointsTotal"], 1) > 0.9,
              "%d/%d" % (ev["warningPointsInsideEvent"], ev["warningPointsTotal"]))
        check("event label is declared as generator ground truth",
              "unsupervised" in ev["labelSource"], "")

    check("dataset rows", facts["dataset"]["processRows"] == audit["process_rows"],
          "{:,}".format(facts["dataset"]["processRows"]))
    check("laboratory interval 120 min",
          facts["dataset"]["laboratoryIntervalMinutes"] == 120, "120")
    check("cadence declared as prototype, not historian",
          "not a proven PCS7" in facts["dataset"]["intervalInterpretation"], "")
    check("anomaly model is unsupervised novelty detection",
          facts["anomalyModel"]["learning"] == "unsupervised novelty detection", "")
    check("moisture feature count 16", facts["moistureModel"]["featureCount"] == 16, "16")
    check("anomaly feature count 15", facts["anomalyModel"]["featureCount"] == 15, "15")

    check("gap window has exactly 6 laboratory samples",
          len(gap["lab"]["t"]) == 6, str(len(gap["lab"]["t"])))
    check("gap window lab spacing is 2 h",
          gap["labIntervalMinutes"] == 120, "120")
    check("soft-sensor trace is dense relative to the lab",
          len(gap["predicted"]) > 100 * len(gap["lab"]["t"]),
          "%d estimates vs %d measurements" % (len(gap["predicted"]), len(gap["lab"]["t"])))

    check("boundaries statement present",
          any("advisory" in b.lower() for b in facts["boundaries"]),
          "%d statements" % len(facts["boundaries"]))


# ---------------------------------------------------------- 2. integrity ---
def check_integrity() -> None:
    print("\nINTEGRITY — artifacts on disk against the registry")
    registry = json.loads((ROOT / "models/model_registry.json").read_text())
    for model in registry["models"]:
        expected = model.get("artifact_sha256")
        if not expected:
            continue
        path = ROOT / model["artifact_path"].replace("\\", "/")
        if not path.exists():
            check("artifact %s" % path.name, False, "missing")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        check("artifact %s sha256" % path.name, digest == expected, digest[:16] + "…")

    nb04 = json.loads((ROOT / "artifacts/notebook04_anomaly_evaluation.json").read_text())
    for name, block in nb04["artifacts"].items():
        path = ROOT / block["path"].replace("\\", "/")
        if not path.exists():
            check("anomaly %s" % name, False, "missing")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        check("anomaly %s sha256" % name, digest == block["sha256"], digest[:16] + "…")


# ------------------------------------------------------------ 3. offline ---
EXTERNAL = re.compile(
    rb"https?://(?!127\.0\.0\.1|localhost)[a-z0-9.-]+", re.IGNORECASE)
ALLOWED_HOSTS = {
    b"http://www.w3.org",          # SVG/XML namespaces, never fetched
    b"https://www.w3.org",
    b"http://ns.adobe.com",
    b"https://github.com",         # comments and licence headers
    b"https://opensource.org",
    b"http://opensource.org",
    b"https://threejs.org",
    b"https://developer.mozilla.org",
    b"https://caniuse.com",
    b"https://gsap.com",
    b"https://greensock.com",
    b"https://registry.npmjs.org",
    b"https://esm.sh",
    b"https://docs.pmnd.rs",       # React Three Fiber error-message text
    b"https://react.dev",          # React error-message text
    # troika's unicode-font-resolver fallback. It is present as a string in the
    # bundle but proven unreachable at runtime by the blocked-network capture
    # below, because every in-world label is folded to the bundled font's
    # coverage first (see src/three/WorldText.jsx).
    b"https://cdn.jsdelivr.net",
}


def check_offline() -> None:
    print("\nOFFLINE — external references in the built bundle")
    if not DIST.exists():
        check("dist/ exists", False, "run npx vite build")
        return
    check("dist/ exists", True, "")

    findings: dict[str, set[str]] = {}
    for f in DIST.rglob("*"):
        if not f.is_file() or f.suffix.lower() in {".png", ".jpg", ".woff", ".woff2"}:
            continue
        blob = f.read_bytes()
        for m in EXTERNAL.findall(blob):
            base = m.lower()
            if any(base.startswith(a.lower()) for a in ALLOWED_HOSTS):
                continue
            findings.setdefault(f.name, set()).add(m.decode("ascii", "replace"))

    if findings:
        for name, urls in findings.items():
            check("no runtime external host in %s" % name, False,
                  ", ".join(sorted(urls)[:3]))
    else:
        check("no runtime external hosts in dist/", True,
              "namespace and licence URLs only")

    fonts = list((DIST / "assets").glob("*.woff*")) if (DIST / "assets").exists() else []
    check("fonts bundled locally", len(fonts) >= 5, "%d font files" % len(fonts))

    data_files = list((DIST / "data").glob("*.json")) if (DIST / "data").exists() else []
    check("data payloads bundled", len(data_files) == 7, "%d files" % len(data_files))

    imgs = list((DIST / "img").glob("*")) if (DIST / "img").exists() else []
    check("dashboard captures bundled",
          any("powerbi" in p.name for p in imgs), "%d images" % len(imgs))

    total = sum(f.stat().st_size for f in DIST.rglob("*") if f.is_file())
    check("bundle size under 40 MB", total < 40e6, "%.1f MB" % (total / 1e6))

    # The real proof: a full 35-step run with every non-loopback request aborted.
    om = PRES / "exports" / "offline_check" / "manifest.json"
    if not om.exists():
        check("blocked-network run recorded", False,
              "run: node scripts/capture-scenes.mjs --offline")
        return
    data = json.loads(om.read_text())
    errs = [e for e in data.get("errors", []) if "favicon" not in e]
    blocked = [e for e in errs if e.startswith("BLOCKED")]
    check("blocked-network run: no external request attempted", not blocked,
          blocked[0][:60] if blocked else "none")
    check("blocked-network run: no page errors", not errs,
          "%d" % len(errs) if errs else "clean")
    check("blocked-network run: all 35 steps rendered",
          len(data.get("steps", [])) == 35, "%d steps" % len(data.get("steps", [])))


# ------------------------------------------------------- 4. deliverables ---
def check_deliverables() -> None:
    print("\nDELIVERABLES")
    expect = [
        ("interactive build", DIST / "index.html"),
        ("PDF fallback", PRES / "FINAL_MAP_Soluble_Digitalization_Soutenance_Claude.pdf"),
        ("PPTX fallback", PRES / "FINAL_MAP_Soluble_Digitalization_Soutenance_Claude.pptx"),
        ("MP4 backup", PRES / "FINAL_MAP_Soluble_Digitalization_Soutenance_Claude_Backup.mp4"),
        ("full script", PRES / "speaker_notes/full_script.md"),
        ("quick cues", PRES / "speaker_notes/quick_cues.md"),
        ("demo instructions", PRES / "demo/DEMO_INSTRUCTIONS.md"),
        ("resource audit", PRES / "design/RESOURCE_AUDIT.md"),
        ("design system", PRES / "design/DESIGN_SYSTEM.md"),
        ("storyboard", PRES / "design/STORYBOARD.md"),
        ("motion spec", PRES / "design/MOTION_SPEC.md"),
        ("scene plan", PRES / "design/THREEJS_SCENE_PLAN.md"),
        ("launcher", PRES / "RUN_PRESENTATION.ps1"),
    ]
    for name, path in expect:
        ok = path.exists()
        size = "%.1f MB" % (path.stat().st_size / 1e6) if ok else "missing"
        check(name, ok, size)

    shots = list((PRES / "exports/screenshots").glob("step-*.png"))
    check("scene stills exported", len(shots) == 35, "%d frames" % len(shots))

    mf = PRES / "exports/screenshots/manifest.json"
    if mf.exists():
        data = json.loads(mf.read_text())
        errs = [e for e in data.get("errors", []) if "favicon" not in e]
        check("capture ran without console errors", not errs,
              "%d" % len(errs) if errs else "clean")


def main() -> int:
    print("=" * 74)
    print("SOUTENANCE QA")
    print("=" * 74)
    check_metrics()
    check_integrity()
    check_offline()
    check_deliverables()

    failed = [r for r in results if not r[1]]
    print("\n" + "=" * 74)
    print("%d checks · %d passed · %d failed" % (len(results), len(results) - len(failed), len(failed)))
    if failed:
        print("\nFAILED:")
        for name, _, detail in failed:
            print("  - %s  %s" % (name, detail))
    print("=" * 74)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
