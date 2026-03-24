"""Booster tests"""

import pytest
from app.models.equipment import Booster
from app.models.common import BoosterMode
from app.simulation.equipment.booster import (
    compute_booster_force,
    create_booster_state,
    set_booster_mode,
    BoosterState,
)


class TestBoosterState:
    """Tests for booster state management."""

    def test_create_booster_state(self):
        """Test creating booster state from equipment."""
        booster = Booster(
            id="booster_1",
            path_id="path_1",
            start_s=0.0,
            end_s=10.0,
            wheel_count=4,
            max_drive_force_n=5000.0,
            max_drive_speed_mps=2.0,
            brake_friction_force_n=3000.0,
            mode=BoosterMode.IDLE
        )
        state = create_booster_state(booster)

        assert state.mode == BoosterMode.IDLE
        assert state.current_force_n == 0.0

    def test_create_booster_state_drive(self):
        """Test creating booster state for drive mode."""
        booster = Booster(
            id="booster_1",
            path_id="path_1",
            start_s=0.0,
            end_s=10.0,
            wheel_count=4,
            max_drive_force_n=5000.0,
            max_drive_speed_mps=2.0,
            brake_friction_force_n=3000.0,
            mode=BoosterMode.DRIVE
        )
        state = create_booster_state(booster)

        assert state.mode == BoosterMode.DRIVE


class TestBoosterForce:
    """Tests for booster force computation."""

    @pytest.fixture
    def booster(self):
        """Create a standard booster for testing."""
        return Booster(
            id="booster_1",
            path_id="path_1",
            start_s=0.0,
            end_s=10.0,
            wheel_count=4,
            max_drive_force_n=5000.0,
            max_drive_speed_mps=2.0,
            brake_friction_force_n=3000.0,
            mode=BoosterMode.IDLE
        )

    def test_no_force_when_idle(self, booster):
        """Booster should apply no force in idle mode."""
        state = BoosterState(mode=BoosterMode.IDLE)
        force = compute_booster_force(booster, state, train_s=5.0, train_velocity_mps=1.0, dt=0.01)

        assert force == 0.0

    def test_no_force_outside_zone(self, booster):
        """Booster should apply no force outside its zone."""
        state = BoosterState(mode=BoosterMode.DRIVE)
        force = compute_booster_force(booster, state, train_s=20.0, train_velocity_mps=1.0, dt=0.01)

        assert force == 0.0

    def test_drive_force_in_zone(self, booster):
        """Booster should apply driving force in zone when in drive mode."""
        state = BoosterState(mode=BoosterMode.DRIVE)
        force = compute_booster_force(booster, state, train_s=5.0, train_velocity_mps=0.5, dt=0.01)

        assert force > 0.0  # Positive = driving

    def test_no_drive_force_at_max_speed(self, booster):
        """Booster should apply no force when train is at max speed."""
        state = BoosterState(mode=BoosterMode.DRIVE)
        force = compute_booster_force(booster, state, train_s=5.0, train_velocity_mps=2.0, dt=0.01)

        assert force == 0.0

    def test_brake_force_in_zone(self, booster):
        """Booster should apply braking force in zone when in brake mode."""
        state = BoosterState(mode=BoosterMode.BRAKE)
        force = compute_booster_force(booster, state, train_s=5.0, train_velocity_mps=1.0, dt=0.01)

        assert force < 0.0  # Negative = braking

    def test_drive_force_proportional_to_speed_deficit(self, booster):
        """Drive force should be proportional to how far below max speed."""
        state1 = BoosterState(mode=BoosterMode.DRIVE)
        force_slow = compute_booster_force(booster, state1, train_s=5.0, train_velocity_mps=0.5, dt=0.01)

        state2 = BoosterState(mode=BoosterMode.DRIVE)
        force_faster = compute_booster_force(booster, state2, train_s=5.0, train_velocity_mps=1.5, dt=0.01)

        # Slower train should get more force
        assert force_slow > force_faster

    def test_wheel_count_affects_force(self):
        """More wheels should apply more force."""
        booster_2wheels = Booster(
            id="booster_1",
            path_id="path_1",
            start_s=0.0,
            end_s=10.0,
            wheel_count=2,
            max_drive_force_n=5000.0,
            max_drive_speed_mps=2.0,
            brake_friction_force_n=3000.0,
            mode=BoosterMode.DRIVE
        )
        booster_8wheels = Booster(
            id="booster_2",
            path_id="path_1",
            start_s=0.0,
            end_s=10.0,
            wheel_count=8,
            max_drive_force_n=5000.0,
            max_drive_speed_mps=2.0,
            brake_friction_force_n=3000.0,
            mode=BoosterMode.DRIVE
        )

        state1 = BoosterState(mode=BoosterMode.DRIVE)
        force_2wheels = compute_booster_force(booster_2wheels, state1, train_s=5.0, train_velocity_mps=0.5, dt=0.01)

        state2 = BoosterState(mode=BoosterMode.DRIVE)
        force_8wheels = compute_booster_force(booster_8wheels, state2, train_s=5.0, train_velocity_mps=0.5, dt=0.01)

        # 8 wheels should apply more force (capped at 100%)
        assert force_8wheels >= force_2wheels


class TestBoosterModeChanges:
    """Tests for booster mode changes."""

    def test_set_booster_mode(self):
        """Test changing booster mode."""
        booster = Booster(
            id="booster_1",
            path_id="path_1",
            start_s=0.0,
            end_s=10.0,
            wheel_count=4,
            max_drive_force_n=5000.0,
            max_drive_speed_mps=2.0,
            brake_friction_force_n=3000.0,
            mode=BoosterMode.IDLE
        )
        state = create_booster_state(booster)

        set_booster_mode(booster, state, BoosterMode.DRIVE)

        assert state.mode == BoosterMode.DRIVE
        assert state.current_force_n == 0.0

    def test_set_to_brake_mode(self):
        """Test setting booster to brake mode."""
        booster = Booster(
            id="booster_1",
            path_id="path_1",
            start_s=0.0,
            end_s=10.0,
            wheel_count=4,
            max_drive_force_n=5000.0,
            max_drive_speed_mps=2.0,
            brake_friction_force_n=3000.0,
            mode=BoosterMode.DRIVE
        )
        state = create_booster_state(booster)

        set_booster_mode(booster, state, BoosterMode.BRAKE)

        assert state.mode == BoosterMode.BRAKE