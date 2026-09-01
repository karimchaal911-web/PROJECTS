"""Render both dashboard pages as HTML previews from the LIVE SQL views.

Every displayed value is read from the same PostgreSQL views the Power BI
report queries (DirectQuery), and every color/status rule replicates the
DAX measures in the semantic model 1:1. Nothing is fabricated: run the
pipeline first, then this script.

Output:  powerbi_dashboard/preview/preview_page1_overview.html
         powerbi_dashboard/preview/preview_page2_diagnostics.html

These are layout previews for visual comparison against
``resources/dashboard_templates/*.png`` — the authoritative report is the
PBIP project itself.

Run:  python tools/render_dashboard_preview.py
"""

from __future__ import annotations

import html
import os
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "realtime_pipeline" / "src"))

import psycopg  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

load_dotenv(PROJECT_ROOT / "realtime_pipeline" / ".env")

OUT_DIR = PROJECT_ROOT / "powerbi_dashboard" / "preview"

# Palette — identical to tools/generate_powerbi_report.py and the TMDL
# color measures.
SIDEBAR = "#0B3B2E"
SIDEBAR_TILE = "#12684F"
SIDEBAR_ICON = "#9DBFB4"
GREEN = "#087C5B"
TEAL = "#1B918E"
GREEN_SURFACE = "#E7F4EF"
PAGE_BG = "#F3F6F4"
BORDER = "#D6E0DC"
TEXT = "#17231F"
TEXT2 = "#66756F"
AMBER = "#F2A12E"
AMBER_TEXT = "#B26A00"
AMBER_SURFACE = "#FFF0D5"
AMBER_SURFACE2 = "#FDE7C8"
RED = "#DF5558"
RED_DARK = "#C83F45"
RED_SURFACE = "#FBE2E3"
GRAY_SURFACE = "#E5E9E7"
WHITE = "#FFFFFF"

TARGET_BAND = (0.07018, 0.08074)  # measures 'Target Band Low/High' (TMDL)
MOISTURE_WATCH = (0.06904, 0.08188)  # 'Predicted/Lab Card BG' watch band (TMDL)
RISK_WARNING, RISK_CRITICAL = 0.5, 0.8

# 'DAT/Feed/Steam/Airflow/Vacuum Status' normal & watch bands (from TMDL,
# derived from the training-data reference profile quantiles).
VARIABLE_BANDS = {
    "DAT": ((166.4639, 180.9040), (156.8914, 196.4670)),
    "Feed": ((23.9570, 28.0910), (20.9770, 34.0636)),
    "Steam": ((7.9900, 8.5190), (6.3430, 9.6290)),
    "Airflow": ((22633.7815, 25130.0026), (19519.2635, 25345.5958)),
    "Vacuum": ((46.2891, 49.9760), (44.1563, 55.0516)),
}


def connect() -> psycopg.Connection:
    return psycopg.connect(
        f"host={os.getenv('DB_HOST')} port={os.getenv('DB_PORT')} "
        f"dbname={os.getenv('DB_NAME')} user={os.getenv('DB_USER')} "
        f"password={os.getenv('DB_PASSWORD')}"
    )


def fetch_state(conn: psycopg.Connection) -> dict:
    state: dict = {}
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM public.vw_dryer_latest')
        columns = [d.name for d in cur.description]
        row = cur.fetchone()
        state["latest"] = dict(zip(columns, row)) if row else {}

        cur.execute(
            'SELECT "Sample Timestamp", "Validated Absolute Error" '
            'FROM public.vw_dryer_lab_samples '
            'WHERE "Validated Absolute Error" IS NOT NULL '
            'ORDER BY "Sample Timestamp" DESC LIMIT 1'
        )
        row = cur.fetchone()
        state["validated"] = (
            {"timestamp": row[0], "abs_error": float(row[1])} if row else None
        )

        latest_ts = state["latest"].get("Timestamp")
        state["trend"] = []
        state["events"] = []
        state["contributors"] = []
        if latest_ts is not None:
            cur.execute(
                '''SELECT "Timestamp", "Predicted Final Moisture",
                          "Anomaly Risk", "Final Moisture (%%H2O)",
                          "Anomaly Detected", "Steam Pressure",
                          "Air Flow Rate ", "Wet Product Feed Rate",
                          "Dryer Air Temperature", "Vacuum"
                   FROM public.vw_dryer_dashboard_powerbi
                   WHERE "Timestamp" > %s - INTERVAL '8 hours'
                   ORDER BY "Timestamp"''',
                (latest_ts,),
            )
            state["trend"] = cur.fetchall()

        cur.execute(
            'SELECT "Event ID", "Event Start", "Event End", "Duration Min", '
            '       "Rows In Event", "Peak Timestamp", "Peak Anomaly Score", '
            '       "Peak Anomaly Risk", "Severity", "Subsystem", '
            '       "Diagnosis", "Possible Causes", '
            '       "Recommended Verification", "Predicted Moisture At Peak" '
            'FROM public.vw_dryer_anomaly_events '
            'ORDER BY "Peak Timestamp" DESC LIMIT 8'
        )
        state["events"] = cur.fetchall()

        if state["events"]:
            peak_ts = state["events"][0][5]
            cur.execute(
                'SELECT contribution_rank, feature_name, observed_value, '
                '       reference_center, deviation_percent, '
                '       deviation_direction, variable_severity, '
                '       contribution_score '
                'FROM public.vw_dryer_contributors_powerbi '
                'WHERE "Timestamp" = %s ORDER BY contribution_rank LIMIT 6',
                (peak_ts,),
            )
            state["contributors"] = cur.fetchall()

            lab_before = None
            cur.execute(
                'SELECT "Sample Timestamp", "Laboratory Moisture" '
                'FROM public.vw_dryer_lab_samples '
                'WHERE "Sample Timestamp" <= %s '
                'ORDER BY "Sample Timestamp" DESC LIMIT 1',
                (peak_ts,),
            )
            row = cur.fetchone()
            if row:
                lab_before = f"{float(row[1]):.4f} % at {row[0]:%H:%M}"
            state["event_lab_context"] = (
                lab_before or "No laboratory result before this event"
            )

        cur.execute('SELECT COUNT(*) FROM public.vw_dryer_lab_samples')
        state["lab_count"] = cur.fetchone()[0]
        cur.execute(
            'SELECT MAX("Inference Timestamp") FROM public.dryer_model_outputs'
        )
        state["last_ingest"] = cur.fetchone()[0]
    return state


