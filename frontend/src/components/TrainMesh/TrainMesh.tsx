import { useMemo, useRef } from 'react';
import * as THREE from 'three';
import type { TrainPhysicsState, InterpolatedPath } from '../../types';

interface TrainMeshProps {
  trainState: TrainPhysicsState;
  path: InterpolatedPath;
  color?: string;
  selected?: boolean;
}

/**
 * Convert our coordinate system (x, y, z where z=up) to Three.js (x, y, z where y=up)
 */
function toThreeVec(v: [number, number, number]): THREE.Vector3 {
  return new THREE.Vector3(v[0], v[2], v[1]);
}

export function TrainMesh({ trainState, path, color = '#dc2626', selected = false }: TrainMeshProps) {
  const groupRef = useRef<THREE.Group>(null);

  // Find the sample point closest to the train's front position
  const frontPoint = useMemo(() => {
    return path.points.find((p) => Math.abs(p.s - trainState.s_front_m) < 0.5);
  }, [path.points, trainState.s_front_m]);

  // Calculate train orientation from Frenet-Serret frame
  const { position, quaternion, length } = useMemo(() => {
    if (!frontPoint) {
      return {
        position: new THREE.Vector3(0, 0, 0),
        quaternion: new THREE.Quaternion(),
        length: trainState.s_front_m - trainState.s_rear_m,
      };
    }

    // Convert position to Three.js coordinates
    const pos = toThreeVec(frontPoint.position);

    // Create rotation matrix from Frenet-Serret frame (also convert)
    const tangent = toThreeVec(frontPoint.tangent);
    const normal = toThreeVec(frontPoint.normal);
    const binormal = toThreeVec(frontPoint.binormal);

    // The train's forward direction is along the tangent
    const matrix = new THREE.Matrix4().makeBasis(
      tangent,   // X: forward
      binormal,  // Y: up (perpendicular to track surface)
      normal     // Z: right (towards center of curvature)
    );

    const quat = new THREE.Quaternion().setFromRotationMatrix(matrix);
    const trainLength = trainState.s_front_m - trainState.s_rear_m;

    return { position: pos, quaternion: quat, length: trainLength };
  }, [frontPoint, trainState]);

  if (!frontPoint) return null;

  return (
    <group ref={groupRef} position={position} quaternion={quaternion}>
      {/* Train body - main car */}
      <mesh castShadow receiveShadow>
        <boxGeometry args={[length * 0.9, 1.2, 1.5]} />
        <meshStandardMaterial
          color={selected ? '#fbbf24' : color}
          metalness={0.6}
          roughness={0.4}
        />
      </mesh>

      {/* Roof */}
      <mesh position={[0, 0.8, 0]} castShadow>
        <boxGeometry args={[length * 0.85, 0.4, 1.3]} />
        <meshStandardMaterial color={color} metalness={0.6} roughness={0.4} />
      </mesh>

      {/* Wheels */}
      <WheelSet position={[-length * 0.35, -0.6, 0]} />
      <WheelSet position={[length * 0.35, -0.6, 0]} />

      {/* Velocity indicator arrow */}
      {trainState.velocity_mps > 0.5 && (
        <mesh position={[length * 0.5 + 1, 0, 0]}>
          <coneGeometry args={[0.3, 1.5, 8]} />
          <meshBasicMaterial color="#22c55e" />
        </mesh>
      )}
    </group>
  );
}

function WheelSet({ position }: { position: [number, number, number] }) {
  return (
    <group position={position}>
      {/* Left wheel */}
      <mesh position={[0, 0, 0.7]} rotation={[Math.PI / 2, 0, 0]} castShadow>
        <cylinderGeometry args={[0.25, 0.25, 0.15, 16]} />
        <meshStandardMaterial color="#1f2937" metalness={0.8} roughness={0.2} />
      </mesh>
      {/* Right wheel */}
      <mesh position={[0, 0, -0.7]} rotation={[Math.PI / 2, 0, 0]} castShadow>
        <cylinderGeometry args={[0.25, 0.25, 0.15, 16]} />
        <meshStandardMaterial color="#1f2937" metalness={0.8} roughness={0.2} />
      </mesh>
      {/* Axle */}
      <mesh rotation={[Math.PI / 2, 0, 0]} castShadow>
        <cylinderGeometry args={[0.08, 0.08, 1.4, 8]} />
        <meshStandardMaterial color="#374151" metalness={0.6} roughness={0.3} />
      </mesh>
    </group>
  );
}