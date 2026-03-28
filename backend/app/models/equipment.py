from pydantic import BaseModel
from typing import List, Optional, Union, Dict, Any
from .common import FailSafeMode, BrakeState, BoosterMode
from enum import Enum


class EquipmentType(str, Enum):
    LSM_LAUNCH = "lsm_launch"
    LIFT = "lift"
    PNEUMATIC_BRAKE = "pneumatic_brake"
    TRIM_BRAKE = "trim_brake"
    BOOSTER = "booster"
    TRACK_SWITCH = "track_switch"


ForceCurvePoint = Dict[str, Any]
ForceCurve = List[ForceCurvePoint]


class LSMLaunch(BaseModel):
    """Linear Synchronous Motor launch system.

    The LSM consists of multiple stator segments along the track that generate
    traveling magnetic waves to push against permanent magnets on vehicles.

    Force is calculated based on overlap between vehicle magnets and track stators,
    with electromagnetic parameters determining the force per stator.
    """
    equipment_type: EquipmentType = EquipmentType.LSM_LAUNCH
    id: str
    path_id: str
    start_s: float  # Start position on path (arc length)
    end_s: float  # End position on path (arc length)

    # Stator configuration
    stator_count: int  # Number of stator segments
    stator_length_m: float = 1.5  # Length of each stator segment (default 1.5m)
    stator_spacing_m: Optional[float] = None  # Center-to-center spacing (auto-calculated if None)

    # Electromagnetic parameters
    # Force equation: F = B * I * L * efficiency
    # Where B = magnetic field (Tesla), I = current (Amps), L = active length (m)
    magnetic_field_tesla: float = 1.2  # Permanent magnet field strength (typical NdFeB: 1.0-1.4 T)
    max_current_amps: float = 500.0  # Maximum stator current
    active_length_m: float = 0.3  # Effective magnetic interaction length per stator
    efficiency: float = 0.85  # System efficiency (losses due to gap, eddy currents, etc.)

    # Derived/calculated values
    max_force_per_stator_n: Optional[float] = None  # Auto-calculated if None: B * I * L * efficiency

    # Speed effects
    max_speed_mps: float = 50.0  # Design max speed (force drops to zero approaching this)
    back_emf_factor: float = 0.02  # Back-EMF coefficient (V per m/s)

    # Control
    target_launch_velocity_mps: Optional[float] = None  # Target exit velocity
    enabled: bool = True

    # Legacy support (for backward compatibility)
    max_force_n: Optional[float] = None  # Total max force (deprecated, use electromagnetic params)
    magnetic_field_strength: Optional[float] = None  # Deprecated (renamed to magnetic_field_tesla)
    force_curve: Optional[ForceCurve] = None  # Custom force curve override


class Lift(BaseModel):
    equipment_type: EquipmentType = EquipmentType.LIFT
    id: str
    path_id: str
    start_s: float
    end_s: float
    lift_speed_mps: float = 5.0  # Default lift speed in m/s
    max_pull_force_n: float = 5000.0  # Default max pull force in N
    engagement_point_s: Optional[float] = None  # Defaults to start_s
    release_point_s: Optional[float] = None  # Defaults to end_s
    enabled: bool = True


class PneumaticBrake(BaseModel):
    equipment_type: EquipmentType = EquipmentType.PNEUMATIC_BRAKE
    id: str
    path_id: str
    start_s: float
    end_s: float
    max_brake_force_n: float
    response_time_s: float
    air_pressure: float
    fail_safe_mode: FailSafeMode
    force_curve: Optional[ForceCurve] = None
    state: BrakeState = BrakeState.OPEN


class TrimBrake(BaseModel):
    equipment_type: EquipmentType = EquipmentType.TRIM_BRAKE
    id: str
    path_id: str
    start_s: float
    end_s: float
    max_trim_force_n: float
    force_curve: Optional[ForceCurve] = None
    enabled: bool = True


class Booster(BaseModel):
    equipment_type: EquipmentType = EquipmentType.BOOSTER
    id: str
    path_id: str
    start_s: float
    end_s: float
    wheel_count: int
    max_drive_force_n: float
    max_drive_speed_mps: float
    brake_friction_force_n: float
    mode: BoosterMode = BoosterMode.IDLE


class TrackSwitch(BaseModel):
    equipment_type: EquipmentType = EquipmentType.TRACK_SWITCH
    id: str
    junction_id: str
    incoming_path_id: str
    outgoing_path_ids: List[str]
    current_alignment: str
    actuation_time_s: float = 2.0
    locked_when_occupied: bool = True


Equipment = Union[LSMLaunch, Lift, PneumaticBrake, TrimBrake, Booster, TrackSwitch]