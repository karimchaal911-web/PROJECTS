import * as THREE from 'three';

/**
 * Procedural industrial surface treatment.
 *
 * WHY THIS EXISTS. Every material in the film was a flat PBR constant, so a
 * painted vessel, a machined riding ring and a rolled duct differed only by
 * three numbers. Real industrial surfaces do not: paint is never uniformly
 * glossy, machined steel carries a lathe direction, a rolled shell has weld
 * courses, and dust settles unevenly on everything in a drying plant. The
 * absence of that variation is what makes clean geometry read as CAD.
 *
 * WHAT IT IS ALLOWED TO SAY. This project's visual rule is truth-first, and
 * that constrains this file hard:
 *
 *   - NO albedo maps. Nothing here invents a stain, a rust bloom, a scrape or
 *     a paint failure on equipment nobody photographed. Colour stays exactly
 *     what the palette says it is.
 *   - Only ROUGHNESS and NORMAL are modulated — how a surface scatters light,
 *     which is a property of the material class, not of this plant's history.
 *   - Amplitudes are small by construction (see AMP). This is micro-surface
 *     breakup, not weathering.
 *   - Weld and cladding seams appear only where the fabrication method
 *     guarantees them: circumferential courses on rolled cylinders and bands
 *     on insulation cladding.
 *
 * WHAT IT IS NOT APPLIED TO. The information layer — architecture stack, value
 * ring, roadmap rail, manifold, evidence panels, the report plane — stays
 * perfectly clean. Those objects are diagrams. Texturing a diagram is decoration,
 * and decoration is what makes a deck look generated.
 *
 * SELF-CONTAINED. Everything is generated into DataTextures at runtime. No
 * image asset, no fetch, no CDN — the show still runs with the network down.
 *
 * COST. Seven families, generated once, lazily, behind the boot panel: about
 * 12 ms of JS and ~2 MB of texture memory in total. Materials share one GPU
 * upload per family; `applySurface` hands out clones that differ only in their
 * UV transform, which is a uniform, not a texture.
 */

/* ------------------------------------------------------------------ noise --- */

function hash2(x, y, seed) {
  let h = (x | 0) * 374761393 + (y | 0) * 668265263 + (seed | 0) * 1442695041;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967295;
}

/** Tileable value noise with independent periods per axis (integers). */
function vnoise(u, v, px, py, seed) {
  const x = u * px;
  const y = v * py;
  const x0 = Math.floor(x);
  const y0 = Math.floor(y);
  const fx = x - x0;
  const fy = y - y0;
  const sx = fx * fx * (3 - 2 * fx);
  const sy = fy * fy * (3 - 2 * fy);
  const wx0 = ((x0 % px) + px) % px;
  const wy0 = ((y0 % py) + py) % py;
  const wx1 = (wx0 + 1) % px;
  const wy1 = (wy0 + 1) % py;
  const a = hash2(wx0, wy0, seed);
  const b = hash2(wx1, wy0, seed);
  const c = hash2(wx0, wy1, seed);
  const d = hash2(wx1, wy1, seed);
  return (a * (1 - sx) + b * sx) * (1 - sy) + (c * (1 - sx) + d * sx) * sy;
}

/** Fractal sum. Returns 0..1. `stretch` > 1 elongates the pattern along u. */
function fbm(u, v, period, octaves, seed, stretch = 1) {
  let sum = 0;
  let amp = 1;
  let norm = 0;
  let p = period;
  for (let i = 0; i < octaves; i += 1) {
    const px = Math.max(1, Math.round(p / stretch));
    const py = Math.max(1, Math.round(p));
    sum += amp * vnoise(u, v, px, py, seed + i * 131);
    norm += amp;
    amp *= 0.5;
    p *= 2;
  }
  return sum / norm;
}

/** Distance to the nearest of `n` evenly spaced circumferential seams, 0..1. */
function seamBand(v, n, width) {
  const t = v * n;
  const d = Math.abs(t - Math.round(t)) / n;
  return Math.max(0, 1 - d / width);
}

