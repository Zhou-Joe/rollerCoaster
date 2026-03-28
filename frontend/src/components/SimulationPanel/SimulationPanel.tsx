import { Box, Text, Group, Badge, Divider, Tabs } from '@mantine/core';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useEffect, useRef, useState } from 'react';
import type { SimulationState, InterpolatedPath } from '../../types';
import { computeTrainKinematics } from '../../utils/trainKinematics';

interface SimulationPanelProps {
  simulationState: SimulationState;
  interpolatedPaths: Map<string, InterpolatedPath>;
}

// History data point interface
interface HistoryPoint {
  time: number;
  vx: number;
  vy: number;
  vz: number;
  vTotal: number;
  aForeAft: number;
  aRightLeft: number;
  aEyeUpDown: number;
  aTotal: number;
  kineticJ: number;
  potentialJ: number;
  totalJ: number;
  // Equipment forces
  lsmForceN: number;
  liftForceN: number;
  brakeForceN: number;
  equipmentForceN: number;
}

const MAX_HISTORY_POINTS = 200;

// Chart wrapper component that ensures container has dimensions
function ChartWrapper({ data, lines, yAxisFormatter }: {
  data: HistoryPoint[];
  lines: { dataKey: string; stroke: string; name: string; strokeWidth?: number }[];
  yAxisFormatter?: (value: number) => string;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          setDimensions({ width, height });
        }
      }
    });

    resizeObserver.observe(container);
    return () => resizeObserver.disconnect();
  }, []);

  const { width, height } = dimensions;

  return (
    <Box ref={containerRef} style={{ height: 150, background: '#1a1a1a', borderRadius: 4, padding: 4, minWidth: 200 }}>
      {width > 0 && height > 0 && data.length > 0 && (
        <ResponsiveContainer width={width} height={height}>
          <LineChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 10, fill: '#888' }}
              stroke="#444"
              tickFormatter={(value) => value.toFixed(1)}
              label={{ value: 'Time (s)', position: 'insideBottom', offset: -2, fontSize: 10, fill: '#888' }}
            />
            <YAxis tick={{ fontSize: 10, fill: '#888' }} stroke="#444" tickFormatter={yAxisFormatter} />
            <Tooltip
              contentStyle={{ background: '#2a2a2a', border: '1px solid #444', fontSize: 11 }}
              labelStyle={{ color: '#fff' }}
              formatter={(value) => [(value as number).toFixed(3), '']}
              labelFormatter={(label) => `Time: ${(label as number).toFixed(2)}s`}
            />
            <Legend wrapperStyle={{ fontSize: 10 }} />
            {lines.map((line) => (
              <Line
                key={line.dataKey}
                type="monotone"
                dataKey={line.dataKey}
                stroke={line.stroke}
                dot={false}
                strokeWidth={line.strokeWidth || 1.5}
                name={line.name}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}
    </Box>
  );
}

// Train history card component
function TrainCard({ train, path, history }: { 
  train: SimulationState['trains'][0]; 
  path: InterpolatedPath | undefined;
  history: HistoryPoint[];
}) {
  const { worldVelocity, localAcceleration, totalWorldAcceleration: totalAccel, position } =
    computeTrainKinematics(path, train.s_front_m, train.velocity_mps, train.acceleration_mps2);
  const distance = train.s_front_m;

  return (
    <Box p="sm" mb="sm" style={{ background: '#2a2a2a', borderRadius: 4 }}>
      <Text size="sm" c="white" fw={600} mb="xs">{train.train_id}</Text>
      
      {/* Velocity Table */}
      <Text size="xs" c="gray.4" mb={4}>Velocity (m/s) - World Coordinates</Text>
      <Box style={{ fontSize: '11px' }} mb="xs">
        <Box style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #444', paddingBottom: 2, marginBottom: 2 }}>
          <Text size="xs" c="gray.5" style={{ width: '25%' }}>Vx</Text>
          <Text size="xs" c="gray.5" style={{ width: '25%' }}>Vy</Text>
          <Text size="xs" c="gray.5" style={{ width: '25%' }}>Vz</Text>
          <Text size="xs" c="gray.5" style={{ width: '25%', textAlign: 'right' }}>V</Text>
        </Box>
        <Box style={{ display: 'flex', justifyContent: 'space-between' }}>
          <Text size="xs" style={{ width: '25%', color: getSpeedColor(worldVelocity.x), fontFamily: 'monospace' }}>{worldVelocity.x.toFixed(2)}</Text>
          <Text size="xs" style={{ width: '25%', color: getSpeedColor(worldVelocity.y), fontFamily: 'monospace' }}>{worldVelocity.y.toFixed(2)}</Text>
          <Text size="xs" style={{ width: '25%', color: getSpeedColor(worldVelocity.z), fontFamily: 'monospace' }}>{worldVelocity.z.toFixed(2)}</Text>
          <Text size="xs" style={{ width: '25%', color: train.velocity_mps >= 0 ? '#88ff88' : '#ff8888', fontFamily: 'monospace', fontWeight: 600, textAlign: 'right' }}>{train.velocity_mps.toFixed(2)}</Text>
        </Box>
      </Box>

      {/* Acceleration Table */}
      <Text size="xs" c="gray.4" mb={4}>Acceleration (m/s²) - Train Coordinates</Text>
      <Box style={{ fontSize: '11px' }} mb="xs">
        <Box style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #444', paddingBottom: 2, marginBottom: 2 }}>
          <Text size="xs" c="gray.5" style={{ width: '25%' }}>Fore/Aft</Text>
          <Text size="xs" c="gray.5" style={{ width: '25%' }}>Right/Left</Text>
          <Text size="xs" c="gray.5" style={{ width: '25%' }}>Eye Up/Down</Text>
          <Text size="xs" c="gray.5" style={{ width: '25%', textAlign: 'right' }}>|A|</Text>
        </Box>
        <Box style={{ display: 'flex', justifyContent: 'space-between' }}>
          <Text size="xs" style={{ width: '25%', color: getAccelColor(localAcceleration.foreAft), fontFamily: 'monospace' }}>{localAcceleration.foreAft.toFixed(2)}</Text>
          <Text size="xs" style={{ width: '25%', color: getAccelColor(localAcceleration.rightLeft), fontFamily: 'monospace' }}>{localAcceleration.rightLeft.toFixed(2)}</Text>
          <Text size="xs" style={{ width: '25%', color: getAccelColor(localAcceleration.eyeUpDown), fontFamily: 'monospace' }}>{localAcceleration.eyeUpDown.toFixed(2)}</Text>
          <Text size="xs" style={{ width: '25%', color: getAccelColor(totalAccel), fontFamily: 'monospace', fontWeight: 600, textAlign: 'right' }}>{totalAccel.toFixed(2)}</Text>
        </Box>
      </Box>

      {/* Position Table */}
      <Text size="xs" c="gray.4" mb={4}>Position (m)</Text>
      <Box style={{ fontSize: '11px' }} mb="xs">
        <Box style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #444', paddingBottom: 2, marginBottom: 2 }}>
          <Text size="xs" c="gray.5" style={{ width: '25%' }}>X</Text>
          <Text size="xs" c="gray.5" style={{ width: '25%' }}>Y</Text>
          <Text size="xs" c="gray.5" style={{ width: '25%' }}>Z</Text>
          <Text size="xs" c="gray.5" style={{ width: '25%', textAlign: 'right' }}>Dist</Text>
        </Box>
        <Box style={{ display: 'flex', justifyContent: 'space-between' }}>
          <Text size="xs" style={{ width: '25%', color: '#ccc', fontFamily: 'monospace' }}>{position[0].toFixed(1)}</Text>
          <Text size="xs" style={{ width: '25%', color: '#ccc', fontFamily: 'monospace' }}>{position[1].toFixed(1)}</Text>
          <Text size="xs" style={{ width: '25%', color: '#ccc', fontFamily: 'monospace' }}>{position[2].toFixed(1)}</Text>
          <Text size="xs" style={{ width: '25%', color: '#fff', fontFamily: 'monospace', fontWeight: 600, textAlign: 'right' }}>{distance.toFixed(1)}</Text>
        </Box>
      </Box>

      {/* Energy Table */}
      <Text size="xs" c="gray.4" mb={4}>Energy (kJ)</Text>
      <Box style={{ fontSize: '11px' }} mb="xs">
        <Box style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #444', paddingBottom: 2, marginBottom: 2 }}>
          <Text size="xs" c="gray.5" style={{ width: '33%' }}>Kinetic</Text>
          <Text size="xs" c="gray.5" style={{ width: '33%' }}>Potential</Text>
          <Text size="xs" c="gray.5" style={{ width: '33%', textAlign: 'right' }}>Total</Text>
        </Box>
        <Box style={{ display: 'flex', justifyContent: 'space-between' }}>
          <Text size="xs" style={{ width: '33%', color: '#69db7c', fontFamily: 'monospace' }}>
            {((train.energy?.kinetic_j ?? 0) / 1000).toFixed(2)}
          </Text>
          <Text size="xs" style={{ width: '33%', color: '#74c0fc', fontFamily: 'monospace' }}>
            {((train.energy?.potential_j ?? 0) / 1000).toFixed(2)}
          </Text>
          <Text size="xs" style={{ width: '33%', color: '#ffd43b', fontFamily: 'monospace', fontWeight: 600, textAlign: 'right' }}>
            {((train.energy?.total_j ?? 0) / 1000).toFixed(2)}
          </Text>
        </Box>
      </Box>

      <Divider my="xs" color="#444" />

      {/* G-Forces and Acceleration comparison */}
      <Group gap="xs">
        <Badge size="xs" variant="light" color="blue">G: {train.gforces.resultant_g.toFixed(2)}</Badge>
        <Badge size="xs" variant="light" color="orange">|A|: {totalAccel.toFixed(2)} m/s²</Badge>
        <Badge size="xs" variant="light" color="cyan">Mass: {(train.mass_kg / 1000).toFixed(1)}t</Badge>
      </Group>

      <Divider my="sm" color="#444" />

      {/* Charts */}
      <Text size="xs" c="gray.4" mb="xs">History Plots</Text>

      <Tabs defaultValue="velocity">
        <Tabs.List>
          <Tabs.Tab value="velocity" style={{ fontSize: '11px', padding: '4px 8px' }}>Velocity</Tabs.Tab>
          <Tabs.Tab value="accel" style={{ fontSize: '11px', padding: '4px 8px' }}>Acceleration</Tabs.Tab>
          <Tabs.Tab value="energy" style={{ fontSize: '11px', padding: '4px 8px' }}>Energy</Tabs.Tab>
          <Tabs.Tab value="equip" style={{ fontSize: '11px', padding: '4px 8px' }}>Equipment</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="velocity" pt="xs">
          <ChartWrapper
            data={history}
            lines={[
              { dataKey: 'vx', stroke: '#ff6b6b', name: 'Vx' },
              { dataKey: 'vy', stroke: '#69db7c', name: 'Vy' },
              { dataKey: 'vz', stroke: '#74c0fc', name: 'Vz' },
              { dataKey: 'vTotal', stroke: '#ffd43b', name: 'V', strokeWidth: 2 },
            ]}
          />
        </Tabs.Panel>

        <Tabs.Panel value="accel" pt="xs">
          <ChartWrapper
            data={history}
            lines={[
              { dataKey: 'aForeAft', stroke: '#ff6b6b', name: 'Fore/Aft' },
              { dataKey: 'aRightLeft', stroke: '#69db7c', name: 'Right/Left' },
              { dataKey: 'aEyeUpDown', stroke: '#74c0fc', name: 'Eye Up/Down' },
            ]}
          />
        </Tabs.Panel>

        <Tabs.Panel value="energy" pt="xs">
          <ChartWrapper
            data={history}
            lines={[
              { dataKey: 'kineticJ', stroke: '#69db7c', name: 'Kinetic' },
              { dataKey: 'potentialJ', stroke: '#74c0fc', name: 'Potential' },
              { dataKey: 'totalJ', stroke: '#ffd43b', name: 'Total', strokeWidth: 2 },
            ]}
            yAxisFormatter={(value) => `${(value / 1000).toFixed(1)}k`}
          />
        </Tabs.Panel>

        <Tabs.Panel value="equip" pt="xs">
          <ChartWrapper
            data={history}
            lines={[
              { dataKey: 'lsmForceN', stroke: '#69db7c', name: 'LSM' },
              { dataKey: 'liftForceN', stroke: '#74c0fc', name: 'Lift' },
              { dataKey: 'brakeForceN', stroke: '#ff8787', name: 'Brake' },
              { dataKey: 'equipmentForceN', stroke: '#ffd43b', name: 'Total Equip', strokeWidth: 2 },
            ]}
            yAxisFormatter={(value) => `${(value / 1000).toFixed(1)}k`}
          />
        </Tabs.Panel>
      </Tabs>
    </Box>
  );
}

export function SimulationPanel({ simulationState, interpolatedPaths }: SimulationPanelProps) {
  const { time_s, running, trains } = simulationState;
  const prevTimeRef = useRef<number>(0);
  const lastTimeRef = useRef<number>(0); // For reset detection
  
  // Use React state for history to trigger re-renders
  const [histories, setHistories] = useState<Map<string, HistoryPoint[]>>(new Map());

  // Update history for each train
  useEffect(() => {
    const newHistories = new Map(histories);
    let updated = false;

    trains.forEach((train) => {
      const path = interpolatedPaths.get(train.path_id);
      const {
        worldVelocity,
        localAcceleration,
        totalWorldAcceleration: totalAccel,
      } = computeTrainKinematics(path, train.s_front_m, train.velocity_mps, train.acceleration_mps2);

      // Only add point if time has advanced
      if (time_s > prevTimeRef.current) {
        updated = true;

        const existingHistory = newHistories.get(train.train_id) || [];
        const newHistory = [...existingHistory, {
          time: time_s,
          vx: worldVelocity.x,
          vy: worldVelocity.y,
          vz: worldVelocity.z,
          vTotal: train.velocity_mps, // Use signed velocity instead of absolute
          aForeAft: localAcceleration.foreAft,
          aRightLeft: localAcceleration.rightLeft,
          aEyeUpDown: localAcceleration.eyeUpDown,
          aTotal: totalAccel,
          kineticJ: train.energy?.kinetic_j ?? 0,
          potentialJ: train.energy?.potential_j ?? 0,
          totalJ: train.energy?.total_j ?? 0,
          // Equipment forces
          lsmForceN: train.equipment_forces?.lsm_force_n ?? 0,
          liftForceN: train.equipment_forces?.lift_force_n ?? 0,
          brakeForceN: train.equipment_forces?.brake_force_n ?? 0,
          equipmentForceN: train.forces.equipment_n,
        }];

        // Limit history size
        if (newHistory.length > MAX_HISTORY_POINTS) {
          newHistory.shift();
        }

        newHistories.set(train.train_id, newHistory);
      }
    });

    if (updated) {
      setHistories(newHistories);
    }

    prevTimeRef.current = time_s;
  }, [time_s, trains, interpolatedPaths, histories]);

  // Clear history when simulation resets
  useEffect(() => {
    if (time_s < lastTimeRef.current) {
      setHistories(new Map());
      prevTimeRef.current = time_s;
    }
    lastTimeRef.current = time_s;
  }, [time_s]);

  return (
    <Box>
      <Text size="xs" c="dimmed" mb="xs">Simulation</Text>
      
      {/* Time and Status */}
      <Box p="sm" style={{ background: '#2a2a2a', borderRadius: 4 }} mb="sm">
        <Group justify="space-between">
          <Text size="sm" c="white">Time: <span style={{ fontFamily: 'monospace' }}>{time_s.toFixed(2)}s</span></Text>
          <Badge size="sm" color={running ? 'green' : 'gray'}>
            {running ? 'Running' : 'Stopped'}
          </Badge>
        </Group>
      </Box>

      {/* Coordinate system info */}
      <Box p="xs" style={{ background: '#1e3a5f', borderRadius: 4 }} mb="sm">
        <Text size="xs" c="gray.3">
          <strong>Velocity:</strong> world coordinates. <strong>Acceleration:</strong> train coordinates with +Fore, +Right, +Eye Up.
        </Text>
      </Box>

      {/* Train cards */}
      {trains.map((train) => {
        const path = interpolatedPaths.get(train.path_id);
        const history = histories.get(train.train_id) || [];

        return (
          <TrainCard 
            key={train.train_id} 
            train={train} 
            path={path} 
            history={history}
          />
        );
      })}
    </Box>
  );
}

function getSpeedColor(value: number): string {
  const absValue = Math.abs(value);
  if (absValue < 2) return '#88ff88';
  if (absValue < 5) return '#ffff88';
  if (absValue < 10) return '#ffaa55';
  return '#ff5555';
}

function getAccelColor(value: number): string {
  const absValue = Math.abs(value);
  if (absValue < 1) return '#88ff88';
  if (absValue < 3) return '#ffff88';
  if (absValue < 5) return '#ffaa55';
  return '#ff5555';
}
