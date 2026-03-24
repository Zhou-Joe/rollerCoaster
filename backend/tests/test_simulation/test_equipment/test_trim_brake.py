"""Trim brake tests"""

import pytest
from app.models.equipment import TrimBrake
from app.simulation.equipment.trim_brake import (
    compute_trim_brake_force,
    create_trim_brake_state,
    TrimBrakeState,
)


class TestTrimBrakeState:
    """Tests for trim brake state management."""

    def test_create_trim_brake_state(self):
        """Test creating trim brake state from equipment."""
        trim = TrimBrake(
            id="trim_1",
            path_id="path_1",
            start_s=0.0,
            end_s=30.0,
            max_trim_force_n=5000.0,
            enabled=True
        )
        state = create_trim_brake_state(trim)

        assert state.enabled is True
        assert state.current_force_n == 0.0

    def test_create_trim_brake_state_disabled(self):
        """Test creating trim brake state for disabled equipment."""
        trim = TrimBrake(
            id="trim_1",
            path_id="path_1",
            start_s=0.0,
            end_s=30.0,
            max_trim_force_n=5000.0,
            enabled=False
        )
        state = create_trim_brake_state(trim)

        assert state.enabled is False


class TestTrimBrakeForce:
    """Tests for trim brake force computation."""

    @pytest.fixture
    def trim(self):
        """Create a standard trim brake for testing."""
        return TrimBrake(
            id="trim_1",
            path_id="path_1",
            start_s=0.0,
            end_s=30.0,
            max_trim_force_n=5000.0,
            enabled=True
        )

    def test_no_force_when_disabled(self, trim):
        """Trim brake should apply no force when disabled."""
        state = TrimBrakeState(enabled=False)
        force = compute_trim_brake_force(trim, state, train_s=15.0, train_velocity_mps=10.0, dt=0.01)

        assert force == 0.0

    def test_no_force_outside_zone(self, trim):
        """Trim brake should apply no force outside brake zone."""
        state = TrimBrakeState(enabled=True)

        force = compute_trim_brake_force(trim, state, train_s=50.0, train_velocity_mps=10.0, dt=0.01)

        assert force == 0.0

    def test_braking_force_in_zone(self, trim):
        """Trim brake should apply braking force when train is in zone."""
        state = TrimBrakeState(enabled=True)
        force = compute_trim_brake_force(trim, state, train_s=15.0, train_velocity_mps=10.0, dt=0.01)

        assert force < 0.0  # Negative = braking
        assert abs(force) <= trim.max_trim_force_n

    def test_reduced_force_at_low_speed(self, trim):
        """Trim brake should reduce force at very low speeds."""
        state = TrimBrakeState(enabled=True)

        force_high_speed = compute_trim_brake_force(trim, state, train_s=15.0, train_velocity_mps=10.0, dt=0.01)
        state2 = TrimBrakeState(enabled=True)
        force_low_speed = compute_trim_brake_force(trim, state2, train_s=15.0, train_velocity_mps=1.0, dt=0.01)

        # Low speed should have reduced force
        assert abs(force_low_speed) < abs(force_high_speed)

    def test_force_curve_application(self):
        """Test force curve application."""
        trim = TrimBrake(
            id="trim_1",
            path_id="path_1",
            start_s=0.0,
            end_s=30.0,
            max_trim_force_n=5000.0,
            force_curve=[
                {"velocity": 10, "position": 0.0, "force_factor": 0.5},
                {"velocity": 10, "position": 1.0, "force_factor": 1.0},
            ],
            enabled=True
        )
        state = TrimBrakeState(enabled=True)

        # At start (position 0.0)
        force_start = compute_trim_brake_force(trim, state, train_s=0.0, train_velocity_mps=10.0, dt=0.01)
        assert abs(force_start) == pytest.approx(0.5 * 5000.0, rel=0.1)

        # At end (position 1.0)
        state2 = TrimBrakeState(enabled=True)
        force_end = compute_trim_brake_force(trim, state2, train_s=30.0, train_velocity_mps=10.0, dt=0.01)
        assert abs(force_end) == pytest.approx(1.0 * 5000.0, rel=0.1)

    def test_state_updated(self, trim):
        """State should be updated after force computation."""
        state = TrimBrakeState(enabled=True)
        compute_trim_brake_force(trim, state, train_s=15.0, train_velocity_mps=10.0, dt=0.01)

        assert state.current_force_n < 0.0
        assert state.effective_force_n > 0.0