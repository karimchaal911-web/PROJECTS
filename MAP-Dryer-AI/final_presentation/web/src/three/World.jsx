import { Suspense } from 'react';
import Lighting from './Lighting.jsx';
import StudioEnv from './StudioEnv.jsx';
import Rig from './Rig.jsx';
import Plant from './layers/Plant.jsx';
import Dryer from './layers/Dryer.jsx';
import DryerInternals from './layers/DryerInternals.jsx';
import Granules from './layers/Granules.jsx';
import ProcessChain from './layers/ProcessChain.jsx';
import TimeAxis from './layers/TimeAxis.jsx';
import SensorNodes from './layers/SensorNodes.jsx';
import DataPackets from './layers/DataPackets.jsx';
import Architecture from './layers/Architecture.jsx';
import Residence from './layers/Residence.jsx';
import Pathways from './layers/Pathways.jsx';
import Evidence from './layers/Evidence.jsx';
import Dashboard from './layers/Dashboard.jsx';
import Handover from './layers/Handover.jsx';
import Runtime from './layers/Runtime.jsx';
import ValueLoop from './layers/ValueLoop.jsx';
import Roadmap from './layers/Roadmap.jsx';
import Material from './layers/Material.jsx';
import Prewarm from './Prewarm.jsx';
import PerfGuard from './PerfGuard.jsx';
import Post from './Post.jsx';
import { useShow } from '../state/useShow.js';

/**
 * The persistent world.
 *
 * Every layer is mounted once, for the whole show, and never unmounted. Scenes
 * change presence, not membership — that is what lets the camera return to the
 * opening pose in scene 14 and find the same machine still turning.
 */
export default function World() {
  const safeMode = useShow((s) => s.safeMode);
  return (
    <>
      <StudioEnv />
      <Lighting />
      <Rig />
      <Suspense fallback={null}>
        <Material />
        <Plant />
        <Dryer />
        <DryerInternals />
        <Granules />
        <ProcessChain />
        <TimeAxis />
        <SensorNodes />
        <DataPackets />
        <Architecture />
        <Residence />
        <Pathways />
        <Evidence />
        <Dashboard />
        <Handover />
        <Runtime />
        <ValueLoop />
        <Roadmap />
        <Prewarm />
      </Suspense>
      <PerfGuard />
      {/* Post-processing is the first thing safe mode gives up. Unmounting it
          hands rendering straight back to r3f, mid-show, with no reload. */}
      {!safeMode && <Post />}
    </>
  );
}
