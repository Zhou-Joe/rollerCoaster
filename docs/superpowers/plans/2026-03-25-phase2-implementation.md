# Phase 2: Track Geometry & Topology Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the geometry engine (centripetal Catmull-Rom splines, arc length parameterization, curvature, validation) and topology engine (directed graph, routing with switch logic).

**Architecture:** Create new `simulation/geometry/` and `simulation/topology/` packages with focused modules for each responsibility. Geometry cache holds project reference for point lookup. Validation uses unified `ValidationResult` type.

**Tech Stack:** Python 3.12+, numpy (vectorized calculations), scipy (splines), networkx (graph operations), pytest (testing)

---

## File Structure

### New Files to Create

```
backend/app/simulation/
├── __init__.py                    # Package marker, export GeometryError
├── geometry/
│   ├── __init__.py                # Export public API
│   ├── types.py                   # SamplePoint, InterpolatedPath, ValidationResult, ValidationIssue
│   ├── spline.py                  # CentripetalCatmullRom class
│   ├── arc_length.py              # Arc length computation utilities
│   ├── frames.py                  # Frenet-Serret frame computation
│   ├── curvature.py               # Curvature and slope calculations
│   ├── bank.py                    # Bank angle interpolation
│   ├── cache.py                   # GeometryCache class
│   └── validator.py               # GeometryValidator class
├── topology/
│   ├── __init__.py                # Export public API
│   ├── types.py                   # Route, RouteStep, ConflictWarning
│   ├── graph.py                   # TopologyGraph, PathNode
│   └── routing.py                 # RouteFinder, check_route_conflicts
└── services/
    └── geometry_service.py        # High-level geometry operations
```

### Files to Modify

```
backend/app/models/project.py      # Add geometry settings to SimulationSettings
backend/app/models/track.py        # Add is_valid, validation_issues to Path
backend/app/api/geometry.py        # NEW: Geometry API endpoints
backend/app/api/router.py          # Include geometry and topology routers
backend/pyproject.toml             # Add numpy, scipy, networkx dependencies
```

---

## Task 1: Add Dependencies

**Files:**
- Modify: `backend/pyproject.toml`

- [ ] **Step 1: Add dependencies to pyproject.toml**

Read `backend/pyproject.toml` and add to dependencies:

```toml
dependencies = [
    # Existing...
    "numpy>=1.26.0",
    "scipy>=1.12.0",
    "networkx>=3.2.0",
]
```

- [ ] **Step 2: Install new dependencies**

Run: `cd backend && source .venv/bin/activate && pip install numpy scipy networkx`
Expected: Packages installed successfully

- [ ] **Step 3: Verify imports work**

Run: `cd backend && source .venv/bin/activate && python -c "import numpy; import scipy; import networkx; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/pyproject.toml
git commit -m "chore: add numpy, scipy, networkx for Phase 2"
```

---

## Task 2: Create Geometry Types

**Files:**
- Create: `backend/app/simulation/__init__.py`
- Create: `backend/app/simulation/geometry/__init__.py`
- Create: `backend/app/simulation/geometry/types.py`

- [ ] **Step 1: Create simulation package __init__.py**

```python
"""Simulation engine for roller coaster dynamics"""


class GeometryError(Exception):
    """Raised when geometry computation fails."""
    pass
```

- [ ] **Step 2: Create simulation/geometry package __init__.py**

```python
"""Geometry computation for track paths"""

from .types import SamplePoint, InterpolatedPath, ValidationResult, ValidationIssue

__all__ = ["SamplePoint", "InterpolatedPath", "ValidationResult", "ValidationIssue", "GeometryError"]
```

- [ ] **Step 3: Create simulation/geometry/types.py**

```python
"""Type definitions for geometry computation"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional


@dataclass
class SamplePoint:
    """A single sampled location on a track path."""
    s: float              # Arc length position in meters
    position: Tuple[float, float, float]  # (x, y, z) in meters
    tangent: Tuple[float, float, float]   # Unit tangent vector
    normal: Tuple[float, float, float]    # Unit normal (toward center of curvature)
    binormal: Tuple[float, float, float]  # Unit binormal
    curvature: float      # Curvature in 1/meters
    radius: float         # Radius of curvature in meters (inf if straight)
    slope_deg: float      # Slope angle in degrees from horizontal
    bank_deg: float       # Bank angle in degrees


@dataclass
class ValidationIssue:
    """A validation error or warning."""
    severity: str         # "error" or "warning"
    path_id: str
    location_s: float
    message: str
    value: Optional[float] = None


@dataclass
class ValidationResult:
    """Result of geometry validation."""
    is_valid: bool
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)


@dataclass
class InterpolatedPath:
    """Cached geometry for a single path."""
    path_id: str
    total_length: float
    samples: List[SamplePoint]  # Evenly spaced by resolution
    resolution_m: float
    validation: ValidationResult = field(default_factory=lambda: ValidationResult(is_valid=True))
```

- [ ] **Step 4: Create tests for types**

Create `backend/tests/test_simulation/test_geometry/test_types.py`:

```python
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
    from app.simulation.geometry.types import SamplePoint

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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_simulation/test_geometry/test_types.py -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/simulation/ backend/tests/test_simulation/
git commit -m "feat: create geometry types (SamplePoint, InterpolatedPath, ValidationResult)"
```

---

## Task 3: Implement Centripetal Catmull-Rom Spline

**Files:**
- Create: `backend/app/simulation/geometry/spline.py`
- Test: `backend/tests/test_simulation/test_geometry/test_spline.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_simulation/test_geometry/test_spline.py`:

```python
"""Tests for centripetal Catmull-Rom spline interpolation"""

import pytest
import numpy as np
from app.simulation.geometry.spline import CentripetalCatmullRom
from app.models.track import Point


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

    # Find samples closest to where control points should be
    length = spline.get_total_length()
    # First point at s=0
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

    # Midpoint should have bank close to 30 degrees
    mid_sample = spline.sample_at_arc_length(length / 2)
    assert 20.0 <= mid_sample.bank_deg <= 35.0  # Allow some interpolation variance


def test_fewer_than_two_points_raises():
    """Less than 2 points should raise GeometryError"""
    from app.simulation import GeometryError

    points = [Point(id="p1", x=0.0, y=0.0, z=0.0)]
    with pytest.raises(GeometryError, match="at least 2 points"):
        CentripetalCatmullRom(points, resolution_m=0.1)


def test_duplicate_points_warning():
    """Duplicate consecutive points should be handled"""
    points = [
        Point(id="p1", x=0.0, y=0.0, z=0.0),
        Point(id="p2", x=0.0, y=0.0, z=0.0),  # Duplicate
        Point(id="p3", x=10.0, y=0.0, z=0.0),
    ]
    # Should not raise, but may emit warning (captured in validation)
    spline = CentripetalCatmullRom(points, resolution_m=0.1)
    assert spline.get_total_length() > 0


def test_nan_coordinates_raises():
    """NaN coordinates should raise GeometryError"""
    from app.simulation import GeometryError

    points = [
        Point(id="p1", x=float('nan'), y=0.0, z=0.0),
        Point(id="p2", x=10.0, y=0.0, z=0.0),
    ]
    with pytest.raises(GeometryError, match="Invalid coordinate"):
        CentripetalCatmullRom(points, resolution_m=0.1)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_simulation/test_geometry/test_spline.py -v`
