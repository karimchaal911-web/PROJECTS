import { tweenChannels } from './usePresence.js';
import { SCENES } from '../state/scenes.js';

/**
 * Per-scene choreography, appended to the Rig's single transition timeline.
 *
 * Everything here answers "why is this moving?" with narrative, causality,
 * spatial or hierarchical intent. Decorative motion was cut — see
 * design/MOTION_SPEC.md, "Motion that was considered and cut".
 */

/**
 * The easing vocabulary.
 *
 * The camera already had one — TIER_EASE in the scene table gives a nudge, a
 * shot change, an act change and the journey home four different curves. The
 * WORLD did not. Forty-eight channel tweens used ten different curves, which
 * looks varied in a grep and is not: `power2.out` was doing duty for a vessel
 * filling, a chart appearing, a service starting and a label fading, so the
 * variety was incidental rather than meaningful. Motion that eases the same way
 * regardless of what is moving is what makes a film feel assembled from a
 * library.
 *
 * Seven intents, and every world tween now names one:
 *
 *   MECH    something with mass moves. Slow to leave, committed through the
 *           middle, slow to arrive. The material path straightening into a time
 *           axis, the artifact folding into a service, the loop rising.
 *   ARRIVE  an object lands and stops. No wind-up at all — it is already moving
 *           on the first frame — and a long settle, which is what reads as
 *           weight coming to rest rather than as a fade finishing.
 *   DATA    a value resolving. Crisp and short. A number does not have inertia,
 *           and pretending it does is how a dashboard starts to feel syrupy.
 *   REVEAL  something becomes visible without moving. Restrained and almost
 *           linear; anything more assertive turns an appearance into an event.
 *   ALARM   the anomaly grammar: an accelerating departure. A process state
 *           leaving its learned region does not ease politely out of it, and the
 *           constant-rate crawl this used to have made a genuine excursion look
 *           like a scheduled animation.
 *   COUNT   linear, and deliberately so. Used only where the animation is
 *           counting real arrivals — the architecture assembling from packets,
 *           the runtime lighting its checkpoints, the marker crossing the dryer.
 *           Easing these would be a lie about a rate.
 *   SOLID   the one overshoot in the film, reserved for the six laboratory
 *           results, because they are the only directly measured points in it.
 */
export const EASE = {
  MECH: 'power3.inOut',
  ARRIVE: 'power4.out',
  DATA: 'power2.out',
  REVEAL: 'power1.inOut',
  ALARM: 'power2.in',
  COUNT: 'none',
  SOLID: 'back.out(1.4)',
};

/**
 * Every animation channel the show owns, at rest.
 *
 * This exists so that jumping directly to a scene can put the world into a
 * complete state. Previously a number-key jump only applied the destination's
 * layer presence, which left the sub-animations of scenes that were never
 * played frozen at zero — sensors present but unrevealed, packets not flowing,
 * the flow path unstraightened in a scene that assumes a time axis.
 */
/**
 * How far the material has travelled when a scene-03 beat is settled.
 *
 * ONE table, used by both paths. There were two: `buildTransition` walked eight
 * beats through these values while `sceneChannelState` computed a different
 * number from a four-entry lookup, so a number-key jump — or a WebGL context
 * restore — put the chain head somewhere the arrow key never would. Four of the
 * eight beats disagreed, by as much as the whole first half of the chain: beat
 * 5 settled at 0.48 and jumped to 0. Found by scripts/qa-channels.mjs.
 */
export const CHAIN_REACHED = {
  enter: 0.00, acid: 0.02, vapor: 0.16, neutral: 0.33,
  buffer: 0.48, crystal: 0.64, centri: 0.80, todryer: 1.0,
};

export const BASELINE = {
  straighten: 0, flowSpeed: 1, chainHead: 0,
  dryerWire: 0, axisDraw: 0, labRise: 0, traceDraw: 0,
  sensorReveal: 0, packetFlow: 0, archBuild: 0, archLabels: 0, alignPause: 0,
  residenceTravel: 0, residenceRails: 0, residenceAlign: 0,
  artifactCard: 0, artifactFold: 0, serviceLive: 0, inferStream: 0,
  laneSplit: 0, laneFocus: 0, manifoldReveal: 0, supportReveal: 0,
  supportFocus: 0, trajectory: 0,
  evidence: 0, evidenceBeat: 0, evidencePoints: 0,
  dashAssemble: 0, dashPage: 0, dashHighlight: 0,
  runtimeReveal: 0, runtimePath: 0, operatorReveal: 0, loopClose: 0,
  sensorChips: 1, granuleSize: 1,
  ringReveal: 0, ringTravel: 0, roadmapToday: 0, roadmapNext: 0,
  materialReveal: 0,
};

