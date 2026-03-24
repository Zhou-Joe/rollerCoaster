"""Tests for force calculations"""

import pytest
import math
from app.simulation.physics.forces import (
    gravity_force,
    drag_force,
    rolling_resistance_force,
    compute_forces,
)


def test_gravity_force_level():
    """On level ground, gravity contributes no tangential force."""
    force = gravity_force(1000.0, 0.0, 9.81)
    assert force == pytest.approx(0.0, abs=1e-10)


def test_gravity_force_uphill():
    """Going uphill, gravity opposes motion (negative force)."""
    # 30 degree slope
    force = gravity_force(1000.0, math.radians(30), 9.81)
    expected = -1000.0 * 9.81 * math.sin(math.radians(30))
    assert force == pytest.approx(expected, rel=0.01)
    assert force < 0  # Decelerating


def test_gravity_force_downhill():
    """Going downhill, gravity accelerates (negative slope = downhill)."""
    # -30 degree slope (downhill)
    force = gravity_force(1000.0, math.radians(-30), 9.81)
    expected = -1000.0 * 9.81 * math.sin(math.radians(-30))
    assert force == pytest.approx(expected, rel=0.01)
    assert force > 0  # Accelerating


def test_drag_force_stationary():
    """Drag is zero when stationary."""
    force = drag_force(0.0, 0.5, 2.0, 1.225)
    assert force == 0.0


def test_drag_force_opposes_motion():
    """Drag always opposes velocity direction."""
    # Forward motion
    force_forward = drag_force(10.0, 0.5, 2.0, 1.225)
    assert force_forward < 0

    # Backward motion (negative velocity)
    force_backward = drag_force(-10.0, 0.5, 2.0, 1.225)
    assert force_backward > 0

    # Same magnitude
    assert abs(force_forward) == pytest.approx(abs(force_backward))


def test_drag_force_scales_with_velocity_squared():
    """Drag scales with v^2."""
    force_v1 = drag_force(10.0, 0.5, 2.0, 1.225)
    force_v2 = drag_force(20.0, 0.5, 2.0, 1.225)

    # Double velocity should give 4x drag
    assert abs(force_v2) == pytest.approx(4 * abs(force_v1))


def test_rolling_resistance_stationary():
    """Rolling resistance is zero when stationary."""
    force = rolling_resistance_force(1000.0, 0.002, 9.81, 0.0)
    assert force == 0.0


def test_rolling_resistance_opposes_motion():
    """Rolling resistance opposes motion."""
    force_forward = rolling_resistance_force(1000.0, 0.002, 9.81, 10.0)
    assert force_forward < 0

    force_backward = rolling_resistance_force(1000.0, 0.002, 9.81, -10.0)
    assert force_backward > 0


def test_compute_forces_total():
    """Total force should be sum of components."""
    forces = compute_forces(
        mass_kg=1000.0,
        velocity_mps=10.0,
        slope_rad=math.radians(10),
        drag_coefficient=0.5,
        frontal_area_m2=2.0,
        rolling_coefficient=0.002,
        gravity_mps2=9.81,
        air_density_kg_m3=1.225
    )

    expected_total = (
        forces.gravity_tangent_n +
        forces.drag_n +
        forces.rolling_resistance_n +
        forces.equipment_n
    )
    assert forces.total_n == pytest.approx(expected_total)


def test_compute_forces_equipment():
    """Equipment force should be added to total."""
    forces_no_equip = compute_forces(
        mass_kg=1000.0,
        velocity_mps=10.0,
        slope_rad=0.0,
        drag_coefficient=0.5,
        frontal_area_m2=2.0,
        rolling_coefficient=0.002,
        equipment_force_n=0.0
    )

    forces_with_launch = compute_forces(
        mass_kg=1000.0,
        velocity_mps=10.0,
        slope_rad=0.0,
        drag_coefficient=0.5,
        frontal_area_m2=2.0,
        rolling_coefficient=0.002,
        equipment_force_n=5000.0  # 5kN launch force
    )

    diff = forces_with_launch.total_n - forces_no_equip.total_n
    assert diff == pytest.approx(5000.0)