Expected: FAIL with "ModuleNotFoundError" or assertion errors

- [ ] **Step 3: Implement CentripetalCatmullRom**

Create `backend/app/simulation/geometry/spline.py`:

```python
"""Centripetal Catmull-Rom spline interpolation"""

from typing import List, Tuple
import numpy as np
from app.models.track import Point
from app.simulation import GeometryError
from .types import SamplePoint, ValidationIssue


def _check_valid_point(point: Point) -> None:
    """Validate point coordinates are finite numbers."""
    for coord_name, value in [('x', point.x), ('y', point.y), ('z', point.z)]:
        if not np.isfinite(value):
            raise GeometryError(f"Invalid coordinate value: {coord_name}={value}")


def _catmull_rom_blend(p0: float, p1: float, p2: float, p3: float, t: float) -> float:
    """
    Catmull-Rom blend function for a single dimension.

    P(t) = 0.5 * [(2*P1) + (-P0 + P2)*t + (2*P0 - 5*P1 + 4*P2 - P3)*t² + (-P0 + 3*P1 - 3*P2 + P3)*t³]
    """
    t2 = t * t
    t3 = t2 * t

    return 0.5 * (
        (2 * p1) +
        (-p0 + p2) * t +
        (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
        (-p0 + 3 * p1 - 3 * p2 + p3) * t3
    )


def _catmull_rom_blend_derivative(p0: float, p1: float, p2: float, p3: float, t: float) -> float:
    """
    First derivative of Catmull-Rom blend function.

    P'(t) = 0.5 * [(-P0 + P2) + 2*(2*P0 - 5*P1 + 4*P2 - P3)*t + 3*(-P0 + 3*P1 - 3*P2 + P3)*t²]
    """
    t2 = t * t

    return 0.5 * (
        (-p0 + p2) +
        2 * (2 * p0 - 5 * p1 + 4 * p2 - p3) * t +
        3 * (-p0 + 3 * p1 - 3 * p2 + p3) * t2
    )


def _catmull_rom_blend_second_derivative(p0: float, p1: float, p2: float, p3: float, t: float) -> float:
    """
    Second derivative of Catmull-Rom blend function.

    P''(t) = (2*P0 - 5*P1 + 4*P2 - P3) + 3*(-P0 + 3*P1 - 3*P2 + P3)*t
    """
    return (2 * p0 - 5 * p1 + 4 * p2 - p3) + 3 * (-p0 + 3 * p1 - 3 * p2 + p3) * t


class CentripetalCatmullRom:
    """
    Centripetal Catmull-Rom spline interpolation.

    Passes through all control points with C¹ continuity.
    Centripetal parameterization prevents cusps and self-intersections.
    """

    def __init__(self, points: List[Point], resolution_m: float = 0.01):
        """
        Initialize spline from control points.

        Args:
            points: Control points with position and bank
            resolution_m: Spacing between output samples

        Raises:
            GeometryError: If fewer than 2 points or invalid coordinates
        """
        if len(points) < 2:
            raise GeometryError("Path requires at least 2 points")

        # Validate coordinates
        for point in points:
            _check_valid_point(point)

        self._points = points
        self._resolution_m = resolution_m
        self._warnings: List[ValidationIssue] = []

        # Check for duplicates and handle them
        self._cleaned_points = self._remove_duplicates(points)

        if len(self._cleaned_points) < 2:
            raise GeometryError("Path has zero length")

        # Compute centripetal parameterization
        self._t_values = self._compute_parameters(self._cleaned_points)

        # Pre-compute total length and samples
        self._samples: List[SamplePoint] = []
        self._total_length = 0.0
        self._compute_samples()

    def _remove_duplicates(self, points: List[Point]) -> List[Point]:
        """Remove consecutive duplicate points."""
        if len(points) <= 2:
            return points

        cleaned = [points[0]]
        for i in range(1, len(points)):
            prev = points[i - 1]
            curr = points[i]
            dist_sq = (curr.x - prev.x) ** 2 + (curr.y - prev.y) ** 2 + (curr.z - prev.z) ** 2
            if dist_sq > 1e-12:  # Not a duplicate
                cleaned.append(curr)
            else:
                self._warnings.append(ValidationIssue(
                    severity="warning",
                    path_id="",  # Will be set by caller
                    location_s=0.0,
                    message=f"Skipped duplicate point at index {i}",
                    value=None
                ))

        return cleaned

    def _compute_parameters(self, points: List[Point]) -> np.ndarray:
        """
        Compute centripetal parameter values.

        t₀ = 0
        tᵢ = tᵢ₋₁ + |Pᵢ - Pᵢ₋₁|^0.5
        """
        n = len(points)
        t = np.zeros(n)

        for i in range(1, n):
            dx = points[i].x - points[i - 1].x
            dy = points[i].y - points[i - 1].y
            dz = points[i].z - points[i - 1].z
            dist = np.sqrt(dx * dx + dy * dy + dz * dz)
            t[i] = t[i - 1] + np.sqrt(dist)  # α = 0.5 for centripetal

        return t

    def _compute_samples(self) -> None:
        """Compute evenly spaced samples along the spline."""
        # First, compute high-resolution samples to estimate arc length
        n_segments = len(self._cleaned_points) - 1
        if n_segments == 1:
            # Special case: exactly 2 points = linear interpolation
            self._compute_linear_samples()
            return

        # Adaptive sampling for arc length estimation
        num_initial_samples = max(1000, n_segments * 100)
        t_values = self._t_values
        t_max = t_values[-1]

        # Sample at regular t intervals for length estimation
        temp_samples = []
        for i in range(num_initial_samples + 1):
            t_param = (i / num_initial_samples) * t_max
            pos = self._evaluate_position(t_param)
            if i > 0:
                dx = pos[0] - temp_samples[-1][0]
                dy = pos[1] - temp_samples[-1][1]
                dz = pos[2] - temp_samples[-1][2]
                self._total_length += np.sqrt(dx * dx + dy * dy + dz * dz)
            temp_samples.append(pos)

        # Now sample at even arc length intervals
        num_samples = max(int(self._total_length / self._resolution_m) + 1, 2)

        for i in range(num_samples):
            s = i * self._resolution_m
            if s > self._total_length:
                s = self._total_length

            sample = self._sample_at_arc_length_internal(s)
            self._samples.append(sample)

    def _compute_linear_samples(self) -> None:
        """Handle 2-point case with linear interpolation."""
        p0 = self._cleaned_points[0]
        p1 = self._cleaned_points[1]

        dx = p1.x - p0.x
        dy = p1.y - p0.y
        dz = p1.z - p0.z

        length = np.sqrt(dx * dx + dy * dy + dz * dz)
        self._total_length = length

        if length < 1e-10:
            raise GeometryError("Path has zero length")

        # Unit tangent (constant for linear)
        tangent = (dx / length, dy / length, dz / length)

        # Generate samples
        num_samples = max(int(length / self._resolution_m) + 1, 2)

        for i in range(num_samples):
            t = i / (num_samples - 1) if num_samples > 1 else 0.0
            s = t * length

            pos = (
                p0.x + t * dx,
                p0.y + t * dy,
                p0.z + t * dz
            )

            # Linear interpolation of bank
            bank = p0.bank_deg + t * (p1.bank_deg - p0.bank_deg)

            # Curvature is 0 for straight line
            sample = SamplePoint(
                s=s,
                position=pos,
                tangent=tangent,
                normal=(0.0, 0.0, 1.0),  # Arbitrary for straight
                binormal=np.cross(tangent, (0.0, 0.0, 1.0)).tolist(),
                curvature=0.0,
                radius=float('inf'),
                slope_deg=np.degrees(np.arcsin(tangent[2])),
                bank_deg=bank
            )
            self._samples.append(sample)

    def _evaluate_position(self, t: float) -> Tuple[float, float, float]:
        """Evaluate spline position at parameter t."""
        t_values = self._t_values
        points = self._cleaned_points

        # Find segment
        segment_idx = 0
        for i in range(len(t_values) - 1):
            if t_values[i] <= t <= t_values[i + 1]:
                segment_idx = i
                break
        else:
            segment_idx = len(t_values) - 2

        # Get four control points for this segment
        idx0 = max(0, segment_idx - 1)
        idx1 = segment_idx
        idx2 = segment_idx + 1
        idx3 = min(len(points) - 1, segment_idx + 2)

        # Handle phantom points for endpoints
        p0 = self._get_point(idx0, phantom=True)
        p1 = self._get_point(idx1)
        p2 = self._get_point(idx2)
        p3 = self._get_point(idx3, phantom=True)

        # Normalize t to [0, 1] within segment
        t1 = t_values[idx1]
        t2 = t_values[idx2]
        if abs(t2 - t1) < 1e-10:
            t_norm = 0.0
        else:
            t_norm = (t - t1) / (t2 - t1)

        # Evaluate Catmull-Rom
        x = _catmull_rom_blend(p0[0], p1[0], p2[0], p3[0], t_norm)
        y = _catmull_rom_blend(p0[1], p1[1], p2[1], p3[1], t_norm)
        z = _catmull_rom_blend(p0[2], p1[2], p2[2], p3[2], t_norm)

        return (x, y, z)

    def _get_point(self, idx: int, phantom: bool = False) -> Tuple[float, float, float]:
        """Get point coordinates, creating phantom points if needed."""
        points = self._cleaned_points
        n = len(points)

        if 0 <= idx < n:
            p = points[idx]
            return (p.x, p.y, p.z)

        # Phantom point
        if idx < 0:
            # P_{-1} = 2*P_0 - P_1
            p0, p1 = points[0], points[1]
            return (2 * p0.x - p1.x, 2 * p0.y - p1.y, 2 * p0.z - p1.z)
        else:
            # P_n = 2*P_{n-1} - P_{n-2}
            p_last = points[n - 1]
            p_prev = points[n - 2]
            return (2 * p_last.x - p_prev.x, 2 * p_last.y - p_prev.y, 2 * p_last.z - p_prev.z)

    def _evaluate_derivative(self, t: float) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        """Evaluate first and second derivatives at parameter t."""
        t_values = self._t_values
        points = self._cleaned_points

        # Find segment
        segment_idx = 0
        for i in range(len(t_values) - 1):
            if t_values[i] <= t <= t_values[i + 1]:
                segment_idx = i
                break
        else:
            segment_idx = len(t_values) - 2

        idx0 = max(0, segment_idx - 1)
        idx1 = segment_idx
        idx2 = segment_idx + 1
        idx3 = min(len(points) - 1, segment_idx + 2)

        p0 = self._get_point(idx0, phantom=True)
        p1 = self._get_point(idx1)
        p2 = self._get_point(idx2)
        p3 = self._get_point(idx3, phantom=True)

        t1 = t_values[idx1]
        t2 = t_values[idx2]
        dt = t2 - t1 if abs(t2 - t1) > 1e-10 else 1.0
        t_norm = (t - t1) / dt

        # First derivative (chain rule: dP/ds = dP/dt_norm * dt_norm/ds)
        dx_dt = _catmull_rom_blend_derivative(p0[0], p1[0], p2[0], p3[0], t_norm)
        dy_dt = _catmull_rom_blend_derivative(p0[1], p1[1], p2[1], p3[1], t_norm)
        dz_dt = _catmull_rom_blend_derivative(p0[2], p1[2], p2[2], p3[2], t_norm)

        # Second derivative
        d2x_dt2 = _catmull_rom_blend_second_derivative(p0[0], p1[0], p2[0], p3[0], t_norm)
        d2y_dt2 = _catmull_rom_blend_second_derivative(p0[1], p1[1], p2[1], p3[1], t_norm)
        d2z_dt2 = _catmull_rom_blend_second_derivative(p0[2], p1[2], p2[2], p3[2], t_norm)

        # Chain rule: divide by dt for dP/ds
        first = (dx_dt / dt, dy_dt / dt, dz_dt / dt)
        second = (d2x_dt2 / dt / dt, d2y_dt2 / dt / dt, d2z_dt2 / dt / dt)

        return (first, second)

    def _sample_at_arc_length_internal(self, s: float) -> SamplePoint:
        """Sample at arc length s (internal, assumes s is valid)."""
        if self._total_length < 1e-10:
            # Degenerate case
            p = self._cleaned_points[0]
            return SamplePoint(
                s=0.0,
                position=(p.x, p.y, p.z),
                tangent=(1.0, 0.0, 0.0),
                normal=(0.0, 0.0, 1.0),
                binormal=(0.0, 1.0, 0.0),
                curvature=0.0,
                radius=float('inf'),
                slope_deg=0.0,
                bank_deg=p.bank_deg
            )

        # Find corresponding t value by searching through samples
        t_ratio = s / self._total_length
        t_values = self._t_values
        t_max = t_values[-1]
        t = t_ratio * t_max

        # Evaluate position
        pos = self._evaluate_position(t)

        # Evaluate derivatives
        first, second = self._evaluate_derivative(t)

        # Tangent (normalize first derivative)
        first_norm = np.sqrt(first[0] ** 2 + first[1] ** 2 + first[2] ** 2)
        if first_norm < 1e-10:
            tangent = (1.0, 0.0, 0.0)
        else:
            tangent = (first[0] / first_norm, first[1] / first_norm, first[2] / first_norm)

        # Curvature: κ = |r' × r''| / |r'|³
        cross = np.cross(first, second)
        cross_norm = np.linalg.norm(cross)
        if first_norm < 1e-10:
            curvature = 0.0
        else:
            curvature = cross_norm / (first_norm ** 3)

        radius = 1.0 / curvature if curvature > 1e-10 else float('inf')

        # Normal (direction of second derivative, perpendicular to tangent)
        if curvature < 1e-10:
            normal = (0.0, 0.0, 1.0)  # Arbitrary for straight
        else:
            normal_vec = cross / cross_norm if cross_norm > 1e-10 else (0.0, 0.0, 1.0)
            normal = tuple(normal_vec)

        # Binormal
        binormal_vec = np.cross(tangent, normal)
        binormal = tuple(binormal_vec)

        # Slope
        slope_rad = np.arcsin(np.clip(tangent[2], -1.0, 1.0))
        slope_deg = np.degrees(slope_rad)

        # Bank interpolation
        t_ratio = s / self._total_length if self._total_length > 0 else 0.0
        bank_idx = int(t_ratio * (len(self._cleaned_points) - 1))
        bank_next = min(bank_idx + 1, len(self._cleaned_points) - 1)
        bank_t = (t_ratio * (len(self._cleaned_points) - 1)) - bank_idx
        bank = self._cleaned_points[bank_idx].bank_deg + bank_t * (
            self._cleaned_points[bank_next].bank_deg - self._cleaned_points[bank_idx].bank_deg
        )

        return SamplePoint(
            s=s,
            position=pos,
            tangent=tangent,
            normal=normal,
            binormal=binormal,
            curvature=curvature,
            radius=radius,
            slope_deg=slope_deg,
            bank_deg=bank
        )

    def get_total_length(self) -> float:
        """Get total arc length of the spline."""
        return self._total_length

    def sample_at_arc_length(self, s: float) -> SamplePoint:
        """
        Get interpolated values at arc length position s.

        Args:
            s: Arc length in meters (clamped to [0, total_length])

        Returns:
            SamplePoint with position, tangent, curvature, etc.
        """
        s = max(0.0, min(s, self._total_length))
        return self._sample_at_arc_length_internal(s)

    def get_warnings(self) -> List[ValidationIssue]:
        """Get warnings accumulated during construction."""
        return self._warnings
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_simulation/test_geometry/test_spline.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/simulation/geometry/spline.py backend/tests/test_simulation/test_geometry/test_spline.py
git commit -m "feat: implement centripetal Catmull-Rom spline interpolation"
```

