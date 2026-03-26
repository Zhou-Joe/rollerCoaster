import { useMemo, useRef } from 'react';
import * as THREE from 'three';
import type { TrainPhysicsState, InterpolatedPath, Vehicle, Train, Project } from '../../types';

interface TrainMeshProps {
  trainState: TrainPhysicsState;
  path: InterpolatedPath;
  project?: Project;
  color?: string;
  selected?: boolean;
}

/**
 * Convert our coordinate system (x, y, z where z=up) to Three.js (x, y, z where y=up)
 * Our system: x=east, y=north, z=up
 * Three.js: x=east, y=up, z=north (right-handed)
 */
function toThreeVec(v: [number, number, number]): THREE.Vector3 {
  return new THREE.Vector3(v[0], v[2], v[1]);
}

/**
 * Find a sample point on the path at a given arc length position
 */
function findPointAtS(path: InterpolatedPath, s: number): typeof path.points[0] | undefined {
  for (let i = 0; i < path.points.length - 1; i++) {
    const p1 = path.points[i];
    const p2 = path.points[i + 1];
    if (p1.s <= s && p2.s >= s) {
      const t = (s - p1.s) / (p2.s - p1.s);
      return {
        s: s,
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
        binormal: [
          p1.binormal[0] + t * (p2.binormal[0] - p1.binormal[0]),
          p1.binormal[1] + t * (p2.binormal[1] - p1.binormal[1]),
          p1.binormal[2] + t * (p2.binormal[2] - p1.binormal[2]),
        ] as [number, number, number],
        curvature: p1.curvature + t * (p2.curvature - p1.curvature),
        radius: p1.radius + t * (p2.radius - p1.radius),
        slope_deg: p1.slope_deg + t * (p2.slope_deg - p1.slope_deg),
        bank_deg: p1.bank_deg + t * (p2.bank_deg - p1.bank_deg),
      };
    }
  }
  return path.points.find((p) => Math.abs(p.s - s) < 0.5);
}

export function TrainMesh({ trainState, path, project, color = '#dc2626', selected = false }: TrainMeshProps) {
  const groupRef = useRef<THREE.Group>(null);

  const trainDef = useMemo(() => {
    if (!project) return null;
    return project.trains.find(t => t.id === trainState.train_id);
  }, [project, trainState.train_id]);

  const vehicles = useMemo(() => {
    if (!project || !trainDef) return [];
    return trainDef.vehicle_ids.map(vid => project.vehicles.find(v => v.id === vid)).filter(Boolean) as Vehicle[];
  }, [project, trainDef]);

  const vehiclePositions = useMemo(() => {
    const trainLength = trainState.s_front_m - trainState.s_rear_m;
    
    if (vehicles.length > 0) {
      const totalVehicleLength = vehicles.reduce((sum, v) => sum + v.length_m, 0);
      const gapSize = vehicles.length > 1 ? (trainLength - totalVehicleLength) / (vehicles.length - 1) : 0;
      
      const positions: { vehicle: Vehicle; sCenter: number }[] = [];
      let currentS = trainState.s_front_m;
      
      for (let i = 0; i < vehicles.length; i++) {
        const vehicle = vehicles[i];
        const vehicleCenter = currentS - vehicle.length_m / 2;
        positions.push({ vehicle, sCenter: vehicleCenter });
        currentS -= vehicle.length_m + gapSize;
      }
      return positions;
    }
    
    return [{
      vehicle: { id: 'default', length_m: trainLength, dry_mass_kg: 1000, capacity: 4 },
      sCenter: (trainState.s_front_m + trainState.s_rear_m) / 2,
    }];
  }, [vehicles, trainState]);

  if (vehiclePositions.length === 0) return null;

  return (
    <group ref={groupRef}>
      {vehiclePositions.map((vp, idx) => (
        <VehicleMesh
          key={vp.vehicle.id + idx}
          vehicle={vp.vehicle}
          sCenter={vp.sCenter}
          path={path}
          color={color}
          selected={selected}
          isLeading={idx === 0}
          velocity={trainState.velocity_mps}
        />
      ))}
    </group>
  );
}

interface VehicleMeshProps {
  vehicle: Vehicle;
  sCenter: number;
  path: InterpolatedPath;
  color: string;
  selected: boolean;
  isLeading: boolean;
  velocity: number;
}

