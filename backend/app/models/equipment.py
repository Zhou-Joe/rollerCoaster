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
    equipment_type: EquipmentType = EquipmentType.LSM_LAUNCH
    id: str
    path_id: str
    start_s: float
    end_s: float
    stator_count: int
    magnetic_field_strength: float
    max_force_n: float
    force_curve: Optional[ForceCurve] = None
    enabled: bool = True


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