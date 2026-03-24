"""Pneumatic brake tests"""

import pytest
from app.models.equipment import PneumaticBrake
from app.models.common import FailSafeMode, BrakeState
from app.simulation.equipment.pneumatic_brake import (
    compute_pneumatic_brake_force,
    create_pneumatic_brake_state,
    set_brake_state,
    apply_fail_safe,
    PneumaticBrakeState,
)


class TestPneumaticBrakeState:
    """Tests for pneumatic brake state management."""

    def test_create_brake_state(self):
        """Test creating brake state from equipment."""
        brake = PneumaticBrake(
            id="brake_1",
            path_id="path_1",
            start_s=0.0,
            end_s=20.0,
            max_brake_force_n=20000.0,
            response_time_s=0.3,
            air_pressure=7.0,
            fail_safe_mode=FailSafeMode.NORMALLY_OPEN,
            state=BrakeState.OPEN
        )
        state = create_pneumatic_brake_state(brake)

        assert state.state == BrakeState.OPEN
        assert state.current_force_n == 0.0
        assert state.response_progress == 1.0

    def test_create_brake_state_closed(self):
        """Test creating brake state for closed brake."""
        brake = PneumaticBrake(
            id="brake_1",
            path_id="path_1",
            start_s=0.0,
            end_s=20.0,
            max_brake_force_n=20000.0,
            response_time_s=0.3,
            air_pressure=7.0,
            fail_safe_mode=FailSafeMode.NORMALLY_CLOSED,
            state=BrakeState.CLOSED
        )
        state = create_pneumatic_brake_state(brake)

        assert state.state == BrakeState.CLOSED


class TestPneumaticBrakeForce:
    """Tests for pneumatic brake force computation."""

    @pytest.fixture
    def brake_normally_open(self):
        """Create a normally-open brake for testing."""
        return PneumaticBrake(
            id="brake_1",
            path_id="path_1",
            start_s=0.0,
            end_s=20.0,
            max_brake_force_n=20000.0,
            response_time_s=0.1,  # Fast response for testing
            air_pressure=7.0,
            fail_safe_mode=FailSafeMode.NORMALLY_OPEN,
            state=BrakeState.OPEN
        )

    @pytest.fixture
    def brake_normally_closed(self):
        """Create a normally-closed brake for testing."""
        return PneumaticBrake(
            id="brake_1",
            path_id="path_1",
            start_s=0.0,
            end_s=20.0,
            max_brake_force_n=20000.0,
            response_time_s=0.1,
            air_pressure=7.0,
            fail_safe_mode=FailSafeMode.NORMALLY_CLOSED,
            state=BrakeState.CLOSED
        )

    def test_no_force_outside_zone(self, brake_normally_open):
        """Brake should apply no force outside brake zone."""
        state = create_pneumatic_brake_state(brake_normally_open)
        set_brake_state(brake_normally_open, state, BrakeState.CLOSED)

        force = compute_pneumatic_brake_force(
            brake_normally_open, state, train_s=50.0, train_velocity_mps=10.0, dt=0.01
        )

        assert force == 0.0

    def test_no_force_when_open(self, brake_normally_open):
        """Brake should apply no force when open."""
        state = create_pneumatic_brake_state(brake_normally_open)

        force = compute_pneumatic_brake_force(
            brake_normally_open, state, train_s=10.0, train_velocity_mps=10.0, dt=0.01
        )

        assert force == 0.0

    def test_braking_force_when_closed(self, brake_normally_open):
        """Brake should apply braking force when closed."""
        state = create_pneumatic_brake_state(brake_normally_open)
        set_brake_state(brake_normally_open, state, BrakeState.CLOSED)

        # Run enough steps for full response
        for _ in range(20):
            force = compute_pneumatic_brake_force(
                brake_normally_open, state, train_s=10.0, train_velocity_mps=10.0, dt=0.01
            )

        assert force < 0.0  # Negative = braking
        assert abs(force) > 0

    def test_max_force_on_emergency_stop(self, brake_normally_open):
        """Emergency stop should apply maximum braking."""
        state = create_pneumatic_brake_state(brake_normally_open)
        set_brake_state(brake_normally_open, state, BrakeState.EMERGENCY_STOP)

        for _ in range(20):
            force = compute_pneumatic_brake_force(
                brake_normally_open, state, train_s=10.0, train_velocity_mps=10.0, dt=0.01
            )

        assert abs(force) == pytest.approx(brake_normally_open.max_brake_force_n, rel=0.1)

    def test_response_time_simulation(self, brake_normally_open):
        """Brake should have response time delay."""
        state = create_pneumatic_brake_state(brake_normally_open)
        set_brake_state(brake_normally_open, state, BrakeState.CLOSED)

        # First step - should not have full force yet
        force = compute_pneumatic_brake_force(
            brake_normally_open, state, train_s=10.0, train_velocity_mps=10.0, dt=0.01
        )

        # After many steps
        for _ in range(50):
            force_later = compute_pneumatic_brake_force(
                brake_normally_open, state, train_s=10.0, train_velocity_mps=10.0, dt=0.01
            )

        assert abs(force_later) > abs(force)