/* --------------------------------------------------------------- families --- */

/**
 * `rough`  peak-to-peak roughness modulation
 * `bump`   height amplitude fed to the normal map, in texel-relative units
 * `normal` normalScale handed to the material
 * `dust`   how much low-frequency settled dust raises roughness and kills
 *          metalness. Generic, not a claim about where this plant is dirty.
 */
const FAMILY = {
  // painted carbon-steel vessel shells, hoods, chutes
  paint: { size: 256, rough: 0.13, bump: 0.9, normal: 0.16, dust: 0.05, build: buildPaint },
  // machined / polished: riding rings, girth gear, trunnions, nozzles, flanges
  machined: { size: 256, rough: 0.16, bump: 0.7, normal: 0.13, dust: 0.10, build: buildMachined },
  // rolled pipework and ductwork, welded in courses
  pipe: { size: 256, rough: 0.12, bump: 1.5, normal: 0.22, dust: 0.06, build: buildPipe },
  // painted structural steel, platforms, plinths, handrails
  struct: { size: 256, rough: 0.15, bump: 1.2, normal: 0.20, dust: 0.08, build: buildStruct },
  // open grating and walkways
  grating: { size: 256, rough: 0.12, bump: 1.0, normal: 0.18, dust: 0.10, build: buildStruct },
  // concrete floor and foundations
  concrete: { size: 256, rough: 0.10, bump: 2.6, normal: 0.42, dust: 0.04, build: buildConcrete },
  // lagged / insulated line, clad in banded sheet
  lagged: { size: 256, rough: 0.10, bump: 1.6, normal: 0.24, dust: 0.05, build: buildLagged },
};

/**
 * Each builder returns { rough, metal, height } in 0..1 for one texel.
 * They are deliberately different from one another — one noise applied to
 * everything is the same failure as no noise at all.
 */

function buildPaint(u, v, F) {
  // Orange peel over a slow blotch, plus two rolled courses. Paint on a large
  // fabricated shell is smooth at arm's length and never smooth in a highlight.
  const peel = fbm(u, v, 48, 3, 11);
  const blotch = fbm(u, v, 5, 3, 23);
  const seam = seamBand(v, 3, 0.03);
  const dust = Math.max(0, blotch - 0.45) * 2;
  const rough = 1 - F.rough * (0.55 + 0.45 * peel) * (0.4 + 0.6 * blotch)
    - F.dust * dust - seam * 0.06;
  const height = 0.5 + (peel - 0.5) * 0.35 + (blotch - 0.5) * 0.12 - seam * 0.30;
  return { rough, metal: 1 - dust * 0.25, height };
}

function buildMachined(u, v, F) {
  // A turning direction. A riding ring is ground, not cast, and the highlight
  // along it should smear the long way round.
  const lathe = fbm(u, v, 96, 2, 41, 14);
  const wear = fbm(u, v, 7, 3, 59);
  const dust = Math.max(0, wear - 0.55) * 2.2;
  const rough = 1 - F.rough * (0.3 + 0.7 * lathe) - F.dust * dust;
  const height = 0.5 + (lathe - 0.5) * 0.5;
  // Dust is dielectric: where it settles, metalness has to fall or the surface
  // keeps mirroring the environment through the dirt.
  return { rough, metal: 1 - dust * 0.55, height };
}

function buildPipe(u, v, F) {
  // Rolled sheet: a faint longitudinal grain, six circumferential weld courses
  // and a proud seam ridge at each. Only the fabrication is asserted.
  const grain = fbm(u, v, 64, 2, 71, 6);
  const patch = fbm(u, v, 4, 3, 83);
  const seam = seamBand(v, 6, 0.045);
  const dust = Math.max(0, patch - 0.5) * 2;
  const rough = 1 - F.rough * (0.4 + 0.6 * grain) - F.dust * dust + seam * 0.05;
  const height = 0.5 + (grain - 0.5) * 0.25 + seam * 0.42 - (patch - 0.5) * 0.08;
  return { rough, metal: 1 - dust * 0.3, height };
}

