import { useState } from 'react';
import {
  Paper, Text, Group, Button, Stack, NumberInput,
  Accordion, Badge, ActionIcon, TextInput
} from '@mantine/core';
import { IconPlus, IconTrash } from '@tabler/icons-react';
import { useProjectStore } from '../../state/projectStore';
import { updateProject } from '../../api/client';

export function VehicleEditor() {
  const { currentProject } = useProjectStore();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    id: '',
    length_m: 2.0,
    dry_mass_kg: 500,
    capacity: 4,
    passenger_mass_per_person_kg: 75,
  });

  if (!currentProject) {
    return (
      <Paper p="sm" withBorder>
        <Text c="dimmed">No project loaded</Text>
      </Paper>
    );
  }

  const handleAddVehicle = async () => {
    if (!currentProject.id) return;

    const newVehicle = {
      id: form.id || `vehicle_${Date.now()}`,
      length_m: form.length_m,
      dry_mass_kg: form.dry_mass_kg,
      capacity: form.capacity,
      passenger_mass_per_person_kg: form.passenger_mass_per_person_kg,
    };

    try {
      await updateProject(currentProject.id, {
        vehicles: [...currentProject.vehicles, newVehicle]
      });
      setShowForm(false);
      setForm({ id: '', length_m: 2.0, dry_mass_kg: 500, capacity: 4, passenger_mass_per_person_kg: 75 });
      window.location.reload();
    } catch (e) {
      console.error('Failed to add vehicle:', e);
    }
  };

  const handleDeleteVehicle = async (index: number) => {
    if (!currentProject.id) return;
    const newVehicles = [...currentProject.vehicles];
    newVehicles.splice(index, 1);
    try {
      await updateProject(currentProject.id, { vehicles: newVehicles });
      window.location.reload();
    } catch (e) {
      console.error('Failed to delete vehicle:', e);
    }
  };

  const handleCreateTrain = async (vehicleIds: string[]) => {
    if (!currentProject.id || vehicleIds.length === 0) return;
    try {
      await updateProject(currentProject.id, {
        trains: [
          ...currentProject.trains,
          {
            id: `train_${Date.now()}`,
            vehicle_ids: vehicleIds,
          }
        ]
      });
      window.location.reload();
    } catch (e) {
      console.error('Failed to create train:', e);
    }
  };

  const handleDeleteTrain = async (index: number) => {
    if (!currentProject.id) return;
    const newTrains = [...currentProject.trains];
    newTrains.splice(index, 1);
    try {
      await updateProject(currentProject.id, { trains: newTrains });
      window.location.reload();
    } catch (e) {
      console.error('Failed to delete train:', e);
    }
  };

  return (
    <Stack gap="md">
      {/* Vehicles */}
      <Accordion variant="separated" radius="sm">
        <Accordion.Item value="vehicles">
          <Accordion.Control>
            <Group justify="space-between">
              <Text size="sm" fw={600}>Vehicles ({currentProject.vehicles.length})</Text>
              <Badge size="sm">{currentProject.vehicles.length}</Badge>
            </Group>
          </Accordion.Control>
          <Accordion.Panel>
            <Stack gap="xs">
              {!showForm && (
                <Button
                  size="xs"
                  variant="light"
                  leftSection={<IconPlus size={14} />}
                  onClick={() => setShowForm(true)}
                >
                  Add Vehicle
                </Button>
              )}

              {showForm && (
                <Paper p="sm" withBorder style={{ background: '#2a2a2a' }}>
                  <Text size="xs" c="dimmed" mb="xs">New Vehicle</Text>
                  <Stack gap="xs">
                    <TextInput
                      size="xs"
                      label="ID"
                      placeholder="vehicle_1"
                      value={form.id}
                      onChange={(e) => setForm({ ...form, id: e.target.value })}
                    />
                    <Group grow>
                      <NumberInput
                        size="xs"
                        label="Length (m)"
                        value={form.length_m}
                        onChange={(v) => setForm({ ...form, length_m: Number(v) || 0 })}
                        min={0.5}
                        max={10}
                        step={0.1}
                      />
                      <NumberInput
                        size="xs"
                        label="Mass (kg)"
                        value={form.dry_mass_kg}
                        onChange={(v) => setForm({ ...form, dry_mass_kg: Number(v) || 0 })}
                        min={100}
                      />
                    </Group>
                    <NumberInput
                      size="xs"
                      label="Capacity (passengers)"
                      value={form.capacity}
                      onChange={(v) => setForm({ ...form, capacity: Number(v) || 0 })}
                      min={1}
                      max={20}
                    />
                    <Group grow>
                      <Button size="xs" variant="subtle" onClick={() => setShowForm(false)}>
                        Cancel
                      </Button>
                      <Button size="xs" onClick={handleAddVehicle}>
                        Add
                      </Button>
                    </Group>
                  </Stack>
                </Paper>
              )}

              {currentProject.vehicles.map((vehicle, idx) => (
                <Paper key={vehicle.id} p="xs" withBorder style={{ background: '#222' }}>
                  <Group justify="space-between">
                    <Text size="xs" fw={500}>{vehicle.id}</Text>
                    <ActionIcon
                      size="xs"
                      variant="subtle"
                      color="red"
                      onClick={() => handleDeleteVehicle(idx)}
                    >
                      <IconTrash size={12} />
                    </ActionIcon>
                  </Group>
                  <Group gap="xs" mt="xs">
                    <Badge size="xs">{vehicle.length_m}m</Badge>
                    <Badge size="xs">{vehicle.dry_mass_kg}kg</Badge>
                    <Badge size="xs">{vehicle.capacity} seats</Badge>
                  </Group>
                </Paper>
              ))}
            </Stack>
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>

      {/* Trains */}
      <Accordion variant="separated" radius="sm">
        <Accordion.Item value="trains">
          <Accordion.Control>
            <Group justify="space-between">
              <Text size="sm" fw={600}>Trains ({currentProject.trains.length})</Text>
              <Badge size="sm">{currentProject.trains.length}</Badge>
            </Group>
          </Accordion.Control>
          <Accordion.Panel>
            <Stack gap="xs">
              {currentProject.vehicles.length > 0 && currentProject.trains.length === 0 && (
                <Button
                  size="xs"
                  variant="light"
                  leftSection={<IconPlus size={14} />}
                  onClick={() => handleCreateTrain(currentProject.vehicles.map(v => v.id))}
                >
                  Create Train from All Vehicles
                </Button>
              )}

              {currentProject.trains.map((train, idx) => (
                <Paper key={train.id} p="xs" withBorder style={{ background: '#222' }}>
                  <Group justify="space-between">
                    <Text size="xs" fw={500}>{train.id}</Text>
                    <ActionIcon
                      size="xs"
                      variant="subtle"
                      color="red"
                      onClick={() => handleDeleteTrain(idx)}
                    >
                      <IconTrash size={12} />
                    </ActionIcon>
                  </Group>
                  <Text size="xs" c="dimmed" mt="xs">
                    Vehicles: {train.vehicle_ids.join(', ')}
                  </Text>
                  <Group gap="xs" mt="xs">
                    <Badge size="xs">{train.vehicle_ids.length} cars</Badge>
                    {train.load_case && (
                      <Badge size="xs" variant="light">{train.load_case}</Badge>
                    )}
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