# --- DAX replicas -----------------------------------------------------------

def risk_band(risk: float) -> int:
    for band, limit in enumerate((0.2, 0.35, 0.5, 0.65, 0.8)):
        if risk < limit:
            return band
    return 5


def risk_card_colors(risk: float) -> tuple[str, str]:
    bg = [WHITE, GREEN_SURFACE, AMBER_SURFACE, AMBER_SURFACE2,
          RED_SURFACE, RED_DARK][risk_band(risk)]
    fg = WHITE if risk_band(risk) >= 5 else TEXT
    return bg, fg


def severity_colors(severity: str) -> tuple[str, str]:
    table = {
        "NORMAL": (GREEN_SURFACE, GREEN),
        "LOW": (AMBER_SURFACE, AMBER_TEXT),
        "MEDIUM": (AMBER_SURFACE2, AMBER_TEXT),
        "HIGH": (RED_SURFACE, RED_DARK),
        "CRITICAL": (RED_DARK, WHITE),
        "DATA_QUALITY": (GRAY_SURFACE, TEXT2),
    }
    return table.get((severity or "").upper(), (WHITE, TEXT2))


def status_colors(status: str) -> tuple[str, str]:
    table = {
        "NORMAL": (GREEN_SURFACE, GREEN),
        "WATCH": (AMBER_SURFACE, AMBER_TEXT),
        "ANOMALY": (RED_SURFACE, RED_DARK),
        "STALE": (GRAY_SURFACE, TEXT2),
    }
    return table.get(status, (WHITE, TEXT))


def moisture_card_bg(value: float | None) -> str:
    if value is None:
        return WHITE
    if TARGET_BAND[0] <= value <= TARGET_BAND[1]:
        return GREEN_SURFACE
    if MOISTURE_WATCH[0] <= value <= MOISTURE_WATCH[1]:
        return AMBER_SURFACE
    return RED_SURFACE


def variable_status(short: str, value: float | None) -> str:
    if value is None:
        return "NO DATA"
    normal, watch = VARIABLE_BANDS[short]
    if normal[0] <= value <= normal[1]:
        return "NORMAL"
    if watch[0] <= value <= watch[1]:
        return "WATCH"
    return "HIGH"


def variable_colors(status: str) -> tuple[str, str]:
    table = {
        "NORMAL": (GREEN_SURFACE, GREEN),
        "WATCH": (AMBER_SURFACE, AMBER_TEXT),
        "HIGH": (RED_SURFACE, RED_DARK),
    }
    return table.get(status, (WHITE, TEXT2))


def freshness(last_ingest: datetime | None) -> tuple[str, str, str, float]:
    if last_ingest is None:
        return "NO DATA", RED_SURFACE, RED_DARK, float("nan")
    age_min = (datetime.now() - last_ingest).total_seconds() / 60.0
    if age_min <= 2:
        return "LIVE DATA", GREEN_SURFACE, GREEN, age_min
    if age_min <= 10:
        return "DELAYED", AMBER_SURFACE, AMBER_TEXT, age_min
    return "STALE", RED_SURFACE, RED_DARK, age_min


# --- SVG helpers ------------------------------------------------------------

def polyline(points: list[tuple[float, float]], color: str,
             width: float = 2.0, dash: str = "") -> str:
    if len(points) < 2:
        return ""
    path = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<polyline points="{path}" fill="none" stroke="{color}" '
            f'stroke-width="{width}"{dash_attr}/>')


