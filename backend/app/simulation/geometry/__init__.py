"""Geometry computation for track paths"""

from .errors import GeometryError
from .types import SamplePoint, InterpolatedPath, ValidationResult, ValidationIssue
from .spline import CentripetalCatmullRom
from .cache import GeometryCache
from .validator import GeometryValidator

__all__ = [
    "GeometryError",
    "SamplePoint",
    "InterpolatedPath",
    "ValidationResult",
    "ValidationIssue",
    "CentripetalCatmullRom",
    "GeometryCache",
    "GeometryValidator",
]