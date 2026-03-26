import { useState, useCallback } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid, GizmoHelper, GizmoViewport, PerspectiveCamera } from '@react-three/drei';
import { Suspense } from 'react';
import { TrackMesh } from '../TrackMesh';
import { TrainMesh } from '../TrainMesh';
import { EquipmentOverlay } from '../EquipmentOverlay';
import { PointMarkers } from '../PointMarkers/PointMarkers';
import { useProjectStore } from '../../state/projectStore';
import { updateProject, getInterpolatedPath } from '../../api/client';
import { Box, Text } from '@mantine/core';

export function Editor3D() {
  const {
    currentProject,
    interpolatedPaths,
    simulationState,
    editingMode,
    setCurrentProject,
    setInterpolatedPath,
  } = useProjectStore();

  const [selectedPointId, setSelectedPointId] = useState<string | null>(null);

  const handlePointMove = useCallback(async (pointId: string, position: { x: number; y: number; z: number }) => {
    if (!currentProject?.id) return;

    const updatedPoints = currentProject.points.map(p =>
      p.id === pointId
        ? { ...p, x: position.x, y: position.y, z: position.z }
        : p
    );

    // Optimistic update
    const updatedProject = { ...currentProject, points: updatedPoints };
    setCurrentProject(updatedProject);

    // Send to backend
    try {
      await updateProject(currentProject.id, { points: updatedPoints });

      // Refresh interpolated paths
      for (const path of currentProject.paths) {
        try {
          const interpolated = await getInterpolatedPath(currentProject.id, path.id);
          setInterpolatedPath(path.id, interpolated);
        } catch (e) {
          console.error('Failed to refresh path:', path.id, e);
        }
      }
    } catch (e) {
      console.error('Failed to update point:', e);
    }
  }, [currentProject, setCurrentProject, setInterpolatedPath]);

  return (
    <Box
      style={{ width: '100%', height: '100%', position: 'relative' }}
      onClick={() => setSelectedPointId(null)}
    >
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

          {/* Point markers for editing */}
          {currentProject && (
            <PointMarkers
              points={currentProject.points}
              selectedPointId={selectedPointId}
              onSelectPoint={setSelectedPointId}
              onPointMove={handlePointMove}
              editingMode={editingMode === 'edit'}
            />
          )}

          {/* Equipment overlays */}
          {currentProject?.equipment && currentProject.equipment.length > 0 && (
            <EquipmentOverlay
              equipment={currentProject.equipment}
              paths={interpolatedPaths}
            />
          )}

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
        onClick={(e) => e.stopPropagation()}
      >
        <Text size="xs" c="gray.4">
          {currentProject?.metadata?.name || 'No project loaded'}
        </Text>
        <Text size="xs" c="dimmed">
          Paths: {currentProject?.paths.length || 0} |
          Trains: {simulationState?.trains.length || 0} |
          Equipment: {currentProject?.equipment?.length || 0}
        </Text>
        {editingMode === 'edit' && (
          <Text size="xs" c="blue.4" mt={4}>
            Edit Mode: Click and drag points to modify track
          </Text>
        )}
      </Box>
    </Box>
  );
}