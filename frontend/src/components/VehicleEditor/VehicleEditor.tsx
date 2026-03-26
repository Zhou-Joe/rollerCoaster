import { useState } from 'react';
import {
  Paper, Text, Group, Button, Stack, NumberInput,
  Accordion, Badge, ActionIcon, TextInput, Modal
} from '@mantine/core';
import { IconPlus, IconTrash, IconEdit } from '@tabler/icons-react';
import { useProjectStore } from '../../state/projectStore';
import { updateProject } from '../../api/client';
import type { Vehicle, Train } from '../../types';

export function VehicleEditor() {
  const { currentProject } = useProjectStore();
  const [showVehicleForm, setShowVehicleForm] = useState(false);
  const [showTrainForm, setShowTrainForm] = useState(false);
  const [editingVehicle, setEditingVehicle] = useState<number | null>(null);
  const [editingTrain, setEditingTrain] = useState<number | null>(null);
  
  const [vehicleForm, setVehicleForm] = useState({
    id: '',
    length_m: 2.0,
    dry_mass_kg: 500,
    capacity: 4,
    passenger_mass_per_person_kg: 75,
  });

  const [trainForm, setTrainForm] = useState({
    id: '',
    vehicle_ids: [] as string[],
    current_path_id: '',
    front_position_s: 5.0,
  });

  if (!currentProject) {
    return (
      <Paper p="sm" withBorder>
        <Text c="dimmed">No project loaded</Text>
      </Paper>
    );
  }

  const resetVehicleForm = () => {
    setVehicleForm({
      id: '',
      length_m: 2.0,
      dry_mass_kg: 500,
      capacity: 4,
      passenger_mass_per_person_kg: 75,
    });
    setEditingVehicle(null);
    setShowVehicleForm(false);
  };

  const resetTrainForm = () => {
    setTrainForm({
      id: '',
      vehicle_ids: [],
      current_path_id: currentProject.paths[0]?.id || '',
      front_position_s: 5.0,
    });
    setEditingTrain(null);
    setShowTrainForm(false);
  };

  const handleSaveVehicle = async () => {
    if (!currentProject.id) return;

    const newVehicle: Vehicle = {
      id: vehicleForm.id || `vehicle_${Date.now()}`,
      length_m: vehicleForm.length_m,
      dry_mass_kg: vehicleForm.dry_mass_kg,
      capacity: vehicleForm.capacity,
      passenger_mass_per_person_kg: vehicleForm.passenger_mass_per_person_kg,
    };

    let newVehicles: Vehicle[];
    if (editingVehicle !== null) {
      // Update existing
      newVehicles = [...currentProject.vehicles];
      newVehicles[editingVehicle] = newVehicle;
    } else {
      // Add new
      newVehicles = [...currentProject.vehicles, newVehicle];
    }

    try {
      await updateProject(currentProject.id, { vehicles: newVehicles });
      resetVehicleForm();
      window.location.reload();
    } catch (e) {
      console.error('Failed to save vehicle:', e);
    }
  };

  const handleEditVehicle = (index: number) => {
    const vehicle = currentProject.vehicles[index];
    setVehicleForm({
      id: vehicle.id,
      length_m: vehicle.length_m,
      dry_mass_kg: vehicle.dry_mass_kg,
      capacity: vehicle.capacity,
      passenger_mass_per_person_kg: vehicle.passenger_mass_per_person_kg || 75,
    });
    setEditingVehicle(index);
    setShowVehicleForm(true);
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

  const handleSaveTrain = async () => {
    if (!currentProject.id || trainForm.vehicle_ids.length === 0) return;

    const newTrain: Train = {
      id: trainForm.id || `train_${Date.now()}`,
      vehicle_ids: trainForm.vehicle_ids,
      current_path_id: trainForm.current_path_id,
      front_position_s: trainForm.front_position_s,
    };

    let newTrains: Train[];
    if (editingTrain !== null) {
      // Update existing
      newTrains = [...currentProject.trains];
      newTrains[editingTrain] = newTrain;
    } else {
      // Add new
      newTrains = [...currentProject.trains, newTrain];
    }

    try {
      await updateProject(currentProject.id, { trains: newTrains });
      resetTrainForm();
      window.location.reload();
    } catch (e) {
      console.error('Failed to save train:', e);
    }
  };

  const handleEditTrain = (index: number) => {
    const train = currentProject.trains[index];
    setTrainForm({
      id: train.id,
      vehicle_ids: [...train.vehicle_ids],
      current_path_id: train.current_path_id || currentProject.paths[0]?.id || '',
      front_position_s: train.front_position_s || 5.0,
    });
    setEditingTrain(index);
    setShowTrainForm(true);
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
              <Button
                size="xs"
                variant="light"
                leftSection={<IconPlus size={14} />}
                onClick={() => {
                  resetVehicleForm();
                  setShowVehicleForm(true);
                }}
              >
                Add Vehicle
              </Button>

              {currentProject.vehicles.map((vehicle, idx) => (
                <Paper key={vehicle.id} p="xs" withBorder style={{ background: '#222' }}>
                  <Group justify="space-between">
                    <Text size="xs" fw={500}>{vehicle.id}</Text>
                    <Group gap={4}>
                      <ActionIcon
                        size="xs"
                        variant="subtle"
                        color="blue"
                        onClick={() => handleEditVehicle(idx)}
                      >
                        <IconEdit size={12} />
                      </ActionIcon>
                      <ActionIcon
                        size="xs"
                        variant="subtle"
                        color="red"
                        onClick={() => handleDeleteVehicle(idx)}
                      >
                        <IconTrash size={12} />
                      </ActionIcon>
                    </Group>
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
              <Button
                size="xs"
                variant="light"
                leftSection={<IconPlus size={14} />}
                onClick={() => {
                  resetTrainForm();
                  setShowTrainForm(true);
                }}
                disabled={currentProject.vehicles.length === 0}
              >
                Add Train
              </Button>

              {currentProject.trains.map((train, idx) => (
                <Paper key={train.id} p="xs" withBorder style={{ background: '#222' }}>
                  <Group justify="space-between">
                    <Text size="xs" fw={500}>{train.id}</Text>
                    <Group gap={4}>
                      <ActionIcon
                        size="xs"
                        variant="subtle"
                        color="blue"
                        onClick={() => handleEditTrain(idx)}
                      >
                        <IconEdit size={12} />
                      </ActionIcon>
                      <ActionIcon
                        size="xs"
                        variant="subtle"
                        color="red"
                        onClick={() => handleDeleteTrain(idx)}
                      >
                        <IconTrash size={12} />
                      </ActionIcon>
                    </Group>
                  </Group>
                  <Text size="xs" c="dimmed" mt="xs">
                    Vehicles: {train.vehicle_ids.join(', ')}
                  </Text>
                  <Text size="xs" c="dimmed">
                    Path: {train.current_path_id || 'None'} @ {train.front_position_s?.toFixed(1) || 0}m
                  </Text>
                  <Group gap="xs" mt="xs">
                    <Badge size="xs">{train.vehicle_ids.length} cars</Badge>
                  </Group>
                </Paper>
              ))}
            </Stack>
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>

      {/* Vehicle Edit Modal */}
      <Modal
        opened={showVehicleForm}
        onClose={resetVehicleForm}
        title={editingVehicle !== null ? 'Edit Vehicle' : 'Add Vehicle'}
        size="sm"
      >
        <Stack gap="sm">
          <TextInput
            size="xs"
            label="ID"
            placeholder="vehicle_1"
            value={vehicleForm.id}
            onChange={(e) => setVehicleForm({ ...vehicleForm, id: e.target.value })}
          />
          <Group grow>
            <NumberInput
              size="xs"
              label="Length (m)"
              value={vehicleForm.length_m}
              onChange={(v) => setVehicleForm({ ...vehicleForm, length_m: Number(v) || 0 })}
              min={0.5}
              max={10}
              step={0.1}
            />
            <NumberInput
              size="xs"
              label="Dry Mass (kg)"
              value={vehicleForm.dry_mass_kg}
              onChange={(v) => setVehicleForm({ ...vehicleForm, dry_mass_kg: Number(v) || 0 })}
              min={100}
            />
          </Group>
          <Group grow>
            <NumberInput
              size="xs"
              label="Capacity (passengers)"
              value={vehicleForm.capacity}
              onChange={(v) => setVehicleForm({ ...vehicleForm, capacity: Number(v) || 0 })}
              min={1}
              max={20}
            />
            <NumberInput
              size="xs"
              label="Passenger Mass (kg/person)"
              value={vehicleForm.passenger_mass_per_person_kg}
              onChange={(v) => setVehicleForm({ ...vehicleForm, passenger_mass_per_person_kg: Number(v) || 75 })}
              min={50}
              max={150}
            />
          </Group>
          <Group grow mt="md">
            <Button size="xs" variant="subtle" onClick={resetVehicleForm}>
              Cancel
            </Button>
            <Button size="xs" onClick={handleSaveVehicle}>
              {editingVehicle !== null ? 'Update' : 'Add'}
            </Button>
          </Group>
        </Stack>
      </Modal>

      {/* Train Edit Modal */}
      <Modal
        opened={showTrainForm}
        onClose={resetTrainForm}
        title={editingTrain !== null ? 'Edit Train' : 'Add Train'}
        size="sm"
      >
        <Stack gap="sm">
          <TextInput
            size="xs"
            label="ID"
            placeholder="train_1"
            value={trainForm.id}
            onChange={(e) => setTrainForm({ ...trainForm, id: e.target.value })}
          />
          
          <Text size="xs" fw={500}>Select Vehicles (in order):</Text>
          <Stack gap={4}>
            {currentProject.vehicles.map((v) => (
              <Paper
                key={v.id}
                p="xs"
                withBorder
                style={{
                  background: trainForm.vehicle_ids.includes(v.id) ? '#2a4a2a' : '#2a2a2a',
                  cursor: 'pointer',
                }}
                onClick={() => {
                  if (trainForm.vehicle_ids.includes(v.id)) {
                    setTrainForm({
                      ...trainForm,
                      vehicle_ids: trainForm.vehicle_ids.filter(id => id !== v.id)
                    });
                  } else {
                    setTrainForm({
                      ...trainForm,
                      vehicle_ids: [...trainForm.vehicle_ids, v.id]
                    });
                  }
                }}
              >
                <Group justify="space-between">
                  <Text size="xs">{v.id}</Text>
                  <Badge size="xs">{v.length_m}m</Badge>
                </Group>
              </Paper>
            ))}
          </Stack>

          <Text size="xs" c="dimmed">
            Selected: {trainForm.vehicle_ids.join(' → ') || 'None'}
          </Text>

          <NumberInput
            size="xs"
            label="Initial Position on Path (m)"
            value={trainForm.front_position_s}
            onChange={(v) => setTrainForm({ ...trainForm, front_position_s: Number(v) || 0 })}
            min={0}
          />

          <Group grow mt="md">
            <Button size="xs" variant="subtle" onClick={resetTrainForm}>
              Cancel
            </Button>
            <Button 
              size="xs" 
              onClick={handleSaveTrain}
              disabled={trainForm.vehicle_ids.length === 0}
            >
              {editingTrain !== null ? 'Update' : 'Add'}
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  );
}