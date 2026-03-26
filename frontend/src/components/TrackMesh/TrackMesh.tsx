import { useMemo } from 'react';
import * as THREE from 'three';
import type { InterpolatedPath } from '../../types';

interface TrackMeshProps {
  path: InterpolatedPath;
  selected?: boolean;
  color?: string;
}

/**
 * Convert our coordinate system (x, y, z where z=up) to Three.js (x, y, z where y=up)
 */
function toThreeVec(v: [number, number, number]): THREE.Vector3 {
  return new THREE.Vector3(v[0], v[2], v[1]);
}

export function TrackMesh({ path, selected = false, color = '#4a90d9' }: TrackMeshProps) {
  // Create realistic triangular track structure
  const trackStructure = useMemo(() => {
    if (!path.points || path.points.length === 0) {
      return null;
    }

    // Track dimensions (in meters)
    const railRadius = 0.04; // 4cm radius running rails
    const spineRadius = 0.08; // 8cm radius backbone
    const railGauge = 1.1; // Distance between left and right rails
    const railOffset = railGauge / 2;
    const spineDrop = 0.35; // How far below rails the spine sits

    // Create curves for left rail, right rail, and spine
    const leftRailPoints: THREE.Vector3[] = [];
    const rightRailPoints: THREE.Vector3[] = [];
    const spinePoints: THREE.Vector3[] = [];

    for (const point of path.points) {
      const pos = toThreeVec(point.position);
      const tangent = toThreeVec(point.tangent).normalize();
      const normal = toThreeVec(point.normal).normalize();
      const binormal = toThreeVec(point.binormal).normalize();

      // Apply bank rotation around tangent axis
      const bankRad = THREE.MathUtils.degToRad(point.bank_deg || 0);

      // The binormal is HORIZONTAL (perpendicular to tangent and world-up)
      // The normal is VERTICAL (pointing upward from the track plane)
      // After banking, these rotate around the tangent together with the track
      const rotatedNormal = normal.clone().applyAxisAngle(tangent, bankRad);
      const rotatedBinormal = binormal.clone().applyAxisAngle(tangent, bankRad);

      // Left rail: offset in -binormal direction (horizontally to the left when looking forward)
      leftRailPoints.push(pos.clone().add(rotatedBinormal.clone().multiplyScalar(-railOffset)));

      // Right rail: offset in +binormal direction (horizontally to the right when looking forward)
      rightRailPoints.push(pos.clone().add(rotatedBinormal.clone().multiplyScalar(railOffset)));

      // Spine: below the track in the -normal direction (downward from track center)
      spinePoints.push(pos.clone().add(rotatedNormal.clone().multiplyScalar(-spineDrop)));
    }

    // Create smooth curves
    const leftCurve = new THREE.CatmullRomCurve3(leftRailPoints, false, 'catmullrom', 0.5);
    const rightCurve = new THREE.CatmullRomCurve3(rightRailPoints, false, 'catmullrom', 0.5);
    const spineCurve = new THREE.CatmullRomCurve3(spinePoints, false, 'catmullrom', 0.5);

    // Create tube geometries with enough segments for smoothness
    const segments = Math.max(path.points.length * 2, 200);
    const leftRailGeometry = new THREE.TubeGeometry(leftCurve, segments, railRadius, 12, false);
    const rightRailGeometry = new THREE.TubeGeometry(rightCurve, segments, railRadius, 12, false);
    const spineGeometry = new THREE.TubeGeometry(spineCurve, segments, spineRadius, 12, false);

    // Create cross-brace data
    const crossBraces: { position: THREE.Vector3; normal: THREE.Vector3; binormal: THREE.Vector3; bank_deg: number }[] = [];
    const tieSpacing = 1.0;

    for (let s = 0; s < path.total_length; s += tieSpacing) {
      const point = path.points.find((p) => Math.abs(p.s - s) < 0.5);
      if (point) {
        crossBraces.push({
          position: toThreeVec(point.position),
          normal: toThreeVec(point.normal),
          binormal: toThreeVec(point.binormal),
          bank_deg: point.bank_deg || 0,
        });
      }
    }

    return {
      leftRailGeometry,
      rightRailGeometry,
      spineGeometry,
      crossBraces,
      railGauge,
      spineDrop,
    };
  }, [path]);

  if (!trackStructure) return null;

  const railColor = selected ? '#f59e0b' : '#b0b0b0';
  const spineColor = selected ? '#f59e0b' : color;

  return (
    <group>
      {/* Left running rail */}
      <mesh geometry={trackStructure.leftRailGeometry} castShadow receiveShadow>
        <meshStandardMaterial color={railColor} metalness={0.85} roughness={0.15} />
      </mesh>

      {/* Right running rail */}
      <mesh geometry={trackStructure.rightRailGeometry} castShadow receiveShadow>
        <meshStandardMaterial color={railColor} metalness={0.85} roughness={0.15} />
      </mesh>

      {/* Central spine/backbone */}
      <mesh geometry={trackStructure.spineGeometry} castShadow receiveShadow>
        <meshStandardMaterial color={spineColor} metalness={0.7} roughness={0.3} />
      </mesh>

      {/* Cross braces */}
      {trackStructure.crossBraces.map((brace, idx) => (
        <CrossBrace
          key={idx}
          position={brace.position}
          normal={brace.normal}
          binormal={brace.binormal}
          bank_deg={brace.bank_deg}
          gauge={trackStructure.railGauge}
          spineDrop={trackStructure.spineDrop}
        />
      ))}

      {/* Support pillars */}
      <SupportPillars path={path} />
    </group>
  );
}