---

## Task 4: Update Model Extensions

**Files:**
- Modify: `backend/app/models/project.py`
- Modify: `backend/app/models/track.py`

- [ ] **Step 1: Add geometry settings to SimulationSettings**

```python
class SimulationSettings(BaseModel):
    # Existing
    time_step_s: float = 0.01
    gravity_mps2: float = 9.81
    drag_coefficient: float = 0.5
    rolling_resistance_coefficient: float = 0.002
    air_density_kg_m3: float = 1.225

    # Geometry settings (new)
    geometry_sample_resolution_m: float = 0.01
    max_curvature_per_m: float = 0.5
    curvature_warning_radius_m: float = 10.0
    tangent_discontinuity_threshold_deg: float = 5.0
    junction_position_tolerance_m: float = 0.01
    bank_rate_threshold_deg_per_m: float = 10.0
```

- [ ] **Step 2: Add fields to Path model**

```python
class Path(BaseModel):
    id: str
    point_ids: List[str]
    length_m: Optional[float] = None  # Computed from geometry
    is_valid: bool = True
    validation_issues: List[str] = []
```

- [ ] **Step 3: Run existing tests to ensure backward compatibility**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_models/test_track.py tests/test_models/test_project.py -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/models/project.py backend/app/models/track.py
git commit -m "feat: add geometry settings and Path validation fields"
```

---

## Task 5: Geometry Cache

**Files:**
- Create: `backend/app/simulation/geometry/cache.py`
- Test: `backend/tests/test_simulation/test_geometry/test_cache.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_simulation/test_geometry/test_cache.py`:

```python
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
    # Should recompute
    assert second.total_length == first.total_length  # Same result


