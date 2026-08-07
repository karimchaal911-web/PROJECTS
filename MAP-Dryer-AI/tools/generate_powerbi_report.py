"""Regenerate both PBIR report pages to match the reference templates.

Rebuilds ``MAP Dryer AI Dashboard.Report/definition/pages`` as a
1600 × 900 layout that mirrors
``resources/dashboard_templates/dashboard_template_page_1_overview.png``
and ``..._page_2_diagnostics.png``: dark-green 86-px navigation rail,
pill-shaped status controls, six KPI cards with full-card dynamic
coloring, the drying-performance trend with laboratory sample markers,
the operating-assessment gauge, five critical-variable tiles, operator
guidance, and the diagnostics page (filter bar, risk timeline, selected
event, ranked contributors, cause analysis, events table).

All displayed values bind to measures/columns of the DirectQuery model —
no literal data values are embedded. The previous pages are copied to
``POWERBI DASHBOARD/backup_report_pages_<date>/`` the first time this
script runs. Rerunning is deterministic (stable visual names).
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = PROJECT_ROOT / "POWERBI DASHBOARD" / "MAP Dryer AI Dashboard.Report"
PAGES_DIR = REPORT_DIR / "definition" / "pages"
THEME_PATH = (
    REPORT_DIR / "StaticResources" / "RegisteredResources"
    / "OCPIndustrialTheme.json"
)
BACKUP_DIR = PROJECT_ROOT / "POWERBI DASHBOARD" / "backup_report_pages_20260806"

PAGE1 = "0a1b2c3d4e5f60718290"
PAGE2 = "1b2c3d4e5f60718290a1"

VISUAL_SCHEMA = (
    "https://developer.microsoft.com/json-schemas/fabric/item/report/"
    "definition/visualContainer/2.11.0/schema.json"
)
PAGE_SCHEMA = (
    "https://developer.microsoft.com/json-schemas/fabric/item/report/"
    "definition/page/2.1.0/schema.json"
)
PAGES_SCHEMA = (
    "https://developer.microsoft.com/json-schemas/fabric/item/report/"
    "definition/pagesMetadata/1.1.0/schema.json"
)

DASH = "vw_dryer_dashboard_powerbi"
LAB = "vw_dryer_lab_samples"
EVENTS = "vw_dryer_anomaly_events"
CONTRIB = "vw_dryer_contributors_powerbi"

# Template palette
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
RED = "#DF5558"
BAND = "#BFD8CE"
WHITE = "#FFFFFF"


def vid(page: str, key: str) -> str:
    return hashlib.md5(f"{page}/{key}".encode()).hexdigest()[:20]


def lit(value: str) -> dict:
    return {"expr": {"Literal": {"Value": value}}}


def solid(hex_color: str) -> dict:
    return {"solid": {"color": lit(f"'{hex_color}'")}}


def solid_measure(entity: str, prop: str) -> dict:
    return {
        "solid": {
            "color": {
                "expr": {
                    "Measure": {
                        "Expression": {"SourceRef": {"Entity": entity}},
                        "Property": prop,
                    }
                }
            }
        }
    }


def field(entity: str, prop: str, kind: str) -> dict:
    return {
        kind: {
            "Expression": {"SourceRef": {"Entity": entity}},
            "Property": prop,
        }
    }


def projection(entity: str, prop: str, kind: str = "Measure",
               active: bool = False) -> dict:
    out = {
        "field": field(entity, prop, kind),
        "queryRef": f"{entity}.{prop}",
        "nativeQueryRef": prop,
    }
    if active:
        out["active"] = True
    return out


def container_objects(
    title: str | None = None,
    title_color: str = TEXT2,
    title_size: int = 10,
    background: str | None = WHITE,
    background_measure: tuple[str, str] | None = None,
    radius: int = 16,
    border: bool = True,
    shadow: bool = False,
) -> dict:
    objs: dict = {}
    if title is None:
        objs["title"] = [{"properties": {"show": lit("false")}}]
    else:
        objs["title"] = [{
            "properties": {
                "show": lit("true"),
                "text": lit(f"'{title}'"),
                "fontColor": solid(title_color),
                "fontSize": lit(f"{title_size}D"),
            }
        }]
    if background_measure is not None:
        objs["background"] = [{
            "properties": {
                "show": lit("true"),
                "color": solid_measure(*background_measure),
                "transparency": lit("0D"),
            }
        }]
    elif background is not None:
        objs["background"] = [{
            "properties": {
                "show": lit("true"),
                "color": solid(background),
                "transparency": lit("0D"),
            }
        }]
    else:
        objs["background"] = [{"properties": {"show": lit("false")}}]
    if border:
        objs["border"] = [{
            "properties": {
                "show": lit("true"),
                "color": solid(BORDER),
                "radius": lit(f"{radius}D"),
            }
        }]
    else:
        objs["border"] = [{"properties": {"show": lit("false")}}]
    if shadow:
        objs["dropShadow"] = [{
            "properties": {"show": lit("true")}
        }]
    return objs


class Page:
    def __init__(self, page_id: str, display_name: str):
        self.page_id = page_id
        self.display_name = display_name
        self.visuals: list[dict] = []
        self.z = 0

    def add(self, key: str, x: int, y: int, w: int, h: int,
            visual: dict) -> None:
        self.z += 1
        self.visuals.append({
            "$schema": VISUAL_SCHEMA,
            "name": vid(self.page_id, key),
            "position": {
                "x": x, "y": y, "z": self.z * 100,
                "height": h, "width": w,
                "tabOrder": self.z * 100,
            },
            "visual": visual,
        })

    def write(self) -> None:
        page_dir = PAGES_DIR / self.page_id
        visuals_dir = page_dir / "visuals"
        if visuals_dir.exists():
            shutil.rmtree(visuals_dir)
        page_dir.mkdir(parents=True, exist_ok=True)

        page_json = {
            "$schema": PAGE_SCHEMA,
            "name": self.page_id,
            "displayName": self.display_name,
            "displayOption": "FitToPage",
            "height": 900,
            "width": 1600,
            "objects": {
                "background": [{
                    "properties": {
                        "color": solid(PAGE_BG),
                        "transparency": lit("0L"),
                    }
                }],
                "pageRefresh": [{
                    "properties": {
                        "show": lit("true"),
                        "refreshType": lit("1D"),
                        "duration": lit("60D"),
                    }
                }],
            },
        }
        (page_dir / "page.json").write_text(
            json.dumps(page_json, indent=2), encoding="utf-8"
        )
        for visual in self.visuals:
            vdir = visuals_dir / visual["name"]
            vdir.mkdir(parents=True, exist_ok=True)
            (vdir / "visual.json").write_text(
                json.dumps(visual, indent=2), encoding="utf-8"
            )


# ---------------------------------------------------------------------------
# Visual builders
# ---------------------------------------------------------------------------

def shape(fill: str, radius: int = 16, border_color: str | None = None) -> dict:
    line_props: dict = {
        "roundEdge": lit(f"{radius}D"),
        "lineColor": solid(border_color or fill),
        "transparency": lit("0D" if border_color else "100D"),
        "weight": lit("1D"),
    }
    return {
        "visualType": "basicShape",
        "drillFilterOtherVisuals": True,
        "objects": {
            "fill": [{
                "properties": {
                    "show": lit("true"),
                    "fillColor": solid(fill),
                    "transparency": lit("0D"),
                }
            }],
            "line": [{"properties": line_props}],
        },
        "visualContainerObjects": {
            "title": [{"properties": {"show": lit("false")}}],
            "background": [{"properties": {"show": lit("false")}}],
            "border": [{"properties": {"show": lit("false")}}],
        },
    }


def textbox(runs: list[tuple[str, str, str, bool]],
            vertical_center: bool = False) -> dict:
    paragraphs = [
        {
            "textRuns": [{
                "value": value,
                "textStyle": {
                    "fontSize": size,
                    "color": color,
                    **({"fontWeight": "bold"} if bold else {}),
                },
            }]
        }
        for value, size, color, bold in runs
    ]
    props: dict = {"paragraphs": paragraphs}
    if vertical_center:
        props["verticalAlignment"] = "middle"
    return {
        "visualType": "textbox",
        "drillFilterOtherVisuals": True,
        "objects": {"general": [{"properties": props}]},
        "visualContainerObjects": {
            "title": [{"properties": {"show": lit("false")}}],
            "background": [{"properties": {"show": lit("false")}}],
            "border": [{"properties": {"show": lit("false")}}],
        },
    }


def card(
    entity: str,
    value_measure: str,
    title: str | None = None,
    value_size: int = 22,
    value_color: str | None = TEXT,
    value_color_measure: tuple[str, str] | None = None,
    background: str | None = WHITE,
    background_measure: tuple[str, str] | None = None,
    radius: int = 16,
    border: bool = True,
    word_wrap: bool = False,
) -> dict:
    label_props: dict = {"fontSize": lit(f"{value_size}D")}
    if value_color_measure is not None:
        label_props["color"] = solid_measure(*value_color_measure)
    elif value_color is not None:
        label_props["color"] = solid(value_color)
    if word_wrap:
        label_props["wordWrap"] = lit("true")
    return {
        "visualType": "card",
        "drillFilterOtherVisuals": True,
        "query": {
            "queryState": {
                "Values": {
                    "projections": [projection(entity, value_measure)]
                }
            }
        },
        "objects": {
            "categoryLabels": [{"properties": {"show": lit("false")}}],
            "labels": [{"properties": label_props}],
        },
        "visualContainerObjects": container_objects(
            title=title,
            background=background,
            background_measure=background_measure,
            radius=radius,
            border=border,
        ),
    }


def line_chart(
    category: tuple[str, str],
    series: list[tuple[str, str]],
    colors: dict[str, str],
    title: str | None,
    markers_only: list[str] = (),
    dashed: list[str] = (),
    transparent: bool = False,
    legend: bool = True,
    y_start: float | None = None,
    y_end: float | None = None,
    axes: bool = True,
) -> dict:
    data_points = [
        {
            "properties": {"fill": solid(colors[prop])},
            "selector": {"metadata": f"{entity}.{prop}"},
        }
        for entity, prop in series
        if prop in colors
    ]
    line_styles: list[dict] = [{
        "properties": {
            "showMarker": lit("false"),
            "strokeWidth": lit("2D"),
        }
    }]
    for entity, prop in series:
        if prop in markers_only:
            line_styles.append({
                "properties": {
                    "showMarker": lit("true"),
                    "strokeWidth": lit("0D"),
                    "markerSize": lit("4D"),
                },
                "selector": {"metadata": f"{entity}.{prop}"},
            })
        elif prop in dashed:
            line_styles.append({
                "properties": {
                    "lineStyle": lit("'dashed'"),
                    "strokeWidth": lit("1D"),
                    "showMarker": lit("false"),
                },
                "selector": {"metadata": f"{entity}.{prop}"},
            })
    objects: dict = {
        "legend": [{
            "properties": {
                "show": lit("true" if legend else "false"),
                "position": lit("'Top'"),
                "fontSize": lit("8D"),
            }
        }],
        "lineStyles": line_styles,
        "dataPoint": data_points,
        "categoryAxis": [{
            "properties": {
                "show": lit("true" if axes else "false"),
                "fontSize": lit("8D"),
                "labelColor": solid(TEXT2),
                "showAxisTitle": lit("false"),
            }
        }],
    }
    value_axis_props: dict = {
        "show": lit("true" if axes else "false"),
        "fontSize": lit("8D"),
        "labelColor": solid(TEXT2),
        "showAxisTitle": lit("false"),
        "gridlineColor": solid("#E9EFEC"),
    }
    if y_start is not None:
        value_axis_props["start"] = lit(f"{y_start}D")
    if y_end is not None:
        value_axis_props["end"] = lit(f"{y_end}D")
    objects["valueAxis"] = [{"properties": value_axis_props}]

    return {
        "visualType": "lineChart",
        "drillFilterOtherVisuals": True,
        "query": {
            "queryState": {
                "Category": {
                    "projections": [
                        projection(category[0], category[1], "Column",
                                   active=True)
                    ]
                },
                "Y": {
                    "projections": [
                        projection(entity, prop) for entity, prop in series
                    ]
                },
            },
            "sortDefinition": {
                "sort": [{
                    "field": field(category[0], category[1], "Column"),
                    "direction": "Ascending",
                }],
                "isDefaultSort": True,
            },
        },
        "objects": objects,
        "visualContainerObjects": container_objects(
            title=title,
            background=None if transparent else WHITE,
            border=not transparent,
        ),
    }


def build_theme() -> dict:
    return {
        "name": "OCPIndustrialTheme.json",
        "dataColors": [
            GREEN, TEAL, AMBER, RED, "#0B3B2E", "#66756F",
            "#8FBCAD", "#C83F45",
        ],
        "background": WHITE,
        "foreground": TEXT,
        "tableAccent": GREEN,
        "good": GREEN,
        "neutral": AMBER,
        "bad": "#C83F45",
        "textClasses": {
            "callout": {"fontSize": 22, "fontFace": "Segoe UI",
                        "color": TEXT},
            "title": {"fontSize": 12, "fontFace": "Segoe UI Semibold",
                      "color": TEXT},
            "header": {"fontSize": 10, "fontFace": "Segoe UI",
                       "color": TEXT2},
            "label": {"fontSize": 9, "fontFace": "Segoe UI",
                      "color": TEXT2},
        },
        "visualStyles": {
            "*": {
                "*": {
                    "background": [{
                        "show": True, "color": {"solid": {"color": WHITE}},
                        "transparency": 0,
                    }],
                    "border": [{
                        "show": True,
                        "color": {"solid": {"color": BORDER}},
                        "radius": 16,
                    }],
                    "dropShadow": [{
                        "show": True,
                        "color": {"solid": {"color": "#1A2B2410"}},
                        "position": "Outer",
                        "preset": "BottomRight",
                    }],
                    "outspacePane": [{}],
                }
            },
            "page": {
                "*": {
                    "background": [{
                        "color": {"solid": {"color": PAGE_BG}},
                        "transparency": 0,
                    }]
                }
            },
        },
    }


# ---------------------------------------------------------------------------
# Shared page furniture
# ---------------------------------------------------------------------------

def add_chrome(page: Page, title: str, subtitle: str, active_icon: int) -> None:
    page.add("sidebar", 0, 0, 86, 900, shape(SIDEBAR, radius=0))
    page.add("logo", 21, 22, 44, 44, shape(GREEN, radius=12))
    page.add(
        "logo-text", 21, 28, 44, 34,
        textbox([("O", "14pt", WHITE, True)]),
    )
    icons = ["▦", "◉", "◌", "▤"]
    for index, glyph in enumerate(icons):
        y = 120 + index * 64
        if index == active_icon:
            page.add(f"nav-tile-{index}", 17, y - 6, 52, 48,
                     shape(SIDEBAR_TILE, radius=12))
            color = WHITE
        else:
            color = SIDEBAR_ICON
        page.add(
            f"nav-icon-{index}", 21, y, 44, 36,
            textbox([(glyph, "12pt", color, False)]),
        )

    page.add(
        "header-title", 110, 16, 860, 40,
        textbox([(title, "20pt", TEXT, True)]),
    )
    page.add(
        "header-subtitle", 110, 56, 860, 22,
        textbox([(subtitle, "10pt", TEXT2, False)]),
    )
    page.add(
        "pill-live", 1128, 26, 130, 36,
        card(DASH, "Freshness Pill Label", value_size=10,
             value_color_measure=(DASH, "Freshness Pill FG"),
             background_measure=(DASH, "Freshness Pill BG"), radius=18),
    )
    page.add(
        "pill-auto", 1272, 26, 130, 36,
        card(DASH, "Refresh Pill Label", value_size=10,
             value_color=TEXT2, background=PAGE_BG, radius=18),
    )
    page.add(
        "pill-fresh", 1416, 26, 168, 36,
        card(DASH, "Freshness Detail Display", value_size=8,
             value_color=TEXT2, background=WHITE, radius=18),
    )


# ---------------------------------------------------------------------------
# Page 1 — Operations Overview
# ---------------------------------------------------------------------------

def build_page1() -> Page:
    page = Page(PAGE1, "Operations Overview")
    add_chrome(
        page,
        "Soluble MAP Dryer — Operations Overview",
        "Real-time moisture prediction, process stability and anomaly "
        "supervision",
        active_icon=0,
    )

    # KPI row -------------------------------------------------------------
    kpis = [
        ("kpi-pred", "PREDICTED MOISTURE", "Predicted Now Display",
         "Predicted Now Caption", (DASH, "Predicted Card BG"), None),
        ("kpi-lab", "LABORATORY MOISTURE", "Lab Last Moisture Display",
         "Lab Sample Time Display", (DASH, "Lab Card BG"), None),
        ("kpi-err", "VALIDATED ABS ERROR", "Validated Error Display",
         "Validated Error Caption", (DASH, "Error Card BG"),
         (DASH, "Error Card FG")),
        ("kpi-risk", "ANOMALY SCORE", "Latest Anomaly Risk Display",
         None, (DASH, "Card BG (Risk)"), (DASH, "Card FG (Risk)")),
        ("kpi-status", "OPERATING STATUS", "Operating Status",
         "Operating Status Caption", (DASH, "Status BG (Latest)"),
         (DASH, "Status FG (Latest)")),
        ("kpi-sev", "SEVERITY", "Latest Severity",
         "Severity Caption", (DASH, "Severity BG (Latest)"),
         (DASH, "Severity FG (Latest)")),
    ]
    kpi_w = 234
    for index, (key, label, value, caption, bg, fg) in enumerate(kpis):
        x = 110 + index * (kpi_w + 14)
        page.add(
            key, x, 86, kpi_w, 118,
            card(DASH, value, title=label, value_size=20,
                 value_color=None if fg else TEXT,
                 value_color_measure=fg,
                 background_measure=bg),
        )
        if caption:
            page.add(
                key + "-cap", x + 8, 168, kpi_w - 16, 30,
                card(DASH, caption, value_size=8, value_color=TEXT2,
                     background=None, border=False),
            )
    page.add(
        "kpi-risk-cap", 110 + 3 * (kpi_w + 14) + 8, 168, kpi_w - 16, 30,
        textbox([("Warning 0.50 · Critical 0.80", "8pt", TEXT2, False)]),
    )

    # Drying-performance trend -------------------------------------------
    # Time-window selection (1 h / 8 h / 24 h …) — a relative-time slicer
    # in the card's top-right corner, where the template shows its pills.
    page.add(
        "trend-window", 806, 226, 236, 34,
        slicer(DASH, "Timestamp", "Relative"),
    )
    page.add(
        "trend-main", 110, 218, 940, 254,
        line_chart(
            (DASH, "Timestamp"),
            [
                (DASH, "Predicted Moisture (Model)"),
                (DASH, "Moisture Lab Markers"),
                (DASH, "Predicted Moisture (Anomalous)"),
                (DASH, "Target Band Low"),
                (DASH, "Target Band High"),
            ],
            colors={
                "Predicted Moisture (Model)": GREEN,
                "Moisture Lab Markers": TEAL,
                "Predicted Moisture (Anomalous)": RED,
                "Target Band Low": BAND,
                "Target Band High": BAND,
            },
            title=(
                "DRYING PERFORMANCE & PROCESS-RISK TREND — PREDICTED %H2O, "
                "LAB SAMPLES & TARGET BAND"
            ),
            markers_only=["Moisture Lab Markers",
                          "Predicted Moisture (Anomalous)"],
            dashed=["Target Band Low", "Target Band High"],
        ),
    )
    strips = [
        ("strip-steam", "Steam Pressure (Trend)", "STEAM PRESSURE"),
        ("strip-air", "Air Flow (Trend)", "AIR FLOW"),
        ("strip-feed", "Feed Rate (Trend)", "WET FEED"),
        ("strip-temp", "Dryer Temp (Trend)", "DRYER AIR TEMP"),
    ]
    strip_w = 227
    for index, (key, measure_name, label) in enumerate(strips):
        x = 110 + index * (strip_w + 11)
        page.add(
            key, x, 480, strip_w, 78,
            line_chart(
                (DASH, "Timestamp"), [(DASH, measure_name)],
                colors={measure_name: TEAL},
                title=label, legend=False, axes=False,
            ),
        )

    # Current operating assessment ---------------------------------------
    page.add("assess-bg", 1064, 218, 520, 340, shape(WHITE, 16, BORDER))
    page.add(
        "assess-title", 1080, 228, 300, 24,
        textbox([("Current operating assessment", "12pt", TEXT, True)]),
    )
    page.add(
        "assess-sub", 1080, 252, 320, 18,
        textbox([("AI inference from the latest process observation",
                  "8pt", TEXT2, False)]),
    )
    page.add(
        "assess-donut", 1080, 278, 190, 190,
        {
            "visualType": "donutChart",
            "drillFilterOtherVisuals": True,
            "query": {
                "queryState": {
                    "Y": {
                        "projections": [
                            projection(DASH, "Risk Intensity"),
                            projection(DASH, "Risk Gauge Remainder"),
                        ]
                    }
                }
            },
            "objects": {
                "legend": [{"properties": {"show": lit("false")}}],
                "labels": [{"properties": {"show": lit("false")}}],
                "dataPoint": [
                    {
                        "properties": {
                            "fill": solid_measure(DASH, "Risk Gauge Color")
                        },
                        "selector": {
                            "metadata": f"{DASH}.Risk Intensity"
                        },
                    },
                    {
                        "properties": {"fill": solid(GREEN_SURFACE)},
                        "selector": {
                            "metadata": f"{DASH}.Risk Gauge Remainder"
                        },
                    },
                ],
            },
            "visualContainerObjects": container_objects(
                title=None, background=None, border=False
            ),
        },
    )
    page.add(
        "assess-score", 1110, 348, 130, 50,
        card(DASH, "Latest Anomaly Risk Display", value_size=20,
             background=None, border=False),
    )
    page.add(
        "assess-score-cap", 1110, 392, 130, 20,
        textbox([("anomaly score", "8pt", TEXT2, False)]),
    )
    page.add(
        "assess-sev-pill", 1092, 486, 166, 36,
        card(DASH, "Latest Severity", value_size=11,
             value_color_measure=(DASH, "Severity FG (Latest)"),
             background_measure=(DASH, "Severity BG (Latest)"), radius=18),
    )
    page.add(
        "assess-detail", 1290, 278, 278, 244,
        {
            "visualType": "multiRowCard",
            "drillFilterOtherVisuals": True,
            "query": {
                "queryState": {
                    "Values": {
                        "projections": [
                            projection(DASH, "Latest Subsystem"),
                            projection(DASH, "Latest Diagnosis"),
                            projection(EVENTS, "Event Sel Time Display"),
                            projection(DASH, "Lab Age Display"),
                            projection(DASH, "Model Version Display"),
                        ]
                    }
                }
            },
            "objects": {
                "dataLabels": [{
                    "properties": {
                        "fontSize": lit("11D"), "color": solid(TEXT),
                    }
                }],
                "categoryLabels": [{
                    "properties": {
                        "show": lit("true"), "fontSize": lit("8D"),
                        "color": solid(TEXT2),
                    }
                }],
                "card": [{
                    "properties": {
                        "outline": lit("'None'"),
                        "barShow": lit("false"),
                    }
                }],
            },
            "visualContainerObjects": container_objects(
                title=None, background=None, border=False
            ),
        },
    )

    # Critical process variables -----------------------------------------
    page.add("vars-bg", 110, 572, 940, 312, shape(WHITE, 16, BORDER))
    page.add(
        "vars-title", 126, 582, 400, 24,
        textbox([("Critical process variables", "12pt", TEXT, True)]),
    )
    page.add(
        "vars-sub", 126, 606, 400, 18,
        textbox([("Latest values, short-term direction and status",
                  "8pt", TEXT2, False)]),
    )
    variables = [
        ("var-dat", "DRYER AIR TEMP", "DAT"),
        ("var-feed", "WET FEED RATE", "Feed"),
        ("var-steam", "STEAM PRESSURE", "Steam"),
        ("var-air", "AIR FLOW RATE", "Airflow"),
        ("var-vac", "VACUUM", "Vacuum"),
    ]
    var_w = 172
    for index, (key, label, short) in enumerate(variables):
        x = 126 + index * (var_w + 12)
        page.add(
            key, x, 632, var_w, 118,
            card(DASH, f"{short} Value Display", title=label,
                 value_size=15,
                 value_color_measure=(DASH, f"{short} Card FG"),
                 background_measure=(DASH, f"{short} Card BG"), radius=12),
        )
        page.add(
            key + "-delta", x, 754, var_w, 26,
            card(DASH, f"{short} Delta Display", value_size=8,
                 value_color_measure=(DASH, f"{short} Card FG"),
                 background=None, border=False),
        )
        page.add(
            key + "-spark", x, 782, var_w, 74,
            line_chart(
                (DASH, "Timestamp"),
                [(DASH, {
                    "DAT": "Dryer Temp (Trend)",
                    "Feed": "Feed Rate (Trend)",
                    "Steam": "Steam Pressure (Trend)",
                    "Airflow": "Air Flow (Trend)",
                    "Vacuum": "Vacuum (Trend)",
                }[short])],
                colors={
                    "Dryer Temp (Trend)": GREEN,
                    "Feed Rate (Trend)": GREEN,
                    "Steam Pressure (Trend)": GREEN,
                    "Air Flow (Trend)": GREEN,
                    "Vacuum (Trend)": GREEN,
                },
                title=None, legend=False, axes=False, transparent=True,
            ),
        )

    # Operator guidance ----------------------------------------------------
    page.add("guide-bg", 1064, 572, 520, 312, shape(WHITE, 16, BORDER))
    page.add(
        "guide-title", 1080, 582, 300, 24,
        textbox([("Operator guidance", "12pt", TEXT, True)]),
    )
    page.add(
        "guide-sub", 1080, 606, 420, 18,
        textbox([("Explainable diagnosis and recommended checks — advisory "
                  "only", "8pt", TEXT2, False)]),
    )
    page.add(
        "guide-causes-label", 1080, 632, 200, 18,
        textbox([("Possible causes", "9pt", TEXT2, True)]),
    )
    page.add(
        "guide-causes", 1080, 650, 488, 92,
        card(DASH, "Latest Possible Causes", value_size=10,
             background=None, border=False, word_wrap=True),
    )
    page.add(
        "guide-verif-label", 1080, 748, 300, 18,
        textbox([("Recommended verification", "9pt", TEXT2, True)]),
    )
    page.add(
        "guide-verif", 1080, 766, 488, 106,
        card(DASH, "Latest Recommended Verification", value_size=10,
             background=None, border=False, word_wrap=True),
    )

    page.add(
        "footer", 110, 884, 1474, 14,
        textbox([("Decision support only — model diagnostics are advisory "
                  "evidence, not confirmed root cause and not automatic "
                  "process control.", "7pt", TEXT2, False)]),
    )
    return page


# ---------------------------------------------------------------------------
# Page 2 — Diagnostics & Root Cause
# ---------------------------------------------------------------------------

def slicer(entity: str, prop: str, mode: str = "Dropdown") -> dict:
    return {
        "visualType": "slicer",
        "drillFilterOtherVisuals": True,
        "query": {
            "queryState": {
                "Values": {
                    "projections": [
                        projection(entity, prop, "Column", active=True)
                    ]
                }
            }
        },
        "objects": {
            "data": [{"properties": {"mode": lit(f"'{mode}'")}}],
            "general": [{"properties": {}}],
        },
        "visualContainerObjects": container_objects(
            title=None, background=None, border=False
        ),
    }


def build_page2() -> Page:
    page = Page(PAGE2, "Diagnostics & Root Cause")
    add_chrome(
        page,
        "Soluble MAP Dryer — Diagnostics & Root Cause",
        "Investigate abnormal events, ranked contributors and corrective "
        "verification",
        active_icon=1,
    )

    # Filter bar -----------------------------------------------------------
    page.add("filter-bg", 110, 86, 1474, 56, shape(WHITE, 16, BORDER))
    filter_labels = [
        ("flt-time-label", 126, 90, "Time window"),
        ("flt-sev-label", 470, 90, "Severity"),
        ("flt-sub-label", 690, 90, "Subsystem"),
        ("flt-status-label", 928, 90, "Status"),
    ]
    for key, x, y, label in filter_labels:
        page.add(key, x, y, 180, 16,
                 textbox([(label, "7pt", TEXT2, False)]))
    page.add("flt-time", 126, 106, 320, 32,
             slicer(DASH, "Timestamp", "Between"))
    page.add("flt-sev", 470, 106, 200, 32, slicer(EVENTS, "Severity"))
    page.add("flt-sub", 690, 106, 220, 32, slicer(EVENTS, "Subsystem"))
    page.add("flt-status", 928, 106, 200, 32,
             slicer(DASH, "Anomaly Status"))
    page.add(
        "flt-export", 1220, 100, 348, 36,
        textbox([("EXPORT CSV — open the events table's ··· menu",
                  "8pt", TEXT2, True)]),
    )

    # Anomaly score timeline ----------------------------------------------
    page.add(
        "timeline", 110, 156, 940, 300,
        line_chart(
            (DASH, "Timestamp"),
            [
                (DASH, "Risk (Trend)"),
                (DASH, "Risk (Anomalous)"),
                (DASH, "Timeline Selected Marker"),
                (DASH, "Warning Threshold"),
                (DASH, "Critical Threshold"),
            ],
            colors={
                "Risk (Trend)": GREEN,
                "Risk (Anomalous)": RED,
                "Timeline Selected Marker": "#17231F",
                "Warning Threshold": AMBER,
                "Critical Threshold": "#C83F45",
            },
            title=("ANOMALY SCORE TIMELINE — CALIBRATED RISK, EVENT MARKERS "
                   "AND SEVERITY THRESHOLDS"),
            markers_only=["Risk (Anomalous)", "Timeline Selected Marker"],
            dashed=["Warning Threshold", "Critical Threshold"],
            y_start=0.0, y_end=1.0,
        ),
    )

    # Selected event -------------------------------------------------------
    page.add("event-bg", 1064, 156, 520, 300, shape(WHITE, 16, BORDER))
    page.add(
        "event-title", 1080, 166, 200, 24,
        textbox([("Selected event", "12pt", TEXT, True)]),
    )
    page.add(
        "event-time", 1080, 190, 280, 20,
        card(EVENTS, "Event Sel Time Display", value_size=9,
             value_color=TEXT2, background=None, border=False),
    )
    page.add(
        "event-sev-pill", 1400, 166, 168, 34,
        card(EVENTS, "Event Sel Severity", value_size=10,
             value_color_measure=(EVENTS, "Event Sel Severity Pill FG"),
             background_measure=(EVENTS, "Event Sel Severity Pill BG"),
             radius=17),
    )
    page.add(
        "event-detail", 1080, 214, 488, 234,
        {
            "visualType": "multiRowCard",
            "drillFilterOtherVisuals": True,
            "query": {
                "queryState": {
                    "Values": {
                        "projections": [
                            projection(EVENTS, "Event Sel Subsystem"),
                            projection(EVENTS, "Event Sel Diagnosis"),
                            projection(EVENTS, "Event Sel Duration Display"),
                            projection(EVENTS, "Event Sel Peak Risk Display"),
                            projection(EVENTS, "Event Sel Moisture Display"),
                            projection(EVENTS, "Event Sel Lab Context"),
                        ]
                    }
                }
            },
            "objects": {
                "dataLabels": [{
                    "properties": {
                        "fontSize": lit("10D"), "color": solid(TEXT),
                    }
                }],
                "categoryLabels": [{
                    "properties": {
                        "show": lit("true"), "fontSize": lit("8D"),
                        "color": solid(TEXT2),
                    }
                }],
                "card": [{
                    "properties": {
                        "outline": lit("'None'"), "barShow": lit("false"),
                    }
                }],
            },
            "visualContainerObjects": container_objects(
                title=None, background=None, border=False
            ),
        },
    )

    # Ranked contributors --------------------------------------------------
    page.add(
        "contributors", 110, 470, 720, 254,
        {
            "visualType": "barChart",
            "drillFilterOtherVisuals": True,
            "query": {
                "queryState": {
                    "Category": {
                        "projections": [
                            projection(CONTRIB, "Contributor Name",
                                       "Column", active=True)
                        ]
                    },
                    "Y": {
                        "projections": [
                            projection(CONTRIB, "Contribution Score Value")
                        ]
                    },
                    "Tooltips": {
                        "projections": [
                            projection(CONTRIB, "Observed Value", "Column"),
                            projection(CONTRIB, "Deviation Direction",
                                       "Column"),
                            projection(CONTRIB, "Deviation Percent",
                                       "Column"),
                        ]
                    },
                },
                "sortDefinition": {
                    "sort": [{
                        "field": field(CONTRIB, "Contribution Score Value",
                                       "Measure"),
                        "direction": "Descending",
                    }],
                    "isDefaultSort": True,
                },
            },
            "objects": {
                "dataPoint": [{
                    "properties": {
                        "fill": solid_measure(CONTRIB,
                                              "Contributor Bar Color")
                    }
                }],
                "labels": [{
                    "properties": {
                        "show": lit("true"), "fontSize": lit("8D"),
                        "color": solid(TEXT2),
                    }
                }],
                "categoryAxis": [{
                    "properties": {
                        "fontSize": lit("9D"), "labelColor": solid(TEXT),
                        "showAxisTitle": lit("false"),
                    }
                }],
                "valueAxis": [{
                    "properties": {
                        "show": lit("false"), "showAxisTitle": lit("false"),
                    }
                }],
                "legend": [{"properties": {"show": lit("false")}}],
            },
            "visualContainerObjects": container_objects(
                title=("RANKED ABNORMAL CONTRIBUTORS — NORMALIZED DEVIATION "
                       "OF THE SELECTED EVENT (DIAGNOSTIC EVIDENCE, NOT "
                       "CONFIRMED CAUSALITY)")
            ),
        },
    )

    # Cause analysis and verification -------------------------------------
    page.add("cause-bg", 844, 470, 740, 254, shape(WHITE, 16, BORDER))
    page.add(
        "cause-title", 860, 480, 400, 22,
        textbox([("Cause analysis and verification", "12pt", TEXT, True)]),
    )
    page.add(
        "cause-sub", 860, 502, 500, 16,
        textbox([("Operator-readable explanation — diagnostic evidence, "
                  "not automatic control action", "8pt", TEXT2, False)]),
    )
    page.add(
        "cause-causes-label", 860, 524, 200, 16,
        textbox([("Possible causes", "9pt", TEXT2, True)]),
    )
    page.add(
        "cause-causes", 860, 540, 340, 170,
        card(EVENTS, "Event Sel Causes", value_size=9,
             background=None, border=False, word_wrap=True),
    )
    page.add(
        "cause-verif-label", 1216, 524, 240, 16,
        textbox([("Recommended verification", "9pt", TEXT2, True)]),
    )
    page.add(
        "cause-verif", 1216, 540, 352, 100,
        card(EVENTS, "Event Sel Verification", value_size=9,
             background=None, border=False, word_wrap=True),
    )
    page.add(
        "cause-signature", 1216, 644, 352, 70,
        {
            "visualType": "tableEx",
            "drillFilterOtherVisuals": True,
            "query": {
                "queryState": {
                    "Values": {
                        "projections": [
                            projection(CONTRIB, "Contributor Name",
                                       "Column"),
                            projection(CONTRIB, "Deviation Direction",
                                       "Column"),
                            projection(CONTRIB, "Deviation Percent",
                                       "Column"),
                        ]
                    }
                },
                "sortDefinition": {
                    "sort": [{
                        "field": field(CONTRIB, "Deviation Percent",
                                       "Column"),
                        "direction": "Descending",
                    }],
                    "isDefaultSort": True,
                },
            },
            "objects": {
                "values": [{
                    "properties": {
                        "fontSize": lit("8D"),
                        "fontColorPrimary": solid_measure(
                            CONTRIB, "Contributor Bar Color"
                        ),
                    }
                }],
                "columnHeaders": [{
                    "properties": {
                        "fontSize": lit("8D"), "fontColor": solid(TEXT2),
                    }
                }],
            },
            "visualContainerObjects": container_objects(
                title="EVENT SIGNATURE", background=None, border=False,
            ),
        },
    )

    # Recent abnormal events ----------------------------------------------
    event_columns = [
        ("Peak Timestamp", "Column"),
        ("Severity", "Column"),
        ("Peak Anomaly Risk", "Column"),
        ("Duration Min", "Column"),
        ("Subsystem", "Column"),
        ("Diagnosis", "Column"),
    ]
    value_objects = [{
        "properties": {
            "fontSize": lit("9D"),
            "backColor": solid_measure(EVENTS, "Event Row BG"),
            "fontColorPrimary": solid_measure(EVENTS, "Event Row FG"),
        }
    }]
    page.add(
        "events-table", 110, 738, 1474, 148,
        {
            "visualType": "tableEx",
            "drillFilterOtherVisuals": True,
            "query": {
                "queryState": {
                    "Values": {
                        "projections": [
                            projection(EVENTS, name, kind)
                            for name, kind in event_columns
                        ]
                    }
                },
                "sortDefinition": {
                    "sort": [{
                        "field": field(EVENTS, "Peak Timestamp", "Column"),
                        "direction": "Descending",
                    }],
                    "isDefaultSort": True,
                },
            },
            "objects": {
                "values": value_objects,
                "columnHeaders": [{
                    "properties": {
                        "fontSize": lit("9D"), "fontColor": solid(TEXT2),
                        "backColor": solid(WHITE),
                    }
                }],
                "grid": [{
                    "properties": {
                        "gridVertical": lit("false"),
                        "gridHorizontalColor": solid("#EDF1EF"),
                        "rowPadding": lit("6D"),
                    }
                }],
            },
            "visualContainerObjects": container_objects(
                title=("RECENT ABNORMAL EVENTS — ROW SELECTION UPDATES THE "
                       "EVENT, CONTRIBUTOR AND CAUSE VISUALS")
            ),
        },
    )

    page.add(
        "footer2", 110, 888, 1474, 12,
        textbox([("Diagnostic evidence only — verify in the field before "
                  "operational action.", "7pt", TEXT2, False)]),
    )
    return page


def main() -> None:
    if not BACKUP_DIR.exists():
        shutil.copytree(PAGES_DIR, BACKUP_DIR / "pages")
        print(f"Backed up existing pages to {BACKUP_DIR}")

    page1 = build_page1()
    page2 = build_page2()
    page1.write()
    page2.write()

    (PAGES_DIR / "pages.json").write_text(
        json.dumps(
            {
                "$schema": PAGES_SCHEMA,
                "pageOrder": [PAGE1, PAGE2],
                "activePageName": PAGE1,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    THEME_PATH.write_text(
        json.dumps(build_theme(), indent=2), encoding="utf-8"
    )

    print(f"Page 1: {len(page1.visuals)} visuals")
    print(f"Page 2: {len(page2.visuals)} visuals")
    print("Theme updated:", THEME_PATH.name)


if __name__ == "__main__":
    main()
