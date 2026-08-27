import { tweenChannels } from './usePresence.js';

/**
 * Per-scene choreography, appended to the Rig's single transition timeline.
 *
 * Everything here answers "why is this moving?" with narrative, causality,
 * spatial or hierarchical intent. Decorative motion was cut — see
 * design/MOTION_SPEC.md, "Motion that was considered and cut".
 */

export function buildTransition(tl, ctx) {
  const { scene, beat, duration, reduced, camState } = ctx;
  const D = reduced ? 0.4 : duration;
  const beatId = scene.beats?.[beat]?.id ?? null;

  const ch = (values, opts = {}) =>
    tweenChannels(tl, values, { duration: D, ease: 'power2.inOut', position: 0, ...opts });

  switch (scene.id) {
    /* ------------------------------------------------------------ 01 ---- */
    case 'awakening':
      ch({
        straighten: 0, flowSpeed: 0.35, heroGranule: 1, chainHead: 0,
        dryerWire: 0, axisDraw: 0, labRise: 0, traceDraw: 0,
        sensorReveal: 0, packetFlow: 0, archBuild: 0,
        laneSplit: 0, manifoldReveal: 0, trajectory: 0,
        evidence: 0, evidenceBeat: 0, dashAssemble: 0, dashPage: 0,
        runtimeReveal: 0, loopClose: 0, ringReveal: 0, roadmap: 0,
      });
      // The plant is not switched on — it is found. Rim light arriving last is
      // what makes the drum read as a solid object rather than a shape.
      if (!reduced) {
        tl.fromTo(camState, { pz: camState.pz + 7, px: camState.px - 8 },
          { pz: camState.pz, px: camState.px, duration: 4.0, ease: 'power2.out' }, 0);
      }
      break;

    /* ------------------------------------------------------------ 02 ---- */
    case 'material':
      // Long-lens compression: the granule appears to be a macro shot, not a
      // growing object. Fog stands in for depth of field at zero GPU cost.
      ch({ heroGranule: 46, flowSpeed: 0.5, straighten: 0, chainHead: 0 },
        { duration: reduced ? 0.4 : 2.6 });
      break;

    /* ------------------------------------------------------------ 03 ---- */
    case 'chain':
      ch({ heroGranule: 1, flowSpeed: 1, straighten: 0 }, { duration: D });
      // Stations light because the material arrives, not because time passed.
      tweenChannels(tl, { chainHead: 1.0 },
        { duration: reduced ? 0.6 : 16, ease: 'none', position: 0.4 });
      break;

    /* ------------------------------------------------------------ 04 ---- */
    case 'dryer': {
      ch({ chainHead: 1, flowSpeed: 1, straighten: 0, heroGranule: 1 });
      if (beatId === 'machine') {
        ch({ dryerWire: 0, sensorReveal: 0 });
        // A slow drift across the machine, so it is understood in the round.
        // Relative, so it continues from wherever the beat camera settled.
        if (!reduced) {
          tl.to(camState, { px: '-=9', pz: '-=6', duration: 26, ease: 'none' }, D);
        }
      }
      if (beatId === 'physics') {
        ch({ dryerWire: 1, sensorReveal: 0 }, { duration: reduced ? 0.4 : 1.1 });
      }
      if (beatId === 'data') {
        ch({ dryerWire: 0.55 }, { duration: reduced ? 0.4 : 0.8 });
        tweenChannels(tl, { sensorReveal: 1 },
          { duration: reduced ? 0.4 : 1.4, ease: 'power3.out', position: 0.3 });
      }
      break;
    }

    /* ------------------------------------------------------------ 05 ---- */
    case 'gap': {
      ch({ dryerWire: 0, sensorReveal: 0.25, flowSpeed: 1 });
      if (beatId === 'form') {
        // THE move: distance becomes time. Nothing else animates during it.
        tweenChannels(tl, { straighten: 1, axisDraw: 1 },
          { duration: reduced ? 0.5 : 3.2, ease: 'power3.inOut', position: 0.2 });
        ch({ labRise: 0, traceDraw: 0 });
      }
      if (beatId === 'markers') {
        ch({ straighten: 1, axisDraw: 1 });
        // The only overshoot in the film, reserved for the one thing that is
        // actually measured. Overshoot reads as solidity.
        tweenChannels(tl, { labRise: 1.6 },
          { duration: reduced ? 0.4 : 1.8, ease: 'back.out(1.4)', position: 0.15 });
      }
      if (beatId === 'travel') {
        ch({ straighten: 1, axisDraw: 1, labRise: 1.6 });
        if (!reduced) {
          // Constant velocity, no easing — the only linear move in the film.
          // The jury is meant to feel the duration, not admire the camera.
          // It starts where the beat camera settled and travels +X from there.
          tl.to(camState, {
            px: '+=34', tx: '+=34', duration: 6.5, ease: 'none',
          }, D);
        }
      }
      break;
    }

    /* ------------------------------------------------------------ 06 ---- */
    case 'response': {
      ch({ straighten: 1, axisDraw: 1, labRise: 1.6, flowSpeed: 1 });
      if (beatId === 'question') {
        ch({ traceDraw: 0, sensorReveal: 0.5 });
      }
      if (beatId === 'fill') {
        tweenChannels(tl, { sensorReveal: 1 },
          { duration: reduced ? 0.3 : 0.9, ease: 'power2.out', position: 0 });
        // The trace is drawn by the arriving signals, not by a timer.
        tweenChannels(tl, { traceDraw: 1 },
          { duration: reduced ? 0.6 : 5.2, ease: 'power1.inOut', position: 0.6 });
      }
      if (beatId === 'two') {
        ch({ traceDraw: 1, sensorReveal: 1 });
      }
      break;
    }

    /* ------------------------------------------------------------ 07 ---- */
    case 'digital': {
      ch({ straighten: 1, axisDraw: 1, traceDraw: 1, labRise: 1.6 });
      if (beatId === 'sense') {
        ch({ dryerWire: 1, sensorReveal: 1, packetFlow: 0.35, archBuild: 0, alignPause: 0 },
          { duration: reduced ? 0.4 : 1.4 });
      }
      if (beatId === 'stack') {
        ch({ dryerWire: 1, sensorReveal: 1, packetFlow: 1 });
        // Each layer forms when its packets arrive. The architecture is a
        // consequence, not an illustration.
        tweenChannels(tl, { archBuild: 1 },
          { duration: reduced ? 0.8 : 7, ease: 'none', position: 0.4 });
      }
      if (beatId === 'align') {
        ch({ archBuild: 1, packetFlow: 0.25 });
        tweenChannels(tl, { alignPause: 1 },
          { duration: reduced ? 0.5 : 3.5, ease: 'none', position: 0.3 });
      }
      break;
    }

    /* ------------------------------------------------------------ 08 ---- */
    case 'pathways': {
      ch({ dryerWire: 1, archBuild: 1, alignPause: 0 });
      if (beatId === 'split') {
        // One input, two questions. The split must be seen to happen to the
        // same data, so instance targets are reassigned rather than re-emitted.
        tweenChannels(tl, { laneSplit: 1, packetFlow: 1 },
          { duration: reduced ? 0.4 : 1.6, ease: 'power2.inOut', position: 0.2 });
        ch({ manifoldReveal: 0, supportReveal: 0, trajectory: 0, laneFocus: 0 });
      }
      if (beatId === 'quality') {
        ch({ laneSplit: 1, laneFocus: -1, manifoldReveal: 0.25 });
      }
      if (beatId === 'process') {
        ch({ laneSplit: 1, laneFocus: 1 });
        tweenChannels(tl, { manifoldReveal: 1 },
          { duration: reduced ? 0.4 : 1.2, ease: 'power2.out', position: 0.2 });
        tweenChannels(tl, { supportReveal: 1 },
          { duration: reduced ? 0.4 : 1.0, ease: 'power2.out', position: 1.0 });
      }
      if (beatId === 'leave') {
        ch({ manifoldReveal: 1, supportReveal: 1 });
        // The point follows its real recorded trajectory out of the region.
        tweenChannels(tl, { trajectory: 1 },
          { duration: reduced ? 0.8 : 6, ease: 'none', position: 0.3 });
      }
      break;
    }

    /* ------------------------------------------------------------ 09 ---- */
    case 'evidence': {
      ch({
        laneSplit: 0, manifoldReveal: 0, trajectory: 0, supportReveal: 0,
        packetFlow: 0, archBuild: 0, dryerWire: 0, straighten: 1,
        axisDraw: 1, labRise: 1.6, traceDraw: 1, dashAssemble: 0,
      });
      const beats = { moisture: 1, candidates: 2, anomaly: 3, limits: 4 };
      tweenChannels(tl, { evidence: 1, evidenceBeat: beats[beatId] ?? 1 },
        { duration: reduced ? 0.4 : 1.6, ease: 'power3.out', position: 0.3 });
      if (beatId === 'moisture') {
        // 165 real points accumulating: 1.3 s of evidence arriving.
        tweenChannels(tl, { evidencePoints: 1 },
          { duration: reduced ? 0.4 : 1.3, ease: 'power1.out', position: 0.6 });
      }
      break;
    }

    /* ------------------------------------------------------------ 10 ---- */
    case 'supervision': {
      ch({ evidence: 0.3, evidencePoints: 1, straighten: 1 });
      if (beatId === 'become') {
        // The chart's frame thickens into a card and lands exactly registered
        // over the trend rectangle of the real capture. The rectangle was
        // measured from the export, not eyeballed.
        tweenChannels(tl, { dashAssemble: 0.45, dashPage: 0, dashHighlight: 0 },
          { duration: reduced ? 0.4 : 1.8, ease: 'power2.inOut', position: 0.2 });
      }
      if (beatId === 'assemble') {
        tweenChannels(tl, { dashAssemble: 1, dashPage: 0 },
          { duration: reduced ? 0.4 : 1.2, ease: 'power2.out', position: 0 });
        tweenChannels(tl, { dashHighlight: 1 },
          { duration: reduced ? 0.6 : 4.4, ease: 'none', position: 0.8 });
      }
      if (beatId === 'diagnostics') {
        tweenChannels(tl, { dashAssemble: 1, dashHighlight: 1, dashPage: 1 },
          { duration: reduced ? 0.4 : 1.0, ease: 'power2.inOut', position: 0 });
      }
      break;
    }

    /* ------------------------------------------------------------ 11 ---- */
    case 'through': {
      ch({ dashAssemble: 1, dashHighlight: 1, evidence: 0 });
      if (beatId === 'push') {
        // The beat camera holds in front of the dashboard; this leg carries the
        // lens through the plane. Widening the field is what sells the passage.
        if (!reduced) {
          tl.to(camState, {
            pz: '-=26', tz: '-=26', fov: 54,
            duration: 3.2, ease: 'power2.inOut',
          }, D + 0.6);
        }
        tweenChannels(tl, { runtimeReveal: 0.45, dashPage: 0 },
          { duration: reduced ? 0.4 : 2.4, ease: 'power2.out', position: D });
      }
      if (beatId === 'stack') {
        // Camera pose comes from the beat; only the reveal is choreographed.
        tweenChannels(tl, { runtimeReveal: 1 },
          { duration: reduced ? 0.5 : 2.8, ease: 'power3.out', position: 0.3 });
      }
      if (beatId === 'loop') {
        ch({ runtimeReveal: 1 });
        // The closing frame is the proof: dashboard, slabs, returning stream
        // and the still-turning dryer all visible at once.
        tweenChannels(tl, { loopClose: 1 },
          { duration: reduced ? 0.6 : 3.2, ease: 'power2.inOut', position: 0.2 });
      }
      break;
    }

    /* ------------------------------------------------------------ 12 ---- */
    case 'value':
      ch({ runtimeReveal: 0.2, loopClose: 1, dashAssemble: 0, straighten: 0.35 });
      // Altitude is the visual grammar for synthesis. We rise because we are
      // summarising.
      tweenChannels(tl, { ringReveal: 1 },
        { duration: reduced ? 0.5 : 1.8, ease: 'power3.inOut', position: 0.4 });
      break;

    /* ------------------------------------------------------------ 13 ---- */
    case 'roadmap': {
      ch({ ringReveal: 0.5, straighten: 0.2 });
      if (beatId === 'today') {
        tweenChannels(tl, { roadmapToday: 1, roadmapNext: 0 },
          { duration: reduced ? 0.4 : 1.6, ease: 'power3.out', position: 0.2 });
      }
      if (beatId === 'next') {
        // Built vs not-built is carried by material, opacity, line style and
        // position — four redundant channels, because it is the most important
        // honesty signal in the presentation.
        tweenChannels(tl, { roadmapToday: 1, roadmapNext: 1 },
          { duration: reduced ? 0.6 : 3.2, ease: 'none', position: 0.2 });
      }
      break;
    }

    /* ------------------------------------------------------------ 14 ---- */
    case 'return': {
      // The closing rhyme. Same frame, same light, same machine — but the
      // audience can now read the data layer, and that difference is the
      // conclusion.
      ch({
        ringReveal: 0, roadmapToday: 0, roadmapNext: 0, runtimeReveal: 0,
        loopClose: 0, straighten: 0, flowSpeed: 0.8, dryerWire: 0,
        sensorReveal: 0.4, packetFlow: 0.25, traceDraw: 1, dashAssemble: 0,
        evidence: 0,
      }, { duration: reduced ? 0.5 : 1.8 });
      break;
    }

    default:
      break;
  }
}