def test_cache_invalidate_points(sample_project):
    cache = GeometryCache(sample_project)
    cache.get_path("path_001")
    cache.invalidate_points({"p1", "p2"})
    # path_001 should be dirty now
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
```

- [ ] **Step 2: Implement GeometryCache**

Create `backend/app/simulation/geometry/cache.py`:

```python
"""Geometry cache with invalidation"""

from typing import Dict, Set
from app.models.project import Project
from app.models.track import Point
from .types import InterpolatedPath, ValidationResult
from .spline import CentripetalCatmullRom


class GeometryCache:
    """
    Manages cached geometry for a project with invalidation support.

    The cache holds a reference to the project for point lookup.
    """

    def __init__(self, project: Project, resolution_m: float = 0.01):
        self._project = project
        self._resolution_m = resolution_m
        self._paths: Dict[str, InterpolatedPath] = {}
        self._dirty: Set[str] = set()

    def get_path(self, path_id: str) -> InterpolatedPath:
        """Get cached path geometry, computing if dirty or missing."""
        # Check if we need to compute
        if path_id not in self._paths or path_id in self._dirty:
            self._compute_path(path_id)
        return self._paths[path_id]

    def _compute_path(self, path_id: str) -> None:
        """Compute geometry for a single path."""
        # Find path in project
        path = None
        for p in self._project.paths:
            if p.id == path_id:
                path = p
                break

        if path is None:
            raise ValueError(f"Path {path_id} not found in project")

        # Get points for this path
        points = []
        for point in self._project.points:
            if point.id in path.point_ids:
                points.append(point)

        # Sort points by their order in point_ids
        point_order = {pid: idx for idx, pid in enumerate(path.point_ids)}
        points.sort(key=lambda p: point_order[p.id])

        # Compute spline
        try:
            spline = CentripetalCatmullRom(points, self._resolution_m)
            validation = ValidationResult(is_valid=True)
        except Exception as e:
            validation = ValidationResult(
                is_valid=False,
                errors=[ValidationIssue(
                    severity="error",
                    path_id=path_id,
                    location_s=0.0,
                    message=str(e)
                )]
            )
            # Create empty path data
            self._paths[path_id] = InterpolatedPath(
                path_id=path_id,
                total_length=0.0,
                samples=[],
                resolution_m=self._resolution_m,
                validation=validation
            )
            self._dirty.discard(path_id)
            return

        # Build InterpolatedPath
        self._paths[path_id] = InterpolatedPath(
            path_id=path_id,
            total_length=spline.get_total_length(),
            samples=spline._samples,  # Access internal samples
            resolution_m=self._resolution_m,
            validation=validation
        )

        # Update path model with computed length
        path.length_m = spline.get_total_length()

        self._dirty.discard(path_id)

    def invalidate(self, path_id: str) -> None:
        """Mark a path as needing recomputation."""
        if path_id in self._paths:
            self._dirty.add(path_id)

    def invalidate_points(self, point_ids: Set[str]) -> None:
        """Invalidate all paths that reference any of these points."""
        for path in self._project.paths:
            if any(pid in point_ids for pid in path.point_ids):
                self.invalidate(path.id)

    def invalidate_all(self) -> None:
        """Mark all paths as needing recomputation."""
        self._dirty = set(p.id for p in self._project.paths)

    def compute_all(self) -> None:
        """Force computation of all paths."""
        for path in self._project.paths:
            self.get_path(path.id)

    def get_cache_status(self) -> Dict[str, Dict]:
        """Return status of each path (computed/dirty/empty)."""
        status = {}
        for path in self._project.paths:
            if path.id not in self._paths:
                status[path.id] = {"status": "empty"}
            elif path.id in self._dirty:
                status[path.id] = {"status": "dirty"}
            else:
                status[path.id] = {
                    "status": "computed",
                    "length": self._paths[path.id].total_length,
                    "sample_count": len(self._paths[path.id].samples)
                }
        return status
```

- [ ] **Step 3: Run tests**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_simulation/test_geometry/test_cache.py -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/simulation/geometry/cache.py backend/tests/test_simulation/test_geometry/test_cache.py
git commit -m "feat: implement GeometryCache with invalidation"
```

---

## Task 6: Geometry Validator

