"""Tests for physics integrator"""

import pytest
from app.models.project import Project, ProjectMetadata, SimulationSettings
from app.models.track import Point, Path
from app.models.train import Vehicle, Train
from app.models.common import LoadCase, TrainState
from app.simulation.geometry import GeometryCache
from app.simulation.physics import (
    PhysicsSimulator,
    compute_train_mass,
    compute_train_length,
)
from app.simulation.physics.types import ForceComponents


@pytest.fixture
def simple_project():
    """Create a simple project with a train on a track."""
    project = Project(metadata=ProjectMetadata(name="Physics Test"))

    # Straight track going downhill
    project.points = [
        Point(id="p1", x=0, y=0, z=20),
        Point(id="p2", x=50, y=0, z=10),
        Point(id="p3", x=100, y=0, z=0),
    ]
    project.paths = [Path(id="track1", point_ids=["p1", "p2", "p3"])]

    # Vehicle and train
    project.vehicles = [
        Vehicle(
            id="v1",
            length_m=2.0,
            dry_mass_kg=500.0,
            capacity=4,
            passenger_mass_per_person_kg=75.0
        )
    ]
    project.trains = [
        Train(
            id="train1",
            vehicle_ids=["v1", "v1", "v1"],  # 3-car train
            current_path_id="track1",
            front_position_s=5.0,
            load_case=LoadCase.EMPTY
        )
    ]

    return project


def test_compute_train_mass_empty():
    """Compute mass of empty train."""
    vehicle = Vehicle(
        id="v1",
        length_m=2.0,
        dry_mass_kg=500.0,
        capacity=4,
        passenger_mass_per_person_kg=75.0
    )
    train = Train(
        id="t1",
        vehicle_ids=["v1", "v1"],
        load_case=LoadCase.EMPTY
    )

    mass = compute_train_mass(train, [vehicle], LoadCase.EMPTY)
    # 2 vehicles * 500kg = 1000kg
    assert mass == pytest.approx(1000.0)


def test_compute_train_mass_loaded():
    """Compute mass of fully loaded train."""
    vehicle = Vehicle(
        id="v1",
        length_m=2.0,
        dry_mass_kg=500.0,
        capacity=4,
        passenger_mass_per_person_kg=75.0
    )
    train = Train(
        id="t1",
        vehicle_ids=["v1", "v1"],
        load_case=LoadCase.FULLY_LOADED
    )

    mass = compute_train_mass(train, [vehicle], LoadCase.FULLY_LOADED)
    # 2 vehicles * 500kg + 2 * 4 passengers * 75kg = 1000 + 600 = 1600kg
    expected = 2 * 500.0 + 2 * 4 * 75.0
    assert mass == pytest.approx(expected)


def test_compute_train_length():
    """Compute train length with coupling gaps."""
    vehicle = Vehicle(id="v1", length_m=5.0, dry_mass_kg=500.0, capacity=4)
    train = Train(
        id="t1",
        vehicle_ids=["v1", "v1", "v1"],  # 3 cars
        coupling_gap_m=0.5
    )

    length = compute_train_length(train, [vehicle])
    # 3 * 5m + 2 * 0.5m gaps = 15 + 1 = 16m
    expected = 3 * 5.0 + 2 * 0.5
    assert length == pytest.approx(expected)


def test_simulator_creates_train_states(simple_project):
    """Simulator initializes train states from project."""
    cache = GeometryCache(simple_project)
    cache.compute_all()

    simulator = PhysicsSimulator(simple_project, cache)

    assert len(simulator.train_states) == 1
    assert "train1" in simulator.train_states

    state = simulator.get_train_state("train1")
    assert state is not None
    assert state.path_id == "track1"
    assert state.velocity_mps == 0.0


def test_simulator_step_advances_time(simple_project):
    """Step should advance simulation time."""
    cache = GeometryCache(simple_project)
    cache.compute_all()

    simulator = PhysicsSimulator(simple_project, cache)

    result = simulator.step(dt=0.01)

    assert result.time_s == pytest.approx(0.01)
    assert simulator.time_s == pytest.approx(0.01)


def test_simulator_train_accelerates_on_downhill(simple_project):
    """Train should accelerate going downhill due to gravity."""
    cache = GeometryCache(simple_project)
    cache.compute_all()

    simulator = PhysicsSimulator(simple_project, cache)
    simulator.set_train_velocity("train1", 1.0)  # Start with small velocity

    # Run for a bit
    for _ in range(100):
        simulator.step(0.01)

    state = simulator.get_train_state("train1")

    # Train should have accelerated (gravity pulling it downhill)
    # Initial velocity 1.0, should increase
    assert state.velocity_mps > 1.0
    # Position should advance
    assert state.s_front_m > 5.0


def test_simulator_train_stops_at_path_end(simple_project):
    """Train should stop at end of path."""
    cache = GeometryCache(simple_project)
    cache.compute_all()

    simulator = PhysicsSimulator(simple_project, cache)

    # Position train near end
    path_length = cache.get_path("track1").total_length
    simulator.set_train_position("train1", "track1", path_length - 1.0)
    simulator.set_train_velocity("train1", 5.0)

    # Run simulation
    for _ in range(100):
        simulator.step(0.01)

    state = simulator.get_train_state("train1")

    # Train should be at or before path end
    assert state.s_front_m <= path_length
    assert state.velocity_mps == pytest.approx(0.0)


def test_simulator_distance_matches_constant_acceleration_kinematics(simple_project, monkeypatch):
    """Distance should advance with v*dt + 0.5*a*dt^2 for a constant step acceleration."""
    cache = GeometryCache(simple_project)
    cache.compute_all()

    simulator = PhysicsSimulator(simple_project, cache)

    monkeypatch.setattr(
        "app.simulation.physics.integrator.compute_forces",
        lambda **kwargs: ForceComponents(total_n=3000.0),
    )

    simulator.set_train_velocity("train1", 0.0)

    simulator.step(1.0)
    state = simulator.get_train_state("train1")

    assert state.acceleration_mps2 == pytest.approx(2.0)
    assert state.velocity_mps == pytest.approx(2.0)
    assert state.s_front_m == pytest.approx(6.0)


def test_simulator_reset(simple_project):
    """Reset should restore initial state."""
    cache = GeometryCache(simple_project)
    cache.compute_all()

    simulator = PhysicsSimulator(simple_project, cache)

    # Run simulation
    simulator.run(1.0)
    assert simulator.time_s > 0

    # Reset
    simulator.reset()

    assert simulator.time_s == 0.0
    assert simulator.train_states["train1"].velocity_mps == 0.0
