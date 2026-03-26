import { Box, Paper, Text, Group, Progress, Stack, Badge } from '@mantine/core';
import { useProjectStore } from '../../state/projectStore';
import type { InterpolatedPath } from '../../types';

interface TelemetryPanelProps {
  trainId?: string;
}

/**
 * Find a sample point on the path at a given arc length position
 */
function findPointAtS(path: InterpolatedPath, s: number) {
  for (let i = 0; i < path.points.length - 1; i++) {
    const p1 = path.points[i];
    const p2 = path.points[i + 1];
    if (p1.s <= s && p2.s >= s) {
      const t = (s - p1.s) / (p2.s - p1.s);
      return {
        tangent: [
          p1.tangent[0] + t * (p2.tangent[0] - p1.tangent[0]),
          p1.tangent[1] + t * (p2.tangent[1] - p1.tangent[1]),
          p1.tangent[2] + t * (p2.tangent[2] - p1.tangent[2]),
        ] as [number, number, number],
        normal: [
          p1.normal[0] + t * (p2.normal[0] - p1.normal[0]),
          p1.normal[1] + t * (p2.normal[1] - p1.normal[1]),
          p1.normal[2] + t * (p2.normal[2] - p1.normal[2]),
        ] as [number, number, number],
        binormal: [
          p1.binormal[0] + t * (p2.binormal[0] - p1.binormal[0]),
          p1.binormal[1] + t * (p2.binormal[1] - p1.binormal[1]),
          p1.binormal[2] + t * (p2.binormal[2] - p1.binormal[2]),
        ] as [number, number, number],
        curvature: p1.curvature + t * (p2.curvature - p1.curvature),
      };
    }
  }
  return path.points.find((p) => Math.abs(p.s - s) < 0.5);
}

export function TelemetryPanel({ trainId }: TelemetryPanelProps) {
  const { simulationState, selectedTrainId, interpolatedPaths } = useProjectStore();

  const targetTrainId = trainId || selectedTrainId;
  const train = simulationState?.trains.find((t) => t.train_id === targetTrainId);

  // Get the interpolated path for this train to compute world velocities
  const path = train ? interpolatedPaths.get(train.path_id) : null;
  const geometryPoint = train && path ? findPointAtS(path, train.s_front_m) : null;

  // Compute world coordinate velocity components
  const worldVelocity = geometryPoint ? {
    x: train!.velocity_mps * geometryPoint.tangent[0],
    y: train!.velocity_mps * geometryPoint.tangent[1],
    z: train!.velocity_mps * geometryPoint.tangent[2],
  } : { x: 0, y: 0, z: 0 };

  // Compute world coordinate acceleration components (tangent + centripetal)
  // Tangent acceleration is along track direction
  // Centripetal acceleration = v² * curvature, directed toward center (negative normal direction)
  const tangentAccel = geometryPoint ? {
    x: train!.acceleration_mps2 * geometryPoint.tangent[0],
    y: train!.acceleration_mps2 * geometryPoint.tangent[1],
    z: train!.acceleration_mps2 * geometryPoint.tangent[2],
  } : { x: 0, y: 0, z: 0 };

  // Centripetal acceleration: a_c = v² / R = v² * curvature, direction = -normal
  const centripetalMag = geometryPoint ? train!.velocity_mps * train!.velocity_mps * geometryPoint.curvature : 0;
  const centripetalAccel = geometryPoint ? {
    x: -centripetalMag * geometryPoint.normal[0],
    y: -centripetalMag * geometryPoint.normal[1],
    z: -centripetalMag * geometryPoint.normal[2],
  } : { x: 0, y: 0, z: 0 };

  // Total world acceleration
  const worldAccel = {
    x: tangentAccel.x + centripetalAccel.x,
    y: tangentAccel.y + centripetalAccel.y,
    z: tangentAccel.z + centripetalAccel.z,
  };

  // Combined magnitude (should match the scalar values for velocity, different for accel)
  const totalWorldVelocity = Math.sqrt(worldVelocity.x**2 + worldVelocity.y**2 + worldVelocity.z**2);
  const totalWorldAccel = Math.sqrt(worldAccel.x**2 + worldAccel.y**2 + worldAccel.z**2);

  if (!train) {
    return (
      <Paper p="md" withBorder>
        <Text c="dimmed" size="sm">
          No train selected
        </Text>
      </Paper>
    );
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

        {/* World Acceleration Components */}
        <Text size="sm" fw={600} c="gray.3" mt="xs">
          World Acceleration (Three.js coords)
        </Text>

        <MetricRow
          label="  Ax (Right)"
          value={`${worldAccel.x.toFixed(2)} m/s²`}
          color={Math.abs(worldAccel.x) > 5 ? 'orange' : undefined}
        />
        <MetricRow
          label="  Ay (Up)"
          value={`${worldAccel.y.toFixed(2)} m/s²`}
          color={worldAccel.y < -5 ? 'red' : worldAccel.y > 5 ? 'orange' : undefined}
        />
        <MetricRow
          label="  Az (Forward)"
          value={`${worldAccel.z.toFixed(2)} m/s²`}
          color={Math.abs(worldAccel.z) > 5 ? 'orange' : undefined}
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