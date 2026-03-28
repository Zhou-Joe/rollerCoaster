"""Geometry cache with invalidation and junction-aware tangent continuity"""

from typing import Dict, Set, Optional, Tuple
from app.models.project import Project
from app.models.topology import Junction
from .types import InterpolatedPath, ValidationResult, ValidationIssue
from .spline import CentripetalCatmullRom
import numpy as np


class GeometryCache:
    """Manages cached geometry for a project with invalidation support.

    Handles junction tangent continuity to ensure smooth transitions between
    connected paths.
    """

    def __init__(self, project: Project, resolution_m: float = 0.01):
        self._project = project
        self._resolution_m = resolution_m
        self._paths: Dict[str, InterpolatedPath] = {}
        self._dirty: Set[str] = set()
        self._junction_tangents: Dict[str, Dict[str, Tuple[float, float, float]]] = {}
        self._computing: Set[str] = set()  # Track paths currently being computed

    def get_path(self, path_id: str) -> InterpolatedPath:
        """Get cached path geometry, computing if dirty or missing."""
        if path_id not in self._paths or path_id in self._dirty:
            self._compute_path(path_id)
        return self._paths[path_id]

    def _find_junction_for_outgoing_path(self, path_id: str) -> Optional[Junction]:
        """Find junction where this path is an outgoing path."""
        for junction in self._project.junctions:
            if path_id in junction.outgoing_path_ids:
                return junction
        return None

    def _find_junction_for_incoming_path(self, path_id: str) -> Optional[Junction]:
        """Find junction where this path is an incoming path."""
        for junction in self._project.junctions:
            if path_id == junction.incoming_path_id:
                return junction
        return None

    def _get_incoming_tangent_at_junction(
        self, junction: Junction
    ) -> Optional[Tuple[float, float, float]]:
        """Get the tangent at the end of the incoming path for a junction.

        Returns None if the incoming path is already being computed (cycle detection)
        or if the incoming path hasn't been computed yet and can't be computed.
        """
        incoming_path_id = junction.incoming_path_id

        # Check for cycles - if we're already computing this path, don't recurse
        if incoming_path_id in self._computing:
            return None

        # Ensure incoming path is computed first
        if incoming_path_id not in self._paths:
            # Only compute if not already in progress
            if incoming_path_id not in self._computing:
                self._compute_path(incoming_path_id)

        incoming_path = self._paths.get(incoming_path_id)
        if incoming_path is None or len(incoming_path.samples) == 0:
            return None

        # Get tangent at the end of the incoming path
        last_sample = incoming_path.samples[-1]
        tangent = last_sample.tangent

        # Normalize the tangent
        t_arr = np.array(tangent)
        t_norm = np.linalg.norm(t_arr)
        if t_norm < 1e-10:
            return None

        return tuple((t_arr / t_norm).tolist())

    def _get_outgoing_tangent_at_junction(
        self, junction: Junction
    ) -> Optional[Tuple[float, float, float]]:
        """Get the tangent at the start of an outgoing path (for the incoming path's end)."""
        # This is used when computing the incoming path - we want its end tangent
        # to match the start direction of the default outgoing path
        # For now, we don't constrain the end tangent - let the path naturally curve
        return None

    def _compute_path(self, path_id: str) -> None:
        """Compute geometry for a single path with junction-aware tangents."""
        # Check if already computed or currently being computed
        if path_id in self._paths and path_id not in self._dirty:
            return

        # Mark as being computed (for cycle detection)
        self._computing.add(path_id)

        try:
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

            # Check if this path starts at a junction - need incoming tangent
            start_tangent = None
            junction = self._find_junction_for_outgoing_path(path_id)
            if junction:
                # The first point of this path should match the junction point
                # Get the tangent from the incoming path
                start_tangent = self._get_incoming_tangent_at_junction(junction)

            # Check if this path ends at a junction - could constrain end tangent
            # (but typically we let the incoming path end naturally)
            end_tangent = None

            try:
                spline = CentripetalCatmullRom(
                    points,
                    self._resolution_m,
                    start_tangent=start_tangent,
                    end_tangent=end_tangent
                )
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
        finally:
            # Always remove from computing set
            self._computing.discard(path_id)

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