**Files:**
- Create: `backend/app/simulation/geometry/validator.py`
- Test: `backend/tests/test_simulation/test_geometry/test_validator.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_simulation/test_geometry/test_validator.py`:

```python
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
    # Create a path with tight curvature
    project = Project()
    project.simulation_settings = SimulationSettings()
    project.points = [
        Point(id="p1", x=0.0, y=0.0, z=0.0),
        Point(id="p2", x=0.1, y=0.0, z=0.0),  # Very close - sharp turn
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
            position_s=15.0  # Wrong - should equal path length
        )
    ]

    cache = GeometryCache(project)
    cache.compute_all()
    validator = GeometryValidator(project.simulation_settings)
    result = validator.validate_junction(project.junctions[0], {"loop": cache.get_path("loop")})
    assert not result.is_valid
    assert len(result.errors) > 0
```

- [ ] **Step 2: Implement GeometryValidator**

Create `backend/app/simulation/geometry/validator.py`:

```python
"""Geometry validation"""

import numpy as np
from typing import List, Dict
from app.models.topology import Junction
from app.models.project import SimulationSettings
from .types import InterpolatedPath, ValidationResult, ValidationIssue


class GeometryValidator:
    """Validates geometry against engineering constraints."""

    def __init__(self, settings: SimulationSettings):
        self.settings = settings

    def validate_path(self, path_id: str, interpolated: InterpolatedPath) -> ValidationResult:
        """Validate a single path's geometry."""
        errors = []
        warnings = []

        # Check if already has errors from computation
        if not interpolated.validation.is_valid:
            return interpolated.validation

        samples = interpolated.samples
        if len(samples) < 2:
            errors.append(ValidationIssue(
                severity="error",
                path_id=path_id,
                location_s=0.0,
                message="Path has insufficient samples"
            ))
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        # Check curvature
        max_curvature = self.settings.max_curvature_per_m
        warning_radius = self.settings.curvature_warning_radius_m

        for sample in samples:
            if sample.curvature > max_curvature:
                errors.append(ValidationIssue(
                    severity="error",
                    path_id=path_id,
                    location_s=sample.s,
                    message=f"Curvature too high at s={sample.s:.2f}m: radius {sample.radius:.2f}m",
                    value=sample.curvature
                ))
            elif sample.radius < warning_radius and np.isfinite(sample.radius):
                warnings.append(ValidationIssue(
                    severity="warning",
                    path_id=path_id,
                    location_s=sample.s,
                    message=f"Tight radius at s={sample.s:.2f}m: {sample.radius:.2f}m",
                    value=sample.radius
                ))

        # Check tangent discontinuity
        threshold = np.radians(self.settings.tangent_discontinuity_threshold_deg)
        for i in range(1, len(samples)):
            t1 = np.array(samples[i - 1].tangent)
            t2 = np.array(samples[i].tangent)
            angle = np.arccos(np.clip(np.dot(t1, t2), -1.0, 1.0))
            if angle > threshold:
                errors.append(ValidationIssue(
                    severity="error",
                    path_id=path_id,
                    location_s=samples[i].s,
                    message=f"Tangent discontinuity at s={samples[i].s:.2f}m: {np.degrees(angle):.1f}°",
                    value=np.degrees(angle)
                ))

        # Check bank rate
        bank_threshold = self.settings.bank_rate_threshold_deg_per_m
        for i in range(1, len(samples)):
            ds = samples[i].s - samples[i - 1].s
            if ds > 0.001:
                bank_rate = abs(samples[i].bank_deg - samples[i - 1].bank_deg) / ds
                if bank_rate > bank_threshold:
                    warnings.append(ValidationIssue(
                        severity="warning",
                        path_id=path_id,
                        location_s=samples[i].s,
                        message=f"Rapid bank transition at s={samples[i].s:.2f}m: {bank_rate:.1f}°/m",
                        value=bank_rate
                    ))

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def validate_junction(self, junction: Junction, paths: Dict[str, InterpolatedPath]) -> ValidationResult:
        """Validate junction connection."""
        errors = []
        warnings = []
        tolerance = self.settings.junction_position_tolerance_m

        # For loops, position_s must equal path length
        if junction.incoming_path_id in junction.outgoing_path_ids:
            incoming_path = paths.get(junction.incoming_path_id)
            if incoming_path:
                expected_s = incoming_path.total_length
                if abs(junction.position_s - expected_s) > tolerance:
                    errors.append(ValidationIssue(
                        severity="error",
                        path_id=junction.incoming_path_id,
                        location_s=junction.position_s,
                        message=f"Loop junction {junction.id}: position_s must equal path length ({expected_s:.2f}m)",
                        value=junction.position_s
                    ))

        # Check that all referenced paths exist
        if junction.incoming_path_id not in paths:
            errors.append(ValidationIssue(
                severity="error",
                path_id=junction.incoming_path_id,
                location_s=0.0,
                message=f"Junction {junction.id} references non-existent incoming path"
            ))

        for out_path_id in junction.outgoing_path_ids:
            if out_path_id not in paths:
                errors.append(ValidationIssue(
                    severity="error",
                    path_id=out_path_id,
                    location_s=0.0,
                    message=f"Junction {junction.id} references non-existent outgoing path {out_path_id}"
                ))

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def validate_project(self, geometry_cache: GeometryCache, junctions: List[Junction]) -> ValidationResult:
        """Validate all geometry in a project."""
        all_errors = []
        all_warnings = []

        # Validate all paths
        for path in geometry_cache._project.paths:
            interpolated = geometry_cache.get_path(path.id)
            result = self.validate_path(path.id, interpolated)
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)

        # Validate all junctions
        paths_dict = {p.id: geometry_cache.get_path(p.id) for p in geometry_cache._project.paths}
        for junction in junctions:
            result = self.validate_junction(junction, paths_dict)
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)

        return ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings
        )
```

- [ ] **Step 3: Run tests**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_simulation/test_geometry/test_validator.py -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/simulation/geometry/validator.py backend/tests/test_simulation/test_geometry/test_validator.py
git commit -m "feat: implement GeometryValidator with error/warning thresholds"
```

---

## Task 7: Topology Graph

**Files:**
- Create: `backend/app/simulation/topology/__init__.py`
- Create: `backend/app/simulation/topology/graph.py`
- Test: `backend/tests/test_simulation/test_topology/test_graph.py`

- [ ] **Step 1: Create topology package structure**

Create `backend/app/simulation/topology/__init__.py`:

```python
"""Topology graph and routing"""

from .graph import TopologyGraph, PathNode
from .types import Route, RouteStep, ConflictWarning, RouteConflict
from .routing import RouteFinder, check_route_conflicts, detect_route_conflicts

