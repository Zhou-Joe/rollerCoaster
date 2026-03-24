"""Geometry cache with invalidation"""

from typing import Dict, Set
from app.models.project import Project
from .types import InterpolatedPath, ValidationResult, ValidationIssue
from .spline import CentripetalCatmullRom


class GeometryCache:
    """Manages cached geometry for a project with invalidation support."""

    def __init__(self, project: Project, resolution_m: float = 0.01):
        self._project = project
        self._resolution_m = resolution_m
        self._paths: Dict[str, InterpolatedPath] = {}
        self._dirty: Set[str] = set()

    def get_path(self, path_id: str) -> InterpolatedPath:
        """Get cached path geometry, computing if dirty or missing."""
        if path_id not in self._paths or path_id in self._dirty:
            self._compute_path(path_id)
        return self._paths[path_id]

    def _compute_path(self, path_id: str) -> None:
        """Compute geometry for a single path."""
        path = None
        for p in self._project.paths:
            if p.id == path_id:
                path = p
                break

        if path is None:
            raise ValueError(f"Path {path_id} not found in project")

        points = []
        for point in self._project.points:
            if point.id in path.point_ids:
                points.append(point)

        point_order = {pid: idx for idx, pid in enumerate(path.point_ids)}
        points.sort(key=lambda p: point_order[p.id])

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
            self._paths[path_id] = InterpolatedPath(
                path_id=path_id,
                total_length=0.0,
                samples=[],
                resolution_m=self._resolution_m,
                validation=validation
            )
            self._dirty.discard(path_id)
            return

        self._paths[path_id] = InterpolatedPath(
            path_id=path_id,
            total_length=spline.get_total_length(),
            samples=spline._samples,
            resolution_m=self._resolution_m,
            validation=validation
        )

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