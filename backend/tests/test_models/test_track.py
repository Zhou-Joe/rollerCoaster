from app.models.track import Point, Path, Section
from app.models.common import ZoneType, EquipmentConstraint


def test_point_creation():
    point = Point(id="pt_001", x=0.0, y=0.0, z=10.0)
    assert point.id == "pt_001"
    assert point.x == 0.0
    assert point.y == 0.0
    assert point.z == 10.0
    assert point.bank_deg == 0.0
    assert point.editable is True


def test_point_with_bank():
    point = Point(id="pt_002", x=10.0, y=0.0, z=15.0, bank_deg=45.0, editable=False)
    assert point.bank_deg == 45.0
    assert point.editable is False


def test_path_creation():
    path = Path(id="path_001", point_ids=["pt_001", "pt_002", "pt_003"])
    assert path.id == "path_001"
    assert len(path.point_ids) == 3
    assert path.length_m is None


def test_path_with_length():
    path = Path(id="path_001", point_ids=["pt_001", "pt_002"], length_m=100.5)
    assert path.length_m == 100.5


def test_section_creation():
    section = Section(
        id="sec_001",
        path_id="path_001",
        start_s=0.0,
        end_s=50.0,
        zone_type=ZoneType.LAUNCH
    )
    assert section.id == "sec_001"
    assert section.path_id == "path_001"
    assert section.zone_type == ZoneType.LAUNCH
    assert section.label is None


def test_section_with_constraints():
    constraint = EquipmentConstraint(allowed_equipment_types=["lsm_launch"])
    section = Section(
        id="sec_001",
        path_id="path_001",
        start_s=0.0,
        end_s=100.0,
        zone_type=ZoneType.BRAKE,
        label="Final Brake Run",
        equipment_constraints=constraint
    )
    assert section.label == "Final Brake Run"
    assert section.equipment_constraints.allowed_equipment_types == ["lsm_launch"]