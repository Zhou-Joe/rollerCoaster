from enum import Enum
from typing import Tuple, List, Optional
from pydantic import BaseModel


class ZoneType(str, Enum):
    LOAD = "load"
    UNLOAD = "unload"
    LAUNCH = "launch"
    BRAKE = "brake"
    HOLD = "hold"
    FREE = "free"
    MAINTENANCE = "maintenance"


class FailSafeMode(str, Enum):
    NORMALLY_OPEN = "normally_open"
    NORMALLY_CLOSED = "normally_closed"


class BrakeState(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    EMERGENCY_STOP = "emergency_stop"


class BoosterMode(str, Enum):
    DRIVE = "drive"
    BRAKE = "brake"
    IDLE = "idle"


class LoadCase(str, Enum):
    EMPTY = "empty"
    FULLY_LOADED = "fully_loaded"
    CUSTOM = "custom"


class TrainState(str, Enum):
    STOPPED = "stopped"
    MOVING = "moving"
    LOADING = "loading"
    UNLOADING = "unloading"
    IN_MAINTENANCE = "in_maintenance"


class StationType(str, Enum):
    LOAD = "load"
    UNLOAD = "unload"
    TRANSFER = "transfer"
    HOLD = "hold"


Position3D = Tuple[float, float, float]


class EquipmentConstraint(BaseModel):
    allowed_equipment_types: List[str] = []
    min_straightness: Optional[float] = None
    max_curvature: Optional[float] = None