function buildStruct(u, v, F) {
  // Painted rolled section: a coarser, flatter breakup than a vessel shell,
  // because structural paint is a single thick coat over mill scale.
  const mill = fbm(u, v, 26, 4, 97);
  const coat = fbm(u, v, 6, 2, 109);
  const dust = Math.max(0, coat - 0.42) * 1.8;
  const rough = 1 - F.rough * (0.35 + 0.65 * mill) - F.dust * dust;
  const height = 0.5 + (mill - 0.5) * 0.45 + (coat - 0.5) * 0.15;
  return { rough, metal: 1 - dust * 0.2, height };
}

function buildConcrete(u, v, F) {
  // Aggregate. High frequency, high amplitude, almost no gloss variation —
  // concrete is rough everywhere and the interest is all in the normal.
  const agg = fbm(u, v, 40, 4, 137);
  const pit = fbm(u, v, 130, 2, 151);
  const slab = fbm(u, v, 3, 2, 163);
  const rough = 1 - F.rough * (0.4 + 0.6 * slab) - F.dust * (1 - agg) * 0.5;
  const height = 0.5 + (agg - 0.5) * 0.55 + (pit - 0.5) * 0.35;
  return { rough, metal: 1, height };
}

function buildLagged(u, v, F) {
  // Cladding sheet: banded, soft, matte. The bands are the fixing straps.
  const band = seamBand(v, 9, 0.10);
  const cloth = fbm(u, v, 70, 3, 181);
  const sag = fbm(u, v, 5, 2, 191);
  const rough = 1 - F.rough * (0.4 + 0.6 * cloth) + band * 0.04;
  const height = 0.5 + band * 0.5 + (cloth - 0.5) * 0.18 + (sag - 0.5) * 0.22;
  return { rough, metal: 1, height };
}

/* ----------------------------------------------------------- construction --- */

function makeDataTexture(data, size) {
  const t = new THREE.DataTexture(data, size, size, THREE.RGBAFormat);
  t.wrapS = THREE.RepeatWrapping;
  t.wrapT = THREE.RepeatWrapping;
  t.magFilter = THREE.LinearFilter;
  t.minFilter = THREE.LinearMipmapLinearFilter;
  t.generateMipmaps = true;
  t.colorSpace = THREE.NoColorSpace;
  t.needsUpdate = true;
  return t;
}

/**
 * Builds the two maps for one family.
 *
 * The ORM texture packs roughness in green and metalness in blue, which is
 * exactly where MeshStandardMaterial reads them from, so both maps are one
 * upload and one sampler.
 *
 * The mean of each channel is measured rather than assumed, and returned, so
 * `applySurface` can divide the material's scalar by it. Without that step
 * every textured surface silently becomes smoother and less metallic than the
 * palette says, because an 8-bit multiplier can only ever darken.
 */
function buildFamily(name) {
  const F = FAMILY[name];
  const size = F.size;
  const n = size * size;
  const orm = new Uint8Array(n * 4);
  const height = new Float32Array(n);
  let sumR = 0;
  let sumM = 0;

  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      const i = y * size + x;
      const s = F.build(x / size, y / size, F);
      const r = Math.min(1, Math.max(0, s.rough));
      const m = Math.min(1, Math.max(0, s.metal));
      sumR += r;
      sumM += m;
      orm[i * 4] = 255;
      orm[i * 4 + 1] = Math.round(r * 255);
      orm[i * 4 + 2] = Math.round(m * 255);
      orm[i * 4 + 3] = 255;
      height[i] = s.height;
    }
  }

  // Normals by central difference on the height field, wrapped so the map tiles.
  const nrm = new Uint8Array(n * 4);
  const k = F.bump;
  for (let y = 0; y < size; y += 1) {
    const yp = (y + 1) % size;
    const ym = (y + size - 1) % size;
    for (let x = 0; x < size; x += 1) {
      const xp = (x + 1) % size;
      const xm = (x + size - 1) % size;
      const dx = (height[y * size + xp] - height[y * size + xm]) * k;
      const dy = (height[yp * size + x] - height[ym * size + x]) * k;
      // (-dx, -dy, 1) normalised
      const len = Math.hypot(dx, dy, 1);
      const i = (y * size + x) * 4;
      nrm[i] = Math.round(((-dx / len) * 0.5 + 0.5) * 255);
      nrm[i + 1] = Math.round(((-dy / len) * 0.5 + 0.5) * 255);
      nrm[i + 2] = Math.round(((1 / len) * 0.5 + 0.5) * 255);
      nrm[i + 3] = 255;
    }
  }

  return {
    orm: makeDataTexture(orm, size),
    normal: makeDataTexture(nrm, size),
    meanRough: sumR / n,
    meanMetal: sumM / n,
    normalScale: F.normal,
  };
}

