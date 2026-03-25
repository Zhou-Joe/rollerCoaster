"""Safety interlock system

Interlocks enforce safety rules that cannot be overridden by user-authored logic.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

from app.models.equipment import TrackSwitch
from app.models.common import BrakeState


class InterlockResult:
    """Result of an interlock check."""
    allowed: bool
    reason: Optional[str] = None

    def __init__(self, allowed: bool, reason: Optional[str] = None):
        self.allowed = allowed
        self.reason = reason


class InterlockSystem:
    """
    Safety interlock validation system.

    Interlocks are hard safety rules that override any user-authored
    control logic. They prevent dangerous operations.

    Core interlocks:
    - Cannot change switch alignment while switch zone is occupied
    - Cannot dispatch if required downstream path is blocked
    - Cannot open emergency brake during E-stop (except to clear)
    - Cannot create conflicting route commands
    """

    def __init__(self):
        """Initialize interlock system."""
        self.emergency_stop_active = False
        self.occupied_zones: Dict[str, str] = {}  # zone_id -> train_id
        self.switch_states: Dict[str, str] = {}   # switch_id -> current_alignment
        self.switch_occupancy: Dict[str, bool] = {}  # switch_id -> is_occupied
        self.block_occupancy: Dict[str, Optional[str]] = {}  # block_id -> train_id or None
        self.dispatch_permits: Dict[str, bool] = {}  # station_id -> permit_granted
        self.route_reservations: Dict[str, str] = {}  # train_id -> reserved_route

    def check_switch_change(
        self,
        switch_id: str,
        new_alignment: str
    ) -> InterlockResult:
        """
        Check if switch alignment change is allowed.

        Args:
            switch_id: ID of switch to change
            new_alignment: Target alignment

        Returns:
            InterlockResult indicating if change is allowed
        """
        # Cannot change while occupied
        if self.switch_occupancy.get(switch_id, False):
            return InterlockResult(
                allowed=False,
                reason=f"Switch {switch_id} is occupied"
            )

        # Cannot change during emergency stop
        if self.emergency_stop_active:
            return InterlockResult(
                allowed=False,
                reason="Emergency stop is active"
            )

        return InterlockResult(allowed=True)

    def check_dispatch(
        self,
        station_id: str,
        train_id: str,
        route: List[str]
    ) -> InterlockResult:
        """
        Check if dispatch from station is allowed.

        Args:
            station_id: Station to dispatch from
            train_id: Train to dispatch
            route: Planned route (list of block IDs)

        Returns:
            InterlockResult indicating if dispatch is allowed
        """
        # Cannot dispatch during emergency stop
        if self.emergency_stop_active:
            return InterlockResult(
                allowed=False,
                reason="Emergency stop is active"
            )

        # Check if dispatch is permitted by control logic
        if not self.dispatch_permits.get(station_id, False):
            return InterlockResult(
                allowed=False,
                reason=f"Dispatch not permitted for station {station_id}"
            )

        # Check if route is clear
        for block_id in route:
            if self.block_occupancy.get(block_id) is not None:
                return InterlockResult(
                    allowed=False,
                    reason=f"Block {block_id} is occupied"
                )

        return InterlockResult(allowed=True)

    def check_equipment_command(
        self,
        equipment_id: str,
        equipment_type: str,
        command: str,
        parameters: Dict[str, Any]
    ) -> InterlockResult:
        """
        Check if equipment command is allowed.

        Args:
            equipment_id: ID of equipment
            equipment_type: Type of equipment
            command: Command to execute
            parameters: Command parameters

        Returns:
            InterlockResult indicating if command is allowed
        """
        # During emergency stop, only allow closing brakes or emergency operations
        if self.emergency_stop_active:
            if equipment_type == "pneumatic_brake":
                if command in ("close", "emergency_stop"):
                    return InterlockResult(allowed=True)
                else:
                    return InterlockResult(
                        allowed=False,
                        reason="Emergency stop active - can only close brakes"
                    )
            else:
                return InterlockResult(
                    allowed=False,
                    reason="Emergency stop is active"
                )

        return InterlockResult(allowed=True)

    def check_brake_state_change(
        self,
        brake_id: str,
        new_state: BrakeState
    ) -> InterlockResult:
        """
        Check if brake state change is allowed.

        Args:
            brake_id: ID of brake
            new_state: Target state

        Returns:
            InterlockResult indicating if change is allowed
        """
        # During emergency stop, cannot open brakes (except to clear E-stop)
        if self.emergency_stop_active:
            if new_state == BrakeState.OPEN:
                return InterlockResult(
                    allowed=False,
                    reason="Cannot open brakes during emergency stop"
                )

        return InterlockResult(allowed=True)

    def set_emergency_stop(self, active: bool) -> None:
        """
        Set emergency stop state.

        Args:
            active: Whether E-stop is active
        """
        self.emergency_stop_active = active

    def update_block_occupancy(
        self,
        block_id: str,
        train_id: Optional[str]
    ) -> None:
        """
        Update block occupancy.

        Args:
            block_id: ID of block
            train_id: Train occupying block, or None if clear
        """
        self.block_occupancy[block_id] = train_id

    def update_switch_occupancy(
        self,
        switch_id: str,
        occupied: bool
    ) -> None:
        """
        Update switch occupancy.

        Args:
            switch_id: ID of switch
            occupied: Whether switch zone is occupied
        """
        self.switch_occupancy[switch_id] = occupied

    def update_switch_state(
        self,
        switch_id: str,
        alignment: str
    ) -> None:
        """
        Update switch state.

        Args:
            switch_id: ID of switch
            alignment: Current alignment
        """
        self.switch_states[switch_id] = alignment

    def set_dispatch_permit(
        self,
        station_id: str,
        permitted: bool
    ) -> None:
        """
        Set dispatch permit for a station.

        Args:
            station_id: ID of station
            permitted: Whether dispatch is permitted
        """
        self.dispatch_permits[station_id] = permitted

    def reserve_route(
        self,
        train_id: str,
        route: str
    ) -> None:
        """
        Reserve a route for a train.

        Args:
            train_id: ID of train
            route: Route identifier
        """
        self.route_reservations[train_id] = route

    def clear_route_reservation(
        self,
        train_id: str
    ) -> None:
        """
        Clear route reservation for a train.

        Args:
            train_id: ID of train
        """
        self.route_reservations.pop(train_id, None)

    def is_route_clear(self, route: List[str]) -> bool:
        """
        Check if a route is clear.

        Args:
            route: List of block IDs in route

        Returns:
            True if all blocks are clear
        """
        for block_id in route:
            if self.block_occupancy.get(block_id) is not None:
                return False
        return True

    def reset(self) -> None:
        """Reset all interlock states."""
        self.emergency_stop_active = False
        self.switch_occupancy.clear()
        self.block_occupancy.clear()
        self.dispatch_permits.clear()
        self.route_reservations.clear()