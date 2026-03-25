import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid, GizmoHelper, GizmoViewport, PerspectiveCamera } from '@react-three/drei';
import { Suspense } from 'react';
import { TrackMesh } from '../TrackMesh';
import { TrainMesh } from '../TrainMesh';
import { useProjectStore } from '../../state/projectStore';
import { Box, Text } from '@mantine/core';

export function Editor3D() {
  const { currentProject, interpolatedPaths, simulationState } = useProjectStore();

  return (
    <Box style={{ width: '100%', height: '100%', position: 'relative' }}>
      <Canvas shadows>
        <PerspectiveCamera makeDefault position={[50, 50, 50]} fov={50} />
        <OrbitControls
          makeDefault
          minPolarAngle={0}
          maxPolarAngle={Math.PI / 2.1}
          enableDamping
          dampingFactor={0.05}
        />

        {/* Lighting */}
        <ambientLight intensity={0.4} />
        <directionalLight
          position={[100, 100, 50]}
          intensity={1}
          castShadow
          shadow-mapSize={[2048, 2048]}
        />
        <directionalLight position={[-50, 50, -50]} intensity={0.3} />

        {/* Grid */}
        <Grid
          args={[200, 200]}
          cellSize={5}
          cellThickness={0.5}
          cellColor="#6b7280"
          sectionSize={20}
          sectionThickness={1}
          sectionColor="#374151"
          fadeDistance={400}
          fadeStrength={1}
          followCamera={false}
          infiniteGrid
        />

        {/* Axis helper */}
        <axesHelper args={[20]} />

        <Suspense fallback={null}>
          {/* Track meshes */}
          {currentProject?.paths.map((path) => {
            const interpolatedPath = interpolatedPaths.get(path.id);
            if (!interpolatedPath) return null;
            return (
              <TrackMesh
                key={path.id}
                path={interpolatedPath}
                selected={false}
              />
            );
          })}

          {/* Train meshes */}
          {simulationState?.trains.map((trainState) => {
            const path = interpolatedPaths.get(trainState.path_id);
            if (!path) return null;
            return (
              <TrainMesh
                key={trainState.train_id}
                trainState={trainState}
                path={path}
              />
            );
          })}

          {/* Equipment overlays */}
          {/* <EquipmentOverlay /> */}
        </Suspense>

        {/* Gizmo for orientation */}
        <GizmoHelper alignment="bottom-right" margin={[80, 80]}>
          <GizmoViewport labelColor="white" axisHeadScale={1} />
        </GizmoHelper>
      </Canvas>

      {/* Info overlay */}
      <Box
        style={{
          position: 'absolute',
          top: 10,
          left: 10,
          padding: '8px 12px',
          background: 'rgba(0, 0, 0, 0.6)',
          borderRadius: 4,
        }}
      >
        <Text size="xs" c="gray.4">
          {currentProject?.metadata.name || 'No project loaded'}
        </Text>
        <Text size="xs" c="dimmed">
          Paths: {currentProject?.paths.length || 0} |
          Trains: {simulationState?.trains.length || 0}
        </Text>
      </Box>
    </Box>
  );
}