"""Tests for RouteFinder"""

import pytest
from app.models.track import Path
from app.models.topology import Junction
from app.simulation.topology.graph import TopologyGraph
from app.simulation.topology.routing import RouteFinder, check_route_conflicts


@pytest.fixture
def sample_graph():
    paths = [
        Path(id="path1", point_ids=["p1", "p2"], length_m=10.0),
        Path(id="path2", point_ids=["p3", "p4"], length_m=15.0),
        Path(id="path3", point_ids=["p5", "p6"], length_m=20.0),
    ]
    junction = Junction(
        id="j1",
        incoming_path_id="path1",
        outgoing_path_ids=["path2", "path3"],
        position_s=10.0
    )
    graph = TopologyGraph()
    graph.build(paths, [junction])
    return graph


def test_find_route(sample_graph):
    finder = RouteFinder(sample_graph)
    route = finder.find_route("path1", 0.0, "path2", 15.0)

    assert route is not None
    assert route.get_path_sequence() == ["path1", "path2"]
    assert route.total_length == 25.0


def test_find_route_with_switch(sample_graph):
    finder = RouteFinder(sample_graph)

    route = finder.find_route("path1", 0.0, "path2", 15.0, switch_states={"j1": "path2"})
    assert route is not None

    route = finder.find_route("path1", 0.0, "path3", 20.0, switch_states={"j1": "path2"})
    assert route is None


def test_check_route_conflicts():
    from app.simulation.topology.types import Route, RouteStep

    routes = {
        "train1": Route(steps=[RouteStep(path_id="path1", entry_s=0.0, exit_s=10.0)]),
        "train2": Route(steps=[RouteStep(path_id="path1", entry_s=0.0, exit_s=10.0)]),
    }
    positions = {
        "train1": ("path1", 5.0),
        "train2": ("path1", 8.0),
    }

    warnings = check_route_conflicts(routes, positions)
    assert len(warnings) > 0