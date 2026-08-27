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
import Pathways from './layers/Pathways.jsx';
import Evidence from './layers/Evidence.jsx';
import Dashboard from './layers/Dashboard.jsx';
import Runtime from './layers/Runtime.jsx';
import ValueLoop from './layers/ValueLoop.jsx';
import Roadmap from './layers/Roadmap.jsx';

/**
 * The persistent world.
 *
 * Every layer is mounted once, for the whole show, and never unmounted. Scenes
 * change presence, not membership — that is what lets the camera return to the
 * opening pose in scene 14 and find the same machine still turning.
 */
export default function World() {
  return (
    <>
      <StudioEnv />
      <Lighting />
      <Rig />
      <Suspense fallback={null}>
        <Plant />
        <Dryer />
        <DryerInternals />
        <Granules />
        <ProcessChain />
        <TimeAxis />
        <SensorNodes />
        <DataPackets />
        <Architecture />
        <Pathways />
        <Evidence />
        <Dashboard />
        <Runtime />
        <ValueLoop />
        <Roadmap />
      </Suspense>
    </>
  );
}
