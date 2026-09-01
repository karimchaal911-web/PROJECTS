import { useMemo, useRef } from 'react';
import { useFrame, useLoader } from '@react-three/fiber';
import { Line } from '@react-three/drei';
import * as THREE from 'three';
import { C } from '../../lib/palette.js';
import { PBI_PLANE, PBI_HIGHLIGHTS } from '../../lib/curves.js';
import { useChannel } from '../usePresence.js';
import { WMono } from '../WorldText.jsx';

/**
 * The real Power BI report, placed in the world.
 *
 * These are the actual shipped report pages, rendered by
 * tools/render_dashboard_preview.py from the LIVE PostgreSQL views the report
 * queries by DirectQuery, and captured at 2x by scripts/capture-dashboard.mjs.
 * Nothing is added, removed or restyled.
 *
 * The capture is a real replay state taken inside an injected disturbance:
 * anomaly risk 0.95, severity HIGH, ranked contributors present, laboratory
 * reference 40 minutes old, freshness pill LIVE. The previous capture showed
 * DATA STALE, "ingested 8525 min ago" and an empty diagnosis under a heading
 * about real-time supervision, which was the single least defensible thing in
 * the film.
 *
 * `dashAssemble` fades the report up. It no longer pretends to be a morph from
 * the hold-out chart: the two are different charts of different windows, and
 * claiming otherwise while showing both was a visual overclaim.
 */

const POS = new THREE.Vector3(76, 10, 26);

// The capture is a live replay state of the shipped report, not a mock-up:
// see final_presentation/web/scripts/capture-dashboard.mjs.

