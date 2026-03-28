import { Box, Paper, Text, Group, Progress, Stack, Badge } from '@mantine/core';
import { useProjectStore } from '../../state/projectStore';
import { computeTrainKinematics } from '../../utils/trainKinematics';

interface TelemetryPanelProps {
  trainId?: string;
}

export function TelemetryPanel({ trainId }: TelemetryPanelProps) {
  const { simulationState, selectedTrainId, interpolatedPaths } = useProjectStore();

  const targetTrainId = trainId || selectedTrainId;
  const train = simulationState?.trains.find((t) => t.train_id === targetTrainId);

  const path = train ? interpolatedPaths.get(train.path_id) : null;
  const {
    worldVelocity,
    totalWorldVelocity,
    totalWorldAcceleration: totalWorldAccel,
    localAcceleration,
  } = train
    ? computeTrainKinematics(path, train.s_front_m, train.velocity_mps, train.acceleration_mps2)
    : computeTrainKinematics(null, 0, 0, 0);

  if (!train) {
    return null;
  }

  return (
    <Box
      p="md"
      style={{
        background: 'rgba(30, 30, 30, 0.95)',
        borderRadius: 8,
        border: '1px solid #404040',
        minWidth: 280,
      }}
    >
      <Text size="lg" fw={600} c="white" mb="md">
        Train Telemetry
      </Text>

      <Stack gap="xs">
        {/* Train ID */}
        <Group justify="space-between">
          <Text size="sm" c="gray.4">
            Train ID
          </Text>
          <Badge variant="filled" color="blue">
            {train.train_id}
          </Badge>
        </Group>

        {/* Position */}
        <MetricRow
          label="Position"
          value={`${train.s_front_m.toFixed(1)} m`}
        />

        {/* Velocity */}
        <MetricRow
          label="Velocity"
          value={`${train.velocity_mps.toFixed(2)} m/s`}
          color={getSpeedColor(train.velocity_mps)}
        />

        {/* Acceleration */}
        <MetricRow
          label="Acceleration"
          value={`${train.acceleration_mps2.toFixed(2)} m/s²`}
          color={train.acceleration_mps2 > 0 ? 'green' : train.acceleration_mps2 < -3 ? 'red' : 'yellow'}
        />

        {/* Mass */}
        <MetricRow
          label="Mass"
          value={`${(train.mass_kg / 1000).toFixed(1)} t`}
        />

        {/* Divider */}
        <Box my="xs" style={{ borderTop: '1px solid #404040' }} />

        {/* World Velocity Components */}
        <Text size="sm" fw={600} c="gray.3" mt="xs">
          World Velocity (Three.js coords)
        </Text>

        <MetricRow
          label="  Vx (Right)"
          value={`${worldVelocity.x.toFixed(2)} m/s`}
          color={Math.abs(worldVelocity.x) > 10 ? 'orange' : undefined}
        />
        <MetricRow
          label="  Vy (Up)"
          value={`${worldVelocity.y.toFixed(2)} m/s`}
          color={worldVelocity.y < -5 ? 'red' : worldVelocity.y > 5 ? 'green' : undefined}
        />
        <MetricRow
          label="  Vz (Forward)"
          value={`${worldVelocity.z.toFixed(2)} m/s`}
          color={Math.abs(worldVelocity.z) > 10 ? 'orange' : undefined}
        />
        <MetricRow
          label="  |V| (Total)"
          value={`${totalWorldVelocity.toFixed(2)} m/s`}
          bold
          color={getSpeedColor(totalWorldVelocity)}
        />

        {/* Divider */}
        <Box my="xs" style={{ borderTop: '1px solid #404040' }} />

        {/* Train Acceleration Components */}
        <Text size="sm" fw={600} c="gray.3" mt="xs">
          Train Acceleration
        </Text>

        <MetricRow
          label="  Fore/Aft"
          value={`${localAcceleration.foreAft.toFixed(2)} m/s²`}
          color={Math.abs(localAcceleration.foreAft) > 5 ? 'orange' : undefined}
        />
        <MetricRow
          label="  Right/Left"
          value={`${localAcceleration.rightLeft.toFixed(2)} m/s²`}
          color={Math.abs(localAcceleration.rightLeft) > 5 ? 'orange' : undefined}
        />
        <MetricRow
          label="  Eye Up/Down"
          value={`${localAcceleration.eyeUpDown.toFixed(2)} m/s²`}
          color={Math.abs(localAcceleration.eyeUpDown) > 5 ? 'orange' : undefined}
        />
        <MetricRow
          label="  |A| (Total)"
          value={`${totalWorldAccel.toFixed(2)} m/s²`}
          bold
          color={totalWorldAccel > 5 ? 'red' : totalWorldAccel > 2 ? 'yellow' : 'green'}
        />

        {/* Divider */}
        <Box my="xs" style={{ borderTop: '1px solid #404040' }} />

        {/* G-Forces */}
        <Text size="sm" fw={600} c="gray.3" mt="xs">
          G-Forces
        </Text>

        <GForceBar label="Normal" value={train.gforces.normal_g} />
        <GForceBar label="Lateral" value={train.gforces.lateral_g} />
        <GForceBar label="Vertical" value={train.gforces.vertical_g} />
        <GForceBar label="Resultant" value={train.gforces.resultant_g} highlight />

        {/* Divider */}
        <Box my="xs" style={{ borderTop: '1px solid #404040' }} />

        {/* Forces */}
        <Text size="sm" fw={600} c="gray.3" mt="xs">
          Forces
        </Text>

        <MetricRow
          label="Gravity"
          value={`${train.forces.gravity_tangent_n.toFixed(0)} N`}
        />
        <MetricRow
          label="Drag"
          value={`${train.forces.drag_n.toFixed(0)} N`}
        />
        <MetricRow
          label="Equipment"
          value={`${train.forces.equipment_n.toFixed(0)} N`}
          color={train.forces.equipment_n !== 0 ? 'blue' : undefined}
        />
        <MetricRow
          label="Total"
          value={`${train.forces.total_n.toFixed(0)} N`}
          bold
        />

        {/* Equipment Force Breakdown */}
        {train.equipment_forces && (train.equipment_forces.lsm_force_n !== 0 ||
          train.equipment_forces.lift_force_n !== 0 ||
          train.equipment_forces.brake_force_n !== 0) && (
          <>
            <Box my="xs" style={{ borderTop: '1px solid #404040' }} />
            <Text size="sm" fw={600} c="blue.4" mt="xs">
              Equipment Details
            </Text>

            {train.equipment_forces.lsm_force_n !== 0 && (
              <>
                <MetricRow
                  label="LSM Force"
                  value={`${train.equipment_forces.lsm_force_n.toFixed(0)} N`}
                  color="#69db7c"
                  bold
                />
                <MetricRow
                  label="  Stators Active"
                  value={`${train.equipment_forces.lsm_stators_active}`}
                />
                <MetricRow
                  label="  Overlap"
                  value={`${(train.equipment_forces.lsm_overlap_ratio * 100).toFixed(1)}%`}
                />
              </>
            )}

            {train.equipment_forces.lift_force_n !== 0 && (
              <MetricRow
                label="Lift Force"
                value={`${train.equipment_forces.lift_force_n.toFixed(0)} N`}
                color="#74c0fc"
              />
            )}

            {train.equipment_forces.brake_force_n !== 0 && (
              <MetricRow
                label="Brake Force"
                value={`${train.equipment_forces.brake_force_n.toFixed(0)} N`}
                color="#ff8787"
              />
            )}

            {train.equipment_forces.booster_force_n !== 0 && (
              <MetricRow
                label="Booster Force"
                value={`${train.equipment_forces.booster_force_n.toFixed(0)} N`}
                color="#ffd43b"
              />
            )}
          </>
        )}
      </Stack>
    </Box>
  );
}

