"""Interlock system tests"""

import pytest
from app.models.common import BrakeState
from app.simulation.control.interlocks import InterlockSystem, InterlockResult


class TestInterlockSystem:
    """Tests for interlock system."""

    @pytest.fixture
    def interlocks(self):
        """Create an interlock system."""
        return InterlockSystem()

    def test_create_interlocks(self, interlocks):
        """Test creating interlock system."""
        assert interlocks.emergency_stop_active is False
        assert len(interlocks.block_occupancy) == 0


class TestSwitchInterlocks:
    """Tests for switch interlocks."""

    @pytest.fixture
    def interlocks(self):
        """Create interlock system."""
        return InterlockSystem()

    def test_switch_change_allowed(self, interlocks):
        """Test switch change is allowed when not occupied."""
        result = interlocks.check_switch_change("switch_1", "main")
        assert result.allowed is True

    def test_switch_change_blocked_when_occupied(self, interlocks):
        """Test switch change blocked when occupied."""
        interlocks.update_switch_occupancy("switch_1", occupied=True)

        result = interlocks.check_switch_change("switch_1", "main")
        assert result.allowed is False
        assert "occupied" in result.reason.lower()

    def test_switch_change_blocked_during_estop(self, interlocks):
        """Test switch change blocked during E-stop."""
        interlocks.set_emergency_stop(True)

        result = interlocks.check_switch_change("switch_1", "main")
        assert result.allowed is False
        assert "emergency" in result.reason.lower()


class TestDispatchInterlocks:
    """Tests for dispatch interlocks."""

    @pytest.fixture
    def interlocks(self):
        """Create interlock system with dispatch permit."""
        system = InterlockSystem()
        system.set_dispatch_permit("station_1", True)
        return system

    def test_dispatch_allowed_when_clear(self, interlocks):
        """Test dispatch allowed when route is clear."""
        result = interlocks.check_dispatch(
            station_id="station_1",
            train_id="train_1",
            route=["block_1", "block_2"]
        )
        assert result.allowed is True

    def test_dispatch_blocked_without_permit(self, interlocks):
        """Test dispatch blocked without permit."""
        interlocks.set_dispatch_permit("station_1", False)

        result = interlocks.check_dispatch(
            station_id="station_1",
            train_id="train_1",
            route=["block_1", "block_2"]
        )
        assert result.allowed is False
        assert "not permitted" in result.reason.lower()

    def test_dispatch_blocked_when_route_blocked(self, interlocks):
        """Test dispatch blocked when route has occupied blocks."""
        interlocks.update_block_occupancy("block_1", train_id="train_2")

        result = interlocks.check_dispatch(
            station_id="station_1",
            train_id="train_1",
            route=["block_1", "block_2"]
        )
        assert result.allowed is False
        assert "occupied" in result.reason.lower()

    def test_dispatch_blocked_during_estop(self, interlocks):
        """Test dispatch blocked during E-stop."""
        interlocks.set_emergency_stop(True)

        result = interlocks.check_dispatch(
            station_id="station_1",
            train_id="train_1",
            route=["block_1", "block_2"]
        )
        assert result.allowed is False


class TestEquipmentInterlocks:
    """Tests for equipment interlocks."""

    @pytest.fixture
    def interlocks(self):
        """Create interlock system."""
        return InterlockSystem()

    def test_equipment_command_allowed(self, interlocks):
        """Test equipment command allowed normally."""
        result = interlocks.check_equipment_command(
            equipment_id="brake_1",
            equipment_type="pneumatic_brake",
            command="close",
            parameters={}
        )
        assert result.allowed is True

    def test_brake_close_allowed_during_estop(self, interlocks):
        """Test closing brake is allowed during E-stop."""
        interlocks.set_emergency_stop(True)

        result = interlocks.check_equipment_command(
            equipment_id="brake_1",
            equipment_type="pneumatic_brake",
            command="close",
            parameters={}
        )
        assert result.allowed is True

    def test_brake_open_blocked_during_estop(self, interlocks):
        """Test opening brake blocked during E-stop."""
        interlocks.set_emergency_stop(True)

        result = interlocks.check_brake_state_change("brake_1", BrakeState.OPEN)
        assert result.allowed is False
        assert "emergency" in result.reason.lower()

    def test_other_equipment_blocked_during_estop(self, interlocks):
        """Test other equipment blocked during E-stop."""
        interlocks.set_emergency_stop(True)

        result = interlocks.check_equipment_command(
            equipment_id="lsm_1",
            equipment_type="lsm_launch",
            command="enable",
            parameters={}
        )
        assert result.allowed is False


class TestBlockOccupancy:
    """Tests for block occupancy tracking."""

    @pytest.fixture
    def interlocks(self):
        """Create interlock system."""
        return InterlockSystem()

    def test_update_block_occupancy(self, interlocks):
        """Test updating block occupancy."""
        interlocks.update_block_occupancy("block_1", train_id="train_1")

        assert interlocks.block_occupancy["block_1"] == "train_1"

    def test_clear_block_occupancy(self, interlocks):
        """Test clearing block occupancy."""
        interlocks.update_block_occupancy("block_1", train_id="train_1")
        interlocks.update_block_occupancy("block_1", train_id=None)

        assert interlocks.block_occupancy["block_1"] is None

    def test_is_route_clear(self, interlocks):
        """Test route clearance check."""
        route = ["block_1", "block_2", "block_3"]

        assert interlocks.is_route_clear(route) is True

        interlocks.update_block_occupancy("block_2", train_id="train_1")
        assert interlocks.is_route_clear(route) is False


class TestRouteReservation:
    """Tests for route reservations."""

    @pytest.fixture
    def interlocks(self):
        """Create interlock system."""
        return InterlockSystem()

    def test_reserve_route(self, interlocks):
        """Test reserving a route."""
        interlocks.reserve_route("train_1", "main_route")

        assert interlocks.route_reservations["train_1"] == "main_route"

    def test_clear_route_reservation(self, interlocks):
        """Test clearing route reservation."""
        interlocks.reserve_route("train_1", "main_route")
        interlocks.clear_route_reservation("train_1")

        assert "train_1" not in interlocks.route_reservations


class TestEmergencyStop:
    """Tests for emergency stop."""

    @pytest.fixture
    def interlocks(self):
        """Create interlock system."""
        return InterlockSystem()

    def test_set_emergency_stop(self, interlocks):
        """Test setting E-stop."""
        interlocks.set_emergency_stop(True)
        assert interlocks.emergency_stop_active is True

    def test_clear_emergency_stop(self, interlocks):
        """Test clearing E-stop."""
        interlocks.set_emergency_stop(True)
        interlocks.set_emergency_stop(False)
        assert interlocks.emergency_stop_active is False

    def test_reset_clears_estop(self, interlocks):
        """Test that reset clears E-stop."""
        interlocks.set_emergency_stop(True)
        interlocks.reset()
        assert interlocks.emergency_stop_active is False