/**
 * The settled channel state of a given step, independent of how we got there.
 * Used only for random access; the ordinary path animates into these values.
 */
export function sceneChannelState(sceneIndex, beatIndex) {
  const scene = SCENES[sceneIndex];
  const id = scene.beats?.[beatIndex]?.id ?? null;
  const at = (n) => Math.max(0, Math.min(1, n));

  switch (scene.id) {
    case 'awakening':
      return { flowSpeed: 0.35 };
    case 'material':
      return { flowSpeed: 0.5, materialReveal: 1 };
    case 'chain':
      // granuleSize is part of the settled state too: at the chain's camera
      // distances the process-scene granule size reads as gravel, and the
      // transition sets 0.45 for exactly that reason. Omitting it here meant a
      // jump into scene 03 showed granules twice the size the walked path does.
      return { flowSpeed: 1, straighten: 0, granuleSize: 0.45, chainHead: at(CHAIN_REACHED[id] ?? 1) };
    case 'dryer':
      return {
        chainHead: 1,
        dryerWire: id === 'physics' ? 1 : id === 'data' ? 0.5 : 0,
        sensorReveal: id === 'data' ? 1 : 0,
      };
    case 'gap':
      return {
        // The stream is 66-93 units from the lens on the first two beats and
        // 31 on the travel; at its process-scene size it subtends about two
        // pixels out there and reads as dust, and at 2.2 up close it reads as
        // gravel. Sized to the distance the beat actually uses.
        granuleSize: id === 'travel' ? 1.5 : 2.2,
        straighten: 1, axisDraw: 1, sensorReveal: 0.25,
        labRise: id === 'form' ? 0 : 1.6,
      };
    case 'response':
      return {
        granuleSize: 2.8,
        straighten: 1, axisDraw: 1, labRise: 1.6,
        sensorReveal: id === 'fill' ? 1 : 0.5,
        // The value chips belong to scene 04's framing. Here the equipment is
        // far off to the left, so all they contributed was four half-cropped
        // readings bleeding in at the frame edge across the soft-sensor trace.
        sensorChips: 0,
        traceDraw: id === 'fill' ? 1 : 0,
      };
    case 'digital': {
      const residence = id === 'delay' || id === 'align';
      return {
        straighten: 1, axisDraw: 1, labRise: 1.6, traceDraw: 1,
        dryerWire: id === 'sense' ? 1 : 0,
        sensorReveal: 1,
        packetFlow: id === 'sense' ? 0.35 : residence ? 0.25 : 1,
        archBuild: id === 'sense' ? 0 : 1,
        archLabels: id === 'sense' ? 0 : 1,
        alignPause: id === 'align' ? 1 : 0,
        // The value chips are laid out for scene 04's framing and scene 06
        // switches them off; scene 07 is further away still, so they stay off.
        // The walked path inherited that 0 and a jump reset it to 1, which put
        // four foreshortened readings at the frame edge of a scene that has
        // nothing to do with them.
        sensorChips: 0,
        // The lane's settled state: the marker has crossed on both residence
        // beats, and the second beat additionally holds the two rails with the
        // shift applied.
        residenceTravel: residence ? 1 : 0,
        residenceRails: id === 'align' ? 1 : 0,
        residenceAlign: id === 'align' ? 1 : 0,
      };
    }
    case 'pathways':
      return {
        straighten: 1, axisDraw: 1, labRise: 1.6, traceDraw: 1,
        archBuild: 1, archLabels: 1, packetFlow: 1, laneSplit: 1,
        laneFocus: id === 'quality' ? -1 : id === 'process' ? 1 : 0,
        manifoldReveal: id === 'process' ? 1 : id === 'quality' ? 0.25 : 0,
        supportReveal: id === 'process' ? 1 : 0,
        supportFocus: id === 'process' ? 1 : 0,
        trajectory: id === 'process' ? 1 : 0,
      };
    case 'evidence':
      return {
        straighten: 1, axisDraw: 1, labRise: 1.6, traceDraw: 1,
        evidence: 1, evidencePoints: 1,
        evidenceBeat: { moisture: 1, candidates: 2, anomaly: 3, limits: 4 }[id] ?? 1,
      };
    case 'supervision':
      return {
        straighten: 1, evidencePoints: 1,
        dashAssemble: 1,
        dashHighlight: id === 'become' ? 0 : 1,
        dashPage: id === 'diagnostics' ? 1 : 0,
        // The handover has RUN by the time this beat is settled: the artifact
        // is gone, the service is loaded, the stream has landed. A random-access
        // jump to scene 10 must not show a live artifact card floating over a
        // finished dashboard.
        // The handover has RUN by the time this beat is settled: the artifact is
        // gone, the service has handed off, the page is what remains. A
        // random-access jump into scene 10 must not park a live artifact card
        // and a lit service cube on top of a finished dashboard.
        artifactCard: 0,
        artifactFold: id === 'become' ? 1 : 0,
        serviceLive: 0,
        inferStream: 0,
      };
    case 'through':
      return {
        straighten: 1, dashAssemble: 1, dashHighlight: 0,
        runtimeReveal: id === 'loop' ? 0.3 : 1,
        runtimePath: id === 'push' ? 0.18 : 1,
        operatorReveal: id === 'loop' ? 1 : 0,
        loopClose: id === 'loop' ? 1 : 0,
        // 0.7 on THE RUNTIME PATH, not 0.4: that is what the transition raises
        // it to while the camera travels with the data, and the stream is the
        // beat's subject.
        packetFlow: id === 'loop' ? 1 : id === 'path' ? 0.7 : 0.4,
      };
    case 'value':
      return { ringReveal: 1, ringTravel: 1 };
    case 'roadmap':
      return { roadmapToday: 1, roadmapNext: id === 'next' ? 1 : 0 };
    case 'return':
      return { flowSpeed: 0.8, sensorReveal: 1, sensorChips: 0, packetFlow: id === 'questions' ? 0.12 : 0.3, traceDraw: 0 };
    default:
      return {};
  }
}

