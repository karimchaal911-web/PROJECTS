import * as THREE from 'three';

const C = {
  green: 0x017b30,
  leaf: 0x7bd63c,
  mint: 0x55e293,
  cyan: 0x4fc7d7,
  blue: 0x397ea8,
  forest: 0x063d34,
  steel: 0x8d9893,
  darkSteel: 0x26322d,
  bone: 0xf3f1e5,
  amber: 0xf2a33a,
  red: 0xd64c42,
  night: 0x050b09
};

const CHANNEL_NAMES = [
  'atmosphere', 'structure', 'process', 'dryer', 'interior', 'product', 'heat', 'vapor',
  'sensors', 'twin', 'time', 'preprocessing', 'pipeline', 'ridge', 'novelty',
  'validation', 'controlRoom', 'roadmap', 'visibility'
];

function seeded(seed = 9327) {
  let value = seed >>> 0;
  return () => {
    value = (value * 1664525 + 1013904223) >>> 0;
    return value / 4294967296;
  };
}

function track(channels, channel, mat, baseOpacity = mat.opacity ?? 1) {
  mat.transparent = true;
  mat.opacity = baseOpacity;
  mat.userData.channelOpacity = baseOpacity;
  mat.userData.channel = channel;
  channels[channel].push(mat);
  return mat;
}

function standard(channels, channel, color, options = {}) {
  return track(channels, channel, new THREE.MeshStandardMaterial({
    color,
    roughness: options.roughness ?? 0.56,
    metalness: options.metalness ?? 0.34,
    emissive: options.emissive ?? 0x000000,
    emissiveIntensity: options.emissiveIntensity ?? 0,
    side: options.side ?? THREE.FrontSide,
    depthWrite: options.depthWrite ?? true,
    transparent: true,
    opacity: options.opacity ?? 1
  }), options.opacity ?? 1);
}

function physical(channels, channel, color, options = {}) {
  return track(channels, channel, new THREE.MeshPhysicalMaterial({
    color,
    roughness: options.roughness ?? 0.22,
    metalness: options.metalness ?? 0.3,
    transmission: options.transmission ?? 0,
    thickness: options.thickness ?? 0.3,
    ior: options.ior ?? 1.45,
    clearcoat: options.clearcoat ?? 0.45,
    clearcoatRoughness: options.clearcoatRoughness ?? 0.22,
    emissive: options.emissive ?? 0x000000,
    emissiveIntensity: options.emissiveIntensity ?? 0,
    side: options.side ?? THREE.FrontSide,
    depthWrite: options.depthWrite ?? true,
    transparent: true,
    opacity: options.opacity ?? 1
  }), options.opacity ?? 1);
}

function basic(channels, channel, color, options = {}) {
  return track(channels, channel, new THREE.MeshBasicMaterial({
    color,
    wireframe: options.wireframe ?? false,
    side: options.side ?? THREE.FrontSide,
    depthWrite: options.depthWrite ?? false,
    blending: options.blending ?? THREE.NormalBlending,
    transparent: true,
    opacity: options.opacity ?? 1
  }), options.opacity ?? 1);
}

function lineMaterial(channels, channel, color, options = {}) {
  const Type = options.dashed ? THREE.LineDashedMaterial : THREE.LineBasicMaterial;
  return track(channels, channel, new Type({
    color,
    linewidth: 1,
    dashSize: options.dashSize ?? 0.32,
    gapSize: options.gapSize ?? 0.2,
    blending: options.blending ?? THREE.NormalBlending,
    depthWrite: options.depthWrite ?? false,
    transparent: true,
    opacity: options.opacity ?? 1
  }), options.opacity ?? 1);
}

function beam(length, thickness, mat, axis = 'x') {
  const size = axis === 'x' ? [length, thickness, thickness] : axis === 'y' ? [thickness, length, thickness] : [thickness, thickness, length];
  return new THREE.Mesh(new THREE.BoxGeometry(...size), mat);
}

function tube(curve, radius, material, segments = 96) {
  return new THREE.Mesh(new THREE.TubeGeometry(curve, segments, radius, 8, false), material);
}

function createLabelSprite(channels, channel, text, options = {}) {
  const canvas = document.createElement('canvas');
  canvas.width = 1024;
  canvas.height = 256;
  const context = canvas.getContext('2d');
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.fillStyle = options.background ?? 'rgba(5, 11, 9, 0.76)';
  context.beginPath();
  context.roundRect(12, 18, 1000, 220, 36);
  context.fill();
  context.strokeStyle = options.stroke ?? 'rgba(123, 214, 60, 0.62)';
  context.lineWidth = 5;
  context.stroke();
  context.fillStyle = options.color ?? '#edf4ef';
  context.font = `600 ${options.fontSize ?? 72}px "Segoe UI", Arial, sans-serif`;
  context.textAlign = 'center';
  context.textBaseline = 'middle';
  context.fillText(text, 512, 130);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  const material = track(channels, channel, new THREE.SpriteMaterial({ map: texture, transparent: true, opacity: options.opacity ?? 0.92, depthWrite: false }), options.opacity ?? 0.92);
  const sprite = new THREE.Sprite(material);
  sprite.scale.set(options.width ?? 3.2, options.height ?? 0.8, 1);
  return sprite;
}

function createCurvePoints(channels, channel, curve, count, color, size = 0.1, seed = 1) {
  const positions = new Float32Array(count * 3);
  const phases = new Float32Array(count);
  const rand = seeded(seed);
  for (let i = 0; i < count; i += 1) phases[i] = (i / count + rand() * 0.006) % 1;
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const material = track(channels, channel, new THREE.PointsMaterial({
    color,
    size,
    transparent: true,
    opacity: 1,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    sizeAttenuation: true
  }), 1);
  const points = new THREE.Points(geometry, material);
  points.userData.curve = curve;
  points.userData.phases = phases;
  return points;
}

function updateCurvePoints(points, elapsed, speed, wobble = 0) {
  const curve = points.userData.curve;
  const phases = points.userData.phases;
  const positions = points.geometry.attributes.position;
  const p = new THREE.Vector3();
  for (let i = 0; i < phases.length; i += 1) {
    const t = (phases[i] + elapsed * speed) % 1;
    curve.getPoint(t, p);
    positions.setXYZ(i, p.x + Math.sin(i * 1.7 + elapsed) * wobble, p.y + Math.cos(i * 1.3 + elapsed) * wobble, p.z);
  }
  positions.needsUpdate = true;
}

function makeImagePlane(channels, channel, url, position, width, height, rotationY, promises) {
  const material = track(channels, channel, new THREE.MeshBasicMaterial({
    color: 0xffffff,
    transparent: true,
    opacity: 1,
    side: THREE.DoubleSide,
    depthWrite: false,
    toneMapped: false
  }), 1);
  const plane = new THREE.Mesh(new THREE.PlaneGeometry(width, height), material);
  plane.position.copy(position);
  plane.rotation.y = rotationY;
  const loader = new THREE.TextureLoader();
  const pending = loader.loadAsync(url).then((texture) => {
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.anisotropy = 8;
    material.map = texture;
    material.needsUpdate = true;
  });
  promises.push(pending);
  return plane;
}

