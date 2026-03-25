// Types for roller coaster simulation

export interface Point {
  id: string;
  x: number;
  y: number;
  z: number;
  bank_deg?: number;
  editable?: boolean;
}

export interface Path {
  id: string;
  name?: string;
  point_ids: string[];
}

export interface Vehicle {
  id: string;
  length_m: number;
  dry_mass_kg: number;
  capacity: number;
  passenger_mass_per_person_kg?: number;
}

export interface Train {
  id: string;
  vehicle_ids: string[];
  current_path_id?: string;
  front_position_s?: number;
  load_case?: 'empty' | 'loaded' | 'custom';
}

export interface TrainPhysicsState {
  train_id: string;
  path_id: string;
  s_front_m: number;
  s_rear_m: number;
  velocity_mps: number;
  acceleration_mps2: number;
  mass_kg: number;
  forces: {
    gravity_tangent_n: number;
    drag_n: number;
    rolling_resistance_n: number;
    equipment_n: number;
    total_n: number;
  };
  gforces: {
    normal_g: number;
    lateral_g: number;
    vertical_g: number;
    resultant_g: number;
  };
}

export interface SamplePoint {
  s: number;
  position: [number, number, number];
  tangent: [number, number, number];
  normal: [number, number, number];
  binormal: [number, number, number];
  curvature: number;
  radius: number;
  slope_deg: number;
  bank_deg: number;
}

export interface InterpolatedPath {
  path_id: string;
  total_length: number;
  points: SamplePoint[];
}

export interface SimulationState {
  time_s: number;
  running: boolean;
  trains: TrainPhysicsState[];
}

export interface Project {
  id?: string;
  metadata: {
    name: string;
    units: string;
    version: number;
    created_at: string;
    modified_at: string;
  };
  points: Point[];
  paths: Path[];
  vehicles: Vehicle[];
  trains: Train[];
  equipment: Equipment[];
  simulation_settings: {
    time_step_s: number;
    gravity_mps2: number;
    drag_coefficient: number;
    rolling_resistance_coefficient: number;
    air_density_kg_m3: number;
  };
}

export interface Block {
  id: string;
  path_id: string;
  start_s: number;
  end_s: number;
  occupied: boolean;
  train_id: string | null;
}

export interface Station {
  id: string;
  name: string;
  path_id: string;
  start_s: number;
  end_s: number;
  type: 'load' | 'unload' | 'transfer';
}

export interface EquipmentBase {
  id: string;
  path_id: string;
  start_s: number;
  end_s: number;
  equipment_type: string;
  enabled?: boolean;
}

export interface LSMLaunch extends EquipmentBase {
  equipment_type: 'lsm_launch';
  stator_count?: number;
  magnetic_field_strength?: number;
  max_force_n?: number;
  launch_velocity_mps?: number;
}

export interface Lift extends EquipmentBase {
  equipment_type: 'lift';
  chain_speed_mps?: number;
  max_pull_force_n?: number;
  engagement_point_s?: number;
  release_point_s?: number;
}

export interface PneumaticBrake extends EquipmentBase {
  equipment_type: 'pneumatic_brake';
  max_brake_force_n?: number;
  response_time_s?: number;
  air_pressure?: number;
  fail_safe_mode?: 'normally_open' | 'normally_closed';
  state?: 'open' | 'closed' | 'emergency_stop';
}

export interface TrimBrake extends EquipmentBase {
  equipment_type: 'trim_brake';
  max_force_n?: number;
  target_velocity_mps?: number;
}

export interface Booster extends EquipmentBase {
  equipment_type: 'booster';
  max_force_n?: number;
  boost_duration_s?: number;
}

export type Equipment = LSMLaunch | Lift | PneumaticBrake | TrimBrake | Booster | EquipmentBase;