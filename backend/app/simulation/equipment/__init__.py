"""Equipment physics simulation"""

from .lsm import compute_lsm_force, create_lsm_state, LSMState
from .lift import compute_lift_effect, create_lift_state, LiftState
from .pneumatic_brake import (
    compute_pneumatic_brake_force,
    create_pneumatic_brake_state,
    set_brake_state,
    apply_fail_safe,
    PneumaticBrakeState,
)
from .trim_brake import compute_trim_brake_force, create_trim_brake_state, TrimBrakeState
from .booster import compute_booster_force, set_booster_mode, create_booster_state, BoosterState
from .manager import EquipmentManager, EquipmentStates

__all__ = [
    # LSM
    "compute_lsm_force",
    "create_lsm_state",
    "LSMState",
    # Lift
    "compute_lift_effect",
    "create_lift_state",
    "LiftState",
    # Pneumatic Brake
    "compute_pneumatic_brake_force",
    "create_pneumatic_brake_state",
    "set_brake_state",
    "apply_fail_safe",
    "PneumaticBrakeState",
    # Trim Brake
    "compute_trim_brake_force",
    "create_trim_brake_state",
    "TrimBrakeState",
    # Booster
    "compute_booster_force",
    "set_booster_mode",
    "create_booster_state",
    "BoosterState",
    # Manager
    "EquipmentManager",
    "EquipmentStates",
]