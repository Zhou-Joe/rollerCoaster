import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { AppShell, Text, Group, Box, Anchor, Button, Badge, Tabs, ScrollArea } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { useState, useEffect, useCallback } from 'react';
import { healthCheck, listProjects, getProject, getInterpolatedPath, startSimulation, stopSimulation, resetSimulation, stepSimulation, getSimulationState, createProject, updateProject } from './api/client';
import { useProjectStore } from './state/projectStore';
import { Editor3D } from './components/Editor3D';
import { SimulationPlayer } from './components/SimulationPlayer';
import { TelemetryPanel } from './components/TelemetryPanel';
import { TrackEditor } from './components/TrackEditor/TrackEditor';
import { EquipmentEditor } from './components/EquipmentEditor/EquipmentEditor';
import { VehicleEditor } from './components/VehicleEditor/VehicleEditor';

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
  const [activeTab, setActiveTab] = useState<string>('track');

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
    const project = await createProject('Demo Coaster');
    const projectId = project.id!;

    await updateProject(projectId, {
      points: [
        { id: 'p1', x: 0, y: 0, z: 20, bank_deg: 0 },
        { id: 'p2', x: 20, y: 0, z: 25, bank_deg: 0 },
        { id: 'p3', x: 40, y: 0, z: 30, bank_deg: 0 },
        { id: 'p4', x: 60, y: 0, z: 25, bank_deg: 0 },
        { id: 'p5', x: 80, y: 0, z: 20, bank_deg: 0 },
        { id: 'p6', x: 100, y: 0, z: 15, bank_deg: 0 },
        { id: 'p7', x: 100, y: 20, z: 10, bank_deg: 20 },
        { id: 'p8', x: 80, y: 30, z: 5, bank_deg: 30 },
        { id: 'p9', x: 60, y: 30, z: 3, bank_deg: 0 },
        { id: 'p10', x: 40, y: 20, z: 5, bank_deg: -20 },
        { id: 'p11', x: 20, y: 10, z: 10, bank_deg: 0 },
        { id: 'p12', x: 0, y: 0, z: 20, bank_deg: 0 },
      ],
      paths: [
        { id: 'main_track', name: 'Main Track', point_ids: ['p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7', 'p8', 'p9', 'p10', 'p11', 'p12'] }
      ],
      vehicles: [
        { id: 'v1', length_m: 2.0, dry_mass_kg: 500.0, capacity: 4, passenger_mass_per_person_kg: 75 }
      ],
      trains: [
        { id: 'train_1', vehicle_ids: ['v1'] }
      ],
      equipment: [
        {
          equipment_type: 'lift',
          id: 'lift_1',
          path_id: 'main_track',
          start_s: 0,
          end_s: 45,
          chain_speed_mps: 2,
          engagement_point_s: 5,
          release_point_s: 40,
          max_pull_force_n: 5000,
          enabled: true
        },
        {
          equipment_type: 'pneumatic_brake',
          id: 'brake_1',
          path_id: 'main_track',
          start_s: 100,
          end_s: 110,
          max_brake_force_n: 8000,
          fail_safe_mode: 'normally_closed',
          response_time_s: 0.2,
          air_pressure: 6,
          state: 'open',
          enabled: true
        }
      ]
    });

    await refetchProjects();
    await loadProject(projectId);
  };

  const handleNewProject = async () => {
    const project = await createProject('New Project');
    await refetchProjects();
    await loadProject(project.id!);
  };

  return (
    <BrowserRouter>
      <AppShell
        padding={0}
        navbar={{
          width: 320,
          breakpoint: 'sm',
        }}
        header={{ height: 50 }}
        styles={{
          main: {
            background: '#1a1a1a',
          },
        }}
      >
        <AppShell.Navbar style={{ background: '#252525' }}>
          <AppShell.Section p="md">
            <Text fw={700} c="white" size="lg">Roller Coaster Simulator</Text>
            <Group mt="xs">
              <Badge size="sm" color={health ? 'green' : 'red'}>
                {isLoading ? 'Connecting...' : health ? 'Backend Connected' : 'Disconnected'}
              </Badge>
            </Group>
          </AppShell.Section>

          <AppShell.Section p="md" grow>
            <ScrollArea.Autosize mah="calc(100vh - 200px)">
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

              {/* Action buttons */}
              <Group mb="md" grow>
                <Button size="xs" variant="light" onClick={handleNewProject}>
                  New Project
                </Button>
                <Button size="xs" variant="light" onClick={handleCreateDemoProject}>
                  Demo
                </Button>
              </Group>

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
                  <Text size="sm" c="white" fw={500}>{currentProject.metadata?.name || 'Untitled'}</Text>
                  <Group mt="xs">
                    <Badge size="sm">Points: {currentProject.points?.length || 0}</Badge>
                    <Badge size="sm">Paths: {currentProject.paths?.length || 0}</Badge>
                    <Badge size="sm">Trains: {currentProject.trains?.length || 0}</Badge>
                    <Badge size="sm">Equip: {currentProject.equipment?.length || 0}</Badge>
                  </Group>
                </Box>
              )}

              {/* Editor tabs */}
              {editingMode === 'edit' && (
                <Box>
                  <Tabs value={activeTab} onChange={(v) => setActiveTab(v || 'track')}>
                    <Tabs.List>
                      <Tabs.Tab value="track" style={{ fontSize: '12px' }}>Track</Tabs.Tab>
                      <Tabs.Tab value="equipment" style={{ fontSize: '12px' }}>Equipment</Tabs.Tab>
                      <Tabs.Tab value="vehicles" style={{ fontSize: '12px' }}>Vehicles</Tabs.Tab>
                    </Tabs.List>

                    <Tabs.Panel value="track" pt="md">
                      <TrackEditor />
                    </Tabs.Panel>

                    <Tabs.Panel value="equipment" pt="md">
                      <EquipmentEditor />
                    </Tabs.Panel>

                    <Tabs.Panel value="vehicles" pt="md">
                      <VehicleEditor />
                    </Tabs.Panel>
                  </Tabs>
                </Box>
              )}

              {/* Simulation info */}
              {editingMode === 'simulate' && simulationState && (
                <Box>
                  <Text size="xs" c="dimmed" mb="xs">Simulation</Text>
                  <Box p="sm" style={{ background: '#2a2a2a', borderRadius: 4 }}>
                    <Text size="sm" c="white">Time: {simulationState.time_s.toFixed(2)}s</Text>
                    <Text size="xs" c="dimmed">
                      Status: {simulationState.running ? 'Running' : 'Stopped'}
                    </Text>
                  </Box>

                  {simulationState.trains.map((train) => (
                    <Box key={train.train_id} p="sm" mt="sm" style={{ background: '#2a2a2a', borderRadius: 4 }}>
                      <Text size="sm" c="white" fw={500}>{train.train_id}</Text>
                      <Group gap="xs" mt="xs">
                        <Badge size="xs" color={train.velocity_mps > 0 ? 'green' : 'gray'}>
                          {train.velocity_mps.toFixed(1)} m/s
                        </Badge>
                        <Badge size="xs">{train.acceleration_mps2.toFixed(2)} m/s²</Badge>
                      </Group>
                      <Group gap="xs" mt="xs">
                        <Text size="xs" c="dimmed">Pos: {train.s_front_m.toFixed(1)}m</Text>
                      </Group>
                      <Group gap="xs" mt="xs">
                        <Badge size="xs" variant="light">G: {train.gforces.resultant_g.toFixed(2)}</Badge>
                      </Group>
                    </Box>
                  ))}
                </Box>
              )}
            </ScrollArea.Autosize>
          </AppShell.Section>
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
                <Box style={{ height: '100%' }}>
                  <Editor3D />
                </Box>

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