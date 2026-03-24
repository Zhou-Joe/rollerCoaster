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

    def validate_project(self, geometry_cache, junctions: List[Junction]) -> ValidationResult:
        """Validate all geometry in a project."""
        all_errors = []
        all_warnings = []

        for path in geometry_cache._project.paths:
            interpolated = geometry_cache.get_path(path.id)
            result = self.validate_path(path.id, interpolated)
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)

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