interface MetricRowProps {
  label: string;
  value: string;
  color?: string;
  bold?: boolean;
}

function MetricRow({ label, value, color, bold }: MetricRowProps) {
  return (
    <Group justify="space-between">
      <Text size="sm" c="gray.4">
        {label}
      </Text>
      <Text size="sm" c={color || 'white'} fw={bold ? 600 : 400} ff="monospace">
        {value}
      </Text>
    </Group>
  );
}

interface GForceBarProps {
  label: string;
  value: number;
  highlight?: boolean;
}

function GForceBar({ label, value }: GForceBarProps) {
  // G-force display: 0-6G range, centered at 1G
  const percent = Math.min(100, Math.max(0, (value + 2) / 8 * 100));
  const color = value < -1 || value > 5 ? 'red' : value < 0 || value > 4 ? 'yellow' : 'green';

  return (
    <Box>
      <Group justify="space-between" mb={2}>
        <Text size="xs" c="gray.4">
          {label}
        </Text>
        <Text size="xs" c="white" ff="monospace">
          {value.toFixed(2)} G
        </Text>
      </Group>
      <Progress
        value={percent}
        color={color}
        size="xs"
        style={{ background: '#333' }}
      />
    </Box>
  );
}

function getSpeedColor(velocity: number): string {
  const absVelocity = Math.abs(velocity);
  if (absVelocity < 5) return 'green';
  if (absVelocity < 15) return 'yellow';
  if (absVelocity < 25) return 'orange';
  return 'red';
}
