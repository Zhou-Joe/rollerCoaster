import { useState } from 'react';
import {
  Paper, Text, Group, Button, Stack, NumberInput,
  Accordion, Badge, ActionIcon, Modal, TextInput, Select
} from '@mantine/core';
import { IconPlus, IconTrash, IconEdit } from '@tabler/icons-react';
import { useProjectStore } from '../../state/projectStore';
import { updateProject, getInterpolatedPath, resetSimulator, setTrainPosition } from '../../api/client';
import { ExportImportPanel } from '../ExportImportPanel/ExportImportPanel';

export function TrackEditor() {
  const { currentProject, simulationState, interpolatedPaths, setCurrentProject, setInterpolatedPath } = useProjectStore();
  const [newPoint, setNewPoint] = useState({ x: 0, y: 0, z: 5, bank_deg: 0 });
  const [editingPointId, setEditingPointId] = useState<string | null>(null);
  const [editValues, setEditValues] = useState({ x: 0, y: 0, z: 0, bank_deg: 0 });

  // Vehicle editing state
  const [editingVehicleId, setEditingVehicleId] = useState<string | null>(null);
  const [vehicleForm, setVehicleForm] = useState({ id: '', length_m: 2.0, dry_mass_kg: 500, capacity: 4, passenger_mass_per_person_kg: 75 });

  // Train editing state
  const [editingTrainId, setEditingTrainId] = useState<string | null>(null);
  const [trainForm, setTrainForm] = useState({ id: '', vehicle_ids: [] as string[], current_path_id: '', front_position_s: 5.0 });

  if (!currentProject) {
    return (
      <Paper p="sm" withBorder>
        <Text c="dimmed">No project loaded</Text>
      </Paper>
    );
  }

  const refreshPaths = async (projectId: string) => {
    for (const path of currentProject.paths) {
      try {
        const interpolated = await getInterpolatedPath(projectId, path.id);
        setInterpolatedPath(path.id, interpolated);
      } catch (e) {
        console.error('Failed to refresh path:', path.id, e);
      }
    }
  };

  const handleAddPoint = async () => {
    if (!currentProject.id) return;
    try {
      const newPointData = {
        id: `point_${Date.now()}`,
        x: newPoint.x,
        y: newPoint.y,
        z: newPoint.z,
        bank_deg: newPoint.bank_deg,
        editable: true
      };
      const updatedPoints = [...currentProject.points, newPointData];
      await updateProject(currentProject.id, { points: updatedPoints });
      setCurrentProject({ ...currentProject, points: updatedPoints });
      await resetSimulator(currentProject.id);
      await refreshPaths(currentProject.id);
    } catch (e) {
      console.error('Failed to add point:', e);
    }
  };

  const handleDeletePoint = async (pointId: string) => {
    if (!currentProject.id) return;
    try {
      const newPoints = currentProject.points.filter(p => p.id !== pointId);
      const newPaths = currentProject.paths.map(path => ({
        ...path,
        point_ids: path.point_ids.filter(id => id !== pointId)
      })).filter(path => path.point_ids.length >= 2);

      await updateProject(currentProject.id, {
        points: newPoints,
        paths: newPaths
      });
      setCurrentProject({ ...currentProject, points: newPoints, paths: newPaths });
      await resetSimulator(currentProject.id);
      await refreshPaths(currentProject.id);
    } catch (e) {
      console.error('Failed to delete point:', e);
    }
  };

  const handleStartEdit = (point: typeof currentProject.points[0]) => {
    setEditingPointId(point.id);
    setEditValues({
      x: point.x,
      y: point.y,
      z: point.z,
      bank_deg: point.bank_deg || 0
    });
  };

  const handleCancelEdit = () => {
    setEditingPointId(null);
  };

  const handleSaveEdit = async (pointId: string) => {
    if (!currentProject.id) return;
    try {
      const updatedPoints = currentProject.points.map(p =>
        p.id === pointId
          ? { ...p, x: editValues.x, y: editValues.y, z: editValues.z, bank_deg: editValues.bank_deg }
          : p
      );
      await updateProject(currentProject.id, { points: updatedPoints });
      setCurrentProject({ ...currentProject, points: updatedPoints });
      setEditingPointId(null);
      await resetSimulator(currentProject.id);
      await refreshPaths(currentProject.id);
    } catch (e) {
      console.error('Failed to update point:', e);
    }
  };

  const handleCreatePath = async () => {
    if (!currentProject.id || currentProject.points.length < 2) return;
    try {
      const pointIds = currentProject.points.map(p => p.id);
      const newPath = {
        id: `path_${Date.now()}`,
        name: 'Main Track',
        point_ids: pointIds
      };
      const updatedPaths = [...currentProject.paths, newPath];
      await updateProject(currentProject.id, { paths: updatedPaths });
      setCurrentProject({ ...currentProject, paths: updatedPaths });
      await refreshPaths(currentProject.id);
    } catch (e) {
      console.error('Failed to create path:', e);
    }
  };

  const handleDeletePath = async (pathId: string) => {
    if (!currentProject.id) return;
    try {
      const newPaths = currentProject.paths.filter(p => p.id !== pathId);
      await updateProject(currentProject.id, { paths: newPaths });
      setCurrentProject({ ...currentProject, paths: newPaths });
    } catch (e) {
      console.error('Failed to delete path:', e);
    }
  };

  const handleCreateTrain = async () => {
    if (!currentProject.id || currentProject.vehicles.length === 0) return;
    try {
      const newTrain = {
        id: `train_${Date.now()}`,
        vehicle_ids: currentProject.vehicles.map(v => v.id)
      };
      const updatedTrains = [...currentProject.trains, newTrain];
      await updateProject(currentProject.id, { trains: updatedTrains });
      setCurrentProject({ ...currentProject, trains: updatedTrains });
    } catch (e) {
      console.error('Failed to create train:', e);
    }
  };

  const handleDeleteTrain = async (trainId: string) => {
    if (!currentProject.id) return;
    try {
      const newTrains = currentProject.trains.filter(t => t.id !== trainId);
      await updateProject(currentProject.id, { trains: newTrains });
      setCurrentProject({ ...currentProject, trains: newTrains });
    } catch (e) {
      console.error('Failed to delete train:', e);
    }
  };

  const handleEditTrain = (trainId: string) => {
    const train = currentProject.trains.find(t => t.id === trainId);
    if (train) {
      setTrainForm({
        id: train.id,
        vehicle_ids: [...train.vehicle_ids],
        current_path_id: train.current_path_id || '',
        front_position_s: train.front_position_s || 5.0
      });
      setEditingTrainId(trainId);
    }
  };

  const handleSaveTrain = async () => {
    if (!currentProject.id || !editingTrainId) return;
    try {
      // First update simulation position (using original train ID)
      console.log('Setting train position:', { trainId: editingTrainId, pathId: trainForm.current_path_id, position: trainForm.front_position_s });
      await setTrainPosition(currentProject.id, editingTrainId, trainForm.current_path_id, trainForm.front_position_s);
      console.log('Train position updated successfully');

      // Then update project data (may change train ID)
      const updatedTrains = currentProject.trains.map(t =>
        t.id === editingTrainId
          ? { ...t, id: trainForm.id, vehicle_ids: trainForm.vehicle_ids, current_path_id: trainForm.current_path_id, front_position_s: trainForm.front_position_s }
          : t
      );
      await updateProject(currentProject.id, { trains: updatedTrains });
      setCurrentProject({ ...currentProject, trains: updatedTrains });

      setEditingTrainId(null);
    } catch (e) {
      console.error('Failed to save train:', e);
      alert('Failed to save train: ' + (e as Error).message);
    }
  };

  const handleDeleteVehicle = async (vehicleId: string) => {
    if (!currentProject.id) return;
    try {
      // Remove vehicle from any trains that use it
      const updatedTrains = currentProject.trains.map(t => ({
        ...t,
        vehicle_ids: t.vehicle_ids.filter(vid => vid !== vehicleId)
      }));
      const newVehicles = currentProject.vehicles.filter(v => v.id !== vehicleId);
      await updateProject(currentProject.id, { vehicles: newVehicles, trains: updatedTrains });
      setCurrentProject({ ...currentProject, vehicles: newVehicles, trains: updatedTrains });
    } catch (e) {
      console.error('Failed to delete vehicle:', e);
    }
  };

  const handleEditVehicle = (vehicleId: string) => {
    const vehicle = currentProject.vehicles.find(v => v.id === vehicleId);
    if (vehicle) {
      setVehicleForm({
        id: vehicle.id,
        length_m: vehicle.length_m,
        dry_mass_kg: vehicle.dry_mass_kg,
        capacity: vehicle.capacity,
        passenger_mass_per_person_kg: vehicle.passenger_mass_per_person_kg || 75
      });
      setEditingVehicleId(vehicleId);
    }
  };

  const handleSaveVehicle = async () => {
    if (!currentProject.id || !editingVehicleId) return;
    try {
      const updatedVehicles = currentProject.vehicles.map(v =>
        v.id === editingVehicleId
          ? { ...v, id: vehicleForm.id, length_m: vehicleForm.length_m, dry_mass_kg: vehicleForm.dry_mass_kg, capacity: vehicleForm.capacity, passenger_mass_per_person_kg: vehicleForm.passenger_mass_per_person_kg }
          : v
      );
      // Also update vehicle ID in trains if it changed
      const updatedTrains = currentProject.trains.map(t => ({
        ...t,
        vehicle_ids: t.vehicle_ids.map(vid => vid === editingVehicleId ? vehicleForm.id : vid)
      }));
      await updateProject(currentProject.id, { vehicles: updatedVehicles, trains: updatedTrains });
      setCurrentProject({ ...currentProject, vehicles: updatedVehicles, trains: updatedTrains });
      setEditingVehicleId(null);
    } catch (e) {
      console.error('Failed to save vehicle:', e);
    }
  };

  return (
    <Stack gap="md">
      {/* Points Editor */}
      <Accordion variant="separated" radius="sm">
        <Accordion.Item value="points">
          <Accordion.Control>
            <Group justify="space-between">
              <Text size="sm" fw={600}>Track Points ({currentProject.points.length})</Text>
              <Badge size="sm">{currentProject.points.length}</Badge>
            </Group>
          </Accordion.Control>
          <Accordion.Panel>
            <Stack gap="xs">
              {/* Add new point */}
              <Paper p="xs" withBorder style={{ background: '#2a2a2a' }}>
                <Text size="xs" c="dimmed" mb="xs">Add Point</Text>
                <Group grow>
                  <NumberInput
                    size="xs"
                    label="X"
                    value={newPoint.x}
                    onChange={(v) => setNewPoint({ ...newPoint, x: Number(v) || 0 })}
                  />
                  <NumberInput
                    size="xs"
                    label="Y"
                    value={newPoint.y}
                    onChange={(v) => setNewPoint({ ...newPoint, y: Number(v) || 0 })}
                  />
                  <NumberInput
                    size="xs"
                    label="Z"
                    value={newPoint.z}
                    onChange={(v) => setNewPoint({ ...newPoint, z: Number(v) || 0 })}
                    min={0}
                  />
                </Group>
                <Group grow mt="xs">
                  <NumberInput
                    size="xs"
                    label="Bank (°)"
                    value={newPoint.bank_deg}
                    onChange={(v) => setNewPoint({ ...newPoint, bank_deg: Number(v) || 0 })}
                    min={-90}
                    max={90}
                  />
                  <Button size="xs" leftSection={<IconPlus size={14} />} onClick={handleAddPoint}>
                    Add
                  </Button>
                </Group>
              </Paper>

              {/* Existing points list */}
              {currentProject.points.map((point, idx) => (
                <Paper key={point.id} p="xs" withBorder style={{ background: editingPointId === point.id ? '#2a3a4a' : '#222' }}>
                  {editingPointId === point.id ? (
                    // Edit mode
                    <Stack gap="xs">
                      <Group justify="space-between">
                        <Text size="xs" fw={600}>Editing Point {idx + 1}</Text>
                        <Group gap="xs">
                          <Button size="xs" variant="subtle" onClick={handleCancelEdit}>Cancel</Button>
                          <Button size="xs" onClick={() => handleSaveEdit(point.id)}>Save</Button>
                        </Group>
                      </Group>
                      <Group grow>
                        <NumberInput
                          size="xs"
                          label="X"
                          value={editValues.x}
                          onChange={(v) => setEditValues({ ...editValues, x: Number(v) || 0 })}
                          step={0.5}
                        />
                        <NumberInput
                          size="xs"
                          label="Y"
                          value={editValues.y}
                          onChange={(v) => setEditValues({ ...editValues, y: Number(v) || 0 })}
                          step={0.5}
                        />
                        <NumberInput
                          size="xs"
                          label="Z"
                          value={editValues.z}
                          onChange={(v) => setEditValues({ ...editValues, z: Number(v) || 0 })}
                          min={0}
                          step={0.5}
                        />
                      </Group>
                      <NumberInput
                        size="xs"
                        label="Bank Angle (°)"
                        value={editValues.bank_deg}
                        onChange={(v) => setEditValues({ ...editValues, bank_deg: Number(v) || 0 })}
                        min={-90}
                        max={90}
                        step={5}
                      />
                    </Stack>
                  ) : (
                    // View mode
                    <Group justify="space-between">
                      <Group gap="xs">
                        <Badge size="sm" variant="light">{idx + 1}</Badge>
                        <Text size="xs">
                          X: <strong>{point.x.toFixed(1)}</strong>
                          Y: <strong>{point.y.toFixed(1)}</strong>
                          Z: <strong>{point.z.toFixed(1)}</strong>
                        </Text>
                        {point.bank_deg !== 0 && (
                          <Badge size="xs" color="grape">Bank: {point.bank_deg}°</Badge>
                        )}
                      </Group>
                      <Group gap={4}>
                        <ActionIcon
                          size="xs"
                          variant="subtle"
                          color="blue"
                          onClick={() => handleStartEdit(point)}
                        >
                          <IconEdit size={12} />
                        </ActionIcon>
                        <ActionIcon
                          size="xs"
                          variant="subtle"
                          color="red"
                          onClick={() => handleDeletePoint(point.id)}
                        >
                          <IconTrash size={12} />
                        </ActionIcon>
                      </Group>
                    </Group>
                  )}
                </Paper>
              ))}
            </Stack>
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>

      {/* Paths Editor */}
      <Accordion variant="separated" radius="sm">
        <Accordion.Item value="paths">
          <Accordion.Control>
            <Group justify="space-between">
              <Text size="sm" fw={600}>Paths ({currentProject.paths.length})</Text>
              <Badge size="sm">{currentProject.paths.length}</Badge>
            </Group>
          </Accordion.Control>
          <Accordion.Panel>
            <Stack gap="xs">
              {currentProject.paths.length === 0 && (
                <Button
                  size="xs"
                  variant="light"
                  leftSection={<IconPlus size={14} />}
                  onClick={handleCreatePath}
                  disabled={currentProject.points.length < 2}
                >
                  Create Path from Points
                </Button>
              )}
              {currentProject.paths.map((path) => (
                <Paper key={path.id} p="xs" withBorder style={{ background: '#222' }}>
                  <Group justify="space-between">
                    <Text size="xs" fw={500}>{path.name || path.id}</Text>
                    <ActionIcon
                      size="xs"
                      variant="subtle"
                      color="red"
                      onClick={() => handleDeletePath(path.id)}
                    >
                      <IconTrash size={12} />
                    </ActionIcon>
                  </Group>
                  <Text size="xs" c="dimmed">{path.point_ids.length} points</Text>
                  {interpolatedPaths.get(path.id) && (
                    <Text size="xs" c="dimmed">
                      Length: {interpolatedPaths.get(path.id)!.total_length.toFixed(1)}m
                    </Text>
                  )}
                </Paper>
              ))}
            </Stack>
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>

      {/* Vehicles & Trains */}
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
              {currentProject.trains.length === 0 && currentProject.vehicles.length > 0 && (
                <Button
                  size="xs"
                  variant="light"
                  leftSection={<IconPlus size={14} />}
                  onClick={handleCreateTrain}
                >
                  Create Train
                </Button>
              )}
              {currentProject.trains.map((train) => (
                <Paper key={train.id} p="xs" withBorder style={{ background: '#222' }}>
                  <Group justify="space-between">
                    <Text size="xs" fw={500}>{train.id}</Text>
                    <Group gap={4}>
                      <ActionIcon
                        size="xs"
                        variant="subtle"
                        color="blue"
                        onClick={() => handleEditTrain(train.id)}
                      >
                        <IconEdit size={12} />
                      </ActionIcon>
                      <ActionIcon
                        size="xs"
                        variant="subtle"
                        color="red"
                        onClick={() => handleDeleteTrain(train.id)}
                      >
                        <IconTrash size={12} />
                      </ActionIcon>
                    </Group>
                  </Group>
                  <Text size="xs" c="dimmed">{train.vehicle_ids.length} vehicle(s)</Text>
                </Paper>
              ))}
              {simulationState?.trains.map((trainState) => (
                <Paper key={trainState.train_id} p="xs" withBorder style={{ background: '#1a1a1a' }}>
                  <Text size="xs" c="dimmed">Simulation State</Text>
                  <Group gap="xs" mt="xs">
                    <Badge size="xs" color={trainState.velocity_mps > 0 ? 'green' : 'gray'}>
                      {trainState.velocity_mps.toFixed(1)} m/s
                    </Badge>
                    <Text size="xs" c="dimmed">Pos: {trainState.s_front_m.toFixed(1)}m</Text>
                  </Group>
                </Paper>
              ))}
            </Stack>
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>

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
              {currentProject.vehicles.map((vehicle) => (
                <Paper key={vehicle.id} p="xs" withBorder style={{ background: '#222' }}>
                  <Group justify="space-between">
                    <Text size="xs" fw={500}>{vehicle.id}</Text>
                    <Group gap={4}>
                      <ActionIcon
                        size="xs"
                        variant="subtle"
                        color="blue"
                        onClick={() => handleEditVehicle(vehicle.id)}
                      >
                        <IconEdit size={12} />
                      </ActionIcon>
                      <ActionIcon
                        size="xs"
                        variant="subtle"
                        color="red"
                        onClick={() => handleDeleteVehicle(vehicle.id)}
                      >
                        <IconTrash size={12} />
                      </ActionIcon>
                    </Group>
                  </Group>
                  <Group gap="xs" mt="xs">
                    <Text size="xs" c="dimmed">Length: {vehicle.length_m}m</Text>
                    <Text size="xs" c="dimmed">Mass: {vehicle.dry_mass_kg}kg</Text>
                    <Text size="xs" c="dimmed">Capacity: {vehicle.capacity}</Text>
                  </Group>
                </Paper>
              ))}
            </Stack>
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>

      {/* Vehicle Edit Modal */}
      <Modal
        opened={editingVehicleId !== null}
        onClose={() => setEditingVehicleId(null)}
        title="Edit Vehicle"
        size="sm"
      >
        <Stack gap="sm">
          <TextInput
            size="xs"
            label="ID"
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
              label="Capacity"
              value={vehicleForm.capacity}
              onChange={(v) => setVehicleForm({ ...vehicleForm, capacity: Number(v) || 0 })}
              min={1}
            />
            <NumberInput
              size="xs"
              label="Passenger Mass (kg/person)"
              value={vehicleForm.passenger_mass_per_person_kg}
              onChange={(v) => setVehicleForm({ ...vehicleForm, passenger_mass_per_person_kg: Number(v) || 75 })}
              min={50}
            />
          </Group>
          <Group grow mt="md">
            <Button size="xs" variant="subtle" onClick={() => setEditingVehicleId(null)}>Cancel</Button>
            <Button size="xs" onClick={handleSaveVehicle}>Save</Button>
          </Group>
        </Stack>
      </Modal>

      {/* Train Edit Modal */}
      <Modal
        opened={editingTrainId !== null}
        onClose={() => setEditingTrainId(null)}
        title="Edit Train"
        size="sm"
      >
        <Stack gap="sm">
          <TextInput
            size="xs"
            label="ID"
            value={trainForm.id}
            onChange={(e) => setTrainForm({ ...trainForm, id: e.target.value })}
          />
          <Select
            size="xs"
            label="Current Path"
            value={trainForm.current_path_id}
            onChange={(v) => setTrainForm({ ...trainForm, current_path_id: v || '' })}
            data={currentProject.paths.map(p => ({ value: p.id, label: p.name || p.id }))}
          />
          <NumberInput
            size="xs"
            label="Front Position (m)"
            value={trainForm.front_position_s}
            onChange={(v) => setTrainForm({ ...trainForm, front_position_s: Number(v) || 0 })}
            min={0}
          />
          <Text size="xs" fw={500}>Select Vehicles:</Text>
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
                    setTrainForm({ ...trainForm, vehicle_ids: trainForm.vehicle_ids.filter(id => id !== v.id) });
                  } else {
                    setTrainForm({ ...trainForm, vehicle_ids: [...trainForm.vehicle_ids, v.id] });
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
          <Text size="xs" c="dimmed">Selected: {trainForm.vehicle_ids.join(' → ') || 'None'}</Text>
          <Group grow mt="md">
            <Button size="xs" variant="subtle" onClick={() => setEditingTrainId(null)}>Cancel</Button>
            <Button size="xs" onClick={handleSaveTrain} disabled={trainForm.vehicle_ids.length === 0}>Save</Button>
          </Group>
        </Stack>
      </Modal>

      {/* Export/Import Panel */}
      {currentProject.id && (
        <Paper p="sm" withBorder style={{ background: '#2a2a2a' }}>
          <ExportImportPanel
            project={currentProject}
            projectId={currentProject.id}
            onImportSuccess={(newProjectId) => {
              window.location.href = `/?project=${newProjectId}`;
            }}
          />
        </Paper>
      )}
    </Stack>
  );
}