import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { AppShell, Text, Group, Box, Anchor } from '@mantine/core';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useState, useEffect, useCallback } from 'react';
import { healthCheck, listProjects, getProject, getInterpolatedPath, startSimulation, stopSimulation, resetSimulation, stepSimulation } from './api/client';
import { useProjectStore } from './state/projectStore';
import { Editor3D } from './components/Editor3D';
import { SimulationPlayer } from './components/SimulationPlayer';
import { TelemetryPanel } from './components/TelemetryPanel';
import { Sidebar } from './components/Sidebar';

function App() {
  const queryClient = useQueryClient();
  const { data: health, isLoading } = useQuery({
    queryKey: ['health'],
    queryFn: healthCheck,
  });

  const { data: projects } = useQuery({
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
  } = useProjectStore();

  const [simulationInterval, setSimulationInterval] = useState<number | null>(null);

  // Load first project on mount
  useEffect(() => {
    if (projects && projects.length > 0 && !currentProject) {
      const projectId = projects[0].metadata?.name || projects[0].id || '';
      if (projectId) {
        loadProject(projectId);
      }
    }
  }, [projects]);

  const loadProject = async (projectId: string) => {
    try {
      const project = await getProject(projectId);
      setCurrentProject(project);

      // Load interpolated paths
      for (const path of project.paths) {
        try {
          const interpolated = await getInterpolatedPath(projectId, path.id);
          setInterpolatedPath(path.id, interpolated);
        } catch (e) {
          console.error('Failed to load path:', path.id, e);
        }
      }
    } catch (e) {
      console.error('Failed to load project:', e);
    }
  };

  // Simulation polling
  const pollSimulationState = useCallback(async () => {
    if (currentProject) {
      try {
        const state = await stepSimulation(currentProject.metadata.name, 1);
        setSimulationState(state);
      } catch (e) {
        console.error('Failed to poll simulation:', e);
      }
    }
  }, [currentProject, setSimulationState]);

  const handlePlay = async () => {
    if (!currentProject) return;
    await startSimulation(currentProject.metadata.name);
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
    if (!currentProject) return;
    await stopSimulation(currentProject.metadata.name);
    if (simulationState) {
      setSimulationState({ ...simulationState, running: false });
    }

    if (simulationInterval) {
      clearInterval(simulationInterval);
      setSimulationInterval(null);
    }
  };

  const handleStop = async () => {
    if (!currentProject) return;
    await stopSimulation(currentProject.metadata.name);
    if (simulationInterval) {
      clearInterval(simulationInterval);
      setSimulationInterval(null);
    }
  };

  const handleReset = async () => {
    if (!currentProject) return;
    await resetSimulation(currentProject.metadata.name);
    if (simulationInterval) {
      clearInterval(simulationInterval);
      setSimulationInterval(null);
    }
    // Reload simulation state
    queryClient.invalidateQueries({ queryKey: ['simulation'] });
  };

  const handleStep = async (forward: boolean) => {
    if (!currentProject) return;
    if (forward) {
      const state = await stepSimulation(currentProject.metadata.name, 1);
      setSimulationState(state);
    }
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
        <AppShell.Navbar p="xs" style={{ background: '#252525' }}>
          <Text fw={700} mb="md" c="white">Roller Coaster Simulator</Text>
          <Text size="sm" c="dimmed">Phase 6 - Frontend</Text>

          {/* Project selector */}
          {projects && projects.length > 0 && (
            <Group mt="md">
              <Text size="xs" c="dimmed">Project:</Text>
              <select
                style={{
                  background: '#333',
                  color: 'white',
                  border: '1px solid #444',
                  borderRadius: 4,
                  padding: '4px 8px',
                  flex: 1,
                }}
                onChange={(e) => loadProject(e.target.value)}
                value={currentProject?.metadata?.name || ''}
              >
                {projects.map((p) => (
                  <option key={p.metadata?.name || p.id} value={p.metadata?.name || p.id}>
                    {p.metadata?.name || p.id}
                  </option>
                ))}
              </select>
            </Group>
          )}

          {/* Sidebar content */}
          <Box mt="md" style={{ flex: 1, overflow: 'auto' }}>
            <Sidebar />
          </Box>
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