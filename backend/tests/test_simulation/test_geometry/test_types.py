"""Tests for geometry types"""

from app.simulation.geometry.types import (
    SamplePoint, ValidationResult, ValidationIssue, InterpolatedPath
)


def test_sample_point_creation():
    point = SamplePoint(
        s=50.0,
        position=(10.0, 0.0, 5.0),
        tangent=(1.0, 0.0, 0.0),
        normal=(0.0, 0.0, 1.0),
        binormal=(0.0, 1.0, 0.0),
        curvature=0.1,
        radius=10.0,
        slope_deg=5.0,
        bank_deg=15.0
    )
    assert point.s == 50.0
    assert point.position == (10.0, 0.0, 5.0)
    assert point.curvature == 0.1


def test_validation_result_empty():
    result = ValidationResult(is_valid=True)
    assert result.is_valid is True
    assert len(result.errors) == 0
    assert len(result.warnings) == 0


def test_validation_result_with_issues():
    result = ValidationResult(
        is_valid=False,
        errors=[ValidationIssue(
            severity="error",
            path_id="path_001",
            location_s=50.0,
            message="Curvature too high",
            value=0.6
        )],
        warnings=[ValidationIssue(
            severity="warning",
            path_id="path_001",
            location_s=30.0,
            message="Tight radius"
        )]
    )
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert len(result.warnings) == 1


def test_interpolated_path_creation():
    samples = [
        SamplePoint(
            s=0.0, position=(0, 0, 0), tangent=(1, 0, 0),
            normal=(0, 0, 1), binormal=(0, 1, 0),
            curvature=0, radius=float('inf'), slope_deg=0, bank_deg=0
        )
    ]
    path = InterpolatedPath(
        path_id="path_001",
        total_length=100.0,
        samples=samples,
        resolution_m=0.01
    )
    assert path.path_id == "path_001"
    assert path.total_length == 100.0
    assert len(path.samples) == 1
    assert path.resolution_m == 0.01
    assert path.validation.is_valid is True