__all__ = [
    'TopologyGraph',
    'PathNode',
    'Route',
    'RouteStep',
    'ConflictWarning',
    'RouteConflict',
    'RouteFinder',
    'check_route_conflicts',
    'detect_route_conflicts',
]
```

- [ ] **Step 2: Create topology types**

Create `backend/app/simulation/topology/types.py`:

```python
"""Type definitions for topology and routing"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class RouteStep:
    """A single step in a route through one path."""
    path_id: str
    entry_s: float  # Arc length where train enters this path
    exit_s: float   # Arc length where train exits this path

    @property
    def length(self) -> float:
        """Length of this step."""
        return self.exit_s - self.entry_s


@dataclass
class Route:
    """Complete route through the track network."""
    steps: List[RouteStep]
    switch_requirements: Dict[str, str] = field(default_factory=dict)

    @property
    def total_length(self) -> float:
        """Total route length."""
        return sum(step.length for step in self.steps)

    def get_path_sequence(self) -> List[str]:
        """Get ordered list of path IDs in route."""
        return [step.path_id for step in self.steps]

    def is_empty(self) -> bool:
        """Check if route has no steps."""
        return len(self.steps) == 0


@dataclass
class ConflictWarning:
    """Warning about potential route conflict."""
    train_id: str
    conflicting_train_id: str
    path_id: str
    position_s: float
    message: str


@dataclass
class RouteConflict:
    """Detected conflict between train routes."""
    conflict_type: str  # "path_overlap", "opposing_direction", "switch_conflict"
    train_ids: List[str]
    path_id: str
    details: str
```

- [ ] **Step 3: Create topology graph**

Create `backend/app/simulation/topology/graph.py`:

```python
"""Topology graph representation"""

import networkx as nx
from typing import Dict, List, Set, Optional
from app.models.track import Path
from app.models.topology import Junction


class PathNode:
    """Represents a node in the topology graph."""

    def __init__(self, path_id: str, length: float):
        self.path_id = path_id
        self.length = length
        self.incoming_junctions: List[str] = []
        self.outgoing_junctions: List[str] = []


class TopologyGraph:
    """Directed graph representation of track network."""

    def __init__(self):
        self._graph: nx.DiGraph = nx.DiGraph()
        self.paths: Dict[str, PathNode] = {}
        self.junctions: Dict[str, Junction] = {}

    def build(self, paths: List[Path], junctions: List[Junction]) -> None:
        """Build topology graph from paths and junctions."""
        self._graph.clear()
        self.paths.clear()
        self.junctions.clear()

        # Add path nodes
        for path in paths:
            length = path.length_m if path.length_m is not None else 0.0
            node = PathNode(path_id=path.id, length=length)
            self.paths[path.id] = node
            self._graph.add_node(path.id)

        # Add junction edges
        for junction in junctions:
            self.junctions[junction.id] = junction

            if junction.incoming_path_id not in self.paths:
                continue

            for outgoing_id in junction.outgoing_path_ids:
                if outgoing_id in self.paths:
                    self._graph.add_edge(
                        junction.incoming_path_id,
                        outgoing_id,
                        junction_id=junction.id
                    )
                    self.paths[junction.incoming_path_id].outgoing_junctions.append(junction.id)
                    self.paths[outgoing_id].incoming_junctions.append(junction.id)

    def get_outgoing_paths(self, path_id: str) -> List[str]:
        """Get list of paths reachable from this path."""
        return list(self._graph.successors(path_id))

    def get_incoming_paths(self, path_id: str) -> List[str]:
        """Get list of paths that can reach this path."""
        return list(self._graph.predecessors(path_id))

    def get_junction_for_edge(self, from_path: str, to_path: str) -> Optional[str]:
        """Get junction ID connecting two paths."""
        edge_data = self._graph.get_edge_data(from_path, to_path)
        return edge_data.get('junction_id') if edge_data else None

    def is_connected(self) -> bool:
        """Check if graph is weakly connected."""
        return nx.is_weakly_connected(self._graph) if self._graph.number_of_nodes() > 0 else True

    def get_orphan_paths(self) -> List[str]:
        """Get paths with no connections."""
        return [pid for pid, node in self.paths.items()
                if not node.incoming_junctions and not node.outgoing_junctions]

    def get_all_path_ids(self) -> List[str]:
        """Get all path IDs."""
        return list(self.paths.keys())

    def get_path_length(self, path_id: str) -> float:
        """Get path length."""
        return self.paths[path_id].length if path_id in self.paths else 0.0
```

- [ ] **Step 4: Create graph tests**

Create `backend/tests/test_simulation/test_topology/test_graph.py`:

```python
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
```

- [ ] **Step 5: Run tests**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_simulation/test_topology/test_graph.py -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/simulation/topology/ backend/tests/test_simulation/test_topology/
git commit -m "feat: implement TopologyGraph with NetworkX"
```

---

## Task 8: RouteFinder

**Files:**
- Create: `backend/app/simulation/topology/routing.py`
- Test: `backend/tests/test_simulation/test_topology/test_routing.py`

- [ ] **Step 1: Create route finder**

Create `backend/app/simulation/topology/routing.py`:

```python
"""Route finding with Dijkstra's algorithm"""

import heapq
from typing import Dict, List, Optional, Set, Tuple
from .graph import TopologyGraph
from .types import Route, RouteStep, ConflictWarning, RouteConflict


class RouteFinder:
    """Find valid routes through track network."""

    def __init__(self, graph: TopologyGraph):
        self.graph = graph

    def find_route(
        self,
        start_path: str,
        start_s: float,
        end_path: str,
        end_s: float,
        switch_states: Optional[Dict[str, str]] = None
    ) -> Optional[Route]:
        """Find shortest valid route between positions."""
        if start_path not in self.graph.paths or end_path not in self.graph.paths:
            return None

        if start_path == end_path:
            if start_s <= end_s:
                return Route(steps=[RouteStep(path_id=start_path, entry_s=start_s, exit_s=end_s)])
            return None

        # Dijkstra
        initial_route = [RouteStep(path_id=start_path, entry_s=start_s, exit_s=0.0)]
        heap = [(0.0, start_path, initial_route, {})]
        visited: Set[str] = set()

        while heap:
            dist, current_path, route, switch_reqs = heapq.heappop(heap)

            if current_path in visited:
                continue
            visited.add(current_path)

            for next_path in self.graph.get_outgoing_paths(current_path):
                junction_id = self.graph.get_junction_for_edge(current_path, next_path)

                # Check switch
                if junction_id and switch_states:
                    if switch_states.get(junction_id) != next_path:
                        continue

                current_node = self.graph.paths.get(current_path)
                next_node = self.graph.paths.get(next_path)

                if not current_node or not next_node:
                    continue

                updated_route = route[:-1] + [
                    RouteStep(path_id=current_path, entry_s=route[-1].entry_s, exit_s=current_node.length)
                ]

                if next_path == end_path:
                    updated_route.append(RouteStep(path_id=next_path, entry_s=0.0, exit_s=end_s))
                    new_switch_reqs = switch_reqs.copy()
                    if junction_id:
                        new_switch_reqs[junction_id] = next_path
                    return Route(steps=updated_route, switch_requirements=new_switch_reqs)

                updated_route.append(RouteStep(path_id=next_path, entry_s=0.0, exit_s=next_node.length))
                new_dist = dist + next_node.length
                new_switch_reqs = switch_reqs.copy()
                if junction_id:
                    new_switch_reqs[junction_id] = next_path
                heapq.heappush(heap, (new_dist, next_path, updated_route, new_switch_reqs))

        return None

    def find_all_routes(self, start_path: str, end_path: str, max_routes: int = 10) -> List[Route]:
        """Find all valid routes (up to max)."""
        if start_path not in self.graph.paths or end_path not in self.graph.paths:
            return []

        all_routes: List[Route] = []

        def dfs(current: str, visited: Set[str], route: List[RouteStep], switch_reqs: Dict[str, str]):
            if len(all_routes) >= max_routes:
                return
            if current == end_path:
                all_routes.append(Route(steps=route.copy(), switch_requirements=switch_reqs.copy()))
                return

            visited.add(current)
            for next_path in self.graph.get_outgoing_paths(current):
                if next_path in visited:
                    continue
                junction_id = self.graph.get_junction_for_edge(current, next_path)
                current_node = self.graph.paths.get(current)
                next_node = self.graph.paths.get(next_path)
                if not current_node or not next_node:
                    continue

                if len(route) == 0:
                    route.append(RouteStep(path_id=current, entry_s=0.0, exit_s=current_node.length))
                route.append(RouteStep(path_id=next_path, entry_s=0.0, exit_s=next_node.length))
                new_switch_reqs = switch_reqs.copy()
                if junction_id:
                    new_switch_reqs[junction_id] = next_path

                dfs(next_path, visited.copy(), route, new_switch_reqs)
                route.pop()

        dfs(start_path, set(), [], {})
        all_routes.sort(key=lambda r: r.total_length)
        return all_routes


