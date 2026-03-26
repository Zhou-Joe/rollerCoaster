import { useState } from 'react';
import {
  Paper, Text, Group, Stack, Select,
  Accordion, Badge, ActionIcon
} from '@mantine/core';
import { IconSwitchHorizontal, IconRefresh } from '@tabler/icons-react';
import { useProjectStore } from '../../state/projectStore';
import { updateProject } from '../../api/client';
import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export function SwitchControlPanel() {
  const { currentProject } = useProjectStore();
  const [updating, setUpdating] = useState<string | null>(null);

  if (!currentProject) {
    return (
      <Paper p="sm" withBorder>
        <Text c="dimmed">No project loaded</Text>
      </Paper>
    );
  }

  // Get all track switches from equipment
  const switches = currentProject.equipment?.filter(
    (eq: any) => eq.equipment_type === 'track_switch'
  ) || [];

  const handleSwitchAlignment = async (switchEquip: any, newAlignment: string) => {
    if (!currentProject.id) return;

    setUpdating(switchEquip.id);
    try {
      // Call backend API to update switch alignment
      await api.post(`/physics/projects/${currentProject.id}/switches/${switchEquip.id}/alignment`, {
        switch_id: switchEquip.id,
        alignment: newAlignment
      });

      // Update local state
      const newEquipment = currentProject.equipment.map((eq: any) => {
        if (eq.id === switchEquip.id) {
          return { ...eq, current_alignment: newAlignment };
        }
        return eq;
      });

      await updateProject(currentProject.id, { equipment: newEquipment });
    } catch (e) {
      console.error('Failed to switch alignment:', e);
    } finally {
      setUpdating(null);
    }
  };

  const getOutgoingPathNames = (switchEquip: any) => {
    const outgoingIds = switchEquip.outgoing_path_ids || [];
    return outgoingIds.map((id: string) => {
      const path = currentProject.paths.find((p: any) => p.id === id);
      return { value: id, label: path?.name || id.slice(0, 8) };
    }).filter((x: any) => x.value);
  };

  return (
    <Stack gap="md">
      <Accordion variant="separated" radius="sm" defaultValue="switches">
        <Accordion.Item value="switches">
          <Accordion.Control>
            <Group justify="space-between">
              <Text size="sm" fw={600}>Track Switches ({switches.length})</Text>
              <Badge size="sm">{switches.length}</Badge>
            </Group>
          </Accordion.Control>
          <Accordion.Panel>
            <Stack gap="xs">
              {switches.length === 0 && (
                <Text size="xs" c="dimmed">
                  No track switches configured. Add one in the Equipment tab.
                </Text>
              )}

              {switches.map((sw: any) => {
                const outgoingOptions = getOutgoingPathNames(sw);
                const currentAlignment = sw.current_alignment || '';

                return (
                  <Paper key={sw.id} p="sm" withBorder style={{ background: '#2a2a2a' }}>
                    <Group justify="space-between" mb="xs">
                      <Group gap="xs">
                        <IconSwitchHorizontal size={16} color="#74c0fc" />
                        <Text size="xs" fw={500}>{sw.id.slice(0, 12)}...</Text>
                      </Group>
                      <ActionIcon
                        size="xs"
                        variant="subtle"
                        loading={updating === sw.id}
                        onClick={() => {
                          // Toggle to the other path
                          const otherPath = outgoingOptions.find((o: any) => o.value !== currentAlignment);
                          if (otherPath) {
                            handleSwitchAlignment(sw, otherPath.value);
                          }
                        }}
                      >
                        <IconRefresh size={14} />
                      </ActionIcon>
                    </Group>

                    <Group grow>
                      <Select
                        size="xs"
                        label="Current Route"
                        data={outgoingOptions}
                        value={currentAlignment}
                        onChange={(v) => v && handleSwitchAlignment(sw, v)}
                        disabled={updating === sw.id}
                      />
                    </Group>

                    <Group gap="xs" mt="xs">
                      <Text size="xs" c="dimmed">From:</Text>
                      <Text size="xs">{sw.incoming_path_id?.slice(0, 8) || sw.path_id?.slice(0, 8)}...</Text>
                      <Text size="xs" c="blue">→</Text>
                      <Text size="xs" c="dimmed">To:</Text>
                      <Text size="xs">{currentAlignment?.slice(0, 8) || '?'}</Text>
                    </Group>

                    {sw.locked_when_occupied && (
                      <Text size="xs" c="orange" mt="xs">
                        Locked when occupied
                      </Text>
                    )}
                  </Paper>
                );
              })}
            </Stack>
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>
    </Stack>
  );
}
