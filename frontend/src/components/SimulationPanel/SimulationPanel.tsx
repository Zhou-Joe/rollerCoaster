import { Box, Text, Group, Badge, Divider, Tabs } from '@mantine/core';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useEffect, useRef, useState } from 'react';
import type { SimulationState, InterpolatedPath } from '../../types';

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
  ax: number;
  ay: number;
  az: number;
  aTotal: number;
}

const MAX_HISTORY_POINTS = 200;

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
        position: [
          p1.position[0] + t * (p2.position[0] - p1.position[0]),
          p1.position[1] + t * (p2.position[1] - p1.position[1]),
          p1.position[2] + t * (p2.position[2] - p1.position[2]),
        ] as [number, number, number],
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
        curvature: p1.curvature + t * (p2.curvature - p1.curvature),
      };
    }
  }
  return path.points.find((p) => Math.abs(p.s - s) < 0.5);
}

// Train history card component
function TrainCard({ train, path, history }: { 
  train: SimulationState['trains'][0]; 
  path: InterpolatedPath | undefined;
  history: HistoryPoint[];
}) {
  const geometryPoint = train && path ? findPointAtS(path, train.s_front_m) : null;

  // Compute world coordinate velocity components
  const worldVelocity = geometryPoint ? {
    x: train.velocity_mps * geometryPoint.tangent[0],
    y: train.velocity_mps * geometryPoint.tangent[1],
    z: train.velocity_mps * geometryPoint.tangent[2],
  } : { x: 0, y: 0, z: 0 };

  // Compute world coordinate acceleration components
  const tangentAccel = geometryPoint ? {
    x: train.acceleration_mps2 * geometryPoint.tangent[0],
    y: train.acceleration_mps2 * geometryPoint.tangent[1],
    z: train.acceleration_mps2 * geometryPoint.tangent[2],
  } : { x: 0, y: 0, z: 0 };

  const centripetalMag = geometryPoint ? train.velocity_mps * train.velocity_mps * geometryPoint.curvature : 0;
  const centripetalAccel = geometryPoint ? {
    x: -centripetalMag * geometryPoint.normal[0],
    y: -centripetalMag * geometryPoint.normal[1],
    z: -centripetalMag * geometryPoint.normal[2],
  } : { x: 0, y: 0, z: 0 };

  const worldAccel = {
    x: tangentAccel.x + centripetalAccel.x,
    y: tangentAccel.y + centripetalAccel.y,
    z: tangentAccel.z + centripetalAccel.z,
  };

  const totalVelocity = Math.sqrt(worldVelocity.x**2 + worldVelocity.y**2 + worldVelocity.z**2);
  const totalAccel = Math.sqrt(worldAccel.x**2 + worldAccel.y**2 + worldAccel.z**2);

  // Position
  const position = geometryPoint?.position || [0, 0, 0] as [number, number, number];
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
          <Text size="xs" c="gray.5" style={{ width: '25%', textAlign: 'right' }}>|V|</Text>
        </Box>
        <Box style={{ display: 'flex', justifyContent: 'space-between' }}>
          <Text size="xs" style={{ width: '25%', color: getSpeedColor(worldVelocity.x), fontFamily: 'monospace' }}>{worldVelocity.x.toFixed(2)}</Text>
          <Text size="xs" style={{ width: '25%', color: getSpeedColor(worldVelocity.y), fontFamily: 'monospace' }}>{worldVelocity.y.toFixed(2)}</Text>
          <Text size="xs" style={{ width: '25%', color: getSpeedColor(worldVelocity.z), fontFamily: 'monospace' }}>{worldVelocity.z.toFixed(2)}</Text>
          <Text size="xs" style={{ width: '25%', color: getSpeedColor(totalVelocity), fontFamily: 'monospace', fontWeight: 600, textAlign: 'right' }}>{totalVelocity.toFixed(2)}</Text>
        </Box>
      </Box>

      {/* Acceleration Table */}
      <Text size="xs" c="gray.4" mb={4}>Acceleration (m/s²) - World Coordinates</Text>
      <Box style={{ fontSize: '11px' }} mb="xs">
        <Box style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #444', paddingBottom: 2, marginBottom: 2 }}>
          <Text size="xs" c="gray.5" style={{ width: '25%' }}>Ax</Text>
          <Text size="xs" c="gray.5" style={{ width: '25%' }}>Ay</Text>
          <Text size="xs" c="gray.5" style={{ width: '25%' }}>Az</Text>
          <Text size="xs" c="gray.5" style={{ width: '25%', textAlign: 'right' }}>|A|</Text>
        </Box>
        <Box style={{ display: 'flex', justifyContent: 'space-between' }}>
          <Text size="xs" style={{ width: '25%', color: getAccelColor(worldAccel.x), fontFamily: 'monospace' }}>{worldAccel.x.toFixed(2)}</Text>
          <Text size="xs" style={{ width: '25%', color: getAccelColor(worldAccel.y), fontFamily: 'monospace' }}>{worldAccel.y.toFixed(2)}</Text>
          <Text size="xs" style={{ width: '25%', color: getAccelColor(worldAccel.z), fontFamily: 'monospace' }}>{worldAccel.z.toFixed(2)}</Text>
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

      <Divider my="xs" color="#444" />

      {/* G-Forces summary */}
      <Group gap="xs">
        <Badge size="xs" variant="light" color="blue">G: {train.gforces.resultant_g.toFixed(2)}</Badge>
        <Badge size="xs" variant="light" color="cyan">Mass: {(train.mass_kg / 1000).toFixed(1)}t</Badge>
      </Group>

      <Divider my="sm" color="#444" />

      {/* Charts */}
      <Text size="xs" c="gray.4" mb="xs">History Plots</Text>
      
      <Tabs defaultValue="velocity">
        <Tabs.List>
          <Tabs.Tab value="velocity" style={{ fontSize: '11px', padding: '4px 8px' }}>Velocity</Tabs.Tab>
          <Tabs.Tab value="accel" style={{ fontSize: '11px', padding: '4px 8px' }}>Acceleration</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="velocity" pt="xs">
          <Box style={{ height: 150, background: '#1a1a1a', borderRadius: 4, padding: 4 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={history} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#888' }} stroke="#444" />
                <YAxis tick={{ fontSize: 10, fill: '#888' }} stroke="#444" />
                <Tooltip 
                  contentStyle={{ background: '#2a2a2a', border: '1px solid #444', fontSize: 11 }}
                  labelStyle={{ color: '#fff' }}
                />
                <Legend wrapperStyle={{ fontSize: 10 }} />
                <Line type="monotone" dataKey="vx" stroke="#ff6b6b" dot={false} strokeWidth={1.5} name="Vx" />
                <Line type="monotone" dataKey="vy" stroke="#69db7c" dot={false} strokeWidth={1.5} name="Vy" />
                <Line type="monotone" dataKey="vz" stroke="#74c0fc" dot={false} strokeWidth={1.5} name="Vz" />
                <Line type="monotone" dataKey="vTotal" stroke="#ffd43b" dot={false} strokeWidth={2} name="|V|" />
              </LineChart>
            </ResponsiveContainer>
          </Box>
        </Tabs.Panel>

        <Tabs.Panel value="accel" pt="xs">
          <Box style={{ height: 150, background: '#1a1a1a', borderRadius: 4, padding: 4 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={history} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#888' }} stroke="#444" />
                <YAxis tick={{ fontSize: 10, fill: '#888' }} stroke="#444" />
                <Tooltip 
                  contentStyle={{ background: '#2a2a2a', border: '1px solid #444', fontSize: 11 }}
                  labelStyle={{ color: '#fff' }}
                />
                <Legend wrapperStyle={{ fontSize: 10 }} />
                <Line type="monotone" dataKey="ax" stroke="#ff6b6b" dot={false} strokeWidth={1.5} name="Ax" />
                <Line type="monotone" dataKey="ay" stroke="#69db7c" dot={false} strokeWidth={1.5} name="Ay" />
                <Line type="monotone" dataKey="az" stroke="#74c0fc" dot={false} strokeWidth={1.5} name="Az" />
                <Line type="monotone" dataKey="aTotal" stroke="#ffd43b" dot={false} strokeWidth={2} name="|A|" />
              </LineChart>
            </ResponsiveContainer>
          </Box>
        </Tabs.Panel>
      </Tabs>
    </Box>
  );
}

export function SimulationPanel({ simulationState, interpolatedPaths }: SimulationPanelProps) {
  const { time_s, running, trains } = simulationState;
  const prevTimeRef = useRef<number>(0);
  
  // Use React state for history to trigger re-renders
  const [histories, setHistories] = useState<Map<string, HistoryPoint[]>>(new Map());

  // Update history for each train
  useEffect(() => {
    const newHistories = new Map(histories);
    let updated = false;

    trains.forEach((train) => {
      const path = interpolatedPaths.get(train.path_id);
      const geometryPoint = train && path ? findPointAtS(path, train.s_front_m) : null;

      // Compute world coordinate velocity components
      const worldVelocity = geometryPoint ? {
        x: train.velocity_mps * geometryPoint.tangent[0],
        y: train.velocity_mps * geometryPoint.tangent[1],
        z: train.velocity_mps * geometryPoint.tangent[2],
      } : { x: 0, y: 0, z: 0 };

      // Compute world coordinate acceleration components
      const tangentAccel = geometryPoint ? {
        x: train.acceleration_mps2 * geometryPoint.tangent[0],
        y: train.acceleration_mps2 * geometryPoint.tangent[1],
        z: train.acceleration_mps2 * geometryPoint.tangent[2],
      } : { x: 0, y: 0, z: 0 };

      const centripetalMag = geometryPoint ? train.velocity_mps * train.velocity_mps * geometryPoint.curvature : 0;
      const centripetalAccel = geometryPoint ? {
        x: -centripetalMag * geometryPoint.normal[0],
        y: -centripetalMag * geometryPoint.normal[1],
        z: -centripetalMag * geometryPoint.normal[2],
      } : { x: 0, y: 0, z: 0 };

      const worldAccel = {
        x: tangentAccel.x + centripetalAccel.x,
        y: tangentAccel.y + centripetalAccel.y,
        z: tangentAccel.z + centripetalAccel.z,
      };

      const totalVelocity = Math.sqrt(worldVelocity.x**2 + worldVelocity.y**2 + worldVelocity.z**2);
      const totalAccel = Math.sqrt(worldAccel.x**2 + worldAccel.y**2 + worldAccel.z**2);

      // Only add point if time has advanced
      if (time_s > prevTimeRef.current) {
        updated = true;
        
        const existingHistory = newHistories.get(train.train_id) || [];
        const newHistory = [...existingHistory, {
          time: time_s,
          vx: worldVelocity.x,
          vy: worldVelocity.y,
          vz: worldVelocity.z,
          vTotal: totalVelocity,
          ax: worldAccel.x,
          ay: worldAccel.y,
          az: worldAccel.z,
          aTotal: totalAccel,
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
    if (time_s < prevTimeRef.current) {
      setHistories(new Map());
    }
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
          <strong>World Coordinates:</strong> X=Right, Y=Up, Z=Forward (global 3D space)
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