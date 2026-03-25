import { useState } from 'react';
import {
  Paper, Text, Group, Button, Stack, NumberInput, Select,
  Accordion, Badge, ActionIcon, SegmentedControl
} from '@mantine/core';
import { IconPlus, IconTrash } from '@tabler/icons-react';
import { useProjectStore } from '../../state/projectStore';
import { updateProject } from '../../api/client';
import type { Equipment } from '../../types/simulation';

interface EquipmentForm {
  equipment_type: 'lsm_launch' | 'lift' | 'pneumatic_brake' | 'trim_brake' | 'booster';
  id: string;
  path_id: string;
  start_s: number;
  end_s: number;
  // LSM
  stator_count?: number;
  max_force_n?: number;
  launch_velocity_mps?: number;
  // Lift
  chain_speed_mps?: number;
  engagement_point_s?: number;
  release_point_s?: number;
  // Brake
  max_brake_force_n?: number;
  fail_safe_mode?: 'normally_open' | 'normally_closed';
}

export function EquipmentEditor() {
  const { currentProject } = useProjectStore();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<EquipmentForm>({
    equipment_type: 'lsm_launch',
    id: '',
    path_id: '',
    start_s: 0,
    end_s: 10,
    max_force_n: 10000,
  });

  if (!currentProject) {
    return (
      <Paper p="sm" withBorder>
        <Text c="dimmed">No project loaded</Text>
      </Paper>
    );
  }

  const equipmentTypes = [
    { value: 'lsm_launch', label: 'LSM Launch' },
    { value: 'lift', label: 'Lift Hill' },
    { value: 'pneumatic_brake', label: 'Pneumatic Brake' },
    { value: 'trim_brake', label: 'Trim Brake' },
    { value: 'booster', label: 'Booster' },
  ];

  const handleAddEquipment = async () => {
    if (!currentProject.id || !form.path_id) return;

    const newEquipment: Record<string, any> = {
      equipment_type: form.equipment_type,
      id: form.id || `equip_${Date.now()}`,
      path_id: form.path_id,
      start_s: form.start_s,
      end_s: form.end_s,
      enabled: true,
    };

    // Add type-specific fields
    if (form.equipment_type === 'lsm_launch') {
      newEquipment.stator_count = form.stator_count || 4;
      newEquipment.max_force_n = form.max_force_n || 10000;
      newEquipment.launch_velocity_mps = form.launch_velocity_mps || 15;
      newEquipment.magnetic_field_strength = 0.5;
    } else if (form.equipment_type === 'lift') {
      newEquipment.chain_speed_mps = form.chain_speed_mps || 2;
      newEquipment.engagement_point_s = form.engagement_point_s || form.start_s;
      newEquipment.release_point_s = form.release_point_s || form.end_s;
      newEquipment.max_pull_force_n = 5000;
    } else if (form.equipment_type === 'pneumatic_brake') {
      newEquipment.max_brake_force_n = form.max_brake_force_n || 8000;
      newEquipment.fail_safe_mode = form.fail_safe_mode || 'normally_closed';
      newEquipment.response_time_s = 0.2;
      newEquipment.air_pressure = 6;
      newEquipment.state = 'open';
    } else if (form.equipment_type === 'trim_brake') {
      newEquipment.max_force_n = form.max_brake_force_n || 3000;
      newEquipment.target_velocity_mps = 10;
    } else if (form.equipment_type === 'booster') {
      newEquipment.max_force_n = form.max_force_n || 5000;
      newEquipment.boost_duration_s = 2;
    }

    try {
      await updateProject(currentProject.id, {
        equipment: [...currentProject.equipment, newEquipment as Equipment]
      });
      setShowForm(false);
      window.location.reload();
    } catch (e) {
      console.error('Failed to add equipment:', e);
    }
  };

  const handleDeleteEquipment = async (index: number) => {
    if (!currentProject.id) return;
    const newEquipment = [...currentProject.equipment];
    newEquipment.splice(index, 1);
    try {
      await updateProject(currentProject.id, { equipment: newEquipment });
      window.location.reload();
    } catch (e) {
      console.error('Failed to delete equipment:', e);
    }
  };

  const getEquipmentLabel = (eq: any) => {
    switch (eq.equipment_type) {
      case 'lsm_launch': return `LSM Launch (${eq.launch_velocity_mps || 0} m/s)`;
      case 'lift': return `Lift Hill (${eq.chain_speed_mps || 0} m/s)`;
      case 'pneumatic_brake': return `Brake (${eq.max_brake_force_n || 0} N)`;
      case 'trim_brake': return `Trim Brake`;
      case 'booster': return `Booster`;
      default: return eq.equipment_type;
    }
  };

  return (
    <Stack gap="md">
      <Accordion variant="separated" radius="sm">
        <Accordion.Item value="equipment">
          <Accordion.Control>
            <Group justify="space-between">
              <Text size="sm" fw={600}>Equipment ({currentProject.equipment.length})</Text>
              <Badge size="sm">{currentProject.equipment.length}</Badge>
            </Group>
          </Accordion.Control>
          <Accordion.Panel>
            <Stack gap="xs">
              {/* Add equipment button */}
              {!showForm && (
                <Button
                  size="xs"
                  variant="light"
                  leftSection={<IconPlus size={14} />}
                  onClick={() => {
                    setForm({
                      ...form,
                      path_id: currentProject.paths[0]?.id || '',
                      id: `equip_${Date.now()}`
                    });
                    setShowForm(true);
                  }}
                  disabled={currentProject.paths.length === 0}
                >
                  Add Equipment
                </Button>
              )}

              {/* Equipment form */}
              {showForm && (
                <Paper p="sm" withBorder style={{ background: '#2a2a2a' }}>
                  <Text size="xs" c="dimmed" mb="xs">New Equipment</Text>
                  <Stack gap="xs">
                    <Select
                      size="xs"
                      label="Type"
                      data={equipmentTypes}
                      value={form.equipment_type}
                      onChange={(v) => setForm({ ...form, equipment_type: v as any })}
                    />
                    <Select
                      size="xs"
                      label="Path"
                      data={currentProject.paths.map(p => ({ value: p.id, label: p.name || p.id }))}
                      value={form.path_id}
                      onChange={(v) => setForm({ ...form, path_id: v || '' })}
                    />
                    <Group grow>
                      <NumberInput
                        size="xs"
                        label="Start (m)"
                        value={form.start_s}
                        onChange={(v) => setForm({ ...form, start_s: Number(v) || 0 })}
                        min={0}
                      />
                      <NumberInput
                        size="xs"
                        label="End (m)"
                        value={form.end_s}
                        onChange={(v) => setForm({ ...form, end_s: Number(v) || 0 })}
                        min={0}
                      />
                    </Group>

                    {/* Type-specific fields */}
                    {form.equipment_type === 'lsm_launch' && (
                      <>
                        <NumberInput
                          size="xs"
                          label="Launch Velocity (m/s)"
                          value={form.launch_velocity_mps}
                          onChange={(v) => setForm({ ...form, launch_velocity_mps: Number(v) || 0 })}
                        />
                        <NumberInput
                          size="xs"
                          label="Max Force (N)"
                          value={form.max_force_n}
                          onChange={(v) => setForm({ ...form, max_force_n: Number(v) || 0 })}
                        />
                      </>
                    )}

                    {form.equipment_type === 'lift' && (
                      <>
                        <NumberInput
                          size="xs"
                          label="Chain Speed (m/s)"
                          value={form.chain_speed_mps}
                          onChange={(v) => setForm({ ...form, chain_speed_mps: Number(v) || 0 })}
                        />
                        <Group grow>
                          <NumberInput
                            size="xs"
                            label="Engage (m)"
                            value={form.engagement_point_s}
                            onChange={(v) => setForm({ ...form, engagement_point_s: Number(v) || 0 })}
                          />
                          <NumberInput
                            size="xs"
                            label="Release (m)"
                            value={form.release_point_s}
                            onChange={(v) => setForm({ ...form, release_point_s: Number(v) || 0 })}
                          />
                        </Group>
                      </>
                    )}

                    {form.equipment_type === 'pneumatic_brake' && (
                      <>
                        <NumberInput
                          size="xs"
                          label="Brake Force (N)"
                          value={form.max_brake_force_n}
                          onChange={(v) => setForm({ ...form, max_brake_force_n: Number(v) || 0 })}
                        />
                        <SegmentedControl
                          size="xs"
                          fullWidth
                          value={form.fail_safe_mode}
                          onChange={(v) => setForm({ ...form, fail_safe_mode: v as any })}
                          data={[
                            { value: 'normally_closed', label: 'Fail Close' },
                            { value: 'normally_open', label: 'Fail Open' },
                          ]}
                        />
                      </>
                    )}

                    <Group grow>
                      <Button size="xs" variant="subtle" onClick={() => setShowForm(false)}>
                        Cancel
                      </Button>
                      <Button size="xs" onClick={handleAddEquipment}>
                        Add
                      </Button>
                    </Group>
                  </Stack>
                </Paper>
              )}

              {/* Existing equipment list */}
              {currentProject.equipment.map((eq, idx) => (
                <Paper key={idx} p="xs" withBorder style={{ background: '#222' }}>
                  <Group justify="space-between">
                    <Text size="xs" fw={500}>{getEquipmentLabel(eq)}</Text>
                    <ActionIcon
                      size="xs"
                      variant="subtle"
                      color="red"
                      onClick={() => handleDeleteEquipment(idx)}
                    >
                      <IconTrash size={12} />
                    </ActionIcon>
                  </Group>
                  <Group gap="xs" mt="xs">
                    <Text size="xs" c="dimmed">Path: {eq.path_id}</Text>
                    <Badge size="xs">{eq.start_s}m - {eq.end_s}m</Badge>
                  </Group>
                </Paper>
              ))}
            </Stack>
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>
    </Stack>
  );
}