export function createWorld(scene, safeMode = false) {
  const channels = Object.fromEntries(CHANNEL_NAMES.map((name) => [name, []]));
  const texturePromises = [];
  const movingPoints = [];
  const rotators = [];
  const pulseObjects = [];
  const root = new THREE.Group();
  scene.add(root);

  // Deep atmosphere: a deterministic particulate field ties distant chapters together.
  const rand = seeded(1451);
  const dustCount = safeMode ? 480 : 1700;
  const dustPositions = new Float32Array(dustCount * 3);
  for (let i = 0; i < dustCount; i += 1) {
    dustPositions[i * 3] = -34 + rand() * 72;
    dustPositions[i * 3 + 1] = 0.6 + rand() * 21;
    dustPositions[i * 3 + 2] = -74 + rand() * 98;
  }
  const dustGeometry = new THREE.BufferGeometry();
  dustGeometry.setAttribute('position', new THREE.BufferAttribute(dustPositions, 3));
  const dustMaterial = track(channels, 'atmosphere', new THREE.PointsMaterial({
    color: C.mint,
    size: safeMode ? 0.035 : 0.055,
    transparent: true,
    opacity: 0.32,
    depthWrite: false,
    blending: THREE.AdditiveBlending
  }), 0.32);
  const dust = new THREE.Points(dustGeometry, dustMaterial);
  root.add(dust);

  const groundMat = standard(channels, 'structure', 0x0d1512, { roughness: 0.94, metalness: 0.08, opacity: 0.94 });
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(86, 108), groundMat);
  ground.rotation.x = -Math.PI / 2;
  ground.position.set(3, -0.12, -26);
  ground.receiveShadow = !safeMode;
  root.add(ground);

  const grid = new THREE.GridHelper(86, 86, C.green, 0x1d2d27);
  grid.position.set(3, -0.08, -26);
  track(channels, 'structure', grid.material, 0.24);
  root.add(grid);

  // Industrial site skeleton.
  const steel = standard(channels, 'structure', C.steel, { roughness: 0.48, metalness: 0.52, opacity: 0.82 });
  const darkSteel = standard(channels, 'structure', C.darkSteel, { roughness: 0.66, metalness: 0.38, opacity: 0.92 });
  const greenSteel = standard(channels, 'structure', C.forest, { roughness: 0.58, metalness: 0.34, opacity: 0.94 });
  for (let x = -20; x <= 24; x += 5.5) {
    for (const z of [-4.4, 4.4]) {
      const post = beam(8.4, 0.14, greenSteel, 'y');
      post.position.set(x, 4.2, z);
      post.castShadow = !safeMode;
      root.add(post);
    }
    const cross = beam(8.8, 0.12, darkSteel, 'z');
    cross.position.set(x, 6.5, 0);
    root.add(cross);
  }
  for (let x = -20; x < 24; x += 5.5) {
    for (const z of [-4.4, 4.4]) {
      const rail = beam(5.5, 0.11, steel, 'x');
      rail.position.set(x + 2.75, 6.5, z);
      root.add(rail);
    }
  }
  const pipeMat = standard(channels, 'structure', 0xb3bcb7, { roughness: 0.34, metalness: 0.64, opacity: 0.76 });
  for (const [y, z, radius] of [[5.3, -3.55, 0.16], [6.9, -3.0, 0.12], [4.5, 3.55, 0.13]]) {
    const pipe = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, 45, 14), pipeMat);
    pipe.rotation.z = Math.PI / 2;
    pipe.position.set(2, y, z);
    root.add(pipe);
  }

  // Process equipment: subdued enough to let the granule and dryer carry the story.
  const processSteel = standard(channels, 'process', 0x6f7b76, { roughness: 0.53, metalness: 0.44, opacity: 0.95 });
  const processDark = standard(channels, 'process', 0x202b27, { roughness: 0.68, metalness: 0.35, opacity: 0.96 });
  const processGreen = standard(channels, 'process', C.green, { roughness: 0.55, metalness: 0.26, opacity: 0.96 });

  const neutralizer = new THREE.Group();
  neutralizer.position.set(-16.5, 0, 0);
  const tank = new THREE.Mesh(new THREE.CylinderGeometry(1.55, 1.7, 4.9, 28), processSteel);
  tank.position.y = 2.6;
  neutralizer.add(tank);
  const tankTop = new THREE.Mesh(new THREE.ConeGeometry(1.56, 1.05, 28), processGreen);
  tankTop.position.y = 5.55;
  neutralizer.add(tankTop);
  root.add(neutralizer);

  for (const [x, z, s] of [[-10.8, -1.35, 1], [-8.3, 1.25, 0.84]]) {
    const vessel = new THREE.Mesh(new THREE.CylinderGeometry(1.18 * s, 1.42 * s, 4.5 * s, 24), processSteel);
    vessel.position.set(x, 2.35 * s, z);
    root.add(vessel);
    const cone = new THREE.Mesh(new THREE.ConeGeometry(1.42 * s, 1.6 * s, 24), processDark);
    cone.rotation.x = Math.PI;
    cone.position.set(x, 0.12, z);
    root.add(cone);
  }

  const centrifugeGroup = new THREE.Group();
  centrifugeGroup.position.set(-2.0, 1.9, 0);
  const centrifuge = new THREE.Mesh(new THREE.CylinderGeometry(1.48, 1.48, 1.9, 32), processGreen);
  centrifuge.rotation.z = Math.PI / 2;
  centrifugeGroup.add(centrifuge);
  const centrifugeRing = new THREE.Mesh(new THREE.TorusGeometry(1.52, 0.13, 10, 48), processSteel);
  centrifugeRing.rotation.y = Math.PI / 2;
  centrifugeGroup.add(centrifugeRing);
  root.add(centrifugeGroup);
  rotators.push({ object: centrifugeGroup, axis: 'x', speed: 0.28 });

  // Rotary dryer hero.
  const dryer = new THREE.Group();
  dryer.position.set(6.5, 2.55, 0);
  dryer.rotation.z = -0.045;
  root.add(dryer);

  const drumSpin = new THREE.Group();
  dryer.add(drumSpin);
  const shellMat = physical(channels, 'dryer', 0x89938f, {
    roughness: 0.3, metalness: 0.6, clearcoat: 0.72, opacity: 0.82,
    side: THREE.DoubleSide, depthWrite: false
  });
  const shell = new THREE.Mesh(new THREE.CylinderGeometry(2.08, 2.08, 9.4, safeMode ? 36 : 72, 1, true), shellMat);
  shell.rotation.z = Math.PI / 2;
  shell.castShadow = !safeMode;
  drumSpin.add(shell);

  const bandMat = standard(channels, 'dryer', 0x1e2824, { roughness: 0.38, metalness: 0.68, opacity: 0.98 });
  for (const x of [-4.05, -2.25, 0, 2.25, 4.05]) {
    const band = new THREE.Mesh(new THREE.TorusGeometry(2.12, 0.14, 12, 64), bandMat);
    band.rotation.y = Math.PI / 2;
    band.position.x = x;
    drumSpin.add(band);
  }

  const supportMat = standard(channels, 'dryer', C.forest, { roughness: 0.55, metalness: 0.34, opacity: 0.98 });
  for (const x of [-2.9, 2.9]) {
    const support = new THREE.Mesh(new THREE.BoxGeometry(1.15, 1.35, 4.75), supportMat);
    support.position.set(x, -2.18, 0);
    dryer.add(support);
    const rollerMat = standard(channels, 'dryer', 0x111815, { roughness: 0.42, metalness: 0.62, opacity: 1 });
    for (const z of [-1.68, 1.68]) {
      const roller = new THREE.Mesh(new THREE.CylinderGeometry(0.36, 0.36, 0.72, 24), rollerMat);
      roller.rotation.x = Math.PI / 2;
      roller.position.set(x, -1.62, z);
      dryer.add(roller);
    }
  }

  const endRingMat = basic(channels, 'dryer', C.leaf, { opacity: 0.56, blending: THREE.AdditiveBlending });
  for (const x of [-4.72, 4.72]) {
    const ring = new THREE.Mesh(new THREE.TorusGeometry(1.78, 0.025, 8, 64), endRingMat);
    ring.rotation.y = Math.PI / 2;
    ring.position.x = x;
    dryer.add(ring);
  }

  const innerDark = physical(channels, 'interior', 0x151b17, { roughness: 0.42, metalness: 0.46, opacity: 0.72, side: THREE.BackSide, depthWrite: false });
  const innerShell = new THREE.Mesh(new THREE.CylinderGeometry(1.93, 1.93, 9.08, safeMode ? 32 : 56, 1, true), innerDark);
  innerShell.rotation.z = Math.PI / 2;
  drumSpin.add(innerShell);

  const lifterMat = standard(channels, 'interior', 0xaeb6b2, { roughness: 0.45, metalness: 0.58, opacity: 0.86, emissive: C.amber, emissiveIntensity: 0.08 });
  for (let i = 0; i < 10; i += 1) {
    const angle = (i / 10) * Math.PI * 2;
    const lifter = new THREE.Mesh(new THREE.BoxGeometry(8.7, 0.08, 0.3), lifterMat);
    lifter.position.set(0, Math.cos(angle) * 1.56, Math.sin(angle) * 1.56);
    lifter.rotation.x = angle;
    drumSpin.add(lifter);
  }

  const heatMatHot = basic(channels, 'heat', C.amber, { opacity: 0.105, side: THREE.DoubleSide, blending: THREE.AdditiveBlending });
  const heatMatMid = basic(channels, 'heat', 0xe6d83d, { opacity: 0.072, side: THREE.DoubleSide, blending: THREE.AdditiveBlending });
  const heatMatCool = basic(channels, 'heat', C.leaf, { opacity: 0.052, side: THREE.DoubleSide, blending: THREE.AdditiveBlending });
  for (const [x, mat, scale] of [[3.0, heatMatHot, 1], [0, heatMatMid, 0.96], [-3.0, heatMatCool, 0.92]]) {
    const volume = new THREE.Mesh(new THREE.SphereGeometry(1.52, 26, 16), mat);
    volume.position.x = x;
    volume.scale.set(1.45, scale, scale);
    dryer.add(volume);
  }

  const innerGranuleCount = safeMode ? 180 : 640;
  const innerPositions = new Float32Array(innerGranuleCount * 3);
  const innerPhases = new Float32Array(innerGranuleCount);
  for (let i = 0; i < innerGranuleCount; i += 1) innerPhases[i] = i / innerGranuleCount;
  const innerGeometry = new THREE.BufferGeometry();
  innerGeometry.setAttribute('position', new THREE.BufferAttribute(innerPositions, 3));
  const innerGranuleMat = track(channels, 'interior', new THREE.PointsMaterial({
    color: C.leaf, size: 0.12, transparent: true, opacity: 1, depthWrite: false,
    blending: THREE.AdditiveBlending, sizeAttenuation: true
  }), 1);
  const innerGranules = new THREE.Points(innerGeometry, innerGranuleMat);
  dryer.add(innerGranules);

  const twinMat = basic(channels, 'twin', C.mint, { opacity: 0.4, wireframe: true, side: THREE.DoubleSide, blending: THREE.AdditiveBlending });
  const twin = new THREE.Mesh(new THREE.CylinderGeometry(2.18, 2.18, 9.62, 40, 7, true), twinMat);
  twin.rotation.z = Math.PI / 2;
  dryer.add(twin);

  const inletCone = new THREE.Mesh(new THREE.CylinderGeometry(1.05, 1.75, 2.2, 32, 1, true), standard(channels, 'dryer', 0x4b5752, { roughness: 0.56, metalness: 0.48, opacity: 0.9, side: THREE.DoubleSide }));
  inletCone.rotation.z = Math.PI / 2;
  inletCone.position.x = -5.75;
  dryer.add(inletCone);
  const exhaustCone = new THREE.Mesh(new THREE.CylinderGeometry(1.75, 1.1, 2.2, 32, 1, true), standard(channels, 'dryer', 0x4b5752, { roughness: 0.56, metalness: 0.48, opacity: 0.9, side: THREE.DoubleSide }));
  exhaustCone.rotation.z = Math.PI / 2;
  exhaustCone.position.x = 5.75;
  dryer.add(exhaustCone);

  // Process continuation after the dryer.
  const cooler = new THREE.Mesh(new THREE.CylinderGeometry(1.42, 1.42, 5.7, 32, 1, true), processSteel);
  cooler.rotation.z = Math.PI / 2;
  cooler.position.set(15.4, 1.95, 0);
  root.add(cooler);
  const warehouse = new THREE.Mesh(new THREE.BoxGeometry(5.6, 4.5, 7.6), processDark);
  warehouse.position.set(22.2, 2.25, 0);
  root.add(warehouse);
  for (const [x, width] of [[-4.8, 4.8], [12.1, 3.9], [18.7, 3.2]]) {
    const conveyor = new THREE.Mesh(new THREE.BoxGeometry(width, 0.32, 1.18), processDark);
    conveyor.position.set(x, 0.75, 0);
    root.add(conveyor);
  }

  // One luminous granule path through the whole process.
  const productCurve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(-18.2, 4.7, 0), new THREE.Vector3(-15.3, 1.8, 0),
    new THREE.Vector3(-10.6, 2.6, -0.7), new THREE.Vector3(-7.9, 2.2, 0.8),
    new THREE.Vector3(-2.0, 1.9, 0), new THREE.Vector3(1.8, 1.18, 0),
    new THREE.Vector3(6.5, 2.55, 0), new THREE.Vector3(11.2, 1.2, 0),
    new THREE.Vector3(15.4, 1.95, 0), new THREE.Vector3(22.3, 1.1, 0)
  ], false, 'catmullrom', 0.45);
  const productPoints = createCurvePoints(channels, 'product', productCurve, safeMode ? 180 : 760, C.leaf, safeMode ? 0.1 : 0.12, 51);
  root.add(productPoints);
  movingPoints.push({ points: productPoints, speed: 0.028, wobble: 0.012 });
  const heroGranuleMat = standard(channels, 'product', C.bone, { roughness: 0.34, metalness: 0.08, emissive: C.leaf, emissiveIntensity: 3.2, opacity: 1 });
  const heroGranule = new THREE.Mesh(new THREE.IcosahedronGeometry(0.26, 2), heroGranuleMat);
  root.add(heroGranule);
  pulseObjects.push({ object: heroGranule, min: 0.86, max: 1.16, speed: 2.4, phase: 0 });

  const hotAirCurve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(12.4, 3.2, 0.6), new THREE.Vector3(10.0, 3.0, 0.2),
    new THREE.Vector3(7.2, 2.9, -0.25), new THREE.Vector3(4.2, 2.78, 0.28),
    new THREE.Vector3(1.5, 2.7, 0)
  ]);
  const hotAirPoints = createCurvePoints(channels, 'heat', hotAirCurve, safeMode ? 80 : 340, C.amber, 0.09, 71);
  root.add(hotAirPoints);
  movingPoints.push({ points: hotAirPoints, speed: 0.06, wobble: 0.025 });

  // Vapor rises from the exhaust as moisture leaves.
  const vaporCount = safeMode ? 90 : 360;
  const vaporPositions = new Float32Array(vaporCount * 3);
  const vaporPhases = new Float32Array(vaporCount);
  for (let i = 0; i < vaporCount; i += 1) vaporPhases[i] = i / vaporCount;
  const vaporGeometry = new THREE.BufferGeometry();
  vaporGeometry.setAttribute('position', new THREE.BufferAttribute(vaporPositions, 3));
  const vaporMat = track(channels, 'vapor', new THREE.PointsMaterial({
    color: 0xd9f2e7, size: 0.14, transparent: true, opacity: 0.52,
    depthWrite: false, blending: THREE.AdditiveBlending
  }), 0.52);
  const vapor = new THREE.Points(vaporGeometry, vaporMat);
  root.add(vapor);

  // Sensor nodes and expanding pulses hug the dryer rather than floating as labels.
  const sensorGroup = new THREE.Group();
  root.add(sensorGroup);
  const sensorCoreMat = basic(channels, 'sensors', C.mint, { opacity: 1, blending: THREE.AdditiveBlending });
  const sensorRingMat = basic(channels, 'sensors', C.leaf, { opacity: 0.54, blending: THREE.AdditiveBlending, side: THREE.DoubleSide });
  const sensorPositions = [[2.4, 4.2, 0.3], [4.2, 1.35, 1.8], [6.5, 4.65, 0], [8.9, 1.5, -1.72], [10.3, 3.8, 0.9], [1.1, 2.8, -0.8]];
  for (let i = 0; i < sensorPositions.length; i += 1) {
    const position = sensorPositions[i];
    const node = new THREE.Mesh(new THREE.SphereGeometry(0.12, 16, 16), sensorCoreMat);
    node.position.set(...position);
    sensorGroup.add(node);
    const ring = new THREE.Mesh(new THREE.TorusGeometry(0.28, 0.026, 8, 36), sensorRingMat);
    ring.position.copy(node.position);
    ring.rotation.x = Math.PI / 2;
    sensorGroup.add(ring);
    pulseObjects.push({ object: ring, min: 0.7, max: 1.8, speed: 1.5, phase: i * 0.62 });
  }

  // Time tunnel: sparse lab anchors versus dense replay pulses, built in depth.
  const timeGroup = new THREE.Group();
  root.add(timeGroup);
  const timeRingMat = basic(channels, 'time', C.green, { opacity: 0.42, blending: THREE.AdditiveBlending, side: THREE.DoubleSide });
  for (let i = 0; i < 12; i += 1) {
    const ring = new THREE.Mesh(new THREE.TorusGeometry(1.7 + i * 0.05, 0.025, 8, 72), timeRingMat);
    ring.position.set(6.5, 2.1, -2.5 - i * 1.62);
    ring.rotation.z = i * 0.08;
    timeGroup.add(ring);
    rotators.push({ object: ring, axis: 'z', speed: i % 2 === 0 ? 0.025 : -0.018 });
  }
  const timeCurve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(6.5, 2.1, -2.2), new THREE.Vector3(6.5, 2.1, -10.8), new THREE.Vector3(6.5, 2.1, -20.3)
  ]);
  const timeRailMat = basic(channels, 'time', C.leaf, { opacity: 0.72, blending: THREE.AdditiveBlending });
  timeGroup.add(tube(timeCurve, 0.018, timeRailMat, 72));
  const replayPoints = createCurvePoints(channels, 'time', timeCurve, safeMode ? 120 : 480, C.mint, 0.075, 108);
  timeGroup.add(replayPoints);
  movingPoints.push({ points: replayPoints, speed: 0.09, wobble: 0.018 });
  const labMat = physical(channels, 'time', C.bone, { roughness: 0.2, metalness: 0.08, emissive: C.bone, emissiveIntensity: 1.5, opacity: 1 });
  for (const [i, z] of [-3.0, -11.35, -19.8].entries()) {
    const lab = new THREE.Mesh(new THREE.SphereGeometry(0.34, 24, 24), labMat);
    lab.position.set(6.5, 2.1, z);
    timeGroup.add(lab);
    const halo = new THREE.Mesh(new THREE.TorusGeometry(0.58, 0.025, 8, 48), timeRingMat);
    halo.position.copy(lab.position);
    timeGroup.add(halo);
    pulseObjects.push({ object: halo, min: 0.75, max: 1.35, speed: 1.15, phase: i * 1.8 });
    const label = createLabelSprite(channels, 'time', 'LAB', { width: 1.3, height: 0.42, fontSize: 82, opacity: 0.82 });
    label.position.set(7.85, 2.65, z);
    timeGroup.add(label);
  }

  // Preprocessing: raw strands are braided into an ordered signal lattice.
  const preprocessingGroup = new THREE.Group();
  root.add(preprocessingGroup);
  const rawColors = [C.leaf, C.cyan, C.amber, C.mint, C.green, C.bone];
  for (let i = 0; i < 6; i += 1) {
    const start = sensorPositions[i];
    const curve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(start[0], start[1], start[2]),
      new THREE.Vector3(6.2 + Math.sin(i) * 1.8, 3.2 + (i % 3) * 0.45, -4.2),
      new THREE.Vector3(4.7 + (i - 2.5) * 0.44, 2.2 + (i % 2) * 0.42, -10.2),
      new THREE.Vector3(3.2 + (i - 2.5) * 0.34, 2.55, -14.6)
    ]);
    const mat = basic(channels, 'preprocessing', rawColors[i], { opacity: 0.55, blending: THREE.AdditiveBlending });
    preprocessingGroup.add(tube(curve, 0.024, mat, 86));
    const particles = createCurvePoints(channels, 'preprocessing', curve, safeMode ? 36 : 92, rawColors[i], 0.065, 200 + i);
    preprocessingGroup.add(particles);
    movingPoints.push({ points: particles, speed: 0.045 + i * 0.004, wobble: 0.008 });
  }
  const gateMat = physical(channels, 'preprocessing', 0x15372b, { roughness: 0.22, metalness: 0.18, transmission: safeMode ? 0 : 0.2, thickness: 0.5, opacity: 0.72, depthWrite: false });
  const gateEdge = basic(channels, 'preprocessing', C.leaf, { opacity: 0.7, wireframe: true, blending: THREE.AdditiveBlending });
  const gateNames = ['ALIGN', 'CLEAN', 'ENGINEER', 'REPLAY'];
  for (let i = 0; i < 4; i += 1) {
    const gate = new THREE.Mesh(new THREE.BoxGeometry(2.5, 2.5, 0.28), gateMat);
    gate.position.set(3.2, 2.55, -10.6 - i * 2.1);
    preprocessingGroup.add(gate);
    const edge = new THREE.Mesh(new THREE.BoxGeometry(2.7, 2.7, 0.34), gateEdge);
    edge.position.copy(gate.position);
    preprocessingGroup.add(edge);
    const label = createLabelSprite(channels, 'preprocessing', gateNames[i], { width: 2.2, height: 0.54, fontSize: 66 });
    label.position.set(3.2, 4.35, gate.position.z);
    preprocessingGroup.add(label);
  }
  const latticeMat = basic(channels, 'preprocessing', C.mint, { opacity: 0.66, blending: THREE.AdditiveBlending });
  for (let row = 0; row < 5; row += 1) {
    for (let col = 0; col < 7; col += 1) {
      const dot = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.1, 0.1), latticeMat);
      dot.position.set(2.0 + col * 0.4, 1.65 + row * 0.4, -19.0);
      preprocessingGroup.add(dot);
      pulseObjects.push({ object: dot, min: 0.72, max: 1.35, speed: 1.25, phase: row * 0.5 + col * 0.3 });
    }
  }

  // Architecture nodes and portals.
  const pipelineGroup = new THREE.Group();
  root.add(pipelineGroup);
  const glass = physical(channels, 'pipeline', 0x12382d, { roughness: 0.16, metalness: 0.16, transmission: safeMode ? 0 : 0.28, thickness: 0.62, opacity: 0.8, depthWrite: false, emissive: C.green, emissiveIntensity: 0.16 });
  const edge = basic(channels, 'pipeline', C.mint, { opacity: 0.68, wireframe: true, blending: THREE.AdditiveBlending });
  const portalMat = basic(channels, 'pipeline', C.cyan, { opacity: 0.36, blending: THREE.AdditiveBlending, side: THREE.DoubleSide });
  const pipelineNodes = [];
  function addNode(name, position, geometry, scale = 1, color = 'green') {
    const group = new THREE.Group();
    group.position.set(...position);
    const body = new THREE.Mesh(geometry, glass);
    body.scale.setScalar(scale);
    group.add(body);
    const outline = new THREE.Mesh(geometry.clone(), edge);
    outline.scale.setScalar(scale * 1.12);
    group.add(outline);
    const label = createLabelSprite(channels, 'pipeline', name, {
      width: name.length > 10 ? 3.7 : 2.7,
      height: 0.64,
      stroke: color === 'blue' ? 'rgba(79,199,215,.72)' : 'rgba(123,214,60,.68)'
    });
    label.position.set(0, 2.0 * scale, 0);
    group.add(label);
    pipelineGroup.add(group);
    pipelineNodes.push(group);
    rotators.push({ object: outline, axis: 'y', speed: 0.12 + pipelineNodes.length * 0.012 });
    return group;
  }
  const sensorNode = addNode('SENSORS', [3.2, 2.55, -8.4], new THREE.OctahedronGeometry(1.05, 0), 0.9);
  const pythonNode = addNode('PYTHON', [3.2, 2.55, -18.2], new THREE.DodecahedronGeometry(1.15, 0), 1, 'blue');
  const modelHub = addNode('MODELS', [3.2, 2.55, -23.4], new THREE.IcosahedronGeometry(1.18, 1), 1);
  const dbNode = addNode('POSTGRESQL', [3.2, 2.45, -38], new THREE.CylinderGeometry(1.3, 1.3, 2.25, 32), 1, 'blue');
  const powerNode = addNode('POWER BI', [3.2, 2.55, -47], new THREE.BoxGeometry(2.25, 2.25, 0.55), 1, 'blue');
  const portalPositions = [-8.4, -17.1, -23.4, -37, -46];
  for (let i = 0; i < portalPositions.length; i += 1) {
    const portal = new THREE.Mesh(new THREE.TorusGeometry(2.0 + (i % 2) * 0.28, 0.045, 8, 80), portalMat);
    portal.position.set(3.2, 2.55, portalPositions[i]);
    portal.rotation.z = i * 0.16;
    pipelineGroup.add(portal);
    rotators.push({ object: portal, axis: 'z', speed: i % 2 ? -0.05 : 0.065 });
  }

  const ridgePosition = new THREE.Vector3(-7.2, 2.6, -30);
  const svmPosition = new THREE.Vector3(12.4, 2.7, -30);
  const pipelineCurves = [
    new THREE.CatmullRomCurve3([new THREE.Vector3(6.5, 2.8, 0), new THREE.Vector3(5.2, 3, -4), sensorNode.position, pythonNode.position]),
    new THREE.CatmullRomCurve3([pythonNode.position, modelHub.position]),
    new THREE.CatmullRomCurve3([modelHub.position, new THREE.Vector3(-0.5, 3.3, -26), ridgePosition]),
    new THREE.CatmullRomCurve3([modelHub.position, new THREE.Vector3(7.5, 3.3, -26), svmPosition]),
    new THREE.CatmullRomCurve3([ridgePosition, new THREE.Vector3(-3.2, 2.7, -34), dbNode.position]),
    new THREE.CatmullRomCurve3([svmPosition, new THREE.Vector3(8.6, 2.7, -34), dbNode.position]),
    new THREE.CatmullRomCurve3([dbNode.position, powerNode.position])
  ];
  for (let i = 0; i < pipelineCurves.length; i += 1) {
    const curve = pipelineCurves[i];
    const pathMat = basic(channels, 'pipeline', i === 3 || i === 5 ? C.cyan : C.leaf, { opacity: 0.54, blending: THREE.AdditiveBlending });
    pipelineGroup.add(tube(curve, 0.026, pathMat, 88));
    const packets = createCurvePoints(channels, 'pipeline', curve, safeMode ? 44 : 120, i === 3 || i === 5 ? C.cyan : C.mint, 0.07, 300 + i);
    pipelineGroup.add(packets);
    movingPoints.push({ points: packets, speed: 0.055 + i * 0.002, wobble: 0.006 });
  }

  // Ridge branch: a continuous luminous estimate braided through sparse lab anchors.
  const ridgeGroup = new THREE.Group();
  root.add(ridgeGroup);
  const ridgeCurvePoints = [];
  for (let i = 0; i < 84; i += 1) {
    const x = -11.5 + i * 0.105;
    const y = 2.7 + Math.sin(i * 0.29) * 0.5 + Math.sin(i * 0.095) * 0.26;
    ridgeCurvePoints.push(new THREE.Vector3(x, y, -30));
  }
  const ridgeCurve = new THREE.CatmullRomCurve3(ridgeCurvePoints);
  const ridgeTraceMat = basic(channels, 'ridge', C.leaf, { opacity: 0.92, blending: THREE.AdditiveBlending });
  ridgeGroup.add(tube(ridgeCurve, 0.045, ridgeTraceMat, 120));
  const ridgeShadowMat = basic(channels, 'ridge', C.green, { opacity: 0.14, blending: THREE.AdditiveBlending });
  ridgeGroup.add(tube(ridgeCurve, 0.16, ridgeShadowMat, 120));
  const ridgePulse = createCurvePoints(channels, 'ridge', ridgeCurve, safeMode ? 22 : 74, C.bone, 0.09, 401);
  ridgeGroup.add(ridgePulse);
  movingPoints.push({ points: ridgePulse, speed: 0.08, wobble: 0 });
  const labAnchorMat = physical(channels, 'ridge', C.bone, { roughness: 0.2, metalness: 0.06, emissive: C.bone, emissiveIntensity: 1.4, opacity: 1 });
  for (let i = 0; i < ridgeCurvePoints.length; i += 14) {
    const anchor = new THREE.Mesh(new THREE.SphereGeometry(0.15, 16, 16), labAnchorMat);
    anchor.position.copy(ridgeCurvePoints[i]);
    ridgeGroup.add(anchor);
  }
  const ridgeLabel = createLabelSprite(channels, 'ridge', 'CONTINUOUS ADVISORY ESTIMATE', { width: 5.4, height: 0.72, fontSize: 54 });
  ridgeLabel.position.set(-7.2, 5.0, -30);
  ridgeGroup.add(ridgeLabel);

  // One-Class SVM branch: normal envelope, an escaping point, and evidence bars.
  const noveltyGroup = new THREE.Group();
  noveltyGroup.position.copy(svmPosition);
  root.add(noveltyGroup);
  const envelopeMat = basic(channels, 'novelty', C.leaf, { opacity: 0.48, wireframe: true, blending: THREE.AdditiveBlending });
  const envelope = new THREE.Mesh(new THREE.SphereGeometry(1, safeMode ? 20 : 36, safeMode ? 12 : 24), envelopeMat);
  envelope.scale.set(3.45, 1.75, 2.2);
  envelope.rotation.z = -0.22;
  noveltyGroup.add(envelope);
  const normalCount = safeMode ? 100 : 420;
  const normalPositions = new Float32Array(normalCount * 3);
  const normalRand = seeded(772);
  for (let i = 0; i < normalCount; i += 1) {
    const radius = Math.cbrt(normalRand());
    const theta = normalRand() * Math.PI * 2;
    const phi = Math.acos(2 * normalRand() - 1);
    normalPositions[i * 3] = Math.sin(phi) * Math.cos(theta) * radius * 3.0;
    normalPositions[i * 3 + 1] = Math.cos(phi) * radius * 1.42;
    normalPositions[i * 3 + 2] = Math.sin(phi) * Math.sin(theta) * radius * 1.75;
  }
  const normalGeometry = new THREE.BufferGeometry();
  normalGeometry.setAttribute('position', new THREE.BufferAttribute(normalPositions, 3));
  const normalMat = track(channels, 'novelty', new THREE.PointsMaterial({ color: C.mint, size: 0.075, opacity: 0.42, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }), 0.42);
  noveltyGroup.add(new THREE.Points(normalGeometry, normalMat));
  const anomalyMat = standard(channels, 'novelty', C.amber, { roughness: 0.25, metalness: 0.12, emissive: C.amber, emissiveIntensity: 3.8, opacity: 1 });
  const anomaly = new THREE.Mesh(new THREE.IcosahedronGeometry(0.24, 1), anomalyMat);
  anomaly.position.set(4.5, 1.75, 0.6);
  noveltyGroup.add(anomaly);
  pulseObjects.push({ object: anomaly, min: 0.84, max: 1.36, speed: 2.5, phase: 0.5 });
  const alertLineMat = lineMaterial(channels, 'novelty', C.amber, { opacity: 0.82 });
  const alertLine = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(2.4, 0.9, 0.3), anomaly.position]), alertLineMat);
  noveltyGroup.add(alertLine);
  const contributorMat = standard(channels, 'novelty', C.amber, { roughness: 0.38, metalness: 0.24, emissive: C.amber, emissiveIntensity: 0.8, opacity: 0.9 });
  for (let i = 0; i < 4; i += 1) {
    const bar = new THREE.Mesh(new THREE.BoxGeometry(0.18 + i * 0.12, 0.22, 0.18), contributorMat);
    bar.position.set(4.1, -1.35 + i * 0.55, 0.4);
    bar.scale.x = 1 + i * 1.4;
    noveltyGroup.add(bar);
  }
  const noveltyLabel = createLabelSprite(channels, 'novelty', 'LEARNED NORMAL ENVELOPE', { width: 4.9, height: 0.68, fontSize: 54 });
  noveltyLabel.position.set(0, 3.5, 0);
  noveltyGroup.add(noveltyLabel);

  // Validation theatre.
  const validationGroup = new THREE.Group();
  root.add(validationGroup);
  const validationFloorMat = physical(channels, 'validation', 0x202821, { roughness: 0.24, metalness: 0.18, transmission: safeMode ? 0 : 0.12, thickness: 0.4, opacity: 0.72, depthWrite: false });
  const validationFloor = new THREE.Mesh(new THREE.PlaneGeometry(18, 10), validationFloorMat);
  validationFloor.rotation.x = -Math.PI / 2;
  validationFloor.position.set(3.2, 0.02, -40.8);
  validationGroup.add(validationFloor);
  const evidenceFrameMat = physical(channels, 'validation', 0x16221c, { roughness: 0.18, metalness: 0.34, transmission: safeMode ? 0 : 0.16, thickness: 0.45, opacity: 0.84, depthWrite: false, emissive: C.green, emissiveIntensity: 0.08 });
  const evidenceFrame = new THREE.Mesh(new THREE.BoxGeometry(12.3, 7.05, 0.32), evidenceFrameMat);
  evidenceFrame.position.set(3.2, 3.35, -40.45);
  validationGroup.add(evidenceFrame);
  const evidencePlane = makeImagePlane(channels, 'validation', './assets/evidence/holdout_predictions.png', new THREE.Vector3(3.2, 3.35, -40.22), 11.65, 6.55, 0, texturePromises);
  evidencePlane.material.color.setHex(0xd9e0dc);
  evidencePlane.material.userData.channelOpacity = 0.94;
  validationGroup.add(evidencePlane);
  const validationLabel = createLabelSprite(channels, 'validation', 'CHRONOLOGICAL TEST / SYNTHETIC PROTOTYPE', { width: 6.2, height: 0.64, fontSize: 48, background: 'rgba(13,17,14,.88)' });
  validationLabel.position.set(3.2, 7.45, -40.1);
  validationGroup.add(validationLabel);
  const metricGlowMat = basic(channels, 'validation', C.leaf, { opacity: 0.18, blending: THREE.AdditiveBlending });
  for (let i = 0; i < 3; i += 1) {
    const glow = new THREE.Mesh(new THREE.CylinderGeometry(0.45, 0.45, 2.1 + i * 0.45, 28), metricGlowMat);
    glow.position.set(-0.2 + i * 3.4, 1.0 + i * 0.22, -38.9);
    validationGroup.add(glow);
  }

  // Premium control room with authentic screens integrated into a curved spatial console.
  const controlRoom = new THREE.Group();
  root.add(controlRoom);
  const roomFloorMat = physical(channels, 'controlRoom', 0x08100d, { roughness: 0.16, metalness: 0.52, clearcoat: 0.7, opacity: 0.88, depthWrite: false });
  const roomFloor = new THREE.Mesh(new THREE.PlaneGeometry(30, 17), roomFloorMat);
  roomFloor.rotation.x = -Math.PI / 2;
  roomFloor.position.set(3.2, 0.01, -53.5);
  controlRoom.add(roomFloor);
  const consoleMat = physical(channels, 'controlRoom', 0x10211a, { roughness: 0.16, metalness: 0.32, transmission: safeMode ? 0 : 0.2, thickness: 0.5, opacity: 0.78, depthWrite: false, emissive: C.blue, emissiveIntensity: 0.08 });
  const screenFrameMat = standard(channels, 'controlRoom', 0x182520, { roughness: 0.26, metalness: 0.62, opacity: 0.94, emissive: C.cyan, emissiveIntensity: 0.06 });
  const centralFrame = new THREE.Mesh(new THREE.BoxGeometry(12.7, 7.2, 0.36), screenFrameMat);
  centralFrame.position.set(3.2, 3.6, -52.8);
  controlRoom.add(centralFrame);
  const overviewPlane = makeImagePlane(channels, 'controlRoom', './assets/dashboard/overview.png', new THREE.Vector3(3.2, 3.6, -52.56), 12.1, 6.7, 0, texturePromises);
  overviewPlane.material.color.setHex(0x82938a);
  overviewPlane.material.userData.channelOpacity = 0.78;
  controlRoom.add(overviewPlane);
  const diagFrame = new THREE.Mesh(new THREE.BoxGeometry(8.1, 4.75, 0.3), screenFrameMat);
  diagFrame.position.set(10.8, 3.25, -55.2);
  diagFrame.rotation.y = -0.48;
  controlRoom.add(diagFrame);
  const diagnosticsPlane = makeImagePlane(channels, 'controlRoom', './assets/dashboard/diagnostics.png', new THREE.Vector3(10.65, 3.25, -54.94), 7.65, 4.3, -0.48, texturePromises);
  diagnosticsPlane.material.color.setHex(0x788c82);
  diagnosticsPlane.material.userData.channelOpacity = 0.72;
  controlRoom.add(diagnosticsPlane);
  const evidenceSideFrame = new THREE.Mesh(new THREE.BoxGeometry(7.2, 4.15, 0.28), screenFrameMat);
  evidenceSideFrame.position.set(-3.6, 3.0, -55.2);
  evidenceSideFrame.rotation.y = 0.5;
  controlRoom.add(evidenceSideFrame);
  const evidenceSide = makeImagePlane(channels, 'controlRoom', './assets/evidence/holdout_predictions.png', new THREE.Vector3(-3.48, 3.0, -54.96), 6.75, 3.7, 0.5, texturePromises);
  evidenceSide.material.color.setHex(0x687c72);
  evidenceSide.material.userData.channelOpacity = 0.58;
  controlRoom.add(evidenceSide);
  for (let i = 0; i < 5; i += 1) {
    const console = new THREE.Mesh(new THREE.BoxGeometry(3.6, 0.58, 1.7), consoleMat);
    const angle = -0.6 + i * 0.3;
    console.position.set(3.2 + Math.sin(angle) * 8.6, 0.8, -48.1 - Math.cos(angle) * 1.8);
    console.rotation.y = -angle;
    controlRoom.add(console);
  }
  const roomArcMat = basic(channels, 'controlRoom', C.cyan, { opacity: 0.24, blending: THREE.AdditiveBlending, side: THREE.DoubleSide });
  for (const radius of [7.8, 11.5, 14.2]) {
    const arc = new THREE.Mesh(new THREE.TorusGeometry(radius, 0.035, 8, 96, Math.PI * 1.1), roomArcMat);
    arc.position.set(3.2, 0.04, -52.5);
    arc.rotation.x = Math.PI / 2;
    arc.rotation.z = Math.PI * 0.95;
    controlRoom.add(arc);
  }

  // Roadmap in depth; future stages are visibly outlined, not claimed as built.
  const roadmapGroup = new THREE.Group();
  root.add(roadmapGroup);
  const roadmapSolidMat = standard(channels, 'roadmap', C.green, { roughness: 0.38, metalness: 0.24, emissive: C.green, emissiveIntensity: 0.8, opacity: 0.95 });
  const roadmapWireMat = basic(channels, 'roadmap', C.mint, { opacity: 0.68, wireframe: true, blending: THREE.AdditiveBlending });
  const roadmapLineMat = lineMaterial(channels, 'roadmap', C.mint, { opacity: 0.5, dashed: true, dashSize: 0.45, gapSize: 0.28 });
  const roadmapNames = ['PROTOTYPE', 'READ-ONLY', 'SHADOW MODE', 'GOVERNED ADVISORY'];
  const roadmapPoints = [];
  for (let i = 0; i < 4; i += 1) {
    const position = new THREE.Vector3(3.2 + Math.sin(i * 0.72) * 1.8, 2.1 + i * 0.35, -57.5 - i * 4.1);
    roadmapPoints.push(position);
    const geometry = i === 0 ? new THREE.IcosahedronGeometry(0.8, 1) : new THREE.IcosahedronGeometry(0.9 + i * 0.08, 1);
    const node = new THREE.Mesh(geometry, i === 0 ? roadmapSolidMat : roadmapWireMat);
    node.position.copy(position);
    roadmapGroup.add(node);
    rotators.push({ object: node, axis: i % 2 ? 'x' : 'y', speed: 0.08 + i * 0.025 });
    const label = createLabelSprite(channels, 'roadmap', roadmapNames[i], { width: i > 1 ? 4.2 : 3.0, height: 0.62, fontSize: 54 });
    label.position.set(position.x + (i % 2 ? 2.6 : -2.6), position.y + 1.25, position.z);
    roadmapGroup.add(label);
    if (i > 0) {
      const connector = new THREE.Line(new THREE.BufferGeometry().setFromPoints([roadmapPoints[i - 1], position]), roadmapLineMat);
      connector.computeLineDistances();
      roadmapGroup.add(connector);
    }
  }

  // Persistent visibility ribbon: it outlives sparse laboratory anchors.
  const visibilityCurve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(1.4, 4.5, 0), new THREE.Vector3(6.5, 5.1, 0),
    new THREE.Vector3(11.3, 4.0, -1.5), new THREE.Vector3(9.2, 3.2, -6.5),
    new THREE.Vector3(6.5, 2.6, -12), new THREE.Vector3(6.5, 2.5, -20),
    new THREE.Vector3(3.2, 3.0, -30), new THREE.Vector3(3.2, 3.0, -47)
  ]);
  const visibilityMat = basic(channels, 'visibility', C.mint, { opacity: 0.52, blending: THREE.AdditiveBlending });
  root.add(tube(visibilityCurve, 0.038, visibilityMat, 180));
  const visibilityHaloMat = basic(channels, 'visibility', C.green, { opacity: 0.08, blending: THREE.AdditiveBlending });
  root.add(tube(visibilityCurve, 0.18, visibilityHaloMat, 180));
  const visibilityPoints = createCurvePoints(channels, 'visibility', visibilityCurve, safeMode ? 90 : 360, C.bone, 0.075, 613);
  root.add(visibilityPoints);
  movingPoints.push({ points: visibilityPoints, speed: 0.045, wobble: 0.01 });
  for (let i = 0; i < 3; i += 1) {
    const orbit = new THREE.Mesh(new THREE.TorusGeometry(2.45 + i * 0.28, 0.025, 8, 84), basic(channels, 'visibility', i === 1 ? C.cyan : C.leaf, { opacity: 0.32 - i * 0.06, blending: THREE.AdditiveBlending }));
    orbit.position.set(6.5, 2.55, 0);
    orbit.rotation.set(Math.PI / 2.4 + i * 0.35, 0.15 + i * 0.28, i * 0.52);
    root.add(orbit);
    rotators.push({ object: orbit, axis: i % 2 ? 'y' : 'z', speed: 0.08 + i * 0.025 });
  }

  // Set every channel to hidden until the director applies scene 1.
  function setChannel(name, value) {
    for (const mat of channels[name] || []) {
      const baseOpacity = mat.userData.channelOpacity ?? 1;
      mat.opacity = value * baseOpacity;
      mat.visible = mat.opacity > 0.0015;
      mat.needsUpdate = true;
    }
  }
  for (const name of CHANNEL_NAMES) setChannel(name, 0);

  const tmp = new THREE.Vector3();
  function animate(elapsed, reducedMotion) {
    const motionTime = reducedMotion ? 0 : elapsed;
    if (!reducedMotion) {
      drumSpin.rotation.x = elapsed * 0.22;
      twin.rotation.x = -elapsed * 0.075;
      dust.rotation.y = elapsed * 0.0025;
      noveltyGroup.rotation.y = Math.sin(elapsed * 0.22) * 0.08;
      controlRoom.position.y = Math.sin(elapsed * 0.27) * 0.018;
      for (const item of movingPoints) updateCurvePoints(item.points, elapsed, item.speed, item.wobble);
      for (const item of rotators) item.object.rotation[item.axis] += item.speed * 0.008;
    } else {
      for (const item of movingPoints) updateCurvePoints(item.points, 0, 0, 0);
    }

    const granulePhase = (motionTime * 0.032 + 0.16) % 1;
    productCurve.getPoint(granulePhase, tmp);
    heroGranule.position.copy(tmp);

    const innerAttribute = innerGranules.geometry.attributes.position;
    for (let i = 0; i < innerPhases.length; i += 1) {
      const phase = (innerPhases[i] + motionTime * 0.038) % 1;
      const x = -4.25 + phase * 8.5;
      const cascade = Math.sin(phase * Math.PI * 7 + i * 0.11 + motionTime * 0.9);
      const angle = phase * Math.PI * 5 + motionTime * 0.62 + (i % 13) * 0.16;
      const radius = 1.0 + (i % 9) * 0.045;
      const y = -0.65 + Math.max(0, Math.sin(angle)) * 1.35 + cascade * 0.08;
      const z = Math.cos(angle) * radius * 0.92;
      innerAttribute.setXYZ(i, x, y, z);
    }
    innerAttribute.needsUpdate = true;

    const vaporAttribute = vapor.geometry.attributes.position;
    for (let i = 0; i < vaporPhases.length; i += 1) {
      const phase = (vaporPhases[i] + motionTime * 0.055) % 1;
      const spiral = phase * Math.PI * 7 + i * 0.31;
      vaporAttribute.setXYZ(
        i,
        11.3 + Math.cos(spiral) * (0.2 + phase * 0.9),
        3.0 + phase * 5.6,
        0.3 + Math.sin(spiral) * (0.2 + phase * 1.0)
      );
    }
    vaporAttribute.needsUpdate = true;

    for (const item of pulseObjects) {
      const wave = (Math.sin(motionTime * item.speed + item.phase) + 1) / 2;
      const scale = item.min + (item.max - item.min) * wave;
      item.object.scale.setScalar(scale);
    }
  }

  const objectCount = root.getObjectByProperty ? (() => {
    let count = 0;
    root.traverse(() => { count += 1; });
    return count;
  })() : 0;

  return {
    root,
    channels,
    setChannel,
    animate,
    ready: Promise.all(texturePromises),
    stats: { objects: objectCount, materials: Object.values(channels).reduce((sum, list) => sum + list.length, 0) },
    actors: { dryer, drumSpin, heroGranule, timeGroup, preprocessingGroup, pipelineGroup, ridgeGroup, noveltyGroup, validationGroup, controlRoom, roadmapGroup }
  };
}
