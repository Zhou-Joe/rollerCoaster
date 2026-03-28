"""Equipment manager tests"""

import pytest
from app.models.equipment import LSMLaunch, Lift, PneumaticBrake, TrimBrake, Booster
from app.models.common import FailSafeMode, BrakeState, BoosterMode
from app.models.project import Project, ProjectMetadata
from app.simulation.equipment.manager import EquipmentManager, EquipmentStates


class TestEquipmentStates:
    """Tests for equipment states container."""

    def test_empty_states(self):
        """Test creating empty equipment states."""
        states = EquipmentStates()

        assert len(states.lsm) == 0
        assert len(states.lift) == 0
        assert len(states.pneumatic_brake) == 0
        assert len(states.trim_brake) == 0
        assert len(states.booster) == 0


class TestEquipmentManager:
    """Tests for equipment manager."""

    @pytest.fixture
    def project_with_equipment(self):
        """Create a project with various equipment."""
        return Project(
            metadata=ProjectMetadata(name="Test Project"),
            equipment=[
                LSMLaunch(
                    id="lsm_1",
                    path_id="path_1",
                    start_s=0.0,
                    end_s=100.0,
                    stator_count=10,
                    magnetic_field_strength=1.0,
                    max_force_n=50000.0,
                    enabled=True
                ).model_dump(),
                Lift(
                    id="lift_1",
                    path_id="path_1",
                    start_s=100.0,
                    end_s=200.0,
                    lift_speed_mps=2.0,
                    max_pull_force_n=30000.0,
                    engagement_point_s=105.0,
                    release_point_s=195.0,
                    enabled=True
                ).model_dump(),
                PneumaticBrake(
                    id="brake_1",
                    path_id="path_1",
                    start_s=200.0,
                    end_s=220.0,
                    max_brake_force_n=20000.0,
                    response_time_s=0.1,
                    air_pressure=7.0,
                    fail_safe_mode=FailSafeMode.NORMALLY_OPEN,
                    state=BrakeState.OPEN
                ).model_dump(),
                TrimBrake(
                    id="trim_1",
                    path_id="path_1",
                    start_s=220.0,
                    end_s=250.0,
                    max_trim_force_n=5000.0,
                    enabled=True
                ).model_dump(),
                Booster(
                    id="booster_1",
                    path_id="path_1",
                    start_s=250.0,
                    end_s=260.0,
                    wheel_count=4,
                    max_drive_force_n=5000.0,
                    max_drive_speed_mps=2.0,
                    brake_friction_force_n=3000.0,
                    mode=BoosterMode.IDLE
                ).model_dump(),
            ]
        )

    def test_initialize_states(self, project_with_equipment):
        """Test initializing states for all equipment."""
        manager = EquipmentManager(project_with_equipment)

        assert len(manager.states.lsm) == 1
        assert len(manager.states.lift) == 1
        assert len(manager.states.pneumatic_brake) == 1
        assert len(manager.states.trim_brake) == 1
        assert len(manager.states.booster) == 1

    def test_compute_equipment_force_lsm(self, project_with_equipment):
        """Test computing equipment force from LSM."""
        manager = EquipmentManager(project_with_equipment)

        force, velocity_override, breakdown = manager.compute_equipment_force(
            train_path_id="path_1",
            train_s=50.0,
            train_velocity_mps=10.0,
            train_mass_kg=10000.0,
            dt=0.01
        )

        assert force > 0.0  # LSM should be accelerating
        assert velocity_override is None  # No lift engaged

    def test_compute_equipment_force_lift(self, project_with_equipment):
        """Test computing equipment force from lift."""
        manager = EquipmentManager(project_with_equipment)

        force, velocity_override, breakdown = manager.compute_equipment_force(
            train_path_id="path_1",
            train_s=150.0,
            train_velocity_mps=1.0,
            train_mass_kg=10000.0,
            dt=0.01
        )

        # When lift is engaged, it returns velocity override
        assert velocity_override == 2.0  # Lift speed override

    def test_compute_equipment_force_brake(self, project_with_equipment):
        """Test computing equipment force from brake."""
        manager = EquipmentManager(project_with_equipment)

        # Close the brake
        manager.set_brake_state("brake_1", BrakeState.CLOSED)

        # Run multiple steps to let brake engage
        for _ in range(20):
            force, velocity_override, breakdown = manager.compute_equipment_force(
                train_path_id="path_1",
                train_s=210.0,
                train_velocity_mps=10.0,
                train_mass_kg=10000.0,
                dt=0.01
            )

        assert force < 0.0  # Brake should be decelerating
        assert velocity_override is None  # No lift engaged

    def test_compute_equipment_force_booster(self, project_with_equipment):
        """Test computing equipment force from booster."""
        manager = EquipmentManager(project_with_equipment)

        manager.set_booster_mode("booster_1", BoosterMode.DRIVE)

        force, velocity_override, breakdown = manager.compute_equipment_force(
            train_path_id="path_1",
            train_s=255.0,
            train_velocity_mps=0.5,
            train_mass_kg=10000.0,
            dt=0.01
        )

        assert force > 0.0  # Booster should be driving
        assert velocity_override is None  # No lift engaged

    def test_compute_equipment_force_no_equipment(self):
        """Test computing force with no equipment."""
        project = Project(id="proj_1", name="Empty Project")
        manager = EquipmentManager(project)

        force, velocity_override, breakdown = manager.compute_equipment_force(
            train_path_id="path_1",
            train_s=50.0,
            train_velocity_mps=10.0,
            train_mass_kg=10000.0,
            dt=0.01
        )

        assert force == 0.0
        assert velocity_override is None

    def test_compute_equipment_force_wrong_path(self, project_with_equipment):
        """Test computing force when train is on different path."""
        manager = EquipmentManager(project_with_equipment)

        force, velocity_override, breakdown = manager.compute_equipment_force(
            train_path_id="path_2",
            train_s=50.0,
            train_velocity_mps=10.0,
            train_mass_kg=10000.0,
            dt=0.01
        )

        assert force == 0.0
        assert velocity_override is None

    def test_set_lsm_enabled(self, project_with_equipment):
        """Test enabling/disabling LSM."""
        manager = EquipmentManager(project_with_equipment)

        manager.set_lsm_enabled("lsm_1", False)
        assert manager.states.lsm["lsm_1"].enabled is False

        manager.set_lsm_enabled("lsm_1", True)
        assert manager.states.lsm["lsm_1"].enabled is True

    def test_set_brake_state(self, project_with_equipment):
        """Test setting brake state."""
        manager = EquipmentManager(project_with_equipment)

        manager.set_brake_state("brake_1", BrakeState.CLOSED)
        assert manager.states.pneumatic_brake["brake_1"].state == BrakeState.CLOSED

    def test_set_booster_mode(self, project_with_equipment):
        """Test setting booster mode."""
        manager = EquipmentManager(project_with_equipment)

        manager.set_booster_mode("booster_1", BoosterMode.DRIVE)
        assert manager.states.booster["booster_1"].mode == BoosterMode.DRIVE

    def test_set_trim_enabled(self, project_with_equipment):
        """Test enabling/disabling trim brake."""
        manager = EquipmentManager(project_with_equipment)

        manager.set_trim_enabled("trim_1", False)
        assert manager.states.trim_brake["trim_1"].enabled is False

    def test_apply_all_fail_safes(self, project_with_equipment):
        """Test applying fail-safe behavior to all brakes."""
        manager = EquipmentManager(project_with_equipment)

        # Set brake to OPEN
        manager.set_brake_state("brake_1", BrakeState.OPEN)

        # Apply fail-safe (normally_open should stay open)
        manager.apply_all_fail_safes()

        assert manager.states.pneumatic_brake["brake_1"].state == BrakeState.OPEN

    def test_reset(self, project_with_equipment):
        """Test resetting equipment states."""
        manager = EquipmentManager(project_with_equipment)

        # Modify some states
        manager.set_lsm_enabled("lsm_1", False)
        manager.set_brake_state("brake_1", BrakeState.CLOSED)

        # Reset
        manager.reset()

        # States should be back to initial
        assert manager.states.lsm["lsm_1"].enabled is True
        assert manager.states.pneumatic_brake["brake_1"].state == BrakeState.OPEN

    def test_get_equipment_state(self, project_with_equipment):
        """Test getting equipment state by ID."""
        manager = EquipmentManager(project_with_equipment)

        lsm_state = manager.get_equipment_state("lsm_1")
        assert lsm_state is not None
        assert lsm_state.enabled is True

        brake_state = manager.get_equipment_state("brake_1")
        assert brake_state is not None

        # Non-existent equipment
        unknown_state = manager.get_equipment_state("unknown")
        assert unknown_state is None