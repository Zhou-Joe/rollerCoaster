import pytest
from app.models.common import (
    ZoneType, FailSafeMode, BrakeState, BoosterMode,
    LoadCase, TrainState, StationType, EquipmentConstraint
)


def test_zone_type_values():
    assert ZoneType.LOAD.value == "load"
    assert ZoneType.UNLOAD.value == "unload"
    assert ZoneType.LAUNCH.value == "launch"
    assert ZoneType.BRAKE.value == "brake"
    assert ZoneType.HOLD.value == "hold"
    assert ZoneType.FREE.value == "free"
    assert ZoneType.MAINTENANCE.value == "maintenance"


def test_fail_safe_mode_values():
    assert FailSafeMode.NORMALLY_OPEN.value == "normally_open"
    assert FailSafeMode.NORMALLY_CLOSED.value == "normally_closed"


def test_brake_state_values():
    assert BrakeState.OPEN.value == "open"
    assert BrakeState.CLOSED.value == "closed"
    assert BrakeState.EMERGENCY_STOP.value == "emergency_stop"


def test_booster_mode_values():
    assert BoosterMode.DRIVE.value == "drive"
    assert BoosterMode.BRAKE.value == "brake"
    assert BoosterMode.IDLE.value == "idle"


def test_load_case_values():
    assert LoadCase.EMPTY.value == "empty"
    assert LoadCase.FULLY_LOADED.value == "fully_loaded"
    assert LoadCase.CUSTOM.value == "custom"


def test_train_state_values():
    assert TrainState.STOPPED.value == "stopped"
    assert TrainState.MOVING.value == "moving"
    assert TrainState.LOADING.value == "loading"
    assert TrainState.UNLOADING.value == "unloading"
    assert TrainState.IN_MAINTENANCE.value == "in_maintenance"


def test_station_type_values():
    assert StationType.LOAD.value == "load"
    assert StationType.UNLOAD.value == "unload"
    assert StationType.TRANSFER.value == "transfer"
    assert StationType.HOLD.value == "hold"


def test_equipment_constraint_defaults():
    constraint = EquipmentConstraint()
    assert constraint.allowed_equipment_types == []
    assert constraint.min_straightness is None
    assert constraint.max_curvature is None


def test_equipment_constraint_with_values():
    constraint = EquipmentConstraint(
        allowed_equipment_types=["lsm_launch", "booster"],
        min_straightness=0.95,
        max_curvature=0.01
    )
    assert constraint.allowed_equipment_types == ["lsm_launch", "booster"]
    assert constraint.min_straightness == 0.95
    assert constraint.max_curvature == 0.01