"""LSM Launch system tests"""

import pytest
from app.models.equipment import LSMLaunch
from app.simulation.equipment.lsm import (
    compute_lsm_force,
    create_lsm_state,
    LSMState,
)


class TestLSMState:
    """Tests for LSM state management."""

    def test_create_lsm_state(self):
        """Test creating LSM state from equipment."""
        lsm = LSMLaunch(
            id="lsm_1",
            path_id="path_1",
            start_s=0.0,
            end_s=100.0,
            stator_count=10,
            magnetic_field_strength=0.9,
            max_force_n=50000.0,
            enabled=True
        )
        state = create_lsm_state(lsm)

        assert state.enabled is True
        assert state.current_force_n == 0.0
        assert state.stators_active == 0

    def test_create_lsm_state_disabled(self):
        """Test creating LSM state for disabled equipment."""
        lsm = LSMLaunch(
            id="lsm_1",
            path_id="path_1",
            start_s=0.0,
            end_s=100.0,
            stator_count=10,
            magnetic_field_strength=0.9,
            max_force_n=50000.0,
            enabled=False
        )
        state = create_lsm_state(lsm)

        assert state.enabled is False


class TestLSMForce:
    """Tests for LSM force computation."""

    @pytest.fixture
    def lsm(self):
        """Create a standard LSM for testing."""
        return LSMLaunch(
            id="lsm_1",
            path_id="path_1",
            start_s=0.0,
            end_s=100.0,
            stator_count=10,
            magnetic_field_strength=1.0,
            max_force_n=50000.0,
            enabled=True
        )

    def test_no_force_when_disabled(self, lsm):
        """LSM should apply no force when disabled."""
        state = LSMState(enabled=False)
        force = compute_lsm_force(lsm, state, train_s=50.0, train_velocity_mps=10.0, train_mass_kg=10000.0)

        assert force == 0.0

    def test_no_force_outside_zone(self, lsm):
        """LSM should apply no force outside launch zone."""
        state = LSMState(enabled=True)

        # Before zone
        force = compute_lsm_force(lsm, state, train_s=-10.0, train_velocity_mps=10.0, train_mass_kg=10000.0)
        assert force == 0.0

        # After zone
        force = compute_lsm_force(lsm, state, train_s=150.0, train_velocity_mps=10.0, train_mass_kg=10000.0)
        assert force == 0.0

    def test_force_in_zone(self, lsm):
        """LSM should apply force when train is in zone."""
        state = LSMState(enabled=True)
        force = compute_lsm_force(lsm, state, train_s=50.0, train_velocity_mps=10.0, train_mass_kg=10000.0)

        assert force > 0.0
        assert force <= lsm.max_force_n

    def test_force_decreases_at_high_speed(self, lsm):
        """LSM force should decrease as speed increases."""
        state = LSMState(enabled=True)

        force_low_speed = compute_lsm_force(lsm, state, train_s=50.0, train_velocity_mps=5.0, train_mass_kg=10000.0)
        state2 = LSMState(enabled=True)
        force_high_speed = compute_lsm_force(lsm, state2, train_s=50.0, train_velocity_mps=30.0, train_mass_kg=10000.0)

        assert force_low_speed > force_high_speed

    def test_force_clamped_to_max(self, lsm):
        """Force should never exceed max_force_n."""
        state = LSMState(enabled=True)
        force = compute_lsm_force(lsm, state, train_s=50.0, train_velocity_mps=0.0, train_mass_kg=10000.0)

        assert force <= lsm.max_force_n

    def test_state_updated(self, lsm):
        """LSM state should be updated after force computation."""
        state = LSMState(enabled=True)
        compute_lsm_force(lsm, state, train_s=50.0, train_velocity_mps=10.0, train_mass_kg=10000.0)

        assert state.current_force_n > 0.0
        assert state.stators_active > 0

    def test_force_curve_interpolation(self):
        """Test force curve interpolation."""
        lsm = LSMLaunch(
            id="lsm_1",
            path_id="path_1",
            start_s=0.0,
            end_s=100.0,
            stator_count=10,
            magnetic_field_strength=1.0,
            max_force_n=50000.0,
            force_curve=[
                {"position": 0.0, "velocity_min": 0, "velocity_max": 100, "force": 40000},
                {"position": 0.5, "velocity_min": 0, "velocity_max": 100, "force": 45000},
                {"position": 1.0, "velocity_min": 0, "velocity_max": 100, "force": 30000},
            ],
            enabled=True
        )
        state = LSMState(enabled=True)

        # At start
        force_start = compute_lsm_force(lsm, state, train_s=0.0, train_velocity_mps=10.0, train_mass_kg=10000.0)
        assert force_start == 40000.0

        # At midpoint
        state2 = LSMState(enabled=True)
        force_mid = compute_lsm_force(lsm, state2, train_s=50.0, train_velocity_mps=10.0, train_mass_kg=10000.0)
        assert force_mid == 45000.0

        # At end
        state3 = LSMState(enabled=True)
        force_end = compute_lsm_force(lsm, state3, train_s=100.0, train_velocity_mps=10.0, train_mass_kg=10000.0)
        assert force_end == 30000.0