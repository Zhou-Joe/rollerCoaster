"""Centripetal Catmull-Rom spline interpolation with rotation-minimizing frames"""

from typing import List, Tuple
import numpy as np
from app.models.track import Point
from .errors import GeometryError
from .types import SamplePoint, ValidationIssue


def _check_valid_point(point: Point) -> None:
    """Validate point coordinates are finite numbers."""
    for coord_name, value in [('x', point.x), ('y', point.y), ('z', point.z)]:
        if not np.isfinite(value):
            raise GeometryError(f"Invalid coordinate value: {coord_name}={value}")


def _catmull_rom_blend(p0: float, p1: float, p2: float, p3: float, t: float) -> float:
    """Catmull-Rom blend function for a single dimension."""
    t2 = t * t
    t3 = t2 * t
    return 0.5 * (
        (2 * p1) +
        (-p0 + p2) * t +
        (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
        (-p0 + 3 * p1 - 3 * p2 + p3) * t3
    )


def _catmull_rom_blend_derivative(p0: float, p1: float, p2: float, p3: float, t: float) -> float:
    """First derivative of Catmull-Rom blend function."""
    t2 = t * t
    return 0.5 * (
        (-p0 + p2) +
        2 * (2 * p0 - 5 * p1 + 4 * p2 - p3) * t +
        3 * (-p0 + 3 * p1 - 3 * p2 + p3) * t2
    )


def _catmull_rom_blend_second_derivative(p0: float, p1: float, p2: float, p3: float, t: float) -> float:
    """Second derivative of Catmull-Rom blend function."""
    return (2 * p0 - 5 * p1 + 4 * p2 - p3) + 3 * (-p0 + 3 * p1 - 3 * p2 + p3) * t


def _normalize(v: np.ndarray) -> np.ndarray:
    """Normalize a vector, returning zero vector if magnitude is too small."""
    norm = np.linalg.norm(v)
    if norm < 1e-10:
        return np.array([0.0, 0.0, 0.0])
    return v / norm


def _compute_rotation_minimizing_frames(
    tangents: List[np.ndarray],
) -> Tuple[List[np.ndarray], List[np.ndarray]]:
    """
    Compute rotation-minimizing frames using parallel transport (double reflection method).

    This ensures the normal/binormal vectors don't flip at inflection points.
    """
    n = len(tangents)
    if n == 0:
        return [], []

    normals: List[np.ndarray] = []
    binormals: List[np.ndarray] = []

    # Initialize first frame
    t0 = tangents[0]

    # Choose an initial "up" direction that's perpendicular to tangent
    # Try world-up first, but use another axis if tangent is nearly vertical
    world_up = np.array([0.0, 0.0, 1.0])
    if abs(np.dot(t0, world_up)) > 0.999:
        world_up = np.array([0.0, 1.0, 0.0])

    # First normal is perpendicular to tangent and world_up
    b0 = _normalize(np.cross(t0, world_up))
    n0 = _normalize(np.cross(b0, t0))

    normals.append(n0)
    binormals.append(b0)

    # Propagate frame using parallel transport (double reflection method)
    for i in range(1, n):
        t_prev = tangents[i - 1]
        t_curr = tangents[i]
        n_prev = normals[i - 1]
        b_prev = binormals[i - 1]

        # Reflection 1: reflect in the plane bisecting t_prev and t_curr
        v1 = t_prev + t_curr
        v1_norm = np.linalg.norm(v1)

        if v1_norm < 1e-10:
            # Tangents are opposite, use previous frame
            n_curr = n_prev.copy()
            b_curr = b_prev.copy()
        else:
            v1 = v1 / v1_norm
            # Reflect n_prev and b_prev
            n_curr = n_prev - 2 * np.dot(n_prev, v1) * v1
            b_curr = b_prev - 2 * np.dot(b_prev, v1) * v1

        # Normalize and ensure orthogonality
        b_curr = _normalize(b_curr)
        n_curr = _normalize(np.cross(b_curr, t_curr))
        b_curr = _normalize(np.cross(t_curr, n_curr))

        normals.append(n_curr)
        binormals.append(b_curr)

    return normals, binormals


class CentripetalCatmullRom:
    """Centripetal Catmull-Rom spline interpolation with rotation-minimizing frames."""

    def __init__(self, points: List[Point], resolution_m: float = 0.01):
        if len(points) < 2:
            raise GeometryError("Path requires at least 2 points")

        for point in points:
            _check_valid_point(point)

        self._points = points
        self._resolution_m = resolution_m
        self._warnings: List[ValidationIssue] = []
        self._cleaned_points = self._remove_duplicates(points)

        if len(self._cleaned_points) < 2:
            raise GeometryError("Path has zero length")

        self._t_values = self._compute_parameters(self._cleaned_points)
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
            if dist_sq > 1e-12:
                cleaned.append(curr)
            else:
                self._warnings.append(ValidationIssue(
                    severity="warning",
                    path_id="",
                    location_s=0.0,
                    message=f"Skipped duplicate point at index {i}"
                ))
        return cleaned

    def _compute_parameters(self, points: List[Point]) -> np.ndarray:
        """Compute centripetal parameter values."""
        n = len(points)
        t = np.zeros(n)
        for i in range(1, n):
            dx = points[i].x - points[i - 1].x
            dy = points[i].y - points[i - 1].y
            dz = points[i].z - points[i - 1].z
            dist = np.sqrt(dx * dx + dy * dy + dz * dz)
            t[i] = t[i - 1] + np.sqrt(dist)
        return t

    def _compute_samples(self) -> None:
        """Compute evenly spaced samples along the spline with rotation-minimizing frames."""
        n_segments = len(self._cleaned_points) - 1
        if n_segments == 1:
            self._compute_linear_samples()
            return

        num_initial_samples = max(1000, n_segments * 100)
        t_values = self._t_values
        t_max = t_values[-1]

        # First pass: compute total length
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

        # Second pass: compute samples at regular arc length intervals
        num_samples = max(int(self._total_length / self._resolution_m) + 1, 2)

        # Collect all positions and tangents first
        positions: List[Tuple[float, float, float]] = []
        tangents: List[np.ndarray] = []

        for i in range(num_samples):
            s = i * self._resolution_m
            if s > self._total_length:
                s = self._total_length

            t_ratio = s / self._total_length if self._total_length > 0 else 0.0
            t = t_ratio * t_max

            pos = self._evaluate_position(t)
            first, second = self._evaluate_derivative(t)

            first_norm = np.sqrt(first[0] ** 2 + first[1] ** 2 + first[2] ** 2)
            if first_norm < 1e-10:
                tangent = np.array([1.0, 0.0, 0.0])
            else:
                tangent = np.array([first[0] / first_norm, first[1] / first_norm, first[2] / first_norm])

            positions.append(pos)
            tangents.append(tangent)

        # Compute rotation-minimizing frames
        normals, binormals = _compute_rotation_minimizing_frames(tangents)

        # Create sample points
        for i in range(num_samples):
            s = i * self._resolution_m
            if s > self._total_length:
                s = self._total_length

            pos = positions[i]
            tangent = tangents[i]
            normal = normals[i]
            binormal = binormals[i]

            # Compute curvature from second derivative
            t_ratio = s / self._total_length if self._total_length > 0 else 0.0
            t = t_ratio * t_max
            first, second = self._evaluate_derivative(t)

            first_norm = np.linalg.norm(first)
            cross = np.cross(first, second)
            cross_norm = np.linalg.norm(cross)
            if first_norm < 1e-10:
                curvature = 0.0
            else:
                curvature = cross_norm / (first_norm ** 3)

            radius = 1.0 / curvature if curvature > 1e-10 else float('inf')

            slope_rad = np.arcsin(np.clip(tangent[2], -1.0, 1.0))
            slope_deg = np.degrees(slope_rad)

            # Interpolate bank angle from control points
            bank_idx = int(t_ratio * (len(self._cleaned_points) - 1))
            bank_next = min(bank_idx + 1, len(self._cleaned_points) - 1)
            bank_t = (t_ratio * (len(self._cleaned_points) - 1)) - bank_idx
            bank = self._cleaned_points[bank_idx].bank_deg + bank_t * (
                self._cleaned_points[bank_next].bank_deg - self._cleaned_points[bank_idx].bank_deg
            )

            self._samples.append(SamplePoint(
                s=s,
                position=pos,
                tangent=tuple(tangent.tolist()),
                normal=tuple(normal.tolist()),
                binormal=tuple(binormal.tolist()),
                curvature=curvature,
                radius=radius,
                slope_deg=slope_deg,
                bank_deg=bank
            ))

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

        tangent = (dx / length, dy / length, dz / length)
        num_samples = max(int(length / self._resolution_m) + 1, 2)

        for i in range(num_samples):
            t = i / (num_samples - 1) if num_samples > 1 else 0.0
            s = t * length

            pos = (p0.x + t * dx, p0.y + t * dy, p0.z + t * dz)
            bank = p0.bank_deg + t * (p1.bank_deg - p0.bank_deg)

            sample = SamplePoint(
                s=s,
                position=pos,
                tangent=tangent,
                normal=(0.0, 0.0, 1.0),
                binormal=tuple(np.cross(tangent, (0.0, 0.0, 1.0)).tolist()),
                curvature=0.0,
                radius=float('inf'),
                slope_deg=np.degrees(np.arcsin(np.clip(tangent[2], -1.0, 1.0))),
                bank_deg=bank
            )
            self._samples.append(sample)

    def _evaluate_position(self, t: float) -> Tuple[float, float, float]:
        """Evaluate spline position at parameter t."""
        t_values = self._t_values
        points = self._cleaned_points

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
        if abs(t2 - t1) < 1e-10:
            t_norm = 0.0
        else:
            t_norm = (t - t1) / (t2 - t1)

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

        if idx < 0:
            p0, p1 = points[0], points[1]
            return (2 * p0.x - p1.x, 2 * p0.y - p1.y, 2 * p0.z - p1.z)
        else:
            p_last = points[n - 1]
            p_prev = points[n - 2]
            return (2 * p_last.x - p_prev.x, 2 * p_last.y - p_prev.y, 2 * p_last.z - p_prev.z)

    def _evaluate_derivative(self, t: float) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        """Evaluate first and second derivatives at parameter t."""
        t_values = self._t_values
        points = self._cleaned_points

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

        dx_dt = _catmull_rom_blend_derivative(p0[0], p1[0], p2[0], p3[0], t_norm)
        dy_dt = _catmull_rom_blend_derivative(p0[1], p1[1], p2[1], p3[1], t_norm)
        dz_dt = _catmull_rom_blend_derivative(p0[2], p1[2], p2[2], p3[2], t_norm)

        d2x_dt2 = _catmull_rom_blend_second_derivative(p0[0], p1[0], p2[0], p3[0], t_norm)
        d2y_dt2 = _catmull_rom_blend_second_derivative(p0[1], p1[1], p2[1], p3[1], t_norm)
        d2z_dt2 = _catmull_rom_blend_second_derivative(p0[2], p1[2], p2[2], p3[2], t_norm)

        first = (dx_dt / dt, dy_dt / dt, dz_dt / dt)
        second = (d2x_dt2 / dt / dt, d2y_dt2 / dt / dt, d2z_dt2 / dt / dt)

        return (first, second)

    def get_total_length(self) -> float:
        """Get total arc length of the spline."""
        return self._total_length

    def sample_at_arc_length(self, s: float) -> SamplePoint:
        """Get interpolated values at arc length position s."""
        s = max(0.0, min(s, self._total_length))
        # Find closest sample
        idx = int(s / self._resolution_m)
        if idx >= len(self._samples):
            idx = len(self._samples) - 1
        return self._samples[idx]

    def get_warnings(self) -> List[ValidationIssue]:
        """Get warnings accumulated during construction."""
        return self._warnings