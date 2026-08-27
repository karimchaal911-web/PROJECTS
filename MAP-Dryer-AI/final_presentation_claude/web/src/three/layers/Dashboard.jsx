import { useMemo, useRef } from 'react';
import { useFrame, useLoader } from '@react-three/fiber';
import { Line } from '@react-three/drei';
import * as THREE from 'three';
import { C } from '../../lib/palette.js';
import { PBI_PLANE, pbiRectToLocal } from '../../lib/curves.js';
import { useChannel } from '../usePresence.js';
import { WMono } from '../WorldText.jsx';

/**
 * The real Power BI report, placed in the world.
 *
 * These are the actual exported pages of the shipped PBIP project — not a
 * recreation. Nothing is added, removed or restyled, and the highlight
 * sequence only points at elements that genuinely exist on those pages,
 * including the PROTOTYPE · REPLAY pill and the advisory footer.
 *
 * The `dashAssemble` channel drives the scene 09 → 10 transformation: the
 * hold-out chart's frame thickens into a card and lands registered over the
 * trend rectangle of this capture. That rectangle was measured from the 1600×900
 * export (see PBI_TREND_UV) rather than eyeballed, which is what makes the
 * transformation honest rather than a sleight of hand.
 */

const POS = new THREE.Vector3(76, 10, 26);

// Highlight regions, in UV of the 1600×900 overview export.
const HIGHLIGHTS = [
  { id: 'predicted', u: [0.068, 0.213], v: [0.098, 0.228], label: 'PREDICTED FINAL MOISTURE' },
  { id: 'lab', u: [0.223, 0.368], v: [0.098, 0.228], label: 'LATEST LAB MOISTURE' },
  { id: 'error', u: [0.378, 0.523], v: [0.098, 0.228], label: 'VALIDATED MOISTURE ERROR' },
  { id: 'risk', u: [0.533, 0.678], v: [0.098, 0.228], label: 'CURRENT ANOMALY RISK' },
  { id: 'status', u: [0.688, 0.988], v: [0.098, 0.228], label: 'PROCESS STATUS · SEVERITY' },
  { id: 'trend', u: [0.069, 0.655], v: [0.240, 0.625], label: 'MOISTURE & RISK TREND — ROLLING 8 h' },
  { id: 'vars', u: [0.069, 0.655], v: [0.638, 0.972], label: 'CRITICAL PROCESS VARIABLES' },
  { id: 'diag', u: [0.665, 0.988], v: [0.240, 0.972], label: 'DIAGNOSIS CONTEXT · OPERATOR GUIDANCE' },
];

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
  const matA = useMemo(() => new THREE.MeshBasicMaterial({
    map: overview, transparent: true, opacity: 0, toneMapped: false,
    fog: false, side: THREE.DoubleSide,
  }), [overview]);
  const matB = useMemo(() => new THREE.MeshBasicMaterial({
    map: diagnostics, transparent: true, opacity: 0, toneMapped: false,
    fog: false, side: THREE.DoubleSide,
  }), [diagnostics]);

  const rect = useMemo(() => pbiRectToLocal(), []);
  const highlightRefs = useRef([]);

  const toLocal = (u, v) => ({
    x: -PBI_PLANE.w / 2 + ((u[0] + u[1]) / 2) * PBI_PLANE.w,
    y: PBI_PLANE.h / 2 - ((v[0] + v[1]) / 2) * PBI_PLANE.h,
    w: (u[1] - u[0]) * PBI_PLANE.w,
    h: (v[1] - v[0]) * PBI_PLANE.h,
  });

  const boxes = useMemo(() => HIGHLIGHTS.map((h) => ({ ...h, ...toLocal(h.u, h.v) })), []);

  useFrame(() => {
    const p = presence.current;
    if (group.current) {
      group.current.visible = p > 0.01;
      if (p <= 0.01) return;
    }
    const a = assemble.current;
    const pg = page.current;

    // The capture fades up under the chart once the frame has become a card.
    const base = p * THREE.MathUtils.clamp((a - 0.3) / 0.5, 0, 1);
    matA.opacity = base * (1 - pg);
    matB.opacity = base * pg;

    const h = highlight.current;
    highlightRefs.current.forEach((g, i) => {
      if (!g) return;
      // Reading order, 0.55 s apart, expressed as slices of the channel.
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

      {/* registration guide: the rectangle the hold-out chart lands on */}
      <Line
        points={[
          [rect.x0, rect.y0, 0.03], [rect.x1, rect.y0, 0.03],
          [rect.x1, rect.y1, 0.03], [rect.x0, rect.y1, 0.03],
          [rect.x0, rect.y0, 0.03],
        ]}
        color={C.ocpGreen}
        lineWidth={1}
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
          <WMono position={[b.x - b.w / 2, b.y + b.h / 2 + 0.42, 0.05]} fontSize={0.32}
            color={C.ocpLime} fillOpacity={0}>
            {b.label}
          </WMono>
        </group>
      ))}
    </group>
  );
}