def scale_series(rows, x_index, y_index, w, h, y_min, y_max,
                 t_min, t_max, max_points=260):
    stride = max(len(rows) // max_points, 1)
    points = []
    span = (t_max - t_min).total_seconds() or 1.0
    for row in rows[::stride]:
        value = row[y_index]
        if value is None:
            continue
        x = (row[x_index] - t_min).total_seconds() / span * w
        y = h - (float(value) - y_min) / (y_max - y_min) * h
        points.append((x, min(max(y, 0), h)))
    return points


def esc(value) -> str:
    return html.escape(str(value))


# --- Page chrome ------------------------------------------------------------

STYLE = f"""
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #DDE3DF; font-family: 'Segoe UI', Inter, sans-serif;
       display: flex; justify-content: center; padding: 20px; }}
.canvas {{ position: relative; width: 1600px; height: 900px;
           background: {PAGE_BG}; overflow: hidden; }}
.abs {{ position: absolute; }}
.card {{ background: {WHITE}; border: 1px solid {BORDER};
         border-radius: 16px;
         box-shadow: 0 1px 2px rgba(26,43,36,0.06); }}
.pill {{ border-radius: 18px; display: flex; align-items: center;
         justify-content: center; font-size: 11px; font-weight: 600;
         letter-spacing: 0.4px; }}
.kpi-label {{ font-size: 10px; font-weight: 600; color: {TEXT2};
              letter-spacing: 0.5px; }}
.kpi-value {{ font-size: 24px; font-weight: 700; color: {TEXT}; }}
.kpi-caption {{ font-size: 9.5px; color: {TEXT2}; }}
.section-title {{ font-size: 15px; font-weight: 700; color: {TEXT}; }}
.section-sub {{ font-size: 10px; color: {TEXT2}; }}
.small-label {{ font-size: 10.5px; font-weight: 600; color: {TEXT2}; }}
table {{ border-collapse: collapse; width: 100%; font-size: 11px; }}
th {{ text-align: left; color: {TEXT2}; font-weight: 600; padding: 5px 8px;
      border-bottom: 1px solid {BORDER}; font-size: 10px; }}
td {{ padding: 5px 8px; border-bottom: 1px solid #EDF1EF; }}
"""


def sidebar_html(active: int) -> str:
    icons = ""
    glyphs = [
        # bar chart, trend, magnifier, notes — consistent 2px stroke icons
        '<rect x="4" y="10" width="3" height="8"/>'
        '<rect x="10" y="6" width="3" height="12"/>'
        '<rect x="16" y="2" width="3" height="16"/>',
        '<polyline points="2,16 8,10 12,13 20,4" fill="none" '
        'stroke-width="2.4"/>',
        '<circle cx="10" cy="10" r="6" fill="none" stroke-width="2.4"/>'
        '<line x1="15" y1="15" x2="20" y2="20" stroke-width="2.4"/>',
        '<rect x="3" y="3" width="16" height="16" rx="2" fill="none" '
        'stroke-width="2.2"/><line x1="7" y1="8" x2="15" y2="8" '
        'stroke-width="2"/><line x1="7" y1="12" x2="15" y2="12" '
        'stroke-width="2"/>',
    ]
    for index, glyph in enumerate(glyphs):
        y = 114 + index * 64
        tile = (
            f'<div class="abs" style="left:17px;top:{y}px;width:52px;'
            f'height:48px;background:{SIDEBAR_TILE};border-radius:12px;">'
            f'</div>' if index == active else ""
        )
        color = WHITE if index == active else SIDEBAR_ICON
        icons += tile + (
            f'<div class="abs" style="left:31px;top:{y + 12}px;">'
            f'<svg width="24" height="24" viewBox="0 0 22 22" fill="{color}" '
            f'stroke="{color}">{glyph}</svg></div>'
        )
    return (
        f'<div class="abs" style="left:0;top:0;width:86px;height:900px;'
        f'background:{SIDEBAR};"></div>'
        f'<div class="abs" style="left:21px;top:22px;width:44px;height:44px;'
        f'background:{GREEN};border-radius:12px;display:flex;'
        f'align-items:center;justify-content:center;color:{WHITE};'
        f'font-weight:700;font-size:18px;">O</div>' + icons
    )


def header_html(title: str, subtitle: str, state: dict) -> str:
    label, pill_bg, pill_fg, _ = freshness(state["last_ingest"])
    latest_ts = state["latest"].get("Timestamp")
    ingest = state["last_ingest"]
    if latest_ts is not None and ingest is not None:
        age_min = (datetime.now() - ingest).total_seconds() / 60.0
        detail = (f"Latest {latest_ts:%Y-%m-%d %H:%M:%S} · ingested "
                  f"{age_min:.0f} min ago")
    else:
        detail = "no data received"
    return (
        f'<div class="abs" style="left:110px;top:20px;font-size:26px;'
        f'font-weight:700;color:{TEXT};">{esc(title)}</div>'
        f'<div class="abs" style="left:110px;top:58px;font-size:12px;'
        f'color:{TEXT2};">{esc(subtitle)}</div>'
        f'<div class="abs pill" style="left:1128px;top:26px;width:130px;'
        f'height:36px;background:{pill_bg};color:{pill_fg};">{label}</div>'
        f'<div class="abs pill" style="left:1272px;top:26px;width:130px;'
        f'height:36px;background:{GRAY_SURFACE};color:{TEXT};">'
        f'AUTO 60 SEC</div>'
        f'<div class="abs pill" style="left:1416px;top:26px;width:168px;'
        f'height:36px;background:{WHITE};border:1px solid {BORDER};'
        f'color:{TEXT2};font-size:8.5px;font-weight:400;padding:0 8px;'
        f'text-align:center;">{esc(detail)}</div>'
        f'<div class="abs" style="left:110px;top:80px;width:1474px;'
        f'border-bottom:1px solid {BORDER};"></div>'
    )


def wrap_page(body: str, title: str) -> str:
    return (f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
            f"<title>{esc(title)}</title><style>{STYLE}</style></head>"
            f"<body><div class='canvas'>{body}</div></body></html>")


# --- Page 1 -----------------------------------------------------------------

def build_page1(state: dict) -> str:
    latest = state["latest"]
    parts = [sidebar_html(0), header_html(
        "Soluble MAP Dryer — Operations Overview",
        "Real-time moisture prediction, process stability and anomaly "
        "supervision", state)]

    predicted = latest.get("Predicted Final Moisture")
    lab_moisture = latest.get("Latest Lab Final Moisture")
    lab_ts = latest.get("Latest Lab Sample Timestamp")
    lab_age = latest.get("Lab Result Age Min")
    risk = float(latest.get("Anomaly Risk") or 0.0)
    severity = latest.get("Severity") or "—"
    subsystem = latest.get("Likely Subsystem") or "—"
    anomaly = bool(latest.get("Anomaly Detected"))
    fresh_label, _, _, _ = freshness(state["last_ingest"])
    if fresh_label in ("STALE", "NO DATA"):
        status = "STALE"
    elif anomaly:
        status = "ANOMALY"
    elif risk >= 0.35:
        status = "WATCH"
    else:
        status = "NORMAL"

    validated = state["validated"]
    risk_bg, risk_fg = risk_card_colors(risk)
    status_bg, status_fg = status_colors(status)
    severity_bg, severity_fg = severity_colors(severity)
    error_value = validated["abs_error"] if validated else None
    if error_value is None:
        error_bg, error_fg = WHITE, TEXT2
        error_display = "Awaiting next laboratory result"
        error_caption = "No validated comparison yet"
        error_size = 12
    else:
        error_bg = (GREEN_SURFACE if error_value <= 0.05
                    else AMBER_SURFACE if error_value <= 0.10 else RED_SURFACE)
        error_fg = (GREEN if error_value <= 0.05
                    else AMBER_TEXT if error_value <= 0.10 else RED_DARK)
        error_display = f"{error_value:.4f} %"
        error_caption = f"Validated at {validated['timestamp']:%H:%M}"
        error_size = 24

    ts = latest.get("Timestamp")
    kpis = [
        ("PREDICTED MOISTURE",
         f"{predicted:.4f} %" if predicted is not None else "—",
         f"Updated {ts:%H:%M:%S}" if ts else "No prediction yet",
         moisture_card_bg(predicted), TEXT, 24),
        ("LABORATORY MOISTURE",
         f"{lab_moisture:.4f} %" if lab_moisture is not None else "—",
         (f"Sampled {lab_ts:%H:%M} · {lab_age:.0f} min ago"
          if lab_ts else "—"),
         moisture_card_bg(lab_moisture), TEXT, 24),
        ("VALIDATED ABS ERROR", error_display, error_caption,
         error_bg, error_fg, error_size),
        ("ANOMALY SCORE", f"{risk:.2f}",
         "Warning 0.50 · Critical 0.80", risk_bg, risk_fg, 24),
        ("OPERATING STATUS", status,
         {"ANOMALY": "Requires verification", "WATCH": "Monitor closely",
          "STALE": "Data not current"}.get(status, "Stable operation"),
         status_bg, status_fg, 22),
        ("SEVERITY", esc(severity), esc(subsystem)[:34],
         severity_bg, severity_fg, 22),
    ]
    for index, (label, value, caption, bg, fg, size) in enumerate(kpis):
        x = 110 + index * 248
        parts.append(
            f'<div class="abs card" style="left:{x}px;top:86px;width:234px;'
            f'height:118px;background:{bg};padding:14px 16px;">'
            f'<div class="kpi-label"'
            f'{f" style=\"color:{WHITE};opacity:0.82;\"" if bg == RED_DARK else ""}'
            f'>{label}</div>'
            f'<div class="kpi-value" style="margin-top:12px;color:{fg};'
            f'font-size:{size}px;">{value}</div>'
            f'<div class="kpi-caption" style="margin-top:8px;color:'
            f'{fg if bg == RED_DARK else TEXT2};">{caption}</div></div>'
        )

    # Trend chart with target band + lab markers + anomaly markers
    trend = state["trend"]
    chart_w, chart_h = 880, 168
    svg = ""
    if trend:
        t_min, t_max = trend[0][0], trend[-1][0]
        # Domain follows the data and the target band rather than a fixed
        # literal, so the series is always framed by what is actually plotted.
        values = [float(r[1]) for r in trend if r[1] is not None]
        values += [float(r[3]) for r in trend if r[3] is not None]
        values += [TARGET_BAND[0], TARGET_BAND[1]]
        v_lo, v_hi = min(values), max(values)
        pad = (v_hi - v_lo) * 0.18 or 0.001
        y_lo, y_hi = v_lo - pad, v_hi + pad
        band_top = chart_h - (TARGET_BAND[1] - y_lo) / (y_hi - y_lo) * chart_h
        band_bot = chart_h - (TARGET_BAND[0] - y_lo) / (y_hi - y_lo) * chart_h
        pred_pts = scale_series(trend, 0, 1, chart_w, chart_h, y_lo, y_hi,
                                t_min, t_max)
        svg = (
            f'<rect x="0" y="{band_top:.0f}" width="{chart_w}" '
            f'height="{band_bot - band_top:.0f}" fill="{GREEN_SURFACE}" '
            f'opacity="0.75"/>'
            + polyline(pred_pts, GREEN, 2.0)
        )
        span = (t_max - t_min).total_seconds() or 1.0
        for row in trend:
            if row[3] is not None:  # actual laboratory sample marker
                x = (row[0] - t_min).total_seconds() / span * chart_w
                y = chart_h - (float(row[3]) - y_lo) / (y_hi - y_lo) * chart_h
                svg += (f'<circle cx="{x:.0f}" cy="{y:.0f}" r="5" '
                        f'fill="{TEAL}" stroke="{WHITE}" stroke-width="1.5"/>')
        stride = max(len(trend) // 500, 1)
        for row in trend[::stride]:
            if row[4] and row[1] is not None:  # anomaly marker on prediction
                x = (row[0] - t_min).total_seconds() / span * chart_w
                y = chart_h - (float(row[1]) - y_lo) / (y_hi - y_lo) * chart_h
                svg += (f'<circle cx="{x:.0f}" cy="{y:.0f}" r="3" '
                        f'fill="{RED}"/>')
        axis = (f'<div style="display:flex;justify-content:space-between;'
                f'font-size:9px;color:{TEXT2};margin-top:2px;">'
                f'<span>{t_min:%H:%M}</span><span>{t_max:%H:%M}</span></div>')
    else:
        axis = ""
    parts.append(
        f'<div class="abs card" style="left:110px;top:218px;width:940px;'
        f'height:254px;padding:14px 16px;">'
        f'<div style="position:absolute;right:16px;top:12px;display:flex;'
        f'gap:8px;">'
        f'<div class="pill" style="width:74px;height:26px;'
        f'background:{GRAY_SURFACE};color:{TEXT};font-size:9.5px;">'
        f'Last 8 h</div>'
        f'<div class="pill" style="width:64px;height:26px;'
        f'background:{WHITE};border:1px solid {BORDER};color:{TEXT2};'
        f'font-size:9.5px;">1 h · 24 h</div></div>'
        f'<div class="section-title">Drying performance &amp; process-risk '
        f'trend</div>'
        f'<div class="section-sub">Predicted %H2O (line), laboratory samples '
        f'(markers), target band, anomaly markers — last 8 h</div>'
        f'<div style="margin-top:8px;display:flex;gap:14px;font-size:9.5px;'
        f'color:{TEXT2};"><span style="color:{GREEN};">■ Predicted</span>'
        f'<span style="color:{TEAL};">● Laboratory sample</span>'
        f'<span style="color:{RED};">● Anomaly</span>'
        f'<span style="color:{GREEN};opacity:0.5;">▮ Target band '
        f'{TARGET_BAND[0]:.4f}–{TARGET_BAND[1]:.4f} %</span></div>'
        f'<svg width="{chart_w}" height="{chart_h}" '
        f'style="margin-top:4px;">{svg}</svg>{axis}</div>'
    )

    # Secondary strips
    strip_series = [
        ("STEAM PRESSURE", 5), ("AIR FLOW", 6), ("WET FEED", 7),
        ("DRYER AIR TEMP", 8),
    ]
    for index, (label, column) in enumerate(strip_series):
        x = 110 + index * 238
        svg_strip = ""
        if trend:
            values = [float(r[column]) for r in trend if r[column] is not None]
            if values:
                lo, hi = min(values), max(values)
                hi = hi if hi > lo else lo + 1
                pts = scale_series(trend, 0, column, 195, 34, lo, hi,
                                   trend[0][0], trend[-1][0], 130)
                svg_strip = polyline(pts, TEAL, 1.5)
        parts.append(
            f'<div class="abs card" style="left:{x}px;top:480px;width:227px;'
            f'height:78px;padding:8px 14px;border-radius:12px;">'
            f'<div class="kpi-label" style="font-size:8.5px;">{label}</div>'
            f'<svg width="195" height="34" style="margin-top:4px;">'
            f'{svg_strip}</svg></div>'
        )

    # Current operating assessment
    gauge_color = ([GREEN, GREEN, AMBER, AMBER, RED, RED_DARK]
                   [risk_band(risk)])
    circumference = 2 * 3.14159 * 70
    arc = circumference * min(max(risk, 0.02), 1.0)
    diagnosis = latest.get("Probable Diagnosis") or "—"
    last_event = state["events"][0][5] if state["events"] else None
    model_version = latest.get("Model Version") or "—"
    parts.append(
        f'<div class="abs card" style="left:1064px;top:218px;width:520px;'
        f'height:340px;padding:14px 16px;">'
        f'<div class="section-title">Current operating assessment</div>'
        f'<div class="section-sub">AI inference from the latest process '
        f'observation</div>'
        f'<svg width="190" height="190" viewBox="0 0 190 190" '
        f'style="margin-top:12px;">'
        f'<circle cx="95" cy="95" r="70" fill="none" '
        f'stroke="{GREEN_SURFACE}" stroke-width="18"/>'
        f'<circle cx="95" cy="95" r="70" fill="none" stroke="{gauge_color}" '
        f'stroke-width="18" stroke-linecap="round" '
        f'stroke-dasharray="{arc:.0f} {circumference:.0f}" '
        f'transform="rotate(-90 95 95)"/>'
        f'<text x="95" y="92" text-anchor="middle" font-size="30" '
        f'font-weight="700" fill="{TEXT}">{risk:.2f}</text>'
        f'<text x="95" y="112" text-anchor="middle" font-size="10" '
        f'fill="{TEXT2}">anomaly score</text></svg>'
        f'<div class="pill" style="position:absolute;left:28px;top:262px;'
        f'width:166px;height:36px;background:{severity_bg};'
        f'color:{severity_fg};">{esc(severity)} SEVERITY</div>'
        f'<div style="position:absolute;left:226px;top:60px;width:278px;">'
        f'<div class="small-label">Subsystem</div>'
        f'<div style="font-size:14px;font-weight:700;color:{TEXT};'
        f'margin:2px 0 10px;">{esc(subsystem)}</div>'
        f'<div class="small-label">Diagnosis</div>'
        f'<div style="font-size:12.5px;font-weight:600;color:{TEXT};'
        f'margin:2px 0 10px;">{esc(diagnosis)}</div>'
        f'<div class="small-label">Last event</div>'
        f'<div style="font-size:12px;color:{TEXT};margin:2px 0 10px;">'
        f'{f"{last_event:%Y-%m-%d %H:%M:%S}" if last_event else "—"}</div>'
        f'<div class="small-label">Model</div>'
        f'<div style="font-size:11px;color:{TEXT2};margin-top:2px;">'
        f'{esc(model_version)}</div></div></div>'
    )

    # Critical process variables
    parts.append(
        f'<div class="abs card" style="left:110px;top:572px;width:940px;'
        f'height:312px;padding:12px 16px;">'
        f'<div class="section-title">Critical process variables</div>'
        f'<div class="section-sub">Latest values, short-term direction and '
        f'status</div></div>'
    )
    variable_defs = [
        ("DAT", "Dryer air temp.", "Dryer Air Temperature", "°C", "0.1f", 8),
        ("Feed", "Wet feed rate", "Wet Product Feed Rate", "t/h", "0.1f", 7),
        ("Steam", "Steam pressure", "Steam Pressure", "bar", "0.2f", 5),
        ("Airflow", "Air flow rate", "Air Flow Rate ", "m³/h", ",.0f", 6),
        ("Vacuum", "Vacuum", "Vacuum", "mmH2O", "0.1f", 9),
    ]
    for index, (short, label, column, unit, fmt, t_col) in enumerate(
        variable_defs
    ):
        x = 126 + index * 184
        value = latest.get(column)
        value = float(value) if value is not None else None
        vstatus = variable_status(short, value)
        bg, fg = variable_colors(vstatus)
        display = format(value, fmt) if value is not None else "—"
        delta = ""
        spark = ""
        if trend:
            values = [float(r[t_col]) for r in trend[-60:]
                      if r[t_col] is not None]
            if len(values) >= 2:
                d = values[-1] - values[0]
                delta = f"Δ {'+' if d >= 0 else ''}{d:.1f}"
            lo, hi = min(values), max(values)
            hi = hi if hi > lo else lo + 1
            pts = [( i / max(len(values) - 1, 1) * 150,
                     44 - (v - lo) / (hi - lo) * 40 + 2)
                   for i, v in enumerate(values)]
            spark = polyline(pts, fg, 1.5)
        parts.append(
            f'<div class="abs card" style="left:{x}px;top:632px;width:172px;'
            f'height:224px;background:{bg};border-radius:12px;'
            f'padding:12px 11px;">'
            f'<div class="kpi-label" style="font-size:9px;">{label}</div>'
            f'<div style="font-size:19px;font-weight:700;color:{TEXT};'
            f'margin-top:8px;">{display} <span style="font-size:11px;'
            f'font-weight:600;">{unit}</span></div>'
            f'<div style="font-size:10px;color:{TEXT2};margin-top:6px;">'
            f'{delta}</div>'
            f'<div class="pill" style="width:84px;height:22px;'
            f'background:{WHITE};color:{fg};font-size:9px;margin-top:8px;">'
            f'{vstatus}</div>'
            f'<svg width="150" height="48" style="margin-top:10px;">{spark}'
            f'</svg></div>'
        )

    # Operator guidance
    causes = latest.get("Possible Causes") or "—"
    verification = latest.get("Recommended Verification") or "—"
    parts.append(
        f'<div class="abs card" style="left:1064px;top:572px;width:520px;'
        f'height:312px;padding:14px 16px;">'
        f'<div class="section-title">Operator guidance</div>'
        f'<div class="section-sub">Explainable diagnosis and recommended '
        f'checks — advisory only</div>'
        f'<div class="small-label" style="margin-top:12px;">Possible causes'
        f'</div>'
        f'<div style="font-size:11.5px;color:{TEXT};margin-top:4px;'
        f'line-height:1.5;">{esc(causes)[:360]}</div>'
        f'<div style="border-top:1px solid {BORDER};margin:12px 0;"></div>'
        f'<div class="small-label">Recommended verification</div>'
        f'<div style="font-size:11.5px;font-weight:600;color:{TEXT};'
        f'margin-top:4px;line-height:1.5;">{esc(verification)[:330]}</div>'
        f'</div>'
    )
    parts.append(
        f'<div class="abs" style="left:110px;top:886px;font-size:8.5px;'
        f'color:{TEXT2};">Decision support only — model diagnostics are '
        f'advisory evidence, not confirmed root cause and not automatic '
        f'process control. Rendered from live SQL views '
        f'{datetime.now():%Y-%m-%d %H:%M:%S}.</div>'
    )
    return wrap_page("".join(parts), "MAP Dryer — Operations Overview")


# --- Page 2 -----------------------------------------------------------------

def build_page2(state: dict) -> str:
    parts = [sidebar_html(1), header_html(
        "Soluble MAP Dryer — Diagnostics & Root Cause",
        "Investigate abnormal events, ranked contributors and corrective "
        "verification", state)]

    # Filter bar
    filters = [("Time window", "Last 24 hours", 126, 320),
               ("Severity", "All severities", 470, 200),
               ("Subsystem", "All subsystems", 690, 220),
               ("Status", "Anomalies only", 928, 200)]
    bar = (f'<div class="abs card" style="left:110px;top:86px;width:1474px;'
           f'height:56px;"></div>')
    for label, value, x, width in filters:
        bar += (
            f'<div class="abs" style="left:{x}px;top:92px;font-size:9px;'
            f'color:{TEXT2};">{label}</div>'
            f'<div class="abs" style="left:{x}px;top:106px;width:{width}px;'
            f'font-size:12.5px;font-weight:600;color:{TEXT};">{value} '
            f'<span style="color:{TEXT2};font-size:9px;">▾</span></div>'
        )
    bar += (f'<div class="abs pill" style="left:1408px;top:96px;width:140px;'
            f'height:36px;background:{GRAY_SURFACE};color:{TEXT};'
            f'font-size:10px;">EXPORT CSV</div>')
    parts.append(bar)

    # Anomaly score timeline with severity bands
    trend = state["trend"]
    chart_w, chart_h = 880, 210
    svg = ""
    axis = ""
    if trend:
        t_min, t_max = trend[0][0], trend[-1][0]
        warn_y = chart_h - RISK_WARNING * chart_h
        crit_y = chart_h - RISK_CRITICAL * chart_h
        svg += (
            f'<rect x="0" y="0" width="{chart_w}" height="{crit_y:.0f}" '
            f'fill="{RED_SURFACE}" opacity="0.55"/>'
            f'<rect x="0" y="{crit_y:.0f}" width="{chart_w}" '
            f'height="{warn_y - crit_y:.0f}" fill="{AMBER_SURFACE}" '
            f'opacity="0.55"/>'
            f'<rect x="0" y="{warn_y:.0f}" width="{chart_w}" '
            f'height="{chart_h - warn_y:.0f}" fill="{GREEN_SURFACE}" '
            f'opacity="0.55"/>'
        )
        risk_pts = scale_series(trend, 0, 2, chart_w, chart_h, 0.0, 1.0,
                                t_min, t_max, 500)
        svg += polyline(risk_pts, GREEN, 1.8)
        span = (t_max - t_min).total_seconds() or 1.0
        for row in trend[::max(len(trend) // 800, 1)]:
            if row[4] and row[2] is not None:
                x = (row[0] - t_min).total_seconds() / span * chart_w
                y = chart_h - float(row[2]) * chart_h
                svg += (f'<circle cx="{x:.0f}" cy="{y:.0f}" r="3.5" '
                        f'fill="{RED}"/>')
        svg += (f'<text x="{chart_w - 6}" y="{crit_y - 5:.0f}" '
                f'text-anchor="end" font-size="10" fill="{RED_DARK}">'
                f'Critical</text>'
                f'<text x="{chart_w - 6}" y="{warn_y - 5:.0f}" '
                f'text-anchor="end" font-size="10" fill="{AMBER_TEXT}">'
                f'Warning</text>')
        axis = (f'<div style="display:flex;justify-content:space-between;'
                f'font-size:9px;color:{TEXT2};margin-top:2px;">'
                f'<span>{t_min:%H:%M}</span><span>{t_max:%H:%M}</span></div>')
    parts.append(
        f'<div class="abs card" style="left:110px;top:156px;width:940px;'
        f'height:300px;padding:14px 16px;">'
        f'<div class="section-title">Anomaly score timeline</div>'
        f'<div class="section-sub">Calibrated risk with severity bands and '
        f'event markers — last 8 h</div>'
        f'<svg width="{chart_w}" height="{chart_h}" style="margin-top:10px;">'
        f'{svg}</svg>{axis}</div>'
    )

    # Selected event (latest)
    events = state["events"]
    if events:
        event = events[0]
        (_, _, _, duration, _, peak_ts, _, peak_risk, severity, subsystem,
         diagnosis, causes, verification, moisture_at_peak) = event
        severity_bg, severity_fg = severity_colors(severity)
        parts.append(
            f'<div class="abs card" style="left:1064px;top:156px;'
            f'width:520px;height:300px;padding:14px 16px;">'
            f'<div class="section-title">Selected event</div>'
            f'<div class="section-sub">{peak_ts:%Y-%m-%d %H:%M:%S} · latest '
            f'anomaly</div>'
            f'<div class="pill" style="position:absolute;right:16px;'
            f'top:14px;width:150px;height:32px;background:{severity_bg};'
            f'color:{severity_fg};">{esc(severity)} SEVERITY</div>'
            f'<div class="small-label" style="margin-top:14px;">Primary '
            f'subsystem</div>'
            f'<div style="font-size:15px;font-weight:700;color:{TEXT};'
            f'margin:2px 0 8px;">{esc(subsystem)}</div>'
            f'<div class="small-label">Diagnosis</div>'
            f'<div style="font-size:12px;font-weight:600;color:{TEXT};'
            f'margin:2px 0 10px;line-height:1.4;">{esc(diagnosis)}</div>'
            f'<div style="display:flex;gap:26px;margin-top:6px;">'
            f'<div><div class="small-label">Duration</div>'
            f'<div style="font-size:13px;font-weight:700;color:{TEXT};">'
            f'{duration:.1f} min</div></div>'
            f'<div><div class="small-label">Peak score</div>'
            f'<div style="font-size:13px;font-weight:700;color:{RED_DARK};">'
            f'{peak_risk:.2f}</div></div>'
            f'<div><div class="small-label">Moisture at event</div>'
            f'<div style="font-size:13px;font-weight:700;color:{TEXT};">'
            f'{f"{moisture_at_peak:.4f} %" if moisture_at_peak is not None else "—"}'
            f'</div></div></div>'
            f'<div class="small-label" style="margin-top:10px;">Latest lab '
            f'context</div>'
            f'<div style="font-size:11px;color:{TEXT};">'
            f'{esc(state.get("event_lab_context", "—"))}</div></div>'
        )
    else:
        parts.append(
            f'<div class="abs card" style="left:1064px;top:156px;width:520px;'
            f'height:300px;padding:14px 16px;">'
            f'<div class="section-title">Selected event</div>'
            f'<div class="section-sub">No abnormal events in the selected '
            f'window.</div></div>'
        )

    # Ranked contributors
    rows_html = ""
    contributors = state["contributors"]
    if contributors:
        max_score = max(float(c[7]) for c in contributors) or 1.0
        for (rank, name, observed, center, dev_pct, direction, var_sev,
             score) in contributors:
            fraction = float(score) / max_score
            color = (RED if (var_sev or "").upper() == "HIGH"
                     else AMBER if (var_sev or "").upper() == "MEDIUM"
                     else GREEN)
            rows_html += (
                f'<div style="display:flex;align-items:center;gap:10px;'
                f'margin-top:13px;">'
                f'<div style="width:170px;font-size:11px;color:{TEXT};'
                f'text-align:right;">{esc(name)}</div>'
                f'<div style="flex:1;background:#EDF1EF;border-radius:6px;'
                f'height:14px;"><div style="width:{fraction * 100:.0f}%;'
                f'background:{color};height:14px;border-radius:6px;"></div>'
                f'</div>'
                f'<div style="width:44px;font-size:11px;font-weight:700;'
                f'color:{TEXT};">{float(score):.2f}</div>'
                f'<div style="width:120px;font-size:9.5px;color:{TEXT2};">'
                f'{esc(direction)} · obs {float(observed):,.1f} · '
                f'ref {float(center):,.1f}</div></div>'
            )
    else:
        rows_html = (f'<div style="margin-top:40px;font-size:11px;'
                     f'color:{TEXT2};">No abnormal contributors recorded '
                     f'for this selection.</div>')
    parts.append(
        f'<div class="abs card" style="left:110px;top:470px;width:720px;'
        f'height:254px;padding:14px 16px;">'
        f'<div class="section-title">Ranked abnormal contributors</div>'
        f'<div class="section-sub">Normalized deviation of the selected '
        f'anomaly — diagnostic evidence, not confirmed causality</div>'
        f'{rows_html}</div>'
    )

    # Cause analysis + event signature
    if events:
        causes_text = events[0][11] or "—"
        verification_text = events[0][12] or "—"
    else:
        causes_text = verification_text = "—"
    signature = ""
    for (rank, name, observed, center, dev_pct, direction, var_sev,
         score) in contributors[:4]:
        chip_bg, chip_fg = {
            "HIGH": (RED_SURFACE, RED_DARK),
            "MEDIUM": (AMBER_SURFACE2, AMBER_TEXT),
        }.get((var_sev or "").upper(), (GREEN_SURFACE, GREEN))
        signature += (
            f'<div style="display:flex;align-items:center;gap:8px;'
            f'margin-top:6px;">'
            f'<div style="width:150px;font-size:9.5px;color:{TEXT};">'
            f'{esc(name)}</div>'
            f'<div class="pill" style="width:74px;height:18px;'
            f'background:{chip_bg};color:{chip_fg};font-size:8.5px;">'
            f'{esc(direction)}</div>'
            f'<div style="font-size:9.5px;color:{TEXT2};">'
            f'{float(dev_pct):+.1f} %</div></div>'
        )
    parts.append(
        f'<div class="abs card" style="left:844px;top:470px;width:740px;'
        f'height:254px;padding:14px 16px;">'
        f'<div class="section-title">Cause analysis and verification</div>'
        f'<div class="section-sub">Operator-readable explanation — '
        f'diagnostic evidence, not automatic control action</div>'
        f'<div style="display:flex;gap:20px;margin-top:10px;">'
        f'<div style="width:340px;">'
        f'<div class="small-label">Possible causes</div>'
        f'<div style="font-size:10.5px;color:{TEXT};margin-top:4px;'
        f'line-height:1.45;">{esc(causes_text)[:420]}</div></div>'
        f'<div style="width:330px;">'
        f'<div class="small-label">Recommended verification</div>'
        f'<div style="font-size:10.5px;font-weight:600;color:{TEXT};'
        f'margin-top:4px;line-height:1.45;">{esc(verification_text)[:220]}'
        f'</div>'
        f'<div class="small-label" style="margin-top:10px;">Event signature '
        f'(normalized deviation)</div>{signature}</div></div></div>'
    )

    # Recent abnormal events table
    rows = ""
    for event in events:
        (_, _, _, duration, _, peak_ts, _, peak_risk, severity, subsystem,
         diagnosis, _, _, _) = event
        bg = {"HIGH": RED_SURFACE, "MEDIUM": AMBER_SURFACE2,
              "LOW": AMBER_SURFACE, "CRITICAL": RED_DARK}.get(
            (severity or "").upper(), WHITE)
        fg = {"HIGH": RED_DARK, "MEDIUM": AMBER_TEXT, "LOW": AMBER_TEXT,
              "CRITICAL": WHITE}.get((severity or "").upper(), TEXT)
        rows += (
            f'<tr style="background:{bg};color:{fg};">'
            f'<td>{peak_ts:%Y-%m-%d %H:%M:%S}</td>'
            f'<td style="font-weight:700;">ANOMALY</td>'
            f'<td>{peak_risk:.2f}</td>'
            f'<td style="font-weight:700;">{esc(severity)}</td>'
            f'<td>{esc(subsystem)}</td>'
            f'<td>{esc(diagnosis)[:70]}</td>'
            f'<td>{duration:.1f} min</td></tr>'
        )
    if not rows:
        rows = (f'<tr><td colspan="7" style="color:{TEXT2};">No abnormal '
                f'events recorded.</td></tr>')
    parts.append(
        f'<div class="abs card" style="left:110px;top:738px;width:1474px;'
        f'height:148px;padding:12px 16px;overflow:hidden;">'
        f'<div class="section-title" style="font-size:13px;">Recent abnormal '
        f'events</div>'
        f'<table style="margin-top:8px;"><tr><th>Timestamp</th><th>Status'
        f'</th><th>Score</th><th>Severity</th><th>Subsystem</th>'
        f'<th>Diagnosis</th><th>Duration</th></tr>{rows}</table></div>'
    )
    parts.append(
        f'<div class="abs" style="left:110px;top:888px;font-size:8.5px;'
        f'color:{TEXT2};">Diagnostic evidence only — verify in the field '
        f'before operational action. Rendered from live SQL views '
        f'{datetime.now():%Y-%m-%d %H:%M:%S}.</div>'
    )
    return wrap_page("".join(parts), "MAP Dryer — Diagnostics & Root Cause")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        state = fetch_state(conn)
    if not state["latest"]:
        print("No rows in vw_dryer_latest — run the pipeline first.")
        sys.exit(1)
    page1 = OUT_DIR / "preview_page1_overview.html"
    page2 = OUT_DIR / "preview_page2_diagnostics.html"
    page1.write_text(build_page1(state), encoding="utf-8")
    page2.write_text(build_page2(state), encoding="utf-8")
    print(f"Wrote {page1}")
    print(f"Wrote {page2}")
    print(
        f"State: latest={state['latest'].get('Timestamp')} "
        f"labs={state['lab_count']} events={len(state['events'])} "
        f"contributors={len(state['contributors'])}"
    )


if __name__ == "__main__":
    main()
