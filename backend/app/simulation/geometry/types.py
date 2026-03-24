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