function VehicleMesh({ vehicle, sCenter, path, color, selected, isLeading, velocity }: VehicleMeshProps) {
  const centerPoint = useMemo(() => findPointAtS(path, sCenter), [path, sCenter]);

  const { position, quaternion, length } = useMemo(() => {
    if (!centerPoint) {
      return {
        position: new THREE.Vector3(0, 0, 0),
        quaternion: new THREE.Quaternion(),
        length: vehicle.length_m,
      };
    }

    const pos = toThreeVec(centerPoint.position);
    
    // Transform tangent and normal from backend coordinates
    // Backend: (x, y, z) with z=up
    // Three.js: (x, z, y) with y=up (swizzle y and z)
    const tangent = toThreeVec(centerPoint.tangent).normalize();
    const normal = toThreeVec(centerPoint.normal).normalize();
    
    // CRITICAL: The swizzle transformation changes the handedness of the Frenet frame.
    // In backend: T × N = B (right-handed)
    // After swizzle: T × N = -B (the frame becomes left-handed!)
    // We must recompute binormal to ensure a proper right-handed frame in Three.js coords.
    // This ensures det([T, N, B]) = +1 for a valid rotation matrix.
    const binormal = new THREE.Vector3().crossVectors(tangent, normal).normalize();

    // Apply bank rotation around tangent axis
    const bankRad = THREE.MathUtils.degToRad(centerPoint.bank_deg || 0);
    const rotatedNormal = normal.clone().applyAxisAngle(tangent, bankRad);
    const rotatedBinormal = binormal.clone().applyAxisAngle(tangent, bankRad);

    // Build rotation matrix: columns are the basis vectors
    // Local X (forward) -> tangent, Local Y (up) -> normal, Local Z (right) -> binormal
    const matrix = new THREE.Matrix4();
    matrix.makeBasis(tangent, rotatedNormal, rotatedBinormal);
    
    const quat = new THREE.Quaternion().setFromRotationMatrix(matrix);

    return { position: pos, quaternion: quat, length: vehicle.length_m };
  }, [centerPoint, vehicle.length_m]);

  if (!centerPoint) return null;

  const vehicleColor = isLeading ? '#1e40af' : color;

  return (
    <group position={position} quaternion={quaternion}>
      <mesh castShadow receiveShadow position={[0, 0.5, 0]}>
        <boxGeometry args={[length * 0.9, 1.0, 1.4]} />
        <meshStandardMaterial color={selected ? '#fbbf24' : vehicleColor} metalness={0.6} roughness={0.4} />
      </mesh>

      <mesh position={[0, 1.1, 0]} castShadow>
        <boxGeometry args={[length * 0.85, 0.3, 1.2]} />
        <meshStandardMaterial color={vehicleColor} metalness={0.6} roughness={0.4} />
      </mesh>

      {isLeading && (
        <mesh position={[length * 0.45 + 0.3, 0.5, 0]} castShadow>
          <boxGeometry args={[0.6, 0.8, 1.2]} />
          <meshStandardMaterial color={vehicleColor} metalness={0.6} roughness={0.4} />
        </mesh>
      )}

      <WheelSet position={[-length * 0.35, 0.1, 0]} />
      <WheelSet position={[length * 0.35, 0.1, 0]} />

      {isLeading && velocity > 0.5 && (
        <mesh position={[length * 0.5 + 1.5, 0.8, 0]}>
          <coneGeometry args={[0.25, 1.0, 8]} />
          <meshBasicMaterial color="#22c55e" />
        </mesh>
      )}
    </group>
  );
}

function WheelSet({ position }: { position: [number, number, number] }) {
  return (
    <group position={position}>
      <mesh position={[0, 0, 0.6]} rotation={[0, 0, Math.PI / 2]} castShadow>
        <cylinderGeometry args={[0.2, 0.2, 0.12, 16]} />
        <meshStandardMaterial color="#1f2937" metalness={0.8} roughness={0.2} />
      </mesh>
      <mesh position={[0, 0, -0.6]} rotation={[0, 0, Math.PI / 2]} castShadow>
        <cylinderGeometry args={[0.2, 0.2, 0.12, 16]} />
        <meshStandardMaterial color="#1f2937" metalness={0.8} roughness={0.2} />
      </mesh>
      <mesh rotation={[0, 0, Math.PI / 2]} castShadow>
        <cylinderGeometry args={[0.06, 0.06, 1.2, 8]} />
        <meshStandardMaterial color="#374151" metalness={0.6} roughness={0.3} />
      </mesh>
    </group>
  );
}