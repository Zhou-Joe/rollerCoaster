import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { AppShell, Text, Group, Box, Anchor, Button, Badge } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { useState, useEffect, useCallback } from 'react';
import { healthCheck, listProjects, getProject, getInterpolatedPath, startSimulation, stopSimulation, resetSimulation, stepSimulation, getSimulationState, createProject, updateProject } from './api/client';
import { useProjectStore } from './state/projectStore';
import { Editor3D } from './components/Editor3D';
import { SimulationPlayer } from './components/SimulationPlayer';
import { TelemetryPanel } from './components/TelemetryPanel';

function App() {
  const { data: health, isLoading } = useQuery({
    queryKey: ['health'],
    queryFn: healthCheck,
  });

  const { data: projects, refetch: refetchProjects } = useQuery({
    queryKey: ['projects'],
    queryFn: listProjects,
  });

  const {
    currentProject,
    setCurrentProject,
    simulationState,
    setSimulationState,
    setInterpolatedPath,
    playbackSpeed,
    editingMode,
    setEditingMode,
  } = useProjectStore();

  const [simulationInterval, setSimulationInterval] = useState<number | null>(null);

  // Load first project on mount
  useEffect(() => {
    if (projects && projects.length > 0 && !currentProject) {
      loadProject(projects[0].id!);
    }
  }, [projects]);

  const loadProject = async (projectId: string) => {
    try {
      const project = await getProject(projectId);
      setCurrentProject(project);

      // Load interpolated paths for rendering
      for (const path of project.paths) {
        try {
          const interpolated = await getInterpolatedPath(projectId, path.id);
          setInterpolatedPath(path.id, interpolated);
        } catch (e) {
          console.error('Failed to load path:', path.id, e);
        }
      }

      // Initialize simulation state
      try {
        const state = await getSimulationState(projectId);
        setSimulationState(state);
      } catch (e) {
        console.error('Failed to get simulation state:', e);
      }
    } catch (e) {
      console.error('Failed to load project:', e);
    }
  };

  // Simulation polling
  const pollSimulationState = useCallback(async () => {
    if (currentProject?.id) {
      try {
        const state = await stepSimulation(currentProject.id, 1);
        setSimulationState(state);
      } catch (e) {
        console.error('Failed to poll simulation:', e);
      }
    }
  }, [currentProject, setSimulationState]);

  const handlePlay = async () => {
    if (!currentProject?.id) return;
    await startSimulation(currentProject.id);
    if (simulationState) {
      setSimulationState({ ...simulationState, running: true });
    }

    // Start polling
    const interval = window.setInterval(() => {
      pollSimulationState();
    }, 100 / playbackSpeed);
    setSimulationInterval(interval);
  };

  const handlePause = async () => {
    if (!currentProject?.id) return;
    await stopSimulation(currentProject.id);
    if (simulationState) {
      setSimulationState({ ...simulationState, running: false });
    }

    if (simulationInterval) {
      clearInterval(simulationInterval);
      setSimulationInterval(null);
    }
  };

  const handleStop = async () => {
    if (!currentProject?.id) return;
    await stopSimulation(currentProject.id);
    if (simulationInterval) {
      clearInterval(simulationInterval);
      setSimulationInterval(null);
    }
  };

  const handleReset = async () => {
    if (!currentProject?.id) return;
    await resetSimulation(currentProject.id);
    if (simulationInterval) {
      clearInterval(simulationInterval);
      setSimulationInterval(null);
    }
    // Reload simulation state
    try {
      const state = await getSimulationState(currentProject.id);
      setSimulationState(state);
    } catch (e) {
      console.error('Failed to reset simulation:', e);
    }
  };

  const handleStep = async (forward: boolean) => {
    if (!currentProject?.id) return;
    if (forward) {
      const state = await stepSimulation(currentProject.id, 1);
      setSimulationState(state);
    }
  };

  const handleCreateDemoProject = async () => {
    // Create a demo project with track, vehicles, and trains
    const project = await createProject('Demo Coaster');
    const projectId = project.id!;

    // Add track points
    await updateProject(projectId, {
      points: [
        { id: 'p1', x: 0, y: 0, z: 20 },
        { id: 'p2', x: 20, y: 0, z: 25 },
        { id: 'p3', x: 40, y: 0, z: 30 },
        { id: 'p4', x: 60, y: 0, z: 25 },
        { id: 'p5', x: 80, y: 0, z: 20 },
        { id: 'p6', x: 100, y: 0, z: 15 },
        { id: 'p7', x: 100, y: 20, z: 10 },
        { id: 'p8', x: 80, y: 30, z: 5 },
        { id: 'p9', x: 60, y: 30, z: 3 },
        { id: 'p10', x: 40, y: 20, z: 5 },
        { id: 'p11', x: 20, y: 10, z: 10 },
        { id: 'p12', x: 0, y: 0, z: 20 },
      ],
      paths: [
        { id: 'main_track', name: 'Main Track', point_ids: ['p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7', 'p8', 'p9', 'p10', 'p11', 'p12'] }
      ],
      vehicles: [
        { id: 'v1', length_m: 2.0, dry_mass_kg: 500.0, capacity: 4 }
      ],
      trains: [
        { id: 'train_1', vehicle_ids: ['v1'] }
      ]
    });

    await refetchProjects();
    await loadProject(projectId);
  };

  return (
    <BrowserRouter>
      <AppShell
        padding={0}
        navbar={{
          width: 280,
          breakpoint: 'sm',
        }}
        header={{ height: 50 }}
        styles={{
          main: {
            background: '#1a1a1a',
          },
        }}
      >
        <AppShell.Navbar p="md" style={{ background: '#252525' }}>
          <Text fw={700} mb="sm" c="white" size="lg">Roller Coaster Simulator</Text>

          {/* Backend status */}
          <Group mb="md">
            <Badge size="sm" color={health ? 'green' : 'red'}>
              {isLoading ? 'Connecting...' : health ? 'Backend Connected' : 'Disconnected'}
            </Badge>
          </Group>

          {/* Project selector */}
          {projects && projects.length > 0 && (
            <Box mb="md">
              <Text size="xs" c="dimmed" mb="xs">Project</Text>
              <select
                style={{
                  background: '#333',
                  color: 'white',
                  border: '1px solid #444',
                  borderRadius: 4,
                  padding: '8px',
                  width: '100%',
                }}
                onChange={(e) => loadProject(e.target.value)}
                value={currentProject?.id || ''}
              >
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.metadata?.name || 'Untitled'}
                  </option>
                ))}
              </select>
            </Box>
          )}

          {/* Create demo button */}
          <Button
            variant="light"
            size="sm"
            mb="md"
            onClick={handleCreateDemoProject}
          >
            Create Demo Project
          </Button>

          {/* Mode selector */}
          <Box mb="md">
            <Text size="xs" c="dimmed" mb="xs">Mode</Text>
            <Group gap="xs">
              <Button
                size="xs"
                variant={editingMode === 'view' ? 'filled' : 'subtle'}
                onClick={() => setEditingMode('view')}
              >
                View
              </Button>
              <Button
                size="xs"
                variant={editingMode === 'edit' ? 'filled' : 'subtle'}
                onClick={() => setEditingMode('edit')}
              >
                Edit
              </Button>
              <Button
                size="xs"
                variant={editingMode === 'simulate' ? 'filled' : 'subtle'}
                onClick={() => setEditingMode('simulate')}
              >
                Simulate
              </Button>
            </Group>
          </Box>

          {/* Project info */}
          {currentProject && (
            <Box mb="md" p="sm" style={{ background: '#2a2a2a', borderRadius: 4 }}>
              <Text size="xs" c="dimmed" mb="xs">Project Info</Text>
              <Text size="sm" c="white">{currentProject.metadata?.name || 'Untitled'}</Text>
              <Group mt="xs">
                <Badge size="sm">Points: {currentProject.points?.length || 0}</Badge>
                <Badge size="sm">Paths: {currentProject.paths?.length || 0}</Badge>
                <Badge size="sm">Trains: {currentProject.trains?.length || 0}</Badge>
              </Group>
            </Box>
          )}

          {/* Train info */}
          {simulationState && simulationState.trains && simulationState.trains.length > 0 && (
            <Box p="sm" style={{ background: '#2a2a2a', borderRadius: 4 }}>
              <Text size="xs" c="dimmed" mb="xs">Train Status</Text>
              {simulationState.trains.map((train) => (
                <Box key={train.train_id} mb="xs">
                  <Text size="sm" c="white">{train.train_id}</Text>
                  <Group gap="xs">
                    <Badge size="xs" color={train.velocity_mps > 0 ? 'green' : 'gray'}>
                      {train.velocity_mps.toFixed(1)} m/s
                    </Badge>
                    <Text size="xs" c="dimmed">Pos: {train.s_front_m.toFixed(1)}m</Text>
                  </Group>
                </Box>
              ))}
            </Box>
          )}
        </AppShell.Navbar>

        <AppShell.Header p="xs" style={{ background: '#252525' }}>
          <Group justify="space-between" h="100%">
            <Group>
              <Text fw={600} c="white">Roller Coaster Simulator</Text>
              <Anchor component={Link} to="/" size="sm" c="gray.4">
                Dashboard
              </Anchor>
            </Group>
            <Text size="sm" c={health ? 'green' : 'red'}>
              {isLoading ? 'Connecting...' : health ? 'Backend: Connected' : 'Backend: Disconnected'}
            </Text>
          </Group>
        </AppShell.Header>

        <AppShell.Main>
          <Routes>
            <Route path="/" element={
              <Box style={{ height: 'calc(100vh - 50px)', position: 'relative' }}>
                {/* 3D Editor */}
                <Box style={{ height: '100%' }}>
                  <Editor3D />
                </Box>

                {/* Simulation Player - Bottom */}
                <Box
                  style={{
                    position: 'absolute',
                    bottom: 16,
                    left: '50%',
                    transform: 'translateX(-50%)',
                    zIndex: 100,
                  }}
                >
                  <SimulationPlayer
                    onPlay={handlePlay}
                    onPause={handlePause}
                    onStop={handleStop}
                    onReset={handleReset}
                    onStep={handleStep}
                  />
                </Box>

                {/* Telemetry Panel - Right */}
                <Box
                  style={{
                    position: 'absolute',
                    top: 16,
                    right: 16,
                    zIndex: 100,
                  }}
                >
                  <TelemetryPanel />
                </Box>
              </Box>
            } />
          </Routes>
        </AppShell.Main>
      </AppShell>
    </BrowserRouter>
  );
}

export default App;