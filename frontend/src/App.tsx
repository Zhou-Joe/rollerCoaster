import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { AppShell, Text, Group, Box, Anchor, Button, Badge, Tabs, ScrollArea, Modal, Stack, ActionIcon } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { useState, useEffect, useRef } from 'react';
import { healthCheck, listProjects, getProject, getInterpolatedPath, startSimulation, stopSimulation, resetSimulation, stepSimulation, getSimulationState, createProject, updateProject, deleteProject, resetSimulator } from './api/client';
import { useProjectStore } from './state/projectStore';
import { Editor3D } from './components/Editor3D';
import { SimulationPlayer } from './components/SimulationPlayer';
import { TelemetryPanel } from './components/TelemetryPanel';
import { SimulationPanel } from './components/SimulationPanel';
import { TrackEditor } from './components/TrackEditor/TrackEditor';
import { EquipmentEditor } from './components/EquipmentEditor/EquipmentEditor';
import { VehicleEditor } from './components/VehicleEditor/VehicleEditor';
import { JunctionEditor } from './components/JunctionEditor/JunctionEditor';
import { ProjectManager } from './components/ProjectManager/ProjectManager';
import { SwitchControlPanel } from './components/SwitchControlPanel/SwitchControlPanel';
import { IconTrash } from '@tabler/icons-react';

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
    interpolatedPaths,
    playbackSpeed,
    editingMode,
    setEditingMode,
  } = useProjectStore();

  const [activeTab, setActiveTab] = useState<string>('track');
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  // Ref to track if simulation loop should continue - prevents stale updates after stop
  const simulationRunningRef = useRef(false);
  // Ref to track animation frame for cancellation
  const animationFrameRef = useRef<number | null>(null);
  // Ref to track if a step is currently in progress
  const stepInProgressRef = useRef(false);

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

  const handlePlay = async () => {
    if (!currentProject?.id) return;
    await startSimulation(currentProject.id);
    if (simulationState) {
      setSimulationState({ ...simulationState, running: true });
    }

    // Mark simulation as running
    simulationRunningRef.current = true;
    stepInProgressRef.current = false;

    // Calculate steps per frame based on speed
    // At high speeds, we do more backend steps per animation frame
    const getStepsPerFrame = () => {
      if (playbackSpeed <= 1) return 1;
      if (playbackSpeed <= 10) return Math.round(playbackSpeed / 2);
      if (playbackSpeed <= 50) return Math.round(playbackSpeed);
      return Math.round(playbackSpeed * 2);
    };

    const stepsPerFrame = getStepsPerFrame();

    // Target frame time based on speed (for smooth animation)
    const getTargetFrameTime = () => {
      if (playbackSpeed <= 1) return 50; // 20fps for slow-mo
      if (playbackSpeed <= 10) return 33; // 30fps for normal
      return 50; // 20fps for fast speeds (less janky)
    };

    const targetFrameTime = getTargetFrameTime();
    let lastFrameTime = performance.now();

    const runSimulationLoop = async () => {
      if (!simulationRunningRef.current) return;

      const now = performance.now();
      const elapsed = now - lastFrameTime;

      // Only step if enough time has passed and no step is currently in progress
      if (elapsed >= targetFrameTime && !stepInProgressRef.current) {
        lastFrameTime = now;
        stepInProgressRef.current = true;

        try {
          if (currentProject?.id && simulationRunningRef.current) {
            const state = await stepSimulation(currentProject.id, stepsPerFrame);
            if (simulationRunningRef.current) {
              setSimulationState(state);
            }
          }
        } catch (e) {
          console.error('Failed to step simulation:', e);
        } finally {
          stepInProgressRef.current = false;
        }
      }

      // Schedule next frame
      if (simulationRunningRef.current) {
        animationFrameRef.current = requestAnimationFrame(runSimulationLoop);
      }
    };

    // Start the loop
    animationFrameRef.current = requestAnimationFrame(runSimulationLoop);
  };

  const handlePause = async () => {
    // Stop accepting simulation updates immediately
    simulationRunningRef.current = false;
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (!currentProject?.id) return;
    await stopSimulation(currentProject.id);
    if (simulationState) {
      setSimulationState({ ...simulationState, running: false });
    }
  };

  const handleStop = async () => {
    // Stop accepting simulation updates immediately
    simulationRunningRef.current = false;
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (!currentProject?.id) return;
    await stopSimulation(currentProject.id);
    // Update simulation state to show stopped
    if (simulationState) {
      setSimulationState({ ...simulationState, running: false });
    }
  };

  const handleReset = async () => {
    // Stop accepting simulation updates immediately
    simulationRunningRef.current = false;
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (!currentProject?.id) return;
    await resetSimulation(currentProject.id);
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
        // Branch track points
        { id: 'p13', x: 60, y: 50, z: 3, bank_deg: 0 },
        { id: 'p14', x: 40, y: 60, z: 8, bank_deg: 15 },
        { id: 'p15', x: 20, y: 50, z: 15, bank_deg: 0 },
      ],
      paths: [
        { id: 'main_track', name: 'Main Track', point_ids: ['p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7', 'p8', 'p9', 'p10', 'p11', 'p12'] },
        { id: 'branch_track', name: 'Branch Track', point_ids: ['p9', 'p13', 'p14', 'p15'] }
      ],
      junctions: [
        {
          id: 'junction_1',
          incoming_path_id: 'main_track',
          outgoing_path_ids: ['main_track', 'branch_track'],
          position_s: 180
        }
      ],
      vehicles: [
        { id: 'v1', length_m: 2.0, dry_mass_kg: 500.0, capacity: 4, passenger_mass_per_person_kg: 75 },
        { id: 'v2', length_m: 2.0, dry_mass_kg: 500.0, capacity: 4, passenger_mass_per_person_kg: 75 },
        { id: 'v3', length_m: 2.0, dry_mass_kg: 500.0, capacity: 4, passenger_mass_per_person_kg: 75 },
        { id: 'v4', length_m: 2.0, dry_mass_kg: 500.0, capacity: 4, passenger_mass_per_person_kg: 75 },
        { id: 'v5', length_m: 2.0, dry_mass_kg: 500.0, capacity: 4, passenger_mass_per_person_kg: 75 }
      ],
      trains: [
        { id: 'train_1', vehicle_ids: ['v1', 'v2', 'v3', 'v4', 'v5'], current_path_id: 'main_segment_1', front_position_s: 5.0 }
      ],
      equipment: [
        {
          equipment_type: 'lift',
          id: 'lift_1',
          path_id: 'main_segment_1',
          start_s: 0,
          end_s: 130,
          lift_speed_mps: 2,
          engagement_point_s: 5,
          release_point_s: 120,
          enabled: true
        },
        {
          equipment_type: 'pneumatic_brake',
          id: 'brake_1',
          path_id: 'main_segment_2',
          start_s: 10,
          end_s: 20,
          max_brake_force_n: 8000,
          fail_safe_mode: 'normally_closed',
          response_time_s: 0.2,
          air_pressure: 6,
          state: 'open',
          enabled: true
        },
        {
          equipment_type: 'track_switch',
          id: 'switch_1',
          path_id: 'main_track',
          start_s: 175,
          end_s: 185,
          junction_id: 'junction_1',
          incoming_path_id: 'main_track',
          outgoing_path_ids: ['main_track', 'branch_track'],
          current_alignment: 'main_track',
          actuation_time_s: 2.0,
          locked_when_occupied: true
        }
      ],
      simulation_settings: {
        time_step_s: 0.01,
        gravity_mps2: 9.81,
        drag_coefficient: 0.5,
        rolling_resistance_coefficient: 0.05,
        air_density_kg_m3: 1.225
      }
    });

    // Reset simulator to ensure it uses the new project data
    await resetSimulator(projectId);

    await refetchProjects();
    await loadProject(projectId);
  };

  const handleDeleteProject = async (id: string) => {
    try {
      await deleteProject(id);
      setDeleteConfirmId(null);
      await refetchProjects();
      // If we deleted the current project, select another one
      if (currentProject?.id === id) {
        setCurrentProject(null);
        // The useEffect will load the first available project
      }
    } catch (e) {
      console.error('Failed to delete project:', e);
    }
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
              {/* Project Manager */}
              <ProjectManager
                currentProject={currentProject}
                onSelectProject={loadProject}
              />

              {/* Demo button */}
              <Button size="xs" variant="light" onClick={handleCreateDemoProject} fullWidth mb="md">
                Create Demo Coaster
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
                  <Group justify="space-between">
                    <Text size="sm" c="white" fw={500}>{currentProject.metadata?.name || 'Untitled'}</Text>
                    <ActionIcon
                      size="xs"
                      variant="subtle"
                      color="red"
                      onClick={() => setDeleteConfirmId(currentProject.id!)}
                    >
                      <IconTrash size={14} />
                    </ActionIcon>
                  </Group>
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
                      <Tabs.Tab value="junctions" style={{ fontSize: '12px' }}>Junctions</Tabs.Tab>
                      <Tabs.Tab value="equipment" style={{ fontSize: '12px' }}>Equipment</Tabs.Tab>
                      <Tabs.Tab value="vehicles" style={{ fontSize: '12px' }}>Vehicles</Tabs.Tab>
                    </Tabs.List>

                    <Tabs.Panel value="track" pt="md">
                      <TrackEditor />
                    </Tabs.Panel>

                    <Tabs.Panel value="junctions" pt="md">
                      <JunctionEditor />
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
                <>
                  <SimulationPanel
                    simulationState={simulationState}
                    interpolatedPaths={interpolatedPaths}
                  />
                  <Box mt="md">
                    <SwitchControlPanel />
                  </Box>
                </>
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

      {/* Delete Confirmation Modal */}
      <Modal
        opened={deleteConfirmId !== null}
        onClose={() => setDeleteConfirmId(null)}
        title="Delete Project"
        size="sm"
      >
        <Stack gap="md">
          <Text size="sm">
            Are you sure you want to delete this project? This action cannot be undone.
          </Text>
          <Group grow>
            <Button variant="subtle" onClick={() => setDeleteConfirmId(null)}>
              Cancel
            </Button>
            <Button
              color="red"
              onClick={() => handleDeleteProject(deleteConfirmId!)}
            >
              Delete
            </Button>
          </Group>
        </Stack>
      </Modal>
    </BrowserRouter>
  );
}

export default App;