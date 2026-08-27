/**
 * Loads the seven verified data payloads produced by
 * data_build/extract_presentation_data.py.
 *
 * Every layer guards its own data: a failed payload yields an empty structure
 * and the layer renders nothing rather than throwing into the render loop.
 */

const FILES = ['facts', 'gap', 'holdout', 'candidates', 'coefficients', 'anomaly', 'manifold'];

const EMPTY = {
  facts: {},
  gap: { t: [], predicted: [], risk: [], signals: {}, lab: { t: [], moisture: [] } },
  holdout: { t: [], actual: [], predicted: [], metrics: {} },
  candidates: { candidates: [] },
  coefficients: { features: [] },
  anomaly: { coarse: { t: [], risk: [] }, window: { t: [], risk: [] }, event: {} },
  manifold: { normal: { points: [], score: [] }, support: { points: [] }, trajectory: { points: [], risk: [], inEvent: [] } },
};

let cache = null;

export async function loadShowData(onProgress) {
  if (cache) return cache;
  const out = { ...EMPTY };
  let done = 0;
  await Promise.all(
    FILES.map(async (name) => {
      try {
        const res = await fetch(`${import.meta.env.BASE_URL}data/${name}.json`);
        if (!res.ok) throw new Error(`${res.status}`);
        out[name] = await res.json();
      } catch (err) {
        console.warn(`[data] ${name}.json unavailable — layer will render empty`, err);
      } finally {
        done += 1;
        onProgress?.(done / FILES.length);
      }
    })
  );
  cache = out;
  return out;
}

export function getData() {
  return cache ?? EMPTY;
}

/** Convenience: min/max of a numeric array, ignoring nulls. */
export function extent(arr) {
  let lo = Infinity;
  let hi = -Infinity;
  for (const v of arr) {
    if (v == null || !Number.isFinite(v)) continue;
    if (v < lo) lo = v;
    if (v > hi) hi = v;
  }
  return Number.isFinite(lo) ? [lo, hi] : [0, 1];
}

/** Format a moisture value the way the project's data dictionary requires. */
export function fmtMoisture(v, decimals = 4) {
  return v == null ? '—' : `${v.toFixed(decimals)} % H₂O`;
}

export function fmtNum(v, decimals = 2) {
  if (v == null || !Number.isFinite(v)) return '—';
  return v.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function fmtClock(iso) {
  if (!iso) return '—';
  return iso.slice(11, 16);
}
