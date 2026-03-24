"""Equipment state manager

Manages runtime states for all equipment in a project and
aggregates equipment forces for physics simulation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, TYPE_CHECKING

from app.models.equipment import (
    Equipment,
    LSMLaunch,
    Lift,
    PneumaticBrake,
    TrimBrake,
    Booster,
    TrackSwitch,
)
from app.models.common import BrakeState, BoosterMode, FailSafeMode
from .lsm import compute_lsm_force, create_lsm_state, LSMState
from .lift import compute_lift_force, create_lift_state, LiftState
from .pneumatic_brake import (
    compute_pneumatic_brake_force,
    create_pneumatic_brake_state,
    set_brake_state,
    apply_fail_safe,
    PneumaticBrakeState,
)
from .trim_brake import compute_trim_brake_force, create_trim_brake_state, TrimBrakeState
from .booster import compute_booster_force, set_booster_mode, create_booster_state, BoosterState

if TYPE_CHECKING:
    from app.models.project import Project


def _parse_equipment(equipment_dict: dict) -> Equipment:
    """Parse equipment dict to appropriate model based on equipment_type."""
    equipment_type = equipment_dict.get("equipment_type")
    if equipment_type == "lsm_launch":
        return LSMLaunch(**equipment_dict)
    elif equipment_type == "lift":
        return Lift(**equipment_dict)
    elif equipment_type == "pneumatic_brake":
        return PneumaticBrake(**equipment_dict)
    elif equipment_type == "trim_brake":
        return TrimBrake(**equipment_dict)
    elif equipment_type == "booster":
        return Booster(**equipment_dict)
    elif equipment_type == "track_switch":
        return TrackSwitch(**equipment_dict)
    else:
        raise ValueError(f"Unknown equipment type: {equipment_type}")


@dataclass
class EquipmentStates:
    """Container for all equipment runtime states."""
    lsm: Dict[str, LSMState] = field(default_factory=dict)
    lift: Dict[str, LiftState] = field(default_factory=dict)
    pneumatic_brake: Dict[str, PneumaticBrakeState] = field(default_factory=dict)
    trim_brake: Dict[str, TrimBrakeState] = field(default_factory=dict)
    booster: Dict[str, BoosterState] = field(default_factory=dict)


class EquipmentManager:
    """
    Manages equipment states and force computation.

    Coordinates all equipment devices in a project and computes
    the total equipment force acting on trains.
    """

    def __init__(self, project: 'Project'):
        """
        Initialize equipment manager.

        Args:
            project: Project containing equipment definitions
        """
        self.project = project
        self.states = EquipmentStates()
        self._initialize_states()

    def _initialize_states(self) -> None:
        """Initialize states for all equipment in project."""
        for equipment_dict in self.project.equipment:
            equipment = _parse_equipment(equipment_dict)
            self._add_equipment_state(equipment)

    def _add_equipment_state(self, equipment: Equipment) -> None:
        """Add state for a single equipment item."""
        if isinstance(equipment, LSMLaunch):
            self.states.lsm[equipment.id] = create_lsm_state(equipment)
        elif isinstance(equipment, Lift):
            self.states.lift[equipment.id] = create_lift_state(equipment)
        elif isinstance(equipment, PneumaticBrake):
            self.states.pneumatic_brake[equipment.id] = create_pneumatic_brake_state(equipment)
        elif isinstance(equipment, TrimBrake):
            self.states.trim_brake[equipment.id] = create_trim_brake_state(equipment)
        elif isinstance(equipment, Booster):
            self.states.booster[equipment.id] = create_booster_state(equipment)

    def compute_equipment_force(
        self,
        train_path_id: str,
        train_s: float,
        train_velocity_mps: float,
        train_mass_kg: float,
        dt: float = 0.01
    ) -> float:
        """
        Compute total equipment force on a train.

        Sums forces from all equipment that the train is currently
        interacting with.

        Args:
            train_path_id: ID of path the train is on
            train_s: Train front position (arc length)
            train_velocity_mps: Train velocity
            train_mass_kg: Total train mass
            dt: Time step

        Returns:
            Total equipment force in Newtons
        """
        total_force = 0.0

        for equipment_dict in self.project.equipment:
            equipment = _parse_equipment(equipment_dict)

            if isinstance(equipment, LSMLaunch):
                if equipment.path_id == train_path_id:
                    state = self.states.lsm.get(equipment.id)
                    if state:
                        force = compute_lsm_force(
                            equipment, state,
                            train_s, train_velocity_mps, train_mass_kg, dt
                        )
                        total_force += force

            elif isinstance(equipment, Lift):
                if equipment.path_id == train_path_id:
                    state = self.states.lift.get(equipment.id)
                    if state:
                        force = compute_lift_force(
                            equipment, state,
                            train_s, train_velocity_mps, dt
                        )
                        total_force += force

            elif isinstance(equipment, PneumaticBrake):
                if equipment.path_id == train_path_id:
                    state = self.states.pneumatic_brake.get(equipment.id)
                    if state:
                        force = compute_pneumatic_brake_force(
                            equipment, state,
                            train_s, train_velocity_mps, dt
                        )
                        total_force += force  # Already negative for braking

            elif isinstance(equipment, TrimBrake):
                if equipment.path_id == train_path_id:
                    state = self.states.trim_brake.get(equipment.id)
                    if state:
                        force = compute_trim_brake_force(
                            equipment, state,
                            train_s, train_velocity_mps, dt
                        )
                        total_force += force  # Already negative for braking

            elif isinstance(equipment, Booster):
                if equipment.path_id == train_path_id:
                    state = self.states.booster.get(equipment.id)
                    if state:
                        force = compute_booster_force(
                            equipment, state,
                            train_s, train_velocity_mps, dt
                        )
                        total_force += force

        return total_force

    def set_lsm_enabled(self, lsm_id: str, enabled: bool) -> bool:
        """Enable or disable an LSM."""
        if lsm_id in self.states.lsm:
            self.states.lsm[lsm_id].enabled = enabled
            return True
        return False

    def set_brake_state(self, brake_id: str, brake_state: BrakeState) -> bool:
        """Set a pneumatic brake's state."""
        if brake_id in self.states.pneumatic_brake:
            for equipment_dict in self.project.equipment:
                equipment = _parse_equipment(equipment_dict)
                if equipment.id == brake_id and isinstance(equipment, PneumaticBrake):
                    set_brake_state(equipment, self.states.pneumatic_brake[brake_id], brake_state)
                    return True
        return False

    def set_booster_mode(self, booster_id: str, mode: BoosterMode) -> bool:
        """Set a booster's mode."""
        if booster_id in self.states.booster:
            for equipment_dict in self.project.equipment:
                equipment = _parse_equipment(equipment_dict)
                if equipment.id == booster_id and isinstance(equipment, Booster):
                    set_booster_mode(equipment, self.states.booster[booster_id], mode)
                    return True
        return False

    def set_trim_enabled(self, trim_id: str, enabled: bool) -> bool:
        """Enable or disable a trim brake."""
        if trim_id in self.states.trim_brake:
            self.states.trim_brake[trim_id].enabled = enabled
            return True
        return False

    def set_lift_enabled(self, lift_id: str, enabled: bool) -> bool:
        """Enable or disable a lift."""
        if lift_id in self.states.lift:
            self.states.lift[lift_id].enabled = enabled
            return True
        return False

    def apply_all_fail_safes(self) -> None:
        """Apply fail-safe behavior to all pneumatic brakes."""
        for equipment_dict in self.project.equipment:
            equipment = _parse_equipment(equipment_dict)
            if isinstance(equipment, PneumaticBrake):
                state = self.states.pneumatic_brake.get(equipment.id)
                if state:
                    apply_fail_safe(equipment, state)

    def get_equipment_state(self, equipment_id: str) -> Optional[Union[
        LSMState, LiftState, PneumaticBrakeState, TrimBrakeState, BoosterState
    ]]:
        """Get the runtime state of an equipment item."""
        if equipment_id in self.states.lsm:
            return self.states.lsm[equipment_id]
        if equipment_id in self.states.lift:
            return self.states.lift[equipment_id]
        if equipment_id in self.states.pneumatic_brake:
            return self.states.pneumatic_brake[equipment_id]
        if equipment_id in self.states.trim_brake:
            return self.states.trim_brake[equipment_id]
        if equipment_id in self.states.booster:
            return self.states.booster[equipment_id]
        return None

    def reset(self) -> None:
        """Reset all equipment to initial states."""
        self.states = EquipmentStates()
        self._initialize_states()