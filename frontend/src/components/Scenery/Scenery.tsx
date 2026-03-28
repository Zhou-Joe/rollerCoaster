import { useMemo } from 'react';
import type { InterpolatedPath } from '../../types';

interface SceneryProps {
  paths: Map<string, InterpolatedPath>;
  groundSize?: number;
  treeCount?: number;
}

interface TreeProps {
  position: [number, number, number];
  scale?: number;
}

// Simple procedural tree using cones and cylinder
function Tree({ position, scale = 1 }: TreeProps) {
  const trunkHeight = 2 * scale;
  const foliageHeight = 4 * scale;
  const foliageRadius = 1.5 * scale;

  return (
    <group position={position}>
      {/* Trunk */}
      <mesh position={[0, trunkHeight / 2, 0]} castShadow>
        <cylinderGeometry args={[0.2 * scale, 0.3 * scale, trunkHeight, 8]} />
        <meshStandardMaterial color="#5D4037" roughness={0.9} />
      </mesh>
      {/* Foliage layers */}
      <mesh position={[0, trunkHeight + foliageHeight * 0.3, 0]} castShadow>
        <coneGeometry args={[foliageRadius, foliageHeight * 0.6, 8]} />
        <meshStandardMaterial color="#2E7D32" roughness={0.8} />
      </mesh>
      <mesh position={[0, trunkHeight + foliageHeight * 0.6, 0]} castShadow>
        <coneGeometry args={[foliageRadius * 0.7, foliageHeight * 0.5, 8]} />
        <meshStandardMaterial color="#388E3C" roughness={0.8} />
      </mesh>
      <mesh position={[0, trunkHeight + foliageHeight * 0.85, 0]} castShadow>
        <coneGeometry args={[foliageRadius * 0.4, foliageHeight * 0.35, 8]} />
        <meshStandardMaterial color="#43A047" roughness={0.8} />
      </mesh>
    </group>
  );
}

// Calculate track bounds from all paths
function calculateTrackBounds(paths: Map<string, InterpolatedPath>): {
  minX: number; maxX: number;
  minZ: number; maxZ: number;
  centerY: number;
} {
  let minX = Infinity, maxX = -Infinity;
  let minZ = Infinity, maxZ = -Infinity;
  let minY = Infinity;

  paths.forEach((path) => {
    path.points.forEach((point) => {
      minX = Math.min(minX, point.position[0]);
      maxX = Math.max(maxX, point.position[0]);
      minZ = Math.min(minZ, point.position[2]);
      maxZ = Math.max(maxZ, point.position[2]);
      minY = Math.min(minY, point.position[1]);
    });
  });

  return {
    minX,
    maxX,
    minZ,
    maxZ,
    centerY: minY,
  };
}

// Check if a position is too close to the track
function isNearTrack(
  x: number,
  z: number,
  paths: Map<string, InterpolatedPath>,
  buffer: number = 8
): boolean {
  for (const path of paths.values()) {
    for (const point of path.points) {
      const dx = x - point.position[0];
      const dz = z - point.position[2];
      const dist = Math.sqrt(dx * dx + dz * dz);
      if (dist < buffer) {
        return true;
      }
    }
  }
  return false;
}

export function Scenery({ paths, groundSize = 200, treeCount = 80 }: SceneryProps) {
  // Generate tree positions avoiding the track
  const trees = useMemo(() => {
    if (paths.size === 0) return [];

    const bounds = calculateTrackBounds(paths);
    const treePositions: { pos: [number, number, number]; scale: number }[] = [];

    // Use seeded random for consistent tree placement
    const seededRandom = (seed: number) => {
      const x = Math.sin(seed * 12.9898 + seed * 78.233) * 43758.5453;
      return x - Math.floor(x);
    };

    let attempts = 0;
    let placed = 0;
    const maxAttempts = treeCount * 10;

    while (placed < treeCount && attempts < maxAttempts) {
      const seed = attempts * 12345;
      const randX = seededRandom(seed);
      const randZ = seededRandom(seed + 1);
      const randScale = seededRandom(seed + 2);

      // Place trees around the perimeter and in corners
      const margin = 15;
      const x = -groundSize / 2 + margin + randX * (groundSize - 2 * margin);
      const z = -groundSize / 2 + margin + randZ * (groundSize - 2 * margin);

      // Check if position is valid (not near track)
      if (!isNearTrack(x, z, paths, 10)) {
        treePositions.push({
          pos: [x, bounds.centerY, z],
          scale: 0.6 + randScale * 0.8, // Scale between 0.6 and 1.4
        });
        placed++;
      }
      attempts++;
    }

    return treePositions;
  }, [paths, groundSize, treeCount]);

  return (
    <group>
      {/* Grass ground */}
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, -0.1, 0]}
        receiveShadow
      >
        <planeGeometry args={[groundSize, groundSize]} />
        <meshStandardMaterial
          color="#4CAF50"
          roughness={1}
          metalness={0}
        />
      </mesh>

      {/* Slightly darker grass patches for texture effect */}
      {useMemo(() => {
        const patches: [number, number, number][] = [];
        const patchCount = 30;
        for (let i = 0; i < patchCount; i++) {
          const angle = (i / patchCount) * Math.PI * 2;
          const radius = 30 + (i % 3) * 20;
          patches.push([
            Math.cos(angle * 7) * radius * 0.5,
            0.01,
            Math.sin(angle * 11) * radius * 0.5,
          ]);
        }
        return patches;
      }, []).map((pos, i) => (
        <mesh
          key={i}
          rotation={[-Math.PI / 2, 0, 0]}
          position={pos}
        >
          <circleGeometry args={[8 + (i % 5) * 3, 16]} />
          <meshStandardMaterial
            color="#43A047"
            roughness={1}
            transparent
            opacity={0.3}
          />
        </mesh>
      ))}

      {/* Trees */}
      {trees.map((tree, i) => (
        <Tree key={i} position={tree.pos} scale={tree.scale} />
      ))}
    </group>
  );
}