import { Box, Paper, Text, Group, Button, Stack, Badge, Switch, Select } from '@mantine/core';
import { useProjectStore } from '../../state/projectStore';
import { useState, useEffect } from 'react';
import { resetSimulator } from '../../api/client';

interface EquipmentControlPanelProps {
  projectId?: string;
}

export function EquipmentControlPanel({ projectId }: EquipmentControlPanelProps) {
  const { currentProject, setCurrentProject } = useProjectStore();
  const [isUpdating, setIsUpdating] = useState(false);

  if (!currentProject) {
    return (
      <Paper p="sm" withBorder>
        <Text c="dimmed" size="sm">No project loaded</Text>
      </Paper>
    );
  }

  // Filter controllable equipment
  const pneumaticBrakes = currentProject.equipment.filter(
    (eq: any) => eq.equipment_type === 'pneumatic_brake'
  );
  const trimBrakes = currentProject.equipment.filter(
    (eq: any) => eq.equipment_type === 'trim_brake'
  );
  const trackSwitches = currentProject.equipment.filter(
    (eq: any) => eq.equipment_type === 'track_switch'
  );

  const hasControllableEquipment =
    pneumaticBrakes.length > 0 ||
    trimBrakes.length > 0 ||
    trackSwitches.length > 0;

  if (!hasControllableEquipment) {
    return (
      <Paper p="sm" withBorder>
        <Text c="dimmed" size="sm">No controllable equipment</Text>
      </Paper>
    );
  }

  const updateEquipmentState = async (equipmentId: string, updates: any) => {
    if (!currentProject.id) return;
    setIsUpdating(true);
    try {
      const updatedEquipment = currentProject.equipment.map((eq: any) =>
        eq.id === equipmentId ? { ...eq, ...updates } : eq
      );
      await resetSimulator(currentProject.id);
      setCurrentProject({ ...currentProject, equipment: updatedEquipment });
    } catch (e) {
      console.error('Failed to update equipment:', e);
    } finally {
      setIsUpdating(false);
    }
  };

  const toggleBrakeState = (brake: any) => {
    const newState = brake.state === 'closed' ? 'open' : 'closed';
    updateEquipmentState(brake.id, { state: newState });
  };

  const toggleTrimBrake = (brake: any) => {
    updateEquipmentState(brake.id, { enabled: !brake.enabled });
  };

  const changeSwitchAlignment = (switchEq: any, newAlignment: string) => {
    updateEquipmentState(switchEq.id, { current_alignment: newAlignment });
  };

  return (
    <Stack gap="md">
      <Text size="xs" c="dimmed">Equipment Control</Text>

      {/* Pneumatic Brakes */}
      {pneumaticBrakes.length > 0 && (
        <Paper p="sm" withBorder style={{ background: '#2a2a2a' }}>
          <Text size="sm" fw={600} c="white" mb="xs">
            Pneumatic Brakes ({pneumaticBrakes.length})
          </Text>
          <Stack gap="xs">
            {pneumaticBrakes.map((brake: any) => (
              <Paper key={brake.id} p="xs" withBorder style={{ background: '#1a1a1a' }}>
                <Group justify="space-between" mb="xs">
                  <Text size="xs" fw={500} c="white">{brake.id}</Text>
                  <Badge
                    size="xs"
                    color={brake.state === 'closed' ? 'red' : 'green'}
                    variant="filled"
                  >
                    {brake.state === 'closed' ? 'CLOSED' : 'OPEN'}
                  </Badge>
                </Group>
                <Group gap="xs">
                  <Text size="xs" c="dimmed">
                    Force: {(brake.max_brake_force_n || 0).toFixed(0)} N
                  </Text>
                  <Text size="xs" c="dimmed">
                    | s: {brake.start_s}-{brake.end_s}m
                  </Text>
                </Group>
                <Button
                  size="xs"
                  fullWidth
                  mt="xs"
                  color={brake.state === 'closed' ? 'green' : 'red'}
                  variant={brake.state === 'closed' ? 'light' : 'filled'}
                  onClick={() => toggleBrakeState(brake)}
                  disabled={isUpdating}
                >
                  {brake.state === 'closed' ? 'Open Brake' : 'Close Brake'}
                </Button>
              </Paper>
            ))}
          </Stack>
        </Paper>
      )}

      {/* Trim Brakes */}
      {trimBrakes.length > 0 && (
        <Paper p="sm" withBorder style={{ background: '#2a2a2a' }}>
          <Text size="sm" fw={600} c="white" mb="xs">
            Trim Brakes ({trimBrakes.length})
          </Text>
          <Stack gap="xs">
            {trimBrakes.map((brake: any) => (
              <Paper key={brake.id} p="xs" withBorder style={{ background: '#1a1a1a' }}>
                <Group justify="space-between" mb="xs">
                  <Text size="xs" fw={500} c="white">{brake.id}</Text>
                  <Switch
                    size="xs"
                    checked={brake.enabled !== false}
                    onChange={() => toggleTrimBrake(brake)}
                    disabled={isUpdating}
                    label={brake.enabled !== false ? 'Enabled' : 'Disabled'}
                  />
                </Group>
                <Group gap="xs">
                  <Text size="xs" c="dimmed">
                    Target: {(brake.target_velocity_mps || 0).toFixed(1)} m/s
                  </Text>
                  <Text size="xs" c="dimmed">
                    | s: {brake.start_s}-{brake.end_s}m
                  </Text>
                </Group>
              </Paper>
            ))}
          </Stack>
        </Paper>
      )}

      {/* Track Switches */}
      {trackSwitches.length > 0 && (
        <Paper p="sm" withBorder style={{ background: '#2a2a2a' }}>
          <Text size="sm" fw={600} c="white" mb="xs">
            Track Switches ({trackSwitches.length})
          </Text>
          <Stack gap="xs">
            {trackSwitches.map((switchEq: any) => (
              <Paper key={switchEq.id} p="xs" withBorder style={{ background: '#1a1a1a' }}>
                <Group justify="space-between" mb="xs">
                  <Text size="xs" fw={500} c="white">{switchEq.id}</Text>
                  <Badge size="xs" color="blue" variant="filled">
                    {switchEq.current_alignment?.slice(0, 15) || 'None'}...
                  </Badge>
                </Group>
                <Text size="xs" c="dimmed" mb="xs">
                  Outgoing paths:
                </Text>
                <Select
                  size="xs"
                  value={switchEq.current_alignment}
                  onChange={(v) => v && changeSwitchAlignment(switchEq, v)}
                  disabled={isUpdating}
                  data={switchEq.outgoing_path_ids?.map((id: string) => ({
                    value: id,
                    label: id.slice(0, 20),
                  })) || []}
                />
              </Paper>
            ))}
          </Stack>
        </Paper>
      )}
    </Stack>
  );
}
