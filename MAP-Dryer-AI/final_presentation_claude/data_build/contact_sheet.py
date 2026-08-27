"""Assemble the captured stills into contact sheets for the visual QA pass.

Reviewing 35 frames one at a time hides continuity problems; seeing them as a
grid makes tonal jumps, repeated compositions and dead frames obvious at once.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "exports" / "screenshots"
OUT = ROOT / "exports"

COLS = 4
CELL_W = 640
PAD = 10
LABEL_H = 22
BG = (18, 20, 19)
FG = (200, 205, 200)


def main(per_sheet: int = 12) -> None:
    files = sorted(p for p in SRC.glob("step-*.png"))
    if not files:
        print("no captures found")
        return
    manifest = {}
    mf = SRC / "manifest.json"
    if mf.exists():
        data = json.loads(mf.read_text())
        manifest = {s["file"]: s for s in data.get("steps", [])}

    sheets = [files[i:i + per_sheet] for i in range(0, len(files), per_sheet)]
    for n, group in enumerate(sheets, 1):
        probe = Image.open(group[0])
        cell_h = round(CELL_W * probe.height / probe.width)
        rows = (len(group) + COLS - 1) // COLS
        w = COLS * CELL_W + (COLS + 1) * PAD
        h = rows * (cell_h + LABEL_H) + (rows + 1) * PAD
        sheet = Image.new("RGB", (w, h), BG)
        draw = ImageDraw.Draw(sheet)

        for i, f in enumerate(group):
            r, c = divmod(i, COLS)
            x = PAD + c * (CELL_W + PAD)
            y = PAD + r * (cell_h + LABEL_H + PAD)
            im = Image.open(f).convert("RGB").resize((CELL_W, cell_h), Image.LANCZOS)
            sheet.paste(im, (x, y))
            info = manifest.get(f.name, {})
            label = "%s  %s" % (f.name.split("_")[0], (info.get("hero") or "")[:64])
            draw.text((x + 2, y + cell_h + 4), label, fill=FG)

        path = OUT / ("contact_sheet_%d.png" % n)
        sheet.save(path, optimize=True)
        print("wrote %s  (%d frames, %d KB)" % (path.name, len(group), path.stat().st_size // 1024))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 12)
