import { useState, useCallback, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid, GizmoHelper, GizmoViewport, PerspectiveCamera } from '@react-three/drei';
import { Suspense } from 'react';
import { TrackMesh } from '../TrackMesh';
import { TrainMesh } from '../TrainMesh';
import { EquipmentOverlay } from '../EquipmentOverlay';
import { PointMarkers } from '../PointMarkers/PointMarkers';
import { Scenery } from '../Scenery/Scenery';
import { useProjectStore } from '../../state/projectStore';
import { updateProject, getInterpolatedPath, resetSimulator } from '../../api/client';
import { Box, Text, Button, Tooltip } from '@mantine/core';
import { IconRefresh } from '@tabler/icons-react';

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
  const [isDragging, setIsDragging] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Ensure all paths are loaded when simulation state changes
  useEffect(() => {
    if (!currentProject?.id || !simulationState) return;

    // Check if any train is on a path we don't have loaded
    for (const train of simulationState.trains) {
      if (!interpolatedPaths.has(train.path_id)) {
        console.log(`[DEBUG] Loading missing path: ${train.path_id}`);
        getInterpolatedPath(currentProject.id, train.path_id)
          .then(path => {
            setInterpolatedPath(train.path_id, path);
          })
          .catch(err => {
            console.error(`Failed to load path ${train.path_id}:`, err);
          });
      }
    }
  }, [simulationState?.trains, currentProject?.id, interpolatedPaths, setInterpolatedPath]);

  const handlePointMove = useCallback(async (pointId: string, position: { x: number; y: number; z: number }) => {
    if (!currentProject?.id) return;

    const updatedPoints = currentProject.points.map(p =>
      p.id === pointId
        ? { ...p, x: position.x, y: position.y, z: position.z }
        : p
    );

    // Optimistic update - only update local state during drag
    const updatedProject = { ...currentProject, points: updatedPoints };
    setCurrentProject(updatedProject);
  }, [currentProject, setCurrentProject]);

  // Manual refresh function for track geometry
  const handleRefreshTrack = useCallback(async () => {
    if (!currentProject?.id) return;

    setIsRefreshing(true);
    try {
      // Save current points to backend
      await updateProject(currentProject.id, { points: currentProject.points });

      // Reset the simulator so it uses new geometry for physics calculations
      await resetSimulator(currentProject.id);

      // Refresh interpolated paths for 3D rendering
      for (const path of currentProject.paths) {
        try {
          const interpolated = await getInterpolatedPath(currentProject.id, path.id);
          setInterpolatedPath(path.id, interpolated);
        } catch (e) {
          console.error('Failed to refresh path:', path.id, e);
        }
      }
    } catch (e) {
      console.error('Failed to refresh track:', e);
    } finally {
      setIsRefreshing(false);
    }
  }, [currentProject, setInterpolatedPath]);

  return (
    <Box
      style={{ width: '100%', height: '100%', position: 'relative' }}
      onClick={() => setSelectedPointId(null)}
    >
      <Canvas shadows gl={{ antialias: true, alpha: false }} style={{ background: 'linear-gradient(to bottom, #87CEEB, #B0E0E6)' }}>
        <color attach="background" args={['#87CEEB']} />
        <fog attach="fog" args={['#B0E0E6', 100, 400]} />
        <PerspectiveCamera makeDefault position={[50, 50, 50]} fov={50} />
        <OrbitControls
          makeDefault
          minPolarAngle={0}
          maxPolarAngle={Math.PI / 2.1}
          enableDamping
          dampingFactor={0.05}
          enabled={!isDragging}
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

        {/* Scenery - grass ground and trees */}
        <Scenery paths={interpolatedPaths} />

        {/* Grid - semi-transparent to work with grass */}
        <Grid
          args={[200, 200]}
          cellSize={5}
          cellThickness={0.3}
          cellColor="#888"
          sectionSize={20}
          sectionThickness={0.5}
          sectionColor="#666"
          fadeDistance={300}
          fadeStrength={1}
          followCamera={false}
          infiniteGrid
          position={[0, 0.05, 0]}
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
              onDragStateChange={setIsDragging}
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
            if (!path) {
              // Log missing path for debugging
              console.warn(`[TrainMesh] Path ${trainState.path_id} not loaded, train ${trainState.train_id} will not render`);
              // Path not loaded yet, will be loaded by useEffect
              return null;
            }
            return (
              <TrainMesh
                key={trainState.train_id}
                trainState={trainState}
                path={path}
                project={currentProject ?? undefined}
              />
            );
          })}
        </Suspense>

        {/* Gizmo for orientation */}
        <GizmoHelper alignment="bottom-right" margin={[80, 80]}>
          <GizmoViewport labelColor="black" axisHeadScale={1} />
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

      {/* Refresh Track Button - shown in edit mode */}
      {editingMode === 'edit' && (
        <Box
          style={{
            position: 'absolute',
            top: 10,
            right: 10,
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <Tooltip label="Refresh track geometry after dragging points">
            <Button
              size="xs"
              variant="filled"
              color="blue"
              leftSection={<IconRefresh size={14} />}
              onClick={handleRefreshTrack}
              loading={isRefreshing}
            >
              Refresh Track
            </Button>
          </Tooltip>
        </Box>
      )}
    </Box>
  );
}
