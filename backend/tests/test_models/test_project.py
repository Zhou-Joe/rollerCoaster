from app.models.project import Project, ProjectMetadata, SimulationSettings
from app.models.track import Point, Path


def test_project_metadata_defaults():
    meta = ProjectMetadata()
    assert meta.name == "Untitled Project"
    assert meta.version == 1


def test_simulation_settings_defaults():
    settings = SimulationSettings()
    assert settings.time_step_s == 0.01
    assert settings.gravity_mps2 == 9.81


def test_project_creation():
    project = Project()
    assert project.metadata.name == "Untitled Project"
    assert project.points == []


def test_project_with_data():
    project = Project(
        metadata=ProjectMetadata(name="Test Coaster"),
        points=[Point(id="pt_001", x=0.0, y=0.0, z=0.0)],
        paths=[Path(id="path_001", point_ids=["pt_001"])]
    )
    assert project.metadata.name == "Test Coaster"
    assert len(project.points) == 1


def test_project_json_serialization():
    project = Project(metadata=ProjectMetadata(name="JSON Test"))
    json_str = project.model_dump_json()
    loaded = Project.model_validate_json(json_str)
    assert loaded.metadata.name == "JSON Test"