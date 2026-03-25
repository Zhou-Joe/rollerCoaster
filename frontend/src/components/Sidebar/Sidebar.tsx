import { Text, Group, Button, Stack, Accordion, Badge, NumberInput, Paper } from '@mantine/core';
import { useProjectStore } from '../../state/projectStore';
import type { TrainPhysicsState } from '../../types';

export function Sidebar() {
  const {
    currentProject,
    simulationState,
    selectedTrainId,
    setSelectedTrain,
    editingMode,
    setEditingMode,
  } = useProjectStore();

  return (
    <Stack gap="md" p="md">
      {/* Mode Selector */}
      <Paper p="sm" withBorder>
        <Text size="sm" fw={600} mb="xs">
          Mode
        </Text>
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
      </Paper>

      {/* Project Info */}
      {currentProject && (
        <Paper p="sm" withBorder>
          <Text size="sm" fw={600} mb="xs">
            Project
          </Text>
          <Text size="lg">{currentProject.metadata.name}</Text>
          <Group mt="xs">
            <Badge size="sm">Paths: {currentProject.paths.length}</Badge>
            <Badge size="sm">Points: {currentProject.points.length}</Badge>
            <Badge size="sm">Trains: {currentProject.trains.length}</Badge>
          </Group>
        </Paper>
      )}

      {/* Trains List */}
      {simulationState && simulationState.trains.length > 0 && (
        <Accordion variant="separated" radius="sm">
          <Accordion.Item value="trains">
            <Accordion.Control>
              <Text size="sm" fw={600}>
                Trains ({simulationState.trains.length})
              </Text>
            </Accordion.Control>
            <Accordion.Panel>
              <Stack gap="xs">
                {simulationState.trains.map((train) => (
                  <TrainListItem
                    key={train.train_id}
                    train={train}
                    selected={selectedTrainId === train.train_id}
                    onClick={() => setSelectedTrain(
                      selectedTrainId === train.train_id ? null : train.train_id
                    )}
                  />
                ))}
              </Stack>
            </Accordion.Panel>
          </Accordion.Item>
        </Accordion>
      )}

      {/* Paths List */}
      {currentProject && currentProject.paths.length > 0 && (
        <Accordion variant="separated" radius="sm">
          <Accordion.Item value="paths">
            <Accordion.Control>
              <Text size="sm" fw={600}>
                Paths ({currentProject.paths.length})
              </Text>
            </Accordion.Control>
            <Accordion.Panel>
              <Stack gap="xs">
                {currentProject.paths.map((path) => (
                  <Paper
                    key={path.id}
                    p="xs"
                    withBorder
                    style={{ cursor: 'pointer' }}
                  >
                    <Text size="sm">{path.name || path.id}</Text>
                    <Text size="xs" c="dimmed">
                      {path.point_ids.length} points
                    </Text>
                  </Paper>
                ))}
              </Stack>
            </Accordion.Panel>
          </Accordion.Item>
        </Accordion>
      )}

      {/* Settings */}
      {currentProject && (
        <Accordion variant="separated" radius="sm">
          <Accordion.Item value="settings">
            <Accordion.Control>
              <Text size="sm" fw={600}>
                Simulation Settings
              </Text>
            </Accordion.Control>
            <Accordion.Panel>
              <Stack gap="xs">
                <NumberInput
                  label="Time Step (s)"
                  size="xs"
                  value={currentProject.simulation_settings.time_step_s}
                  step={0.001}
                  min={0.001}
                  max={0.1}
                />
                <NumberInput
                  label="Gravity (m/s²)"
                  size="xs"
                  value={currentProject.simulation_settings.gravity_mps2}
                  step={0.01}
                />
                <NumberInput
                  label="Drag Coefficient"
                  size="xs"
                  value={currentProject.simulation_settings.drag_coefficient}
                  step={0.01}
                  min={0}
                  max={2}
                />
              </Stack>
            </Accordion.Panel>
          </Accordion.Item>
        </Accordion>
      )}
    </Stack>
  );
}

interface TrainListItemProps {
  train: TrainPhysicsState;
  selected: boolean;
  onClick: () => void;
}

function TrainListItem({ train, selected, onClick }: TrainListItemProps) {
  return (
    <Paper
      p="xs"
      withBorder
      style={{
        cursor: 'pointer',
        borderColor: selected ? '#3b82f6' : undefined,
        background: selected ? 'rgba(59, 130, 246, 0.1)' : undefined,
      }}
      onClick={onClick}
    >
      <Group justify="space-between">
        <Text size="sm" fw={selected ? 600 : 400}>
          {train.train_id}
        </Text>
        <Badge size="xs" color={train.velocity_mps > 0 ? 'green' : 'gray'}>
          {train.velocity_mps.toFixed(1)} m/s
        </Badge>
      </Group>
      <Text size="xs" c="dimmed">
        Pos: {train.s_front_m.toFixed(1)} m
      </Text>
    </Paper>
  );
}