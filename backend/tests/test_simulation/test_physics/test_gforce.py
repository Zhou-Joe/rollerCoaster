"""Tests for g-force calculations"""

import pytest
import math
from app.simulation.physics.gforce import (
    normal_acceleration,
    compute_gforces,
)


def test_normal_acceleration_zero_curvature():
    """On straight track, normal acceleration is zero."""
    acc = normal_acceleration(10.0, 0.0)
    assert acc == 0.0


def test_normal_acceleration_zero_velocity():
    """When stationary, normal acceleration is zero."""
    acc = normal_acceleration(0.0, 0.1)
    assert acc == 0.0


def test_normal_accelervation_formula():
    """Normal acceleration = v^2 * curvature."""
    # 10 m/s, 0.1 1/m curvature (10m radius)
    acc = normal_acceleration(10.0, 0.1)
    expected = 10.0 ** 2 * 0.1
    assert acc == pytest.approx(expected)


def test_normal_acceleration_scales_with_v_squared():
    """Normal acceleration scales with velocity squared."""
    acc_v1 = normal_acceleration(10.0, 0.1)
    acc_v2 = normal_acceleration(20.0, 0.1)

    assert acc_v2 == pytest.approx(4 * acc_v1)


def test_compute_gforces_straight_level():
    """On straight, level track, g-forces should be ~1g normal."""
    gforces = compute_gforces(
        velocity_mps=10.0,
        curvature_per_m=0.0,
        slope_deg=0.0,
        bank_deg=0.0
    )

    # On level track with no curvature, normal g should be ~1g (gravity into seat)
    assert gforces.normal_g == pytest.approx(1.0, abs=0.01)
    assert gforces.lateral_g == pytest.approx(0.0, abs=0.01)


def test_compute_gforces_with_curvature():
    """Curvature adds to normal g-force."""
    gforces_straight = compute_gforces(
        velocity_mps=10.0,
        curvature_per_m=0.0,
        slope_deg=0.0,
        bank_deg=0.0
    )

    gforces_curved = compute_gforces(
        velocity_mps=10.0,
        curvature_per_m=0.1,  # 10m radius
        slope_deg=0.0,
        bank_deg=0.0
    )

    # Curved should have higher normal g
    assert gforces_curved.normal_g > gforces_straight.normal_g


def test_compute_gforces_banked():
    """Banking creates lateral g-force."""
    gforces_flat = compute_gforces(
        velocity_mps=10.0,
        curvature_per_m=0.1,
        slope_deg=0.0,
        bank_deg=0.0
    )

    gforces_banked = compute_gforces(
        velocity_mps=10.0,
        curvature_per_m=0.1,
        slope_deg=0.0,
        bank_deg=30.0  # 30 degree bank
    )

    # Banked should have lateral g-force
    assert abs(gforces_banked.lateral_g) > abs(gforces_flat.lateral_g)


def test_compute_gforces_resultant():
    """Resultant should be magnitude of components."""
    gforces = compute_gforces(
        velocity_mps=20.0,
        curvature_per_m=0.05,
        slope_deg=10.0,
        bank_deg=15.0
    )

    # Resultant = sqrt(normal^2 + lateral^2 + vertical^2)
    import math
    expected = math.sqrt(
        gforces.normal_g ** 2 +
        gforces.lateral_g ** 2 +
        gforces.vertical_g ** 2
    )
    assert gforces.resultant_g == pytest.approx(expected, rel=0.01)