const built = new Map();
const clones = new Map();
let anisotropy = 4;

function family(name) {
  let f = built.get(name);
  if (!f) {
    f = buildFamily(name);
    f.orm.anisotropy = anisotropy;
    f.normal.anisotropy = anisotropy;
    built.set(name, f);
  }
  return f;
}

/**
 * A per-(family, repeat) clone. `clone()` shares the underlying Source, so all
 * of these are one GPU texture; only the UV transform differs.
 */
function tiled(name, repeat) {
  const [rx, ry] = Array.isArray(repeat) ? repeat : [repeat, repeat];
  const key = `${name}:${rx}:${ry}`;
  let c = clones.get(key);
  if (!c) {
    const f = family(name);
    const orm = f.orm.clone();
    const normal = f.normal.clone();
    orm.repeat.set(rx, ry);
    normal.repeat.set(rx, ry);
    orm.needsUpdate = true;
    normal.needsUpdate = true;
    c = { ...f, orm, normal };
    clones.set(key, c);
  }
  return c;
}

/* ------------------------------------------------------------------- api --- */

/**
 * Give a MeshStandardMaterial the surface behaviour of an industrial family.
 *
 * @param {THREE.MeshStandardMaterial} mat
 * @param {keyof FAMILY} name
 * @param {{repeat?: number|number[], normal?: number, metalness?: boolean}} [opts]
 *   repeat    UV tiling — a number, or [u, v] where the surface is not square.
 *   normal    override the family's normalScale.
 *   metalness false to leave metalness alone — correct for painted surfaces,
 *             where the dust term has nothing to switch off.
 */
export function applySurface(mat, name, opts = {}) {
  if (!mat || !FAMILY[name]) return mat;
  const repeat = opts.repeat ?? 2;
  const t = tiled(name, repeat);

  mat.roughnessMap = t.orm;
  // The scalar is divided by the map's mean so the palette's roughness is what
  // the surface AVERAGES, not what it maxes out at.
  mat.roughness = Math.min(1, mat.roughness / t.meanRough);

  if (opts.metalness !== false && mat.metalness > 0.02) {
    mat.metalnessMap = t.orm;
    mat.metalness = Math.min(1, mat.metalness / t.meanMetal);
  }

  mat.normalMap = t.normal;
  const s = opts.normal ?? t.normalScale;
  mat.normalScale = new THREE.Vector2(s, s);

  mat.needsUpdate = true;
  return mat;
}

/**
 * Build every family up front and match the GPU's anisotropic filtering.
 *
 * Called once from <StudioEnv>, which runs inside the boot window. Generating
 * lazily on first use would put ~12 ms of JS on whichever transition happened
 * to touch a family first, and the film has no budget for a hitch mid-move.
 */
export function primeSurfaces(gl) {
  anisotropy = Math.min(8, gl?.capabilities?.getMaxAnisotropy?.() ?? 4);
  for (const name of Object.keys(FAMILY)) {
    const f = family(name);
    f.orm.anisotropy = anisotropy;
    f.normal.anisotropy = anisotropy;
    f.orm.needsUpdate = true;
    f.normal.needsUpdate = true;
  }
}

export const SURFACE_FAMILIES = Object.keys(FAMILY);
