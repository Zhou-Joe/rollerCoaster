import { useMemo } from 'react';
import { Text } from '@react-three/drei';
import type { Equipment, InterpolatedPath } from '../../types';

interface EquipmentOverlayProps {
  equipment: Equipment[];
  paths: Map<string, InterpolatedPath>;
}

export function EquipmentOverlay({ equipment, paths }: EquipmentOverlayProps) {
  return (
    <group>
      {equipment.map((eq) => {
        const path = paths.get(eq.path_id);
        if (!path) return null;

        const startPoint = path.points.find((p) => Math.abs(p.arc_length - eq.start_s) < 0.5);
        if (!startPoint) return null;

        return (
          <EquipmentMarker
            key={eq.id}
            equipment={eq}
            position={startPoint.position}
          />
        );
      })}
    </group>
  );
}

interface EquipmentMarkerProps {
  equipment: Equipment;
  position: [number, number, number];
}

function EquipmentMarker({ equipment, position }: EquipmentMarkerProps) {
  const color = useMemo(() => {
    switch (equipment.equipment_type) {
      case 'lsm_launch':
        return equipment.enabled ? '#3b82f6' : '#6b7280';
      case 'lift':
        return equipment.enabled ? '#8b5cf6' : '#6b7280';
      case 'pneumatic_brake':
        return equipment.state === 'open' ? '#22c55e' : '#ef4444';
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
        return equipment.state === 'open' ? 'BRAKE ○' : 'BRAKE ●';
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
    </group>
  );
}