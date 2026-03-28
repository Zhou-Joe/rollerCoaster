import type { InterpolatedPath } from '../types';

type Vec3 = [number, number, number];

interface PathFrameSample {
  position: Vec3;
  tangent: Vec3;
  normal: Vec3;
  binormal: Vec3;
  curvature: number;
  bank_deg: number;
}

interface VectorComponents {
  x: number;
  y: number;
  z: number;
}

interface TrainLocalComponents {
  foreAft: number;
  rightLeft: number;
  eyeUpDown: number;
}

export interface TrainKinematics {
  worldVelocity: VectorComponents;
  worldAcceleration: VectorComponents;
  totalWorldVelocity: number;
  totalWorldAcceleration: number;
  localVelocity: TrainLocalComponents;
  localAcceleration: TrainLocalComponents;
  position: Vec3;
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

function lerpVec3(a: Vec3, b: Vec3, t: number): Vec3 {
  return [
    lerp(a[0], b[0], t),
    lerp(a[1], b[1], t),
    lerp(a[2], b[2], t),
  ];
}

function magnitude(v: Vec3): number {
  return Math.hypot(v[0], v[1], v[2]);
}

function normalize(v: Vec3): Vec3 {
  const len = magnitude(v);
  if (len < 1e-9) {
    return [0, 0, 0];
  }
  return [v[0] / len, v[1] / len, v[2] / len];
}

function scale(v: Vec3, scalar: number): Vec3 {
  return [v[0] * scalar, v[1] * scalar, v[2] * scalar];
}

function add(a: Vec3, b: Vec3): Vec3 {
  return [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
}

function dot(a: Vec3, b: Vec3): number {
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}

function rotateAroundAxis(vector: Vec3, axis: Vec3, angleRad: number): Vec3 {
  const unitAxis = normalize(axis);
  const cos = Math.cos(angleRad);
  const sin = Math.sin(angleRad);
  const axisDotVector = dot(unitAxis, vector);
  const cross: Vec3 = [
    unitAxis[1] * vector[2] - unitAxis[2] * vector[1],
    unitAxis[2] * vector[0] - unitAxis[0] * vector[2],
    unitAxis[0] * vector[1] - unitAxis[1] * vector[0],
  ];

  return [
    vector[0] * cos + cross[0] * sin + unitAxis[0] * axisDotVector * (1 - cos),
    vector[1] * cos + cross[1] * sin + unitAxis[1] * axisDotVector * (1 - cos),
    vector[2] * cos + cross[2] * sin + unitAxis[2] * axisDotVector * (1 - cos),
  ];
}

export function findPathFrameAtS(path: InterpolatedPath, s: number): PathFrameSample | null {
  if (!path.points.length) {
    return null;
  }

  const clampedS = Math.max(0, Math.min(s, path.total_length));

  for (let i = 0; i < path.points.length - 1; i += 1) {
    const p1 = path.points[i];
    const p2 = path.points[i + 1];

    if (p1.s <= clampedS && p2.s >= clampedS) {
      const span = p2.s - p1.s;
      const t = span > 0 ? (clampedS - p1.s) / span : 0;

      return {
        position: lerpVec3(p1.position, p2.position, t),
        tangent: normalize(lerpVec3(p1.tangent, p2.tangent, t)),
        normal: normalize(lerpVec3(p1.normal, p2.normal, t)),
        binormal: normalize(lerpVec3(p1.binormal, p2.binormal, t)),
        curvature: lerp(p1.curvature, p2.curvature, t),
        bank_deg: lerp(p1.bank_deg, p2.bank_deg, t),
      };
    }
  }

  const fallback = path.points[path.points.length - 1];
  return {
    position: fallback.position,
    tangent: normalize(fallback.tangent),
    normal: normalize(fallback.normal),
    binormal: normalize(fallback.binormal),
    curvature: fallback.curvature,
    bank_deg: fallback.bank_deg,
  };
}

export function computeTrainKinematics(
  path: InterpolatedPath | null | undefined,
  s: number,
  velocityMps: number,
  accelerationMps2: number
): TrainKinematics {
  const sample = path ? findPathFrameAtS(path, s) : null;

  if (!sample) {
    return {
      worldVelocity: { x: 0, y: 0, z: 0 },
      worldAcceleration: { x: 0, y: 0, z: 0 },
      totalWorldVelocity: 0,
      totalWorldAcceleration: 0,
      localVelocity: { foreAft: 0, rightLeft: 0, eyeUpDown: 0 },
      localAcceleration: { foreAft: 0, rightLeft: 0, eyeUpDown: 0 },
      position: [0, 0, 0],
    };
  }

  const tangentAccel = scale(sample.tangent, accelerationMps2);
  const centripetalAccel = scale(sample.normal, velocityMps * velocityMps * sample.curvature);
  const worldVelocityVec = scale(sample.tangent, velocityMps);
  const worldAccelVec = add(tangentAccel, centripetalAccel);

  const upAxis = normalize(
    rotateAroundAxis(sample.normal, sample.tangent, (sample.bank_deg * Math.PI) / 180)
  );
  const rightAxis = normalize(
    rotateAroundAxis(sample.binormal, sample.tangent, (sample.bank_deg * Math.PI) / 180)
  );

  return {
    worldVelocity: {
      x: worldVelocityVec[0],
      y: worldVelocityVec[1],
      z: worldVelocityVec[2],
    },
    worldAcceleration: {
      x: worldAccelVec[0],
      y: worldAccelVec[1],
      z: worldAccelVec[2],
    },
    totalWorldVelocity: magnitude(worldVelocityVec),
    totalWorldAcceleration: magnitude(worldAccelVec),
    localVelocity: {
      foreAft: dot(worldVelocityVec, sample.tangent),
      rightLeft: dot(worldVelocityVec, rightAxis),
      eyeUpDown: dot(worldVelocityVec, upAxis),
    },
    localAcceleration: {
      foreAft: dot(worldAccelVec, sample.tangent),
      rightLeft: dot(worldAccelVec, rightAxis),
      eyeUpDown: dot(worldAccelVec, upAxis),
    },
    position: sample.position,
  };
}