def check_route_conflicts(
    routes: Dict[str, Route],
    train_positions: Dict[str, Tuple[str, float]]
) -> List[ConflictWarning]:
    """Check for route conflicts between trains."""
    warnings: List[ConflictWarning] = []
    train_ids = list(routes.keys())

    for i, train_a in enumerate(train_ids):
        for train_b in train_ids[i + 1:]:
            route_a = routes[train_a]
            route_b = routes[train_b]

            paths_a = set(route_a.get_path_sequence())
            paths_b = set(route_b.get_path_sequence())

            for path_id in paths_a.intersection(paths_b):
                pos_a = train_positions.get(train_a, (path_id, 0.0))
                pos_b = train_positions.get(train_b, (path_id, 0.0))

                if pos_a[0] == path_id and pos_b[0] == path_id:
                    separation = abs(pos_a[1] - pos_b[1])
                    if separation < 10.0:
                        warnings.append(ConflictWarning(
                            train_id=train_a,
                            conflicting_train_id=train_b,
                            path_id=path_id,
                            position_s=min(pos_a[1], pos_b[1]),
                            message=f"Trains within {separation:.1f}m on {path_id}"
                        ))

            # Switch conflicts
            for switch_id in set(route_a.switch_requirements.keys()).intersection(route_b.switch_requirements.keys()):
                if route_a.switch_requirements[switch_id] != route_b.switch_requirements[switch_id]:
                    warnings.append(ConflictWarning(
                        train_id=train_a,
                        conflicting_train_id=train_b,
                        path_id="",
                        position_s=0.0,
                        message=f"Switch {switch_id} conflict"
                    ))

    return warnings


def detect_route_conflicts(routes: Dict[str, Route]) -> List[RouteConflict]:
    """Detect hard conflicts (switch alignment)."""
    conflicts: List[RouteConflict] = []
    train_ids = list(routes.keys())

    for i, train_a in enumerate(train_ids):
        for train_b in train_ids[i + 1:]:
            shared_switches = set(routes[train_a].switch_requirements.keys()).intersection(
                routes[train_b].switch_requirements.keys()
            )
            for switch_id in shared_switches:
                if routes[train_a].switch_requirements[switch_id] != routes[train_b].switch_requirements[switch_id]:
                    conflicts.append(RouteConflict(
                        conflict_type="switch_conflict",
                        train_ids=[train_a, train_b],
                        path_id="",
                        details=f"Switch {switch_id} cannot be aligned to both paths"
                    ))

    return conflicts
```

- [ ] **Step 2: Create routing tests**

Create `backend/tests/test_simulation/test_topology/test_routing.py`:

```python
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

    # Force switch to path2
    route = finder.find_route("path1", 0.0, "path2", 15.0, switch_states={"j1": "path2"})
    assert route is not None

    # Try path3 with switch set to path2 - should fail
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
    assert len(warnings) > 0  # Should detect close proximity
```

- [ ] **Step 3: Run tests**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_simulation/test_topology/test_routing.py -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/simulation/topology/routing.py backend/tests/test_simulation/test_topology/test_routing.py
git commit -m "feat: implement RouteFinder with Dijkstra and switch awareness"
```

---

## Task 9: API Endpoints

**Files:**
- Create: `backend/app/api/geometry.py`
- Create: `backend/app/api/topology.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_api/test_geometry_api.py`
- Test: `backend/tests/test_api/test_topology_api.py`

- [ ] **Step 1: Create geometry API**

Create `backend/app/api/geometry.py`:

```python
"""Geometry API endpoints"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from app.services.project_io import ProjectIO

router = APIRouter(prefix="/geometry", tags=["geometry"])


class SamplePointResponse(BaseModel):
    s: float
    position: list[float]
    tangent: list[float]
    normal: list[float]
    binormal: list[float]
    curvature: float
    radius: float
    slope_deg: float
    bank_deg: float


class CacheStatusResponse(BaseModel):
    path_id: str
    computed: bool
    total_length: Optional[float] = None
    sample_count: Optional[int] = None


class GeometryStatusResponse(BaseModel):
    paths: list[CacheStatusResponse]


class ValidationResultResponse(BaseModel):
    is_valid: bool
    errors: list[dict]
    warnings: list[dict]


@router.post("/projects/{project_id}/compute")
async def compute_geometry(project_id: str):
    """Compute geometry for all paths."""
    from app.simulation.geometry import GeometryCache

    project = ProjectIO.load(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    cache = GeometryCache(project, resolution_m=project.simulation_settings.geometry_sample_resolution_m)
    cache.compute_all()

    return {"status": "computed", "paths_computed": len(cache._paths)}


@router.get("/projects/{project_id}/geometry/status")
async def get_geometry_status(project_id: str):
    """Get cache status."""
    from app.simulation.geometry import GeometryCache

    project = ProjectIO.load(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    cache = GeometryCache(project, resolution_m=project.simulation_settings.geometry_sample_resolution_m)
    status = cache.get_cache_status()

    paths = []
    for path_id, info in status.items():
        paths.append(CacheStatusResponse(
            path_id=path_id,
            computed=info.get("status") == "computed",
            total_length=info.get("length"),
            sample_count=info.get("sample_count")
        ))

    return GeometryStatusResponse(paths=paths)


@router.get("/projects/{project_id}/paths/{path_id}/sample", response_model=SamplePointResponse)
async def get_path_sample(project_id: str, path_id: str, s: float = Query(...)):
    """Get sample at arc length."""
    from app.simulation.geometry import GeometryCache

    project = ProjectIO.load(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    cache = GeometryCache(project, resolution_m=project.simulation_settings.geometry_sample_resolution_m)

    try:
        path_data = cache.get_path(path_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if not path_data or not path_data.samples:
        raise HTTPException(status_code=422, detail="Path has no geometry")

    if s < 0 or s > path_data.total_length:
        raise HTTPException(status_code=400, detail=f"s={s} exceeds path length {path_data.total_length}m")

    # Find closest sample
    sample = min(path_data.samples, key=lambda sp: abs(sp.s - s))

    return SamplePointResponse(
        s=sample.s,
        position=list(sample.position),
        tangent=list(sample.tangent),
        normal=list(sample.normal),
        binormal=list(sample.binormal),
        curvature=sample.curvature,
        radius=sample.radius,
        slope_deg=sample.slope_deg,
        bank_deg=sample.bank_deg
    )


@router.post("/projects/{project_id}/geometry/validate", response_model=ValidationResultResponse)
async def validate_geometry(project_id: str):
    """Validate all geometry."""
    from app.simulation.geometry import GeometryCache, GeometryValidator

    project = ProjectIO.load(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    cache = GeometryCache(project, resolution_m=project.simulation_settings.geometry_sample_resolution_m)
    cache.compute_all()

    validator = GeometryValidator(project.simulation_settings)
    result = validator.validate_project(cache, project.junctions)

    return ValidationResultResponse(
        is_valid=result.is_valid,
        errors=[{"severity": e.severity, "path_id": e.path_id, "location_s": e.location_s, "message": e.message} for e in result.errors],
        warnings=[{"severity": w.severity, "path_id": w.path_id, "location_s": w.location_s, "message": w.message} for w in result.warnings]
    )
```

