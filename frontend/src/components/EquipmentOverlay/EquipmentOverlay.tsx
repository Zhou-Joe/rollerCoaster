import { useMemo } from 'react';
import { Text } from '@react-three/drei';
import * as THREE from 'three';
import type { Equipment, InterpolatedPath } from '../../types';

/**
 * Convert our coordinate system (x, y, z where z=up) to Three.js (x, y, z where y=up)
 */
function toThreePos(pos: [number, number, number]): THREE.Vector3 {
  return new THREE.Vector3(pos[0], pos[2], pos[1]);
}

interface EquipmentOverlayProps {
  equipment: Equipment[];
  paths: Map<string, InterpolatedPath>;
}

export function EquipmentOverlay({ equipment, paths }: EquipmentOverlayProps) {
  return (
    <group>
      {equipment.map((eq) => {
        const path = paths.get(eq.path_id);
        if (!path || !path.points || path.points.length === 0) return null;

        // Find the point at the equipment's start position
        const startPoint = path.points.find((p) => Math.abs(p.s - eq.start_s) < 1);
        if (!startPoint) return null;

        // Convert position to Three.js coordinates
        const threePos = toThreePos(startPoint.position);

        return (
          <EquipmentMarker
            key={eq.id}
            equipment={eq}
            position={threePos}
          />
        );
      })}
    </group>
  );
}

interface EquipmentMarkerProps {
  equipment: Equipment;
  position: THREE.Vector3;
}

function EquipmentMarker({ equipment, position }: EquipmentMarkerProps) {
  const color = useMemo(() => {
    switch (equipment.equipment_type) {
      case 'lsm_launch':
        return equipment.enabled ? '#3b82f6' : '#6b7280';
      case 'lift':
        return equipment.enabled ? '#8b5cf6' : '#6b7280';
      case 'pneumatic_brake':
        return '#22c55e'; // Green for brakes
      case 'trim_brake':
        return '#f59e0b'; // Orange for trim
      case 'booster':
        return '#06b6d4'; // Cyan for booster
      default:
        return '#6b7280';
    }
  }, [equipment]);

  const label = useMemo(() => {
    switch (equipment.equipment_type) {
      case 'lsm_launch':
        return 'LSM';
      case 'lift':
        return 'LIFT';
      case 'pneumatic_brake':
        return 'BRAKE';
      case 'trim_brake':
        return 'TRIM';
      case 'booster':
        return 'BOOST';
      default:
        return 'EQ';
    }
  }, [equipment]);

  return (
    <group position={position}>
      {/* Equipment marker pole */}
      <mesh position={[0, 3, 0]} castShadow>
        <cylinderGeometry args={[0.1, 0.1, 6, 8]} />
        <meshStandardMaterial color="#374151" metalness={0.5} roughness={0.5} />
      </mesh>

      {/* Equipment marker box */}
      <mesh position={[0, 6.5, 0]} castShadow>
        <boxGeometry args={[2, 1, 0.5]} />
        <meshStandardMaterial color={color} metalness={0.5} roughness={0.4} />
      </mesh>

      {/* Label */}
      <Text
        position={[0, 6.5, 0.3]}
        fontSize={0.4}
        color="white"
        anchorX="center"
        anchorY="middle"
      >
        {label}
      </Text>

      {/* Range indicator - shows equipment extent */}
      <mesh position={[0, 0.05, 0]} receiveShadow>
        <boxGeometry args={[equipment.end_s - equipment.start_s, 0.1, 0.5]} />
        <meshStandardMaterial color={color} transparent opacity={0.3} />
      </mesh>
    </group>
  );
}