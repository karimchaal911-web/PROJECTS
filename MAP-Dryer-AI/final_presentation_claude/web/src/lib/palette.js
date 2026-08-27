/**
 * Design tokens, sampled from the real project assets.
 * See design/DESIGN_SYSTEM.md section 2 for provenance.
 */

export const C = {
  // ground
  inkVoid: '#05100D',
  inkDeep: '#081914',
  forest900: '#003C30',
  forest700: '#0C5A48',

  // OCP identity
  ocpGreen: '#007830',
  ocpLime: '#84B40C',
  ocpLeaf: '#4E9A3C',

  // editorial light
  cream: '#F5F2E4',
  ivory: '#FCF0D8',
  inkEditorial: '#12261E',
  rule: '#D6D2BE',

  // industrial materials
  steelGreen: '#2E4A34',
  steelDark: '#1A2A20',
  dust: '#C9C4B6',
  dustBright: '#E8E4D8',
  granule: '#EFEADA',
  handrail: '#B8952E',
  shell: '#8E8A7E',
  ring: '#6E6A60',
  duct: '#A8A296',
  grating: '#54544A',

  // data + state
  dataTeal: '#2FB6A0',
  dataCyan: '#7FE3D4',
  predict: '#3DD6B0',
  lab: '#F5F2E4',
  warn: '#E8A33D',
  critical: '#D1493F',
  outline: '#6E8A80',
  processWarm: '#FFAE5C',
  keyLight: '#FFF4E2',
  rimLight: '#9FC7BC',
};

/** The two lighting modes the world moves between. */
export const MODES = {
  dark: {
    fog: C.inkDeep,
    fogDensity: 0.0085,
    ambient: 0.60,
    key: 2.1,
    rim: 1.3,
    exposure: 1.12,
    bg: C.inkVoid,
  },
  focus: {
    // dark, but with the environment pushed back
    fog: C.inkDeep,
    fogDensity: 0.013,
    ambient: 0.55,
    key: 2.8,
    rim: 1.5,
    exposure: 1.12,
    bg: C.inkVoid,
  },
  editorial: {
    fog: C.cream,
    fogDensity: 0.003,
    ambient: 0.9,
    key: 1.6,
    rim: 0.35,
    exposure: 1.35,
    bg: C.cream,
  },
  supervision: {
    // dashboard light spilling into a dark control room
    fog: C.inkDeep,
    fogDensity: 0.006,
    ambient: 0.6,
    key: 1.9,
    rim: 0.8,
    exposure: 1.12,
    bg: '#06120F',
  },
};

/** Risk colour ramp matching the dashboard thresholds exactly. */
export function riskColor(risk) {
  if (risk >= 0.8) return C.critical;
  if (risk >= 0.5) return C.warn;
  return C.dataTeal;
}
