import { useState } from 'react';
import {
  Paper, Text, Group, Button, Stack, Select,
  Accordion, Badge, ActionIcon, NumberInput
} from '@mantine/core';
import { IconPlus, IconTrash, IconEdit } from '@tabler/icons-react';
import { useProjectStore } from '../../state/projectStore';
import { updateProject } from '../../api/client';
import type { Junction } from '../../types/simulation';

interface JunctionForm {
  id: string;
  incoming_path_id: string;
  outgoing_path_ids: string[];
  position_s: number;
}

export function JunctionEditor() {
  const { currentProject } = useProjectStore();
  const [showForm, setShowForm] = useState(false);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [form, setForm] = useState<JunctionForm>({
    id: '',
    incoming_path_id: '',
    outgoing_path_ids: ['', ''],
    position_s: 0,
  });

  if (!currentProject) {
    return (
      <Paper p="sm" withBorder>
        <Text c="dimmed">No project loaded</Text>
      </Paper>
    );
  }

  const resetForm = () => {
    setForm({
      id: '',
      incoming_path_id: '',
      outgoing_path_ids: ['', ''],
      position_s: 0,
    });
    setEditingIndex(null);
    setShowForm(false);
  };

  const handleAddJunction = async () => {
    if (!currentProject.id || !form.incoming_path_id || form.outgoing_path_ids.filter(Boolean).length === 0) return;

    const newJunction: Junction = {
      id: form.id || `junction_${Date.now()}`,
      incoming_path_id: form.incoming_path_id,
      outgoing_path_ids: form.outgoing_path_ids.filter(Boolean),
      position_s: form.position_s,
    };

    try {
      if (editingIndex !== null) {
        const newJunctions = [...currentProject.junctions];
        newJunctions[editingIndex] = newJunction;
        await updateProject(currentProject.id, { junctions: newJunctions });
      } else {
        await updateProject(currentProject.id, {
          junctions: [...currentProject.junctions, newJunction]
        });
      }
      resetForm();
      window.location.reload();
    } catch (e) {
      console.error('Failed to save junction:', e);
    }
  };

  const handleEditJunction = (index: number) => {
    const j = currentProject.junctions[index];
    setForm({
      id: j.id,
      incoming_path_id: j.incoming_path_id,
      outgoing_path_ids: [...j.outgoing_path_ids, ''].slice(0, 2),
      position_s: j.position_s,
    });
    setEditingIndex(index);
    setShowForm(true);
  };

  const handleDeleteJunction = async (index: number) => {
    if (!currentProject.id) return;
    const newJunctions = [...currentProject.junctions];
    newJunctions.splice(index, 1);
    try {
      await updateProject(currentProject.id, { junctions: newJunctions });
      window.location.reload();
    } catch (e) {
      console.error('Failed to delete junction:', e);
    }
  };

  return (
    <Stack gap="md">
      <Accordion variant="separated" radius="sm">
        <Accordion.Item value="junctions">
          <Accordion.Control>
            <Group justify="space-between">
              <Text size="sm" fw={600}>Junctions ({currentProject.junctions?.length || 0})</Text>
              <Badge size="sm">{currentProject.junctions?.length || 0}</Badge>
            </Group>
          </Accordion.Control>
          <Accordion.Panel>
            <Stack gap="xs">
              {!showForm && (
                <Button
                  size="xs"
                  variant="light"
                  leftSection={<IconPlus size={14} />}
                  onClick={() => {
                    resetForm();
                    setForm({
                      ...form,
                      incoming_path_id: currentProject.paths[0]?.id || '',
                      id: `junction_${Date.now()}`
                    });
                    setShowForm(true);
                  }}
                  disabled={currentProject.paths.length === 0}
                >
                  Add Junction
                </Button>
              )}

              {showForm && (
                <Paper p="sm" withBorder style={{ background: '#2a2a2a' }}>
                  <Text size="xs" c="dimmed" mb="xs">
                    {editingIndex !== null ? 'Edit Junction' : 'New Junction'}
                  </Text>
                  <Text size="xs" c="gray.5" mb="sm">
                    Junction connects one incoming path to multiple outgoing paths (Y-shape)
                  </Text>
                  <Stack gap="xs">
                    <Select
                      size="xs"
                      label="Incoming Path"
                      data={currentProject.paths.map(p => ({ value: p.id, label: p.name || p.id }))}
                      value={form.incoming_path_id}
                      onChange={(v) => setForm({ ...form, incoming_path_id: v || '' })}
                    />
                    <Select
                      size="xs"
                      label="Outgoing Path 1"
                      data={currentProject.paths.map(p => ({ value: p.id, label: p.name || p.id }))}
                      value={form.outgoing_path_ids[0]}
                      onChange={(v) => setForm({ ...form, outgoing_path_ids: [v || '', form.outgoing_path_ids[1]] })}
                    />
                    <Select
                      size="xs"
                      label="Outgoing Path 2"
                      data={[{ value: '', label: 'None' }, ...currentProject.paths.map(p => ({ value: p.id, label: p.name || p.id }))]}
                      value={form.outgoing_path_ids[1]}
                      onChange={(v) => setForm({ ...form, outgoing_path_ids: [form.outgoing_path_ids[0], v || ''] })}
                    />
                    <NumberInput
                      size="xs"
                      label="Position on Incoming Path (m)"
                      value={form.position_s}
                      onChange={(v) => setForm({ ...form, position_s: Number(v) || 0 })}
                      min={0}
                    />

                    <Group grow>
                      <Button size="xs" variant="subtle" onClick={resetForm}>
                        Cancel
                      </Button>
                      <Button size="xs" onClick={handleAddJunction}>
                        {editingIndex !== null ? 'Update' : 'Add'}
                      </Button>
                    </Group>
                  </Stack>
                </Paper>
              )}

              {currentProject.junctions?.map((j, idx) => (
                <Paper key={idx} p="xs" withBorder style={{ background: '#222' }}>
                  <Group justify="space-between">
                    <Text size="xs" fw={500}>Junction: {j.id.slice(0, 8)}...</Text>
                    <Group gap={4}>
                      <ActionIcon
                        size="xs"
                        variant="subtle"
                        color="blue"
                        onClick={() => handleEditJunction(idx)}
                      >
                        <IconEdit size={12} />
                      </ActionIcon>
                      <ActionIcon
                        size="xs"
                        variant="subtle"
                        color="red"
                        onClick={() => handleDeleteJunction(idx)}
                      >
                        <IconTrash size={12} />
                      </ActionIcon>
                    </Group>
                  </Group>
                  <Group gap="xs" mt="xs">
                    <Text size="xs" c="dimmed">{j.incoming_path_id.slice(0, 8)}</Text>
                    <Text size="xs" c="blue">→</Text>
                    <Text size="xs" c="dimmed">{j.outgoing_path_ids.map(id => id.slice(0, 8)).join(', ')}</Text>
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
