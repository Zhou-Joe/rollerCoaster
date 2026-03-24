from app.models.equipment import (
    EquipmentType, LSMLaunch, Lift, PneumaticBrake,
    TrimBrake, Booster, TrackSwitch
)
from app.models.common import FailSafeMode, BrakeState, BoosterMode


def test_equipment_type_values():
    assert EquipmentType.LSM_LAUNCH.value == "lsm_launch"
    assert EquipmentType.LIFT.value == "lift"


def test_lsm_launch_creation():
    lsm = LSMLaunch(
        id="lsm_001", path_id="path_001", start_s=0.0, end_s=100.0,
        stator_count=10, magnetic_field_strength=1.5, max_force_n=50000.0
    )
    assert lsm.id == "lsm_001"
    assert lsm.equipment_type == EquipmentType.LSM_LAUNCH
    assert lsm.enabled is True


def test_lift_creation():
    lift = Lift(
        id="lift_001", path_id="path_001", start_s=0.0, end_s=50.0,
        lift_speed_mps=2.0, max_pull_force_n=30000.0,
        engagement_point_s=5.0, release_point_s=45.0
    )
    assert lift.equipment_type == EquipmentType.LIFT


def test_pneumatic_brake_creation():
    brake = PneumaticBrake(
        id="brake_001", path_id="path_001", start_s=0.0, end_s=20.0,
        max_brake_force_n=40000.0, response_time_s=0.3, air_pressure=6.0,
        fail_safe_mode=FailSafeMode.NORMALLY_CLOSED
    )
    assert brake.fail_safe_mode == FailSafeMode.NORMALLY_CLOSED
    assert brake.state == BrakeState.OPEN


def test_trim_brake_creation():
    trim = TrimBrake(id="trim_001", path_id="path_001", start_s=50.0, end_s=60.0, max_trim_force_n=15000.0)
    assert trim.equipment_type == EquipmentType.TRIM_BRAKE


def test_booster_creation():
    booster = Booster(
        id="booster_001", path_id="path_001", start_s=0.0, end_s=10.0,
        wheel_count=4, max_drive_force_n=5000.0, max_drive_speed_mps=2.0, brake_friction_force_n=2000.0
    )
    assert booster.mode == BoosterMode.IDLE


def test_track_switch_creation():
    switch = TrackSwitch(
        id="switch_001", junction_id="jct_001", incoming_path_id="path_001",
        outgoing_path_ids=["path_002", "path_003"], current_alignment="path_002"
    )
    assert switch.actuation_time_s == 2.0