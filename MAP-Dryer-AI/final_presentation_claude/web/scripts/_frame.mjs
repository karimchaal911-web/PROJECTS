/**
 * Project world points through a candidate camera pose and print where they
 * land in the frame, as fractions of frame width and height.
 *
 * Composing a beat by arithmetic on paper is how the residence lane ended up
 * twice the width of the frame with its end label outside it. This uses three's
 * own projection so the number on screen is the number that was checked.
 *
 *   node scripts/_frame.mjs
 */
import * as THREE from 'three';

const ASPECT = 16 / 9;

export function frame(pos, target, fov, points) {
  const cam = new THREE.PerspectiveCamera(fov, ASPECT, 0.5, 620);
  cam.position.set(...pos);
  cam.lookAt(new THREE.Vector3(...target));
  cam.updateMatrixWorld(true);
  cam.updateProjectionMatrix();
  const out = [];
  for (const [name, p] of Object.entries(points)) {
    const v = new THREE.Vector3(...p).project(cam);
    out.push({ name, x: (v.x + 1) / 2, y: (1 - v.y) / 2, z: v.z });
  }
  return out;
}

export function report(label, pos, target, fov, points) {
  console.log(`\n${label}  pos=${pos}  target=${target}  fov=${fov}`);
  for (const r of frame(pos, target, fov, points)) {
    const flag = (r.x < 0.44 ? ' <copy-column' : '') + (r.x > 0.97 || r.x < 0.02 ? ' <OFF-FRAME' : '')
      + (r.y > 0.94 || r.y < 0.04 ? ' <OFF-FRAME-Y' : '');
    console.log(`   ${r.name.padEnd(18)} x=${(r.x * 100).toFixed(1).padStart(6)}%  y=${(r.y * 100).toFixed(1).padStart(6)}%${flag}`);
  }
}
