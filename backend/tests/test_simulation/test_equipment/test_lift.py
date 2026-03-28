"""Lift hill system tests"""

import pytest
from app.models.equipment import Lift
from app.simulation.equipment.lift import (
    compute_lift_effect,
    create_lift_state,
    check_lift_release,
    LiftState,
)


class TestLiftState:
    """Tests for lift state management."""

    def test_create_lift_state(self):
        """Test creating lift state from equipment."""
        lift = Lift(
            id="lift_1",
            path_id="path_1",
            start_s=0.0,
            end_s=100.0,
            lift_speed_mps=2.0,
            max_pull_force_n=30000.0,
            engagement_point_s=5.0,
            release_point_s=95.0,
            enabled=True
        )
        state = create_lift_state(lift)

        assert state.enabled is True
        assert state.engaged is False
        assert state.current_force_n == 0.0

    def test_create_lift_state_disabled(self):
        """Test creating lift state for disabled equipment."""
        lift = Lift(
            id="lift_1",
            path_id="path_1",
            start_s=0.0,
            end_s=100.0,
            lift_speed_mps=2.0,
            max_pull_force_n=30000.0,
            engagement_point_s=5.0,
            release_point_s=95.0,
            enabled=False
        )
        state = create_lift_state(lift)

        assert state.enabled is False


class TestLiftForce:
    """Tests for lift force computation."""

    @pytest.fixture
    def lift(self):
        """Create a standard lift for testing."""
        return Lift(
            id="lift_1",
            path_id="path_1",
            start_s=0.0,
            end_s=100.0,
            lift_speed_mps=2.0,
            max_pull_force_n=30000.0,
            engagement_point_s=5.0,
            release_point_s=95.0,
            enabled=True
        )

    def test_no_force_when_disabled(self, lift):
        """Lift should apply no force when disabled."""
        state = LiftState(enabled=False)
        force, velocity = compute_lift_effect(lift, state, train_s=50.0, train_velocity_mps=1.0, dt=0.01)

        assert force == 0.0
        assert state.engaged is False

    def test_no_force_outside_zone(self, lift):
        """Lift should apply no force outside lift zone."""
        state = LiftState(enabled=True)

        # Before engagement zone
        force, velocity = compute_lift_effect(lift, state, train_s=2.0, train_velocity_mps=1.0, dt=0.01)
        assert force == 0.0

        # After release zone
        state2 = LiftState(enabled=True)
        force, velocity = compute_lift_effect(lift, state2, train_s=98.0, train_velocity_mps=1.0, dt=0.01)
        # At release point, should disengage
        assert state2.engaged is False or force == 0.0

    def test_engages_in_engagement_zone(self, lift):
        """Lift should engage when train enters engagement zone."""
        state = LiftState(enabled=True)
        force, velocity = compute_lift_effect(lift, state, train_s=10.0, train_velocity_mps=1.0, dt=0.01)

        assert state.engaged is True
        # When engaged, lift returns velocity override (2.0 m/s)
        assert velocity == 2.0

    def test_velocity_override_when_engaged(self, lift):
        """Lift should return velocity override when engaged."""
        state = LiftState(enabled=True, engaged=True, engagement_progress=1.0)
        force, velocity = compute_lift_effect(lift, state, train_s=50.0, train_velocity_mps=1.0, dt=0.01)

        # When engaged, velocity is overridden to lift speed
        assert velocity == 2.0
        assert force == 0.0  # Force is 0 because lift overrides velocity directly

    def test_no_engagement_when_above_lift_speed(self, lift):
        """Lift should still engage even if train is faster, but it controls velocity."""
        state = LiftState(enabled=True, engaged=True, engagement_progress=1.0)
        force, velocity = compute_lift_effect(lift, state, train_s=50.0, train_velocity_mps=3.0, dt=0.01)

        # Lift overrides velocity to its speed
        assert velocity == 2.0

    def test_velocity_override_when_below_lift_speed(self, lift):
        """Lift should override velocity when engaged."""
        state = LiftState(enabled=True, engaged=True, engagement_progress=1.0)
        force, velocity = compute_lift_effect(lift, state, train_s=50.0, train_velocity_mps=1.0, dt=0.01)

        # Lift overrides velocity to its speed
        assert velocity == 2.0
        assert force == 0.0

    def test_smooth_engagement(self, lift):
        """Engagement should be smooth (ramp up)."""
        state = LiftState(enabled=True, engaged=False, engagement_progress=0.0)

        # First step - should be partially engaged
        force1, velocity = compute_lift_effect(lift, state, train_s=10.0, train_velocity_mps=0.0, dt=0.01)
        assert state.engagement_progress > 0.0

        # After many steps - should be fully engaged
        for _ in range(100):
            compute_lift_effect(lift, state, train_s=10.0, train_velocity_mps=0.0, dt=0.01)

        assert state.engagement_progress == 1.0


class TestLiftRelease:
    """Tests for lift release detection."""

    def test_not_released_before_point(self):
        """Lift should not release before release point."""
        lift = Lift(
            id="lift_1",
            path_id="path_1",
            start_s=0.0,
            end_s=100.0,
            lift_speed_mps=2.0,
            max_pull_force_n=30000.0,
            engagement_point_s=5.0,
            release_point_s=95.0,
            enabled=True
        )
        state = LiftState(enabled=True, engaged=True)

        released = check_lift_release(lift, state, train_s=50.0)

        assert released is False
        assert state.engaged is True

    def test_released_at_point(self):
        """Lift should release at release point."""
        lift = Lift(
            id="lift_1",
            path_id="path_1",
            start_s=0.0,
            end_s=100.0,
            lift_speed_mps=2.0,
            max_pull_force_n=30000.0,
            engagement_point_s=5.0,
            release_point_s=95.0,
            enabled=True
        )
        state = LiftState(enabled=True, engaged=True)

        released = check_lift_release(lift, state, train_s=96.0)

        assert released is True
        assert state.engaged is False