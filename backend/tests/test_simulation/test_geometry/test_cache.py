"""Tests for GeometryCache"""

import pytest
from app.models.project import Project
from app.models.track import Point, Path
from app.simulation.geometry.cache import GeometryCache


@pytest.fixture
def sample_project():
    project = Project()
    project.points = [
        Point(id="p1", x=0.0, y=0.0, z=0.0),
        Point(id="p2", x=10.0, y=0.0, z=5.0),
        Point(id="p3", x=20.0, y=0.0, z=0.0),
    ]
    project.paths = [Path(id="path_001", point_ids=["p1", "p2", "p3"])]
    return project


def test_cache_creation(sample_project):
    cache = GeometryCache(sample_project)
    assert cache._resolution_m == 0.01


def test_cache_get_path_computes(sample_project):
    cache = GeometryCache(sample_project)
    path_data = cache.get_path("path_001")
    assert path_data.path_id == "path_001"
    assert path_data.total_length > 0
    assert len(path_data.samples) > 0


def test_cache_invalidation(sample_project):
    cache = GeometryCache(sample_project)
    first = cache.get_path("path_001")
    cache.invalidate("path_001")
    second = cache.get_path("path_001")
    assert second.total_length == first.total_length


def test_cache_invalidate_points(sample_project):
    cache = GeometryCache(sample_project)
    cache.get_path("path_001")
    cache.invalidate_points({"p1", "p2"})
    assert "path_001" in cache._dirty


def test_cache_status(sample_project):
    cache = GeometryCache(sample_project)
    status = cache.get_cache_status()
    assert "path_001" in status
    assert status["path_001"]["status"] == "empty"

    cache.get_path("path_001")
    status = cache.get_cache_status()
    assert status["path_001"]["status"] == "computed"

    cache.invalidate("path_001")
    status = cache.get_cache_status()
    assert status["path_001"]["status"] == "dirty"