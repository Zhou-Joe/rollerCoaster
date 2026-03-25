import { useMemo } from 'react';
import * as THREE from 'three';
import type { InterpolatedPath } from '../../types';

interface TrackMeshProps {
  path: InterpolatedPath;
  selected?: boolean;
  color?: string;
}

export function TrackMesh({ path, selected = false, color = '#4a90d9' }: TrackMeshProps) {
  // Create track geometry from interpolated path
  const { trackGeometry, railGeometry } = useMemo(() => {
    if (!path.points || path.points.length === 0) {
      return { trackGeometry: null, railGeometry: null };
    }

    // Create a tube along the path for the track rail
    const points = path.points.map((p) => new THREE.Vector3(...p.position));

    // Use CatmullRomCurve3 for smooth interpolation
    const curve = new THREE.CatmullRomCurve3(points, false, 'catmullrom', 0.5);

    // Create tube geometry for rails
    const tubeGeometry = new THREE.TubeGeometry(curve, points.length * 2, 0.15, 8, false);

    // Create cross-tie geometry
    const tiePositions: THREE.Vector3[] = [];
    const tieQuaternions: THREE.Quaternion[] = [];
    const tieSpacing = 1.5; // meters between ties

    for (let s = 0; s < path.total_length; s += tieSpacing) {
      const point = path.points.find((p) => Math.abs(p.s - s) < 0.5);
      if (point) {
        tiePositions.push(new THREE.Vector3(...point.position));
        // Create quaternion from the Frenet-Serret frame
        const tangent = new THREE.Vector3(...point.tangent);
        const normal = new THREE.Vector3(...point.normal);
        const binormal = new THREE.Vector3(...point.binormal);
        const matrix = new THREE.Matrix4().makeBasis(tangent, binormal, normal);
        const quaternion = new THREE.Quaternion().setFromRotationMatrix(matrix);
        tieQuaternions.push(quaternion);
      }
    }

    return {
      trackGeometry: tubeGeometry,
      railGeometry: { positions: tiePositions, quaternions: tieQuaternions },
    };
  }, [path]);

  if (!trackGeometry) return null;

  return (
    <group>
      {/* Main rail - left */}
      <mesh geometry={trackGeometry} castShadow receiveShadow>
        <meshStandardMaterial
          color={selected ? '#f59e0b' : color}
          metalness={0.7}
          roughness={0.3}
        />
      </mesh>

      {/* Cross ties */}
      {railGeometry.positions.map((pos, idx) => (
        <mesh
          key={idx}
          position={pos}
          quaternion={railGeometry.quaternions[idx]}
          castShadow
          receiveShadow
        >
          <boxGeometry args={[0.1, 1.2, 0.08]} />
          <meshStandardMaterial color="#4a5568" metalness={0.3} roughness={0.7} />
        </mesh>
      ))}

      {/* Support pillars - simplified */}
      <SupportPillars path={path} />
    </group>
  );
}

function SupportPillars({ path }: { path: InterpolatedPath }) {
  const pillarPositions = useMemo(() => {
    const positions: { pos: THREE.Vector3; height: number }[] = [];
    const pillarSpacing = 10; // meters between pillars

    for (let s = 0; s < path.total_length; s += pillarSpacing) {
      const point = path.points.find((p) => Math.abs(p.s - s) < 1);
      if (point && point.position[2] > 2) {
        positions.push({
          pos: new THREE.Vector3(point.position[0], point.position[1], 0),
          height: point.position[2],
        });
      }
    }

    return positions;
  }, [path]);

  return (
    <group>
      {pillarPositions.map((pillar, idx) => (
        <mesh
          key={idx}
          position={pillar.pos}
          castShadow
          receiveShadow
        >
          <cylinderGeometry args={[0.3, 0.4, pillar.height, 8]} />
          <meshStandardMaterial color="#64748b" metalness={0.5} roughness={0.5} />
        </mesh>
      ))}
    </group>
  );
}