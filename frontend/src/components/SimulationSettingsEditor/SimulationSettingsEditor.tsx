import { useState } from 'react';
import {
  Paper, Text, Group, Button, Stack, NumberInput,
  Accordion, Badge
} from '@mantine/core';
import { IconDeviceFloppy } from '@tabler/icons-react';
import { useProjectStore } from '../../state/projectStore';
import { updateProject } from '../../api/client';

export function SimulationSettingsEditor() {
  const { currentProject } = useProjectStore();
  const [saving, setSaving] = useState(false);

  const settings = currentProject?.simulation_settings;

  const [form, setForm] = useState({
    time_step_s: settings?.time_step_s ?? 0.01,
    gravity_mps2: settings?.gravity_mps2 ?? 9.81,
    drag_coefficient: settings?.drag_coefficient ?? 0.5,
    rolling_resistance_coefficient: settings?.rolling_resistance_coefficient ?? 0.002,
    air_density_kg_m3: settings?.air_density_kg_m3 ?? 1.225,
  });

  if (!currentProject) {
    return (
      <Paper p="sm" withBorder>
        <Text c="dimmed">No project loaded</Text>
      </Paper>
    );
  }

  const handleSave = async () => {
    if (!currentProject.id) return;
    setSaving(true);
    try {
      await updateProject(currentProject.id, {
        simulation_settings: {
          ...currentProject.simulation_settings,
          ...form,
        }
      });
      window.location.reload();
    } catch (e) {
      console.error('Failed to save settings:', e);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Accordion variant="separated" radius="sm">
      <Accordion.Item value="settings">
        <Accordion.Control>
          <Group justify="space-between">
            <Text size="sm" fw={600}>Simulation Settings</Text>
            <Badge size="sm">Physics</Badge>
          </Group>
        </Accordion.Control>
        <Accordion.Panel>
          <Stack gap="xs">
            <Text size="xs" c="dimmed">Physics Parameters</Text>

            <Group grow>
              <NumberInput
                size="xs"
                label="Gravity (m/s²)"
                value={form.gravity_mps2}
                onChange={(v) => setForm({ ...form, gravity_mps2: Number(v) || 9.81 })}
                min={0}
                max={20}
                step={0.1}
                decimalScale={2}
              />
              <NumberInput
                size="xs"
                label="Time Step (s)"
                value={form.time_step_s}
                onChange={(v) => setForm({ ...form, time_step_s: Number(v) || 0.01 })}
                min={0.001}
                max={0.1}
                step={0.001}
                decimalScale={3}
              />
            </Group>

            <Text size="xs" c="dimmed" mt="xs">Resistance Parameters</Text>

            <NumberInput
              size="xs"
              label="Drag Coefficient (Cd)"
              value={form.drag_coefficient}
              onChange={(v) => setForm({ ...form, drag_coefficient: Number(v) || 0 })}
              min={0}
              max={2}
              step={0.01}
              decimalScale={3}
              description="0 = no air resistance, 0.5 = default"
            />

            <NumberInput
              size="xs"
              label="Rolling Resistance Coefficient (Crr)"
              value={form.rolling_resistance_coefficient}
              onChange={(v) => setForm({ ...form, rolling_resistance_coefficient: Number(v) || 0 })}
              min={0}
              max={0.1}
              step={0.0001}
              decimalScale={4}
              description="0 = no rolling friction, 0.002 = default"
            />

            <NumberInput
              size="xs"
              label="Air Density (kg/m³)"
              value={form.air_density_kg_m3}
              onChange={(v) => setForm({ ...form, air_density_kg_m3: Number(v) || 1.225 })}
              min={0}
              max={3}
              step={0.01}
              decimalScale={3}
              description="1.225 = sea level, 0 = vacuum"
            />

            <Group justify="flex-end" mt="md">
              <Button
                size="xs"
                leftSection={<IconDeviceFloppy size={14} />}
                onClick={handleSave}
                loading={saving}
              >
                Save Settings
              </Button>
            </Group>

            <Text size="xs" c="dimmed" mt="xs">
              Tip: Set Drag Coefficient and Rolling Resistance to 0 for energy conservation (no friction).
            </Text>
          </Stack>
        </Accordion.Panel>
      </Accordion.Item>
    </Accordion>
  );
}