export default function Dashboard() {
  const group = useRef();
  const presence = useChannel('dashboard');
  const assemble = useChannel('dashAssemble', 0);
  const highlight = useChannel('dashHighlight', 0);
  const page = useChannel('dashPage', 0);

  const [overview, diagnostics] = useLoader(THREE.TextureLoader, [
    `${import.meta.env.BASE_URL}img/powerbi_overview.png`,
    `${import.meta.env.BASE_URL}img/powerbi_diagnostics.png`,
  ]);

  useMemo(() => {
    for (const tex of [overview, diagnostics]) {
      tex.colorSpace = THREE.SRGBColorSpace;
      tex.anisotropy = 8;
      tex.minFilter = THREE.LinearMipmapLinearFilter;
      tex.generateMipmaps = true;
    }
  }, [overview, diagnostics]);

  // fog:false — this is a screen, not a surface in the room. Letting the
  // atmosphere wash it would misrepresent the real dashboard's contrast.
  // FrontSide, not DoubleSide. Scene 11 walks the camera behind this plane,
  // and a double-sided report renders its own page MIRRORED at the end of the
  // runtime corridor — reversed headings and a reversed trend chart, which
  // reads as a rendering fault rather than as the back of a screen.
  const matA = useMemo(() => new THREE.MeshBasicMaterial({
    map: overview, transparent: true, opacity: 0, toneMapped: false,
    fog: false, side: THREE.FrontSide,
  }), [overview]);
  const matB = useMemo(() => new THREE.MeshBasicMaterial({
    map: diagnostics, transparent: true, opacity: 0, toneMapped: false,
    fog: false, side: THREE.FrontSide,
  }), [diagnostics]);

  // What the camera sees once it is behind the report: the back of a screen.
  // Dark, matte, and edged in the report's own green so the plane still reads
  // as a physical object at the far end of the runtime.
  const matBack = useMemo(() => new THREE.MeshBasicMaterial({
    color: C.inkDeep, transparent: true, opacity: 0, toneMapped: false,
    fog: false, side: THREE.BackSide,
  }), []);

  const highlightRefs = useRef([]);
  const backEdge = useRef();

  const toLocal = (u, v) => ({
    x: -PBI_PLANE.w / 2 + ((u[0] + u[1]) / 2) * PBI_PLANE.w,
    y: PBI_PLANE.h / 2 - ((v[0] + v[1]) / 2) * PBI_PLANE.h,
    w: (u[1] - u[0]) * PBI_PLANE.w,
    h: (v[1] - v[0]) * PBI_PLANE.h,
  });

  /**
   * `side` decides which end of its own box a callout label hangs from.
   *
   * Every label used to start at its box's LEFT edge and run right. For the
   * two regions on the right of the page — the anomaly state strip and the
   * diagnosis column, which reaches to 99 % of the page width — that put a
   * forty-character caption outside the report and then outside the FRAME:
   * "DIAGNOSIS AND OPERATOR GUIDA" was the last thing visible on the film's
   * most important deliverable. A label belonging to a right-hand region now
   * hangs leftwards from that region's right edge instead.
   */
  const boxes = useMemo(() => PBI_HIGHLIGHTS.map((h) => {
    const local = toLocal(h.u, h.v);
    return { ...h, ...local, side: h.u[1] > 0.62 ? 'right' : 'left' };
  }), []);

  useFrame(() => {
    const p = presence.current;
    if (group.current) {
      group.current.visible = p > 0.01;
      if (p <= 0.01) return;
    }
    const a = assemble.current;
    const pg = page.current;

    // The report is LEGIBLE as soon as it is on screen. It used to be gated
    // behind clamp((a - 0.3) / 0.5), so at the beat that introduces the
    // project's actual deliverable the capture sat at 30 % opacity over a
    // near-black world — an unreadable grey rectangle.
    const base = p * THREE.MathUtils.clamp(a / 0.55, 0, 1);
    matA.opacity = base * (1 - pg);
    matB.opacity = base * pg;
    // The back plate does not fade with `dashAssemble`: the object is still
    // there when the report on its far face has receded.
    matBack.opacity = p * 0.94;
    if (backEdge.current) backEdge.current.material.opacity = p * 0.5;

    const h = highlight.current;
    highlightRefs.current.forEach((g, i) => {
      if (!g) return;
      // Reading order at ~1.3 s per region across five regions, not eight in
      // 4.4 s. Each box stays up once named, so the presenter can refer back.
      const local = THREE.MathUtils.clamp(h * boxes.length - i, 0, 1);
      const active = local > 0.02 && local < 0.995;
      g.visible = local > 0.02 && pg < 0.5;
      g.traverse((o) => {
        if (o.material && o.material.transparent) {
          o.material.opacity = (active ? 0.95 : 0.28) * local * p;
        }
      });
    });
  });

  return (
    <group ref={group} position={POS}>
      <mesh material={matA}>
        <planeGeometry args={[PBI_PLANE.w, PBI_PLANE.h]} />
      </mesh>
      <mesh position={[0, 0, 0.01]} material={matB}>
        <planeGeometry args={[PBI_PLANE.w, PBI_PLANE.h]} />
      </mesh>
      <mesh position={[0, 0, -0.02]} material={matBack}>
        <planeGeometry args={[PBI_PLANE.w, PBI_PLANE.h]} />
      </mesh>
      <Line
        ref={backEdge}
        points={[
          [-PBI_PLANE.w / 2, -PBI_PLANE.h / 2, -0.03], [PBI_PLANE.w / 2, -PBI_PLANE.h / 2, -0.03],
          [PBI_PLANE.w / 2, PBI_PLANE.h / 2, -0.03], [-PBI_PLANE.w / 2, PBI_PLANE.h / 2, -0.03],
          [-PBI_PLANE.w / 2, -PBI_PLANE.h / 2, -0.03],
        ]}
        color={C.ocpGreen}
        lineWidth={1.4}
        transparent
        opacity={0}
      />

      {boxes.map((b, i) => (
        <group key={b.id} ref={(el) => { highlightRefs.current[i] = el; }}>
          <Line
            points={[
              [b.x - b.w / 2, b.y - b.h / 2, 0.04], [b.x + b.w / 2, b.y - b.h / 2, 0.04],
              [b.x + b.w / 2, b.y + b.h / 2, 0.04], [b.x - b.w / 2, b.y + b.h / 2, 0.04],
              [b.x - b.w / 2, b.y - b.h / 2, 0.04],
            ]}
            color={C.ocpGreen}
            lineWidth={2}
            transparent
            opacity={0}
          />
          {/* Lime on a white report page is invisible; the callout label sits
              on the dark ground above each box in the report's own green. */}
          <WMono
            position={[b.side === 'right' ? b.x + b.w / 2 : b.x - b.w / 2, b.y + b.h / 2 + 0.5, 0.05]}
            anchorX={b.side}
            fontSize={0.52}
            color={C.ocpGreen}
            fillOpacity={0}
          >
            {b.label}
          </WMono>
        </group>
      ))}
    </group>
  );
}
