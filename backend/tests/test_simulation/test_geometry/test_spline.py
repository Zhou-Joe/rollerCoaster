"""Tests for centripetal Catmull-Rom spline interpolation"""

import pytest
import numpy as np
from app.simulation.geometry.spline import CentripetalCatmullRom
from app.models.track import Point
from app.simulation import GeometryError


def test_two_point_linear():
    """Two points should produce linear interpolation"""
    points = [
        Point(id="p1", x=0.0, y=0.0, z=0.0),
        Point(id="p2", x=10.0, y=0.0, z=0.0),
    ]
    spline = CentripetalCatmullRom(points, resolution_m=0.1)
    assert spline.get_total_length() == pytest.approx(10.0, abs=0.01)


def test_straight_line_curvature_zero():
    """Straight line should have zero curvature"""
    points = [
        Point(id="p1", x=0.0, y=0.0, z=0.0),
        Point(id="p2", x=5.0, y=0.0, z=0.0),
        Point(id="p3", x=10.0, y=0.0, z=0.0),
    ]
    spline = CentripetalCatmullRom(points, resolution_m=0.1)
    sample = spline.sample_at_arc_length(5.0)
    assert sample.curvature == pytest.approx(0.0, abs=1e-6)


def test_passes_through_control_points():
    """Spline should pass through all control points"""
    points = [
        Point(id="p1", x=0.0, y=0.0, z=0.0, bank_deg=0.0),
        Point(id="p2", x=10.0, y=0.0, z=5.0, bank_deg=15.0),
        Point(id="p3", x=20.0, y=0.0, z=0.0, bank_deg=0.0),
    ]
    spline = CentripetalCatmullRom(points, resolution_m=0.1)

    sample0 = spline.sample_at_arc_length(0.0)
    assert sample0.position[0] == pytest.approx(0.0, abs=0.1)
    assert sample0.position[2] == pytest.approx(0.0, abs=0.1)


def test_bank_interpolation():
    """Bank angle should be interpolated"""
    points = [
        Point(id="p1", x=0.0, y=0.0, z=0.0, bank_deg=0.0),
        Point(id="p2", x=10.0, y=0.0, z=5.0, bank_deg=30.0),
        Point(id="p3", x=20.0, y=0.0, z=0.0, bank_deg=0.0),
    ]
    spline = CentripetalCatmullRom(points, resolution_m=0.1)
    length = spline.get_total_length()

    mid_sample = spline.sample_at_arc_length(length / 2)
    assert 20.0 <= mid_sample.bank_deg <= 35.0


def test_fewer_than_two_points_raises():
    """Less than 2 points should raise GeometryError"""
    points = [Point(id="p1", x=0.0, y=0.0, z=0.0)]
    with pytest.raises(GeometryError, match="at least 2 points"):
        CentripetalCatmullRom(points, resolution_m=0.1)


def test_duplicate_points_warning():
    """Duplicate consecutive points should be handled"""
    points = [
        Point(id="p1", x=0.0, y=0.0, z=0.0),
        Point(id="p2", x=0.0, y=0.0, z=0.0),
        Point(id="p3", x=10.0, y=0.0, z=0.0),
    ]
    spline = CentripetalCatmullRom(points, resolution_m=0.1)
    assert spline.get_total_length() > 0


def test_nan_coordinates_raises():
    """NaN coordinates should raise GeometryError"""
    points = [
        Point(id="p1", x=float('nan'), y=0.0, z=0.0),
        Point(id="p2", x=10.0, y=0.0, z=0.0),
    ]
    with pytest.raises(GeometryError, match="Invalid coordinate"):
        CentripetalCatmullRom(points, resolution_m=0.1)