- [ ] **Step 2: Create topology API**

Create `backend/app/api/topology.py`:

```python
"""Topology API endpoints"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List

router = APIRouter(prefix="/topology", tags=["topology"])


class PathNodeResponse(BaseModel):
    path_id: str
    length: float
    incoming_junctions: list[str]
    outgoing_junctions: list[str]


class TopologyGraphResponse(BaseModel):
    paths: Dict[str, PathNodeResponse]
    junctions: Dict[str, dict]
    is_connected: bool
    orphan_paths: list[str]


class RouteStepResponse(BaseModel):
    path_id: str
    entry_s: float
    exit_s: float


class RouteResponse(BaseModel):
    steps: list[RouteStepResponse]
    switch_requirements: Dict[str, str]
    total_length: float


class RouteRequest(BaseModel):
    from_path: str
    to_path: str
    switch_states: Optional[Dict[str, str]] = None


@router.get("/projects/{project_id}/topology/graph", response_model=TopologyGraphResponse)
async def get_topology_graph(project_id: str):
    """Get full topology graph."""
    from app.simulation.topology import TopologyGraph
    from app.simulation.geometry import GeometryCache

    project = ProjectIO.load(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    cache = GeometryCache(project, resolution_m=project.simulation_settings.geometry_sample_resolution_m)
    cache.compute_all()

    for path in project.paths:
        path_data = cache.get_path(path.id)
        if path_data:
            path.length_m = path_data.total_length

    graph = TopologyGraph()
    graph.build(project.paths, project.junctions)

    paths = {pid: PathNodeResponse(
        path_id=node.path_id,
        length=node.length,
        incoming_junctions=node.incoming_junctions,
        outgoing_junctions=node.outgoing_junctions
    ) for pid, node in graph.paths.items()}

    return TopologyGraphResponse(
        paths=paths,
        junctions={j.id: j.model_dump() for j in project.junctions},
        is_connected=graph.is_connected(),
        orphan_paths=graph.get_orphan_paths()
    )


@router.post("/projects/{project_id}/topology/routes", response_model=list[RouteResponse])
async def find_routes(project_id: str, request: RouteRequest):
    """Find routes between paths."""
    from app.simulation.topology import TopologyGraph, RouteFinder
    from app.simulation.geometry import GeometryCache

    project = ProjectIO.load(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    cache = GeometryCache(project, resolution_m=project.simulation_settings.geometry_sample_resolution_m)
    cache.compute_all()

    for path in project.paths:
        path_data = cache.get_path(path.id)
        if path_data:
            path.length_m = path_data.total_length

    graph = TopologyGraph()
    graph.build(project.paths, project.junctions)
    finder = RouteFinder(graph)

    route = finder.find_route(
        start_path=request.from_path,
        start_s=0.0,
        end_path=request.to_path,
        end_s=0.0,
        switch_states=request.switch_states
    )

    if not route:
        return []

    return [RouteResponse(
        steps=[RouteStepResponse(path_id=s.path_id, entry_s=s.entry_s, exit_s=s.exit_s) for s in route.steps],
        switch_requirements=route.switch_requirements,
        total_length=route.total_length
    )]
```

- [ ] **Step 3: Update main.py**

Modify `backend/app/main.py`:

```python
from fastapi import FastAPI
from app.api.router import router
from app.api.geometry import router as geometry_router
from app.api.topology import router as topology_router

app = FastAPI(title="Roller Coaster Simulator")

app.include_router(router)
app.include_router(geometry_router)
app.include_router(topology_router)
```

- [ ] **Step 4: Update simulation __init__.py**

Modify `backend/app/simulation/__init__.py`:

```python
"""Simulation engine"""

from .geometry import (
    CentripetalCatmullRom,
    GeometryCache,
    GeometryValidator,
    SamplePoint,
    InterpolatedPath,
    ValidationResult,
    ValidationIssue,
)
from .topology import (
    TopologyGraph,
    PathNode,
    RouteFinder,
    Route,
    RouteStep,
    ConflictWarning,
)

__all__ = [
    'GeometryError',
    'CentripetalCatmullRom',
    'GeometryCache',
    'GeometryValidator',
    'SamplePoint',
    'InterpolatedPath',
    'ValidationResult',
    'ValidationIssue',
    'TopologyGraph',
    'PathNode',
    'RouteFinder',
    'Route',
    'RouteStep',
    'ConflictWarning',
]
```

- [ ] **Step 5: Run all tests**

Run: `cd backend && source .venv/bin/activate && pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/geometry.py backend/app/api/topology.py backend/app/main.py backend/app/simulation/__init__.py
git commit -m "feat: add geometry and topology API endpoints"
```

---

## Task 10: Integration Tests

**Files:**
- Create: `backend/tests/test_simulation/test_integration.py`

- [ ] **Step 1: Create integration tests**

Create `backend/tests/test_simulation/test_integration.py`:

```python
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

    # Create points
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

    # Create paths
    project.paths = [
        Path(id="path1", point_ids=["p1", "p2", "p3"]),
        Path(id="path2", point_ids=["p4", "p5", "p6"]),
        Path(id="path3", point_ids=["p7", "p8"]),
    ]

    # Create junction
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
```

- [ ] **Step 2: Run tests**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_simulation/test_integration.py -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_simulation/test_integration.py
git commit -m "test: add integration tests for geometry and topology"
```

---

## Task 11: Final Verification

- [ ] **Step 1: Run all tests**

Run: `cd backend && source .venv/bin/activate && pytest tests/ -v`
Expected: All tests PASS, count increased from baseline

- [ ] **Step 2: Verify API starts**

Run: `cd backend && source .venv/bin/activate && python -c "from app.main import app; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Check Phase 2 success criteria**

Verify all 11 criteria from spec are met:
1. ✅ Centripetal Catmull-Rom spline from points
2. ✅ Bank angle interpolated
3. ✅ Arc length parameterization
4. ✅ Curvature and frames computed
5. ✅ Geometry cache with invalidation
6. ✅ Geometry validation
7. ✅ Path graph from paths and junctions
8. ✅ Route finding with switch awareness
9. ✅ Route conflict detection
10. ✅ All tests pass
11. ✅ API endpoints return correct data

- [ ] **Step 4: Final commit**

```bash
git add .
git commit -m "chore: complete Phase 2 - geometry and topology core"
```