/**
 * Diagnostics: the settled state of a step, as random access computes it.
 *
 * scripts/qa-channels.mjs walks the film the way a presenter does and compares
 * what each step actually settles to against what a number-key jump — or a
 * WebGL context restore — would put there instead. The two are supposed to be
 * the same world. They were not: see the table this check found.
 */
if (typeof window !== 'undefined') {
  window.__SETTLED__ = (sceneIndex, beatIndex) => ({
    ...BASELINE, ...sceneChannelState(sceneIndex, beatIndex),
  });
}

export function buildTransition(tl, ctx) {
  const { scene, beat, duration, reduced, camState, camPose, restored } = ctx;
  const D = reduced ? 0.4 : duration;
  const beatId = scene.beats?.[beat]?.id ?? null;
  /**
   * A restored WebGL context does not re-run the choreography.
   *
   * The Rig has already put every channel into the settled state of the step
   * the presenter is on, and it deliberately leaves the camera alone. Building
   * the beat's timeline on top of that REPLAYS it — and several beats own
   * absolute timings that do not scale with the transition duration, so the
   * effect is not subtle: a context loss during scene 10 re-ran the whole
   * nine-second artifact-to-service sequence on top of a dashboard the
   * presenter had already been talking over for a minute. Caught by
   * scripts/qa-restore.mjs, which reported `artifactCard: 0 -> 1` and
   * `serviceLive: 0 -> 0.999` across a restore that should have changed nothing.
   *
   * Everything below this line is "how we got here". A restore did not get
   * here; it was already here.
   */
  if (restored) return;

  /**
   * Camera choreography, suppressed on a context restore.
   *
   * Kept as a guard even though the early return above makes it unreachable
   * today: these four in-shot moves — the opening settle, the push across the
   * machine, the truck down the time axis, the scene-10 arrival — are the ones
   * that would be most obviously wrong if any future path reached them with a
   * camera that is already where the move ends.
   */
  const cam = (fn) => { if (!restored) fn(); };

  const ch = (values, opts = {}) =>
    tweenChannels(tl, values, { duration: D, ease: 'power2.inOut', position: 0, ...opts });

  switch (scene.id) {
    /* ------------------------------------------------------------ 01 ---- */
    case 'awakening':
      ch({ ...BASELINE, flowSpeed: 0.35 });
      // The plant is not switched on — it is found. Rim light arriving last is
      // what makes the drum read as a solid object rather than a shape.
      cam(() => {
        if (reduced) return;
        tl.fromTo(camState,
          { pz: camPose.pos[2] + 7, px: camPose.pos[0] - 8 },
          { pz: camPose.pos[2], px: camPose.pos[0], duration: 3.4, ease: 'power2.out' }, 0);
      });
      break;

    /* ------------------------------------------------------------ 02 ---- */
    case 'material':
      // The product is a photograph of the real product. Nothing is animated
      // except its arrival; the three words are presenter-driven beats now,
      // not a 1.9 s interval the speaker cannot control.
      ch({ flowSpeed: 0.5, straighten: 0, chainHead: 0, granuleSize: 1 });
      tweenChannels(tl, { materialReveal: 1 },
        { duration: reduced ? 0.4 : 1.6, ease: EASE.REVEAL, position: 0.2 });
      break;

    /* ------------------------------------------------------------ 03 ---- */
    case 'chain': {
      ch({ flowSpeed: 1, straighten: 0, materialReveal: 0, granuleSize: 0.45 });
      // Stations light because the material arrives, not because time passed —
      // and we now travel with it, so the fill tracks the beat we are at.
      // One entry per stage the material actually passes through. The head
      // lands ON a station's own t, which is what puts that station — and only
      // that station — under the tracking key light and at full label strength.
      const reached = CHAIN_REACHED;
      // Eased, not linear: the material ARRIVES at a stage and settles there
      // rather than sliding through it at constant speed.
      tweenChannels(tl, { chainHead: reached[beatId] ?? 1 },
        { duration: reduced ? 0.6 : D * 1.15, ease: EASE.ARRIVE, position: 0.15 });
      break;
    }

    /* ------------------------------------------------------------ 04 ---- */
    case 'dryer': {
      ch({ chainHead: 1, flowSpeed: 1, straighten: 0, materialReveal: 0, granuleSize: 1 });
      if (beatId === 'machine') {
        ch({ dryerWire: 0, sensorReveal: 0 });
        // A slow drift across the machine, so it is understood in the round.
        // It used to run 22 s at a dead-constant velocity and stop where it
        // stopped: the longest single hold in the film, and the one piece of
        // camera work that read as a turntable render. Thirteen seconds is
        // still long enough to see the machine in the round, and the curve now
        // decelerates into rest so the shot ARRIVES rather than being cut off.
        // Eight and a half seconds, not thirteen. The machine is understood
        // in the round about two thirds of the way through the old move; the
        // remainder was the film's longest hold on a shot that had already
        // said what it had to say. The curve still decelerates into rest, so
        // it ARRIVES rather than being cut off.
        cam(() => {
          if (reduced) return;
          tl.to(camState, { px: '-=8', pz: '-=5.4', duration: 8.4, ease: 'power1.out' }, D);
        });
      }
      if (beatId === 'physics') {
        ch({ dryerWire: 1, sensorReveal: 0 }, { duration: reduced ? 0.4 : 1.3 });
      }
      if (beatId === 'data') {
        ch({ dryerWire: 0.5 }, { duration: reduced ? 0.4 : 0.8 });
        tweenChannels(tl, { sensorReveal: 1 },
          { duration: reduced ? 0.4 : 1.4, ease: EASE.DATA, position: 0.3 });
      }
      break;
    }

    /* ------------------------------------------------------------ 05 ---- */
    case 'gap': {
      ch({ dryerWire: 0, sensorReveal: 0.25, flowSpeed: 1,
        granuleSize: beatId === 'travel' ? 1.5 : 2.2 });
      if (beatId === 'form') {
        // THE move: distance becomes time. The camera holds still for it —
        // it used to travel 46 units while the thing it was there to show
        // was happening.
        tweenChannels(tl, { straighten: 1, axisDraw: 1 },
          { duration: reduced ? 0.5 : 2.6, ease: EASE.MECH, position: 0.35 });
        ch({ labRise: 0, traceDraw: 0 });
      }
      if (beatId === 'markers') {
        ch({ straighten: 1, axisDraw: 1 });
        // The only overshoot in the film, reserved for the one thing that is
        // actually measured. Overshoot reads as solidity.
        tweenChannels(tl, { labRise: 1.6 },
          { duration: reduced ? 0.4 : 1.8, ease: EASE.SOLID, position: 0.15 });
      }
      if (beatId === 'travel') {
        ch({ straighten: 1, axisDraw: 1, labRise: 1.6 });
        // Constant velocity, no easing — the only linear move in the film.
        // The jury is meant to feel the duration, not admire the camera. The
        // point lands inside five seconds; the last second and a half was the
        // audience waiting for a move whose meaning they already had.
        cam(() => {
          if (reduced) return;
          tl.to(camState, {
            px: '+=34', tx: '+=34', duration: 5.2, ease: 'none',
          }, D);
        });
      }
      break;
    }

    /* ------------------------------------------------------------ 06 ---- */
    case 'response': {
      ch({ straighten: 1, axisDraw: 1, labRise: 1.6, flowSpeed: 1, sensorChips: 0, granuleSize: 2.8 });
      if (beatId === 'question') {
        ch({ traceDraw: 0, sensorReveal: 0.5 });
      }
      if (beatId === 'fill') {
        tweenChannels(tl, { sensorReveal: 1 },
          { duration: reduced ? 0.3 : 0.9, ease: EASE.DATA, position: 0 });
        // The trace is drawn by the arriving signals, not by a timer.
        tweenChannels(tl, { traceDraw: 1 },
          { duration: reduced ? 0.6 : 4.4, ease: EASE.REVEAL, position: 0.6 });
      }
      break;
    }

    /* ------------------------------------------------------------ 07 ---- */
    case 'digital': {
      ch({ straighten: 1, axisDraw: 1, traceDraw: 1, labRise: 1.6, granuleSize: 1 });
      if (beatId === 'sense') {
        ch({ dryerWire: 1, sensorReveal: 1, packetFlow: 0.35, archBuild: 0, archLabels: 0, alignPause: 0 },
          { duration: reduced ? 0.4 : 1.4 });
      }
      if (beatId === 'stack') {
        // The wireframe has done its job; leaving it up only hazed the frame
        // behind the stack.
        ch({ dryerWire: 0, sensorReveal: 1, packetFlow: 1 });
        // Each layer forms when its packets arrive. The architecture is a
        // consequence, not an illustration — and its label now arrives WITH
        // it, so no name ever floats beside an empty space.
        // The stack builds at a constant rate because it is counting arriving
        // packets, not performing. The labels lag their own slab by a beat —
        // the layer exists first, then it is named.
        tweenChannels(tl, { archBuild: 1 },
          { duration: reduced ? 0.8 : 4.2, ease: EASE.COUNT, position: 0.4 });
        tweenChannels(tl, { archLabels: 1 },
          { duration: reduced ? 0.8 : 4.2, ease: EASE.COUNT, position: 0.85 });
      }
      /* BEAT 3 — the delay is PHYSICAL. A machine with a length. */
      if (beatId === 'delay') {
        ch({ dryerWire: 0, archBuild: 1, archLabels: 1, packetFlow: 0.25, alignPause: 0 });
        ch({ residenceRails: 0, residenceAlign: 0 }, { duration: reduced ? 0.3 : 0.6 });
        // The marker crosses at CONSTANT speed and it is deliberately slow.
        // Twenty-four minutes is the whole claim; easing it, or rushing it,
        // would make it read as a UI progress bar rather than as a plug of
        // material falling down an inclined shell.
        tweenChannels(tl, { residenceTravel: 0 }, { duration: 0.01, position: 0 });
        tweenChannels(tl, { residenceTravel: 1 },
          { duration: reduced ? 0.8 : 4.6, ease: EASE.COUNT, position: D * 0.55 });
      }

      /* BEAT 4 — therefore the data must be shifted. */
      if (beatId === 'align') {
        ch({ dryerWire: 0, archBuild: 1, archLabels: 1, packetFlow: 0.25 });
        ch({ residenceTravel: 1 }, { duration: reduced ? 0.2 : 0.5 });
        // Order matters and it is the order of the argument: the rails and the
        // WRONG pairing arrive first, are held long enough to be understood as
        // wrong, and only then does the correction happen.
        tweenChannels(tl, { residenceRails: 1 },
          { duration: reduced ? 0.4 : 1.3, ease: EASE.DATA, position: 0.15 });
        tweenChannels(tl, { residenceAlign: 1 },
          { duration: reduced ? 0.5 : 1.7, ease: EASE.MECH, position: 2.9 });
        // And the pipeline it belongs to lights up as the shift lands: the
        // ALIGN layer of the stack behind, and the marked packet that waits
        // inside it. The lane is an explanation of the stack, so the stack has
        // to acknowledge the explanation.
        tweenChannels(tl, { alignPause: 1 },
          { duration: reduced ? 0.5 : 2.4, ease: EASE.REVEAL, position: 4.4 });
      }
      break;
    }

    /* ------------------------------------------------------------ 08 ---- */
    case 'pathways': {
      ch({ dryerWire: 0, archBuild: 1, archLabels: 1, alignPause: 0 });
      if (beatId === 'split') {
        // One input, two questions. The split must be seen to happen to the
        // same data, so instance targets are reassigned rather than re-emitted.
        tweenChannels(tl, { laneSplit: 1, packetFlow: 1 },
          { duration: reduced ? 0.4 : 1.6, ease: EASE.MECH, position: 0.2 });
        ch({ manifoldReveal: 0, supportReveal: 0, supportFocus: 0, trajectory: 0, laneFocus: 0 });
      }
      if (beatId === 'quality') {
        ch({ laneSplit: 1, laneFocus: -1, manifoldReveal: 0.25 });
      }
      if (beatId === 'process') {
        ch({ laneSplit: 1, laneFocus: 1 });
        tweenChannels(tl, { manifoldReveal: 1 },
          { duration: reduced ? 0.4 : 1.2, ease: EASE.DATA, position: 0.2 });
        // supportFocus dims the 2,400-point cloud while the 136 support
        // vectors come up, so the claim "these define the boundary" is
        // something the audience can actually see rather than take on trust.
        tweenChannels(tl, { supportReveal: 1, supportFocus: 1 },
          { duration: reduced ? 0.4 : 1.4, ease: EASE.DATA, position: 1.2 });
        // The point follows its real recorded trajectory out of the region.
        // This used to be its own beat with a 6-unit camera move.
        // The trajectory leaves the learned region. Anomaly grammar: fast
        // onset, controlled recovery — `power1.in` starts it drifting and lets
        // it accelerate out, rather than the constant crawl it used to have,
        // which made a departure look like a scheduled animation.
        tweenChannels(tl, { trajectory: 1 },
          { duration: reduced ? 0.8 : 4.6, ease: EASE.ALARM, position: 2.4 });
      }
      break;
    }

    /* ------------------------------------------------------------ 09 ---- */
    case 'evidence': {
      ch({
        laneSplit: 0, manifoldReveal: 0, trajectory: 0, supportReveal: 0,
        supportFocus: 0, packetFlow: 0, archBuild: 0, archLabels: 0,
        dryerWire: 0, straighten: 1, axisDraw: 1, labRise: 1.6, traceDraw: 1,
        dashAssemble: 0, dashHighlight: 0,
      });
      const beats = { moisture: 1, candidates: 2, anomaly: 3, limits: 4 };
      tweenChannels(tl, { evidence: 1, evidenceBeat: beats[beatId] ?? 1 },
        { duration: reduced ? 0.4 : 1.6, ease: EASE.ARRIVE, position: 0.3 });
      if (beatId === 'moisture') {
        // 165 real points accumulating: 1.3 s of evidence arriving.
        tweenChannels(tl, { evidencePoints: 1 },
          { duration: reduced ? 0.4 : 1.3, ease: EASE.COUNT, position: 0.6 });
      }
      break;
    }

    /* ------------------------------------------------------------ 10 ---- */
    case 'supervision': {
      // The evidence gallery goes fully away. It used to be held at 0.3 and
      // stayed legible over the dashboard for the whole scene — two different
      // charts on screen at once, under a headline claiming they were one.
      ch({ evidence: 0, evidencePoints: 1, straighten: 1, runtimeReveal: 0, runtimePath: 0 });
      if (beatId === 'become') {
        /**
         * THE SIGNATURE SEQUENCE — artifact, service, inference, screen.
         *
         * The beat used to be a two-second cross-fade under a keynote headline.
         * It is now the one true transformation in the film, and it is staged
         * as a chain of consequences rather than as a set of simultaneous
         * reveals: each stage may only begin once the previous one has visibly
         * finished, because the argument IS the ordering.
         *
         *   0.4  the artifact resolves and is READ — filenames, hash, notebook
         *   3.2  it tips and folds into a service (the words leave first)
         *   3.6  the service materialises and starts ticking at the project's
         *        own five seconds, so the fold has something to land IN
         *   5.4  inference travels the corridor toward the screen
         *   6.4  the report resolves BECAUSE the stream arrived — not on a timer
         *   7.4  the corridor dissolves as the screen it feeds comes up
         *
         * The last two overlap by 1.2 s on purpose. The service does not exit
         * and then the report arrive; they cross, which is the difference
         * between a sequence of reveals and a hand-over. By the time the beat
         * settles nothing is left in front of the page — a 3.4-unit solid at
         * 68 % of frame width sits squarely on the trend chart, and the rule
         * that nothing shares the frame with the deliverable is older and more
         * important than this sequence.
         */
        ch({ dashPage: 0, dashHighlight: 0 });
        ch({ artifactCard: 0, artifactFold: 0, serviceLive: 0, inferStream: 0 },
          { duration: 0.01 });

        if (reduced) {
          tweenChannels(tl, { artifactCard: 1, artifactFold: 1, serviceLive: 1, inferStream: 1 },
            { duration: 0.5, ease: 'power2.out', position: 0.1 });
          tweenChannels(tl, { dashAssemble: 1 },
            { duration: 0.5, ease: 'power2.out', position: 0.3 });
        } else {
          // Reveal: smooth and restrained. A file does not bounce.
          tweenChannels(tl, { artifactCard: 1 },
            { duration: 1.5, ease: EASE.REVEAL, position: 0.4 });
          // Mechanical: heavy in, decisive through, heavy out. This is an
          // object being handed over, and it should feel like it has mass.
          tweenChannels(tl, { artifactFold: 1 },
            { duration: 1.5, ease: EASE.MECH, position: 3.2 });
          // Data: crisp. A process either loaded or it did not.
          tweenChannels(tl, { serviceLive: 1 },
            { duration: 1.6, ease: EASE.DATA, position: 3.6 });
          tweenChannels(tl, { inferStream: 1 },
            { duration: 2.4, ease: EASE.REVEAL, position: 5.4 });
          tweenChannels(tl, { dashAssemble: 1 },
            { duration: 2.2, ease: EASE.ARRIVE, position: 6.4 });
          // The hand-over completes: the corridor dissolves into the page it
          // was feeding. Not a cut and not a wipe — the two cross.
          tweenChannels(tl, { artifactCard: 0, serviceLive: 0, inferStream: 0 },
            { duration: 2.0, ease: EASE.REVEAL, position: 7.4 });
          // An arrival, not a zoom. Starting nine units further back and
          // settling onto the scene's own pose means the report GROWS into the
          // frame as it resolves — and because the move ends exactly where the
          // settled pose already was, it cannot crop the page.
          cam(() => {
            tl.fromTo(camState,
              { pz: camPose.pos[2] + 9, py: camPose.pos[1] + 1.2 },
              { pz: camPose.pos[2], py: camPose.pos[1], duration: 8.2, ease: 'power2.out' }, 0);
          });
        }
      }
      if (beatId === 'assemble') {
        ch({ dashAssemble: 1, dashPage: 0 });
        // The handover has done its work. Nothing may share the frame with the
        // page the operator actually reads.
        tweenChannels(tl, { artifactCard: 0, inferStream: 0, serviceLive: 0 },
          { duration: reduced ? 0.3 : 1.1, ease: 'power2.in', position: 0 });
        // Five regions, not eight, and 1.3 s each rather than 0.55 s: this is
        // a walkthrough the presenter speaks over, not a light show.
        tweenChannels(tl, { dashHighlight: 1 },
          { duration: reduced ? 0.6 : 5.4, ease: EASE.COUNT, position: 0.8 });
      }
      if (beatId === 'diagnostics') {
        ch({ dashAssemble: 1, dashHighlight: 1 });
        tweenChannels(tl, { dashPage: 1 },
          { duration: reduced ? 0.4 : 1.1, ease: EASE.REVEAL, position: 0.4 });
      }
      break;
    }

    /* ------------------------------------------------------------ 11 ---- */
    case 'through': {
      // Highlight chrome from scene 10 must not survive into this scene; it
      // used to sit on top of the runtime reveal.
      ch({ dashHighlight: 0, evidence: 0 });
      if (beatId === 'push') {
        // Strict order: the callout boxes clear, the camera crosses the plane,
        // and only once it is on the far side does the runtime exist. The
        // report itself needs no fade — it is front-facing, so passing through
        // it swaps the page for the back of the screen on its own.
        tweenChannels(tl, { dashPage: 0 },
          { duration: reduced ? 0.2 : 0.5, ease: 'power2.in', position: 0 });
        tweenChannels(tl, { runtimeReveal: 1 },
          { duration: reduced ? 0.4 : 1.7, ease: EASE.REVEAL, position: D * 0.52 });
        tweenChannels(tl, { runtimePath: 0.18 },
          { duration: reduced ? 0.4 : 1.2, ease: EASE.COUNT, position: D * 0.6 });
      }
      if (beatId === 'path') {
        ch({ runtimeReveal: 1 });
        // Checkpoints light in data-flow order as we reach them.
        tweenChannels(tl, { runtimePath: 1 },
          { duration: reduced ? 0.5 : 3.0, ease: EASE.COUNT, position: 0.2 });
        tweenChannels(tl, { packetFlow: 0.7 },
          { duration: reduced ? 0.4 : 1.4, ease: 'power2.out', position: 0.2 });
      }
      if (beatId === 'loop') {
        // The route recedes to a faint trail arriving from behind the report:
        // the subject of this beat is the report and the person under it, not
        // the plumbing we have just walked.
        ch({ runtimeReveal: 0.3, runtimePath: 1, dashAssemble: 1 });
        // The stream terminates at the operator. It used to run back into the
        // dryer, which reads as closed-loop control — something this project
        // explicitly does not implement.
        //
        // Flow goes to full while layer presence drops to 0.6: fewer packets,
        // moving faster, arriving at a person. The transition used to leave it
        // at the 0.7 the previous beat raised it to while the random-access
        // table said 1, which is the last of the four disagreements
        // scripts/qa-channels.mjs found between the two paths.
        tweenChannels(tl, { packetFlow: 1 },
          { duration: reduced ? 0.4 : 1.5, ease: EASE.DATA, position: 0.3 });
        tweenChannels(tl, { operatorReveal: 1 },
          { duration: reduced ? 0.5 : 1.8, ease: EASE.ARRIVE, position: 0.6 });
        tweenChannels(tl, { loopClose: 1 },
          { duration: reduced ? 0.6 : 3.0, ease: EASE.MECH, position: 0.4 });
      }
      break;
    }

    /* ------------------------------------------------------------ 12 ---- */
    case 'value':
      ch({
        runtimeReveal: 0, runtimePath: 0, operatorReveal: 0, loopClose: 0,
        dashAssemble: 0, dashHighlight: 0, packetFlow: 0, straighten: 0,
      });
      // Altitude is the visual grammar for synthesis. We rise because we are
      // summarising.
      tweenChannels(tl, { ringReveal: 1 },
        { duration: reduced ? 0.5 : 1.6, ease: EASE.MECH, position: 0.5 });
      // One signal travels the loop once. It replaces an ambient breathing
      // pulse that was the only direction cue and could not be read at all.
      tweenChannels(tl, { ringTravel: 1 },
        { duration: reduced ? 0.6 : 4.0, ease: EASE.COUNT, position: 1.1 });
      break;

    /* ------------------------------------------------------------ 13 ---- */
    case 'roadmap': {
      ch({ ringReveal: 0, ringTravel: 0, straighten: 0 });
      if (beatId === 'today') {
        tweenChannels(tl, { roadmapToday: 1, roadmapNext: 0 },
          { duration: reduced ? 0.4 : 1.6, ease: EASE.ARRIVE, position: 0.2 });
      }
      if (beatId === 'next') {
        // Built vs not-built is carried by material, opacity, line style and
        // position — because it is the most important honesty signal here.
        tweenChannels(tl, { roadmapToday: 1 }, { duration: 0.3, position: 0 });
        tweenChannels(tl, { roadmapNext: 1 },
          { duration: reduced ? 0.6 : 3.0, ease: EASE.COUNT, position: 0.4 });
      }
      break;
    }

    /* ------------------------------------------------------------ 14 ---- */
    case 'return': {
      // The closing rhyme. Same frame, same light, same machine — but the
      // audience can now read the data layer, and that difference is the
      // conclusion. The telemetry is fully revealed, never frozen part-way
      // through its own stagger as it used to be.
      ch({
        ringReveal: 0, ringTravel: 0, roadmapToday: 0, roadmapNext: 0,
        runtimeReveal: 0, runtimePath: 0, operatorReveal: 0, loopClose: 0,
        straighten: 0, flowSpeed: 0.8, dryerWire: 0, traceDraw: 0, granuleSize: 1,
        dashAssemble: 0, dashHighlight: 0, evidence: 0, materialReveal: 0,
        laneSplit: 0, archBuild: 0, archLabels: 0,
      }, { duration: reduced ? 0.5 : Math.min(2.0, D) });
      // The value chips are laid out for scene 04's framing; from the opening
      // pose they are off-axis, foreshortened and cropped, and the last frame
      // of the film must be quiet. The instrumented POINTS stay.
      tweenChannels(tl, { sensorChips: 0 },
        { duration: reduced ? 0.3 : 1.0, ease: 'power2.inOut', position: 0 });
      tweenChannels(tl, { sensorReveal: 1, packetFlow: beatId === 'questions' ? 0.12 : 0.3 },
        { duration: reduced ? 0.5 : 2.2, ease: EASE.REVEAL, position: D * 0.45 });
      break;
    }

    default:
      break;
  }
}
