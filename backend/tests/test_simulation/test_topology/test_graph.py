"""Tests for TopologyGraph"""

import pytest
from app.models.track import Point, Path
from app.models.topology import Junction
from app.simulation.topology.graph import TopologyGraph


@pytest.fixture
def sample_paths():
    return [
        Path(id="path1", point_ids=["p1", "p2"], length_m=10.0),
        Path(id="path2", point_ids=["p3", "p4"], length_m=15.0),
        Path(id="path3", point_ids=["p5", "p6"], length_m=20.0),
    ]


@pytest.fixture
def sample_junction():
    return Junction(
        id="j1",
        incoming_path_id="path1",
        outgoing_path_ids=["path2", "path3"],
        position_s=10.0
    )


def test_build_graph(sample_paths, sample_junction):
    graph = TopologyGraph()
    graph.build(sample_paths, [sample_junction])

    assert len(graph.paths) == 3
    assert len(graph.junctions) == 1


def test_get_outgoing_paths(sample_paths, sample_junction):
    graph = TopologyGraph()
    graph.build(sample_paths, [sample_junction])

    outgoing = graph.get_outgoing_paths("path1")
    assert len(outgoing) == 2
    assert "path2" in outgoing
    assert "path3" in outgoing


def test_get_incoming_paths(sample_paths, sample_junction):
    graph = TopologyGraph()
    graph.build(sample_paths, [sample_junction])

    incoming = graph.get_incoming_paths("path2")
    assert incoming == ["path1"]


def test_orphan_paths():
    paths = [
        Path(id="path1", point_ids=["p1", "p2"], length_m=10.0),
        Path(id="path2", point_ids=["p3", "p4"], length_m=15.0),
    ]
    junction = Junction(
        id="j1",
        incoming_path_id="path1",
        outgoing_path_ids=["path2"],
        position_s=10.0
    )

    graph = TopologyGraph()
    graph.build(paths, [junction])

    orphans = graph.get_orphan_paths()
    assert len(orphans) == 0