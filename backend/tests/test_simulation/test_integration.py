"""Integration tests for geometry and topology pipeline"""

import pytest
from app.models.project import Project, ProjectMetadata, SimulationSettings
from app.models.track import Point, Path
from app.models.topology import Junction
from app.simulation.geometry import GeometryCache, GeometryValidator
from app.simulation.topology import TopologyGraph, RouteFinder


@pytest.fixture
def sample_project():
    """Sample project with multiple paths and junctions."""
    project = Project(metadata=ProjectMetadata(name="Test"))

    project.points = [
        Point(id="p1", x=0, y=0, z=0),
        Point(id="p2", x=10, y=0, z=0),
        Point(id="p3", x=20, y=0, z=0),
        Point(id="p4", x=20, y=0, z=0),
        Point(id="p5", x=20, y=10, z=0),
        Point(id="p6", x=20, y=20, z=0),
        Point(id="p7", x=20, y=0, z=5),
        Point(id="p8", x=30, y=0, z=10),
    ]

    project.paths = [
        Path(id="path1", point_ids=["p1", "p2", "p3"]),
        Path(id="path2", point_ids=["p4", "p5", "p6"]),
        Path(id="path3", point_ids=["p7", "p8"]),
    ]

    project.junctions = [
        Junction(id="j1", incoming_path_id="path1", outgoing_path_ids=["path2", "path3"], position_s=20.0)
    ]

    return project


def test_full_geometry_pipeline(sample_project):
    """Test complete geometry computation."""
    cache = GeometryCache(sample_project)
    cache.compute_all()

    for path in sample_project.paths:
        path_data = cache.get_path(path.id)
        assert path_data is not None
        assert path_data.total_length > 0
        assert len(path_data.samples) > 0


def test_topology_routing(sample_project):
    """Test topology and routing together."""
    cache = GeometryCache(sample_project)
    cache.compute_all()

    for path in sample_project.paths:
        path.length_m = cache.get_path(path.id).total_length

    graph = TopologyGraph()
    graph.build(sample_project.paths, sample_project.junctions)

    assert len(graph.paths) == 3

    finder = RouteFinder(graph)
    route = finder.find_route("path1", 0.0, "path2", 20.0)

    assert route is not None
    assert route.get_path_sequence() == ["path1", "path2"]


def test_validation(sample_project):
    """Test validation pipeline."""
    cache = GeometryCache(sample_project)
    cache.compute_all()

    validator = GeometryValidator(sample_project.simulation_settings)
    result = validator.validate_project(cache, sample_project.junctions)

    assert result.is_valid
    assert len(result.errors) == 0


def test_cache_invalidation_integration(sample_project):
    """Test cache invalidation workflow."""
    cache = GeometryCache(sample_project)
    cache.compute_all()

    initial_length = cache.get_path("path1").total_length

    # Simulate point modification by invalidating
    cache.invalidate_points({"p2"})

    # Recompute
    cache.compute_all()
    new_length = cache.get_path("path1").total_length

    assert initial_length == new_length  # Same geometry


def test_route_with_switch_states(sample_project):
    """Test routing respects switch states."""
    cache = GeometryCache(sample_project)
    cache.compute_all()

    for path in sample_project.paths:
        path.length_m = cache.get_path(path.id).total_length

    graph = TopologyGraph()
    graph.build(sample_project.paths, sample_project.junctions)
    finder = RouteFinder(graph)

    # Without switch restriction, should find both routes
    route_to_path2 = finder.find_route("path1", 0.0, "path2", 20.0)
    route_to_path3 = finder.find_route("path1", 0.0, "path3", 15.0)

    assert route_to_path2 is not None
    assert route_to_path3 is not None

    # With switch forced to path2, path3 should not be reachable
    route_blocked = finder.find_route("path1", 0.0, "path3", 15.0, switch_states={"j1": "path2"})
    assert route_blocked is None