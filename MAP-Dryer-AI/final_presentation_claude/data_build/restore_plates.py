"""Prepare the full-screen photographic plates the show renders.

WHY THIS EXISTS
---------------
Scene 02's hero was a 1280 x 960 phone photograph of soluble MAP in storage,
drawn across roughly 2 860 screen pixels at 1920 x 1080 -- a 2.2x magnification
of an already-compressed JPEG. That is the whole of the "blurry hero" problem:
not the grade, not the filter, not the crop. The browser was inventing 55 % of
the pixels on screen with a bilinear filter.

It is fixed in two places, and this script is the smaller half:

1. `Material.jsx` now draws the plate at a size the source can actually carry
   (about 1 000 screen pixels at the closest beat), as an editorial print with
   the type beside it instead of over it. That alone takes the plate from a
   2.2x magnification to a 0.78x minification.

2. This script produces the delivered file. The source is resampled ONCE with
   Lanczos to 2048 x 1536 with a measured unsharp pass either side, and written
   as 4:4:4 progressive JPEG. The upscale adds no detail -- nothing can -- but
   it gives the GPU sampling headroom, so the plate stays clean on a retina
   panel at devicePixelRatio 2 as well as on a 1920 projector at 1.

WHAT THIS IS NOT
----------------
This is resampling and sharpening of the real photograph. No content is
generated, replaced or invented: the bag count, the handwriting on the bulk
bags, the pallet geometry, the racking and the aisle are the ones in the
original file. Compare `assets/process/soluble_map_storage.jpeg` against the
output and every object is the same object.

A generative restoration was considered and NOT used -- see
`higgsfield/MODEL_SELECTION.md` section 7.6 for the reasoning and for the
account state at the time of this pass.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "process"
OUT = ROOT / "web" / "public" / "img"

# name -> (source file, output file, long edge of the delivered plate)
PLATES = {
    "soluble_map": ("soluble_map_storage.jpeg", "soluble_map_storage.jpg", 2048),
}


def restore(src: Path, dst: Path, long_edge: int) -> tuple[int, int]:
    im = Image.open(src).convert("RGB")
    w, h = im.size

    # Pre-sharpen at native resolution: recover the micro-contrast the source
    # JPEG's chroma subsampling cost, before any resampling smears it.
    im = im.filter(ImageFilter.UnsharpMask(radius=1.1, percent=55, threshold=3))

    scale = long_edge / max(w, h)
    if scale > 1.0:
        im = im.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
        # A second, gentler pass to put back the edge acuity Lanczos softens.
        im = im.filter(ImageFilter.UnsharpMask(radius=1.6, percent=42, threshold=2))

    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, "JPEG", quality=90, subsampling=0, progressive=True, optimize=True)
    return im.size


def main() -> int:
    for key, (src_name, dst_name, long_edge) in PLATES.items():
        src = SRC / src_name
        dst = OUT / dst_name
        if not src.exists():
            print(f"MISSING SOURCE {src}", file=sys.stderr)
            return 1
        before = Image.open(src).size
        size = restore(src, dst, long_edge)
        kb = dst.stat().st_size // 1024
        print(f"{key}: {before[0]}x{before[1]} -> {size[0]}x{size[1]}  {kb} KB  {dst.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