class TestFailSafeModes:
    """Tests for fail-safe behavior."""

    def test_normally_open_fail_safe(self):
        """Normally-open brake should stay open on fail-safe."""
        brake = PneumaticBrake(
            id="brake_1",
            path_id="path_1",
            start_s=0.0,
            end_s=20.0,
            max_brake_force_n=20000.0,
            response_time_s=0.1,
            air_pressure=7.0,
            fail_safe_mode=FailSafeMode.NORMALLY_OPEN,
            state=BrakeState.CLOSED
        )
        state = create_pneumatic_brake_state(brake)

        apply_fail_safe(brake, state)

        assert state.state == BrakeState.OPEN

    def test_normally_closed_fail_safe(self):
        """Normally-closed brake should close on fail-safe."""
        brake = PneumaticBrake(
            id="brake_1",
            path_id="path_1",
            start_s=0.0,
            end_s=20.0,
            max_brake_force_n=20000.0,
            response_time_s=0.1,
            air_pressure=7.0,
            fail_safe_mode=FailSafeMode.NORMALLY_CLOSED,
            state=BrakeState.OPEN
        )
        state = create_pneumatic_brake_state(brake)

        apply_fail_safe(brake, state)

        assert state.state == BrakeState.CLOSED


class TestBrakeStateChanges:
    """Tests for brake state changes."""

    def test_set_brake_state(self):
        """Test changing brake state."""
        brake = PneumaticBrake(
            id="brake_1",
            path_id="path_1",
            start_s=0.0,
            end_s=20.0,
            max_brake_force_n=20000.0,
            response_time_s=0.1,
            air_pressure=7.0,
            fail_safe_mode=FailSafeMode.NORMALLY_OPEN,
            state=BrakeState.OPEN
        )
        state = create_pneumatic_brake_state(brake)

        set_brake_state(brake, state, BrakeState.CLOSED)

        assert state.state == BrakeState.CLOSED
        assert state.response_progress == 0.0  # Reset for transition

    def test_set_emergency_stop(self):
        """Test setting emergency stop."""
        brake = PneumaticBrake(
            id="brake_1",
            path_id="path_1",
            start_s=0.0,
            end_s=20.0,
            max_brake_force_n=20000.0,
            response_time_s=0.1,
            air_pressure=7.0,
            fail_safe_mode=FailSafeMode.NORMALLY_OPEN,
            state=BrakeState.OPEN
        )
        state = create_pneumatic_brake_state(brake)

        set_brake_state(brake, state, BrakeState.EMERGENCY_STOP)

        assert state.state == BrakeState.EMERGENCY_STOP