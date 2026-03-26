import { useState, useCallback, useEffect } from 'react';
import { ThreeEvent } from '@react-three/fiber';
import * as THREE from 'three';
import { Html } from '@react-three/drei';
import type { Point } from '../../types';

interface PointMarkersProps {
  points: Point[];
  selectedPointId: string | null;
  onSelectPoint: (id: string | null) => void;
  onPointMove: (id: string, position: { x: number; y: number; z: number }) => void;
  editingMode: boolean;
  onDragStateChange?: (isDragging: boolean) => void;
}

/**
 * Convert our coordinate system (x, y, z where z=up) to Three.js (x, y, z where y=up)
 */
function toThreePos(x: number, y: number, z: number): THREE.Vector3 {
  return new THREE.Vector3(x, z, y);
}

/**
 * Convert Three.js position back to our coordinate system
 */
function fromThreePos(pos: THREE.Vector3): { x: number; y: number; z: number } {
  return { x: pos.x, y: pos.z, z: pos.y };
}

export function PointMarkers({
  points,
  selectedPointId,
  onSelectPoint,
  onPointMove,
  editingMode,
  onDragStateChange
}: PointMarkersProps) {
  const [dragging, setDragging] = useState<string | null>(null);
  const [dragPlane] = useState(() => new THREE.Plane(new THREE.Vector3(0, 1, 0), 0));
  const [dragOffset] = useState(() => new THREE.Vector3());

  // Notify parent when drag state changes
  useEffect(() => {
    onDragStateChange?.(dragging !== null);
  }, [dragging, onDragStateChange]);

  const handlePointerDown = useCallback((e: ThreeEvent<PointerEvent>, pointId: string) => {
    if (!editingMode) return;

    e.stopPropagation();
    setDragging(pointId);
    onSelectPoint(pointId);

    // Calculate drag offset
    const intersection = new THREE.Vector3();
    e.ray.intersectPlane(dragPlane, intersection);
    const point = points.find(p => p.id === pointId);
    if (point) {
      const pointPos = toThreePos(point.x, point.y, point.z);
      dragOffset.copy(intersection).sub(pointPos);
    }

    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  }, [editingMode, points, dragPlane, dragOffset, onSelectPoint]);

  const handlePointerMove = useCallback((e: ThreeEvent<PointerEvent>) => {
    if (!dragging) return;

    e.stopPropagation();
    const intersection = new THREE.Vector3();
    e.ray.intersectPlane(dragPlane, intersection);

    // Apply offset
    intersection.sub(dragOffset);

    // Snap to grid (0.5m)
    intersection.x = Math.round(intersection.x * 2) / 2;
    intersection.y = Math.max(0, Math.round(intersection.y * 2) / 2); // Y >= 0
    intersection.z = Math.round(intersection.z * 2) / 2;

    const newPos = fromThreePos(intersection);
    onPointMove(dragging, newPos);
  }, [dragging, dragPlane, dragOffset, onPointMove]);

  const handlePointerUp = useCallback((e: ThreeEvent<PointerEvent>) => {
    if (!dragging) return;

    e.stopPropagation();
    setDragging(null);
    (e.target as HTMLElement).releasePointerCapture(e.pointerId);
  }, [dragging]);

  if (!editingMode) return null;

  return (
    <group>
      {points.map((point, idx) => {
        const position = toThreePos(point.x, point.y, point.z);
        const isSelected = selectedPointId === point.id;
        const isDraggingThis = dragging === point.id;

        return (
          <group
            key={point.id}
            position={position}
            onPointerDown={(e) => handlePointerDown(e, point.id)}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
          >
            {/* Point sphere */}
            <mesh>
              <sphereGeometry args={[isSelected ? 0.8 : 0.5, 16, 16]} />
              <meshStandardMaterial
                color={isSelected ? '#f59e0b' : isDraggingThis ? '#22c55e' : '#3b82f6'}
                emissive={isSelected ? '#f59e0b' : '#3b82f6'}
                emissiveIntensity={0.3}
              />
            </mesh>

            {/* Vertical line to ground */}
            <mesh position={[0, -position.y / 2, 0]}>
              <cylinderGeometry args={[0.05, 0.05, position.y, 8]} />
              <meshStandardMaterial color="#6b7280" transparent opacity={0.5} />
            </mesh>

            {/* Label */}
            {(isSelected || isDraggingThis) && (
              <Html
                position={[1, 1, 0]}
                style={{
                  background: 'rgba(0,0,0,0.7)',
                  padding: '4px 8px',
                  borderRadius: 4,
                  color: 'white',
                  fontSize: 12,
                  whiteSpace: 'nowrap',
                  pointerEvents: 'none',
                }}
              >
                <div>P{idx + 1}: ({point.x.toFixed(1)}, {point.y.toFixed(1)}, {point.z.toFixed(1)})</div>
              </Html>
            )}
          </group>
        );
      })}
    </group>
  );
}