function CrossBrace({
  position,
  normal,
  binormal,
  bank_deg,
  gauge,
  spineDrop,
}: {
  position: THREE.Vector3;
  normal: THREE.Vector3;
  binormal: THREE.Vector3;
  bank_deg: number;
  gauge: number;
  spineDrop: number;
}) {
  const pipeRadius = 0.025;

  // binormal is HORIZONTAL (lateral, perpendicular to track direction)
  // normal is VERTICAL (upward from track plane)
  // Apply bank rotation to get the correct local frame
  const bankRad = THREE.MathUtils.degToRad(bank_deg);
  
  // Get tangent by crossing normal and binormal
  const tangent = new THREE.Vector3().crossVectors(normal, binormal).normalize();
  
  // Rotate normal and binormal around tangent by bank angle
  const rotatedNormal = normal.clone().applyAxisAngle(tangent, bankRad);
  const rotatedBinormal = binormal.clone().applyAxisAngle(tangent, bankRad);

  // Calculate actual 3D positions of rails and spine
  const leftRailPos = rotatedBinormal.clone().multiplyScalar(-gauge / 2);
  const rightRailPos = rotatedBinormal.clone().multiplyScalar(gauge / 2);
  const spinePos = rotatedNormal.clone().multiplyScalar(-spineDrop);

  // Calculate diagonal lengths
  const leftDiagonalLength = leftRailPos.clone().sub(spinePos).length();
  const rightDiagonalLength = rightRailPos.clone().sub(spinePos).length();

  // Helper function to create orientation for a cylinder between two points
  const createCylinderOrientation = (start: THREE.Vector3, end: THREE.Vector3) => {
    const direction = end.clone().sub(start).normalize();
    const quaternion = new THREE.Quaternion();
    quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction);
    return quaternion;
  };

  // Calculate midpoints for diagonal positions
  const leftDiagonalMid = leftRailPos.clone().add(spinePos).multiplyScalar(0.5);
  const rightDiagonalMid = rightRailPos.clone().add(spinePos).multiplyScalar(0.5);

  // Calculate the horizontal tie orientation (along binormal direction)
  const horizontalTieQuaternion = new THREE.Quaternion();
  horizontalTieQuaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), rotatedBinormal.clone().normalize());

  return (
    <group position={position}>
      {/* Horizontal cross tie between rails - at the rail level */}
      <mesh 
        position={new THREE.Vector3(0, 0, 0)}
        quaternion={horizontalTieQuaternion}
        castShadow
      >
        <cylinderGeometry args={[pipeRadius, pipeRadius, gauge, 8]} />
        <meshStandardMaterial color="#6b7280" metalness={0.6} roughness={0.4} />
      </mesh>

      {/* Left diagonal: left rail to spine */}
      <mesh
        position={leftDiagonalMid}
        quaternion={createCylinderOrientation(leftRailPos, spinePos)}
        castShadow
      >
        <cylinderGeometry args={[pipeRadius, pipeRadius, leftDiagonalLength, 8]} />
        <meshStandardMaterial color="#6b7280" metalness={0.6} roughness={0.4} />
      </mesh>

      {/* Right diagonal: right rail to spine */}
      <mesh
        position={rightDiagonalMid}
        quaternion={createCylinderOrientation(rightRailPos, spinePos)}
        castShadow
      >
        <cylinderGeometry args={[pipeRadius, pipeRadius, rightDiagonalLength, 8]} />
        <meshStandardMaterial color="#6b7280" metalness={0.6} roughness={0.4} />
      </mesh>
    </group>
  );
}

function SupportPillars({ path }: { path: InterpolatedPath }) {
  const pillars = useMemo(() => {
    const result: { position: THREE.Vector3; height: number }[] = [];
    const pillarSpacing = 10;

    for (let s = 0; s < path.total_length; s += pillarSpacing) {
      const point = path.points.find((p) => Math.abs(p.s - s) < 1);
      if (point && point.position[2] > 2) {
        const elevation = point.position[2];
        const lateral = point.position[1];
        const forward = point.position[0];

        result.push({
          position: new THREE.Vector3(forward, elevation / 2, lateral),
          height: elevation,
        });
      }
    }

    return result;
  }, [path]);

  return (
    <group>
      {pillars.map((pillar, idx) => (
        <group key={idx} position={pillar.position}>
          {/* Main pillar column */}
          <mesh castShadow receiveShadow>
            <cylinderGeometry args={[0.2, 0.3, pillar.height, 8]} />
            <meshStandardMaterial color="#64748b" metalness={0.5} roughness={0.5} />
          </mesh>

          {/* Cross bracing on tall pillars */}
          {pillar.height > 5 && (
            <PillarBraces height={pillar.height} />
          )}

          {/* Top connector plate */}
          <mesh position={[0, pillar.height / 2 - 0.2, 0]} castShadow>
            <boxGeometry args={[0.5, 0.15, 0.5]} />
            <meshStandardMaterial color="#475569" metalness={0.6} roughness={0.4} />
          </mesh>
        </group>
      ))}
    </group>
  );
}

function PillarBraces({ height }: { height: number }) {
  const braces: JSX.Element[] = [];
  const braceCount = Math.floor(height / 5);

  for (let i = 1; i <= braceCount; i++) {
    const y = -height / 2 + i * 5;
    braces.push(
      <group key={i} position={[0, y, 0]}>
        <mesh rotation={[0, 0, Math.PI / 4]} castShadow>
          <boxGeometry args={[0.06, 1.2, 0.06]} />
          <meshStandardMaterial color="#94a3b8" metalness={0.4} roughness={0.6} />
        </mesh>
        <mesh rotation={[0, 0, -Math.PI / 4]} castShadow>
          <boxGeometry args={[0.06, 1.2, 0.06]} />
          <meshStandardMaterial color="#94a3b8" metalness={0.4} roughness={0.6} />
        </mesh>
      </group>
    );
  }

  return <group>{braces}</group>;
}