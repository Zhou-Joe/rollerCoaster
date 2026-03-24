"""Tests for GeometryValidator"""

import pytest
from app.models.project import Project, SimulationSettings
from app.models.track import Point, Path
from app.models.topology import Junction
from app.simulation.geometry.cache import GeometryCache
from app.simulation.geometry.validator import GeometryValidator


@pytest.fixture
def sample_project():
    project = Project()
    project.simulation_settings = SimulationSettings()
    project.points = [
        Point(id="p1", x=0.0, y=0.0, z=0.0),
        Point(id="p2", x=10.0, y=0.0, z=0.0),
        Point(id="p3", x=20.0, y=0.0, z=0.0),
    ]
    project.paths = [Path(id="path_001", point_ids=["p1", "p2", "p3"])]
    return project


def test_validate_straight_path(sample_project):
    cache = GeometryCache(sample_project)
    cache.compute_all()
    validator = GeometryValidator(sample_project.simulation_settings)
    result = validator.validate_path("path_001", cache.get_path("path_001"))
    assert result.is_valid
    assert len(result.errors) == 0


def test_validate_curvature_spike():
    project = Project()
    project.simulation_settings = SimulationSettings()
    project.points = [
        Point(id="p1", x=0.0, y=0.0, z=0.0),
        Point(id="p2", x=0.1, y=0.0, z=0.0),
        Point(id="p3", x=0.2, y=0.0, z=0.0),
    ]
    project.paths = [Path(id="path_001", point_ids=["p1", "p2", "p3"])]

    cache = GeometryCache(project)
    cache.compute_all()
    validator = GeometryValidator(project.simulation_settings)
    result = validator.validate_path("path_001", cache.get_path("path_001"))
    # May have curvature warning


def test_validate_junction_loop():
    project = Project()
    project.simulation_settings = SimulationSettings()
    project.points = [
        Point(id="p1", x=0.0, y=0.0, z=0.0),
        Point(id="p2", x=10.0, y=0.0, z=0.0),
    ]
    project.paths = [Path(id="loop", point_ids=["p1", "p2"])]
    project.junctions = [
        Junction(
            id="loop_jct",
            incoming_path_id="loop",
            outgoing_path_ids=["loop"],
            position_s=15.0
        )
    ]

    cache = GeometryCache(project)
    cache.compute_all()
    validator = GeometryValidator(project.simulation_settings)
    result = validator.validate_junction(project.junctions[0], {"loop": cache.get_path("loop")})
    assert not result.is_valid
    assert len(result.errors) > 0