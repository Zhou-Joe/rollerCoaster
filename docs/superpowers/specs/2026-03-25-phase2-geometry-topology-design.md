# Phase 2: Track Geometry & Topology Core Design

**Date:** 2026-03-25
**Project:** Roller Coaster Simulator
**Phase:** 2 of 7

## Overview

Phase 2 builds the computational engines that transform static domain models into usable representations: spline-based geometry processing and topology graph operations with full routing logic.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Spline type | Centripetal Catmull-Rom | Passes through control points, minimizes overshoot on tight corners |
| Bank interpolation | Same spline as position | Consistent smoothness with position |
| Caching | Cache with invalidation | Fast queries for physics, recompute when points change |
| Sample resolution | Configurable, default 1cm | Flexible for different use cases |
| Junction connections | End-to-end only | Simpler model, matches how coasters are built |
| Loops | Junction-based | Consistent model, no special cases |
| Routing | Dijkstra with switch awareness | Finds valid routes considering switch alignment |
| Validation | Essential + warnings | Catches show-stoppers and provides helpful feedback |

## Goals

1. Convert Point lists into smooth, sampled track geometry
2. Compute derived quantities: arc length, curvature, slope, local frames
3. Build directed graph representation of track network
4. Implement routing logic with switch state consideration
5. Add geometry validation with errors and warnings

## Architecture

### Directory Structure

```
backend/app/simulation/
├── __init__.py
├── geometry/
│   ├── __init__.py
│   ├── spline.py         # Centripetal Catmull-Rom interpolation
│   ├── arc_length.py     # Arc length parameterization
│   ├── frames.py         # Frenet-Serret frames with bank
│   ├── curvature.py      # Curvature and slope calculations
│   ├── bank.py           # Bank angle interpolation
│   ├── validator.py      # Geometry validation
│   ├── cache.py          # GeometryCache with invalidation
│   └── types.py          # SamplePoint, InterpolatedPath
├── topology/
│   ├── __init__.py
│   ├── graph.py          # NetworkX path graph
│   ├── routing.py        # RouteFinder with switch logic
│   └── types.py          # Route, RouteStep, ConflictWarning
└── services/
    └── geometry_service.py  # High-level geometry operations
```

### Dependencies

Add to `pyproject.toml`:
- `numpy>=1.26.0` - Vectorized calculations
- `scipy>=1.12.0` - Spline interpolation utilities
- `networkx>=3.2.0` - Graph operations

---

## Geometry Engine

### Centripetal Catmull-Rom Spline

Centripetal parameterization prevents cusps and self-intersections that can occur with uniform Catmull-Rom splines.

**Parameter calculation:**

For points P₀, P₁, ..., Pₙ₋₁:

```
t₀ = 0
tᵢ = tᵢ₋₁ + |Pᵢ - Pᵢ₋₁|^α    where α = 0.5 (centripetal)
```

**Interpolation for position (x, y, z):**

Between control points Pᵢ and Pᵢ₊₁, for parameter t ∈ [tᵢ, tᵢ₊₁]:

```
P(t) = CatmullRom(Pᵢ₋₁, Pᵢ, Pᵢ₊₁, Pᵢ₊₂, (t - tᵢ) / (tᵢ₊₁ - tᵢ))
```

**Bank angle interpolation:**

Bank uses the same centripetal Catmull-Rom spline with bank values at each control point:

```
bank(t) = CatmullRom(bankᵢ₋₁, bankᵢ, bankᵢ₊₁, bankᵢ₊₂, normalized_t)
```

### Edge Cases

| Condition | Behavior |
|-----------|----------|
| < 2 points | Invalid path, raise `GeometryError("Path requires at least 2 points")` |
| Exactly 2 points | **Skip Catmull-Rom entirely.** Use pure linear interpolation between P₀ and P₁. No phantom points needed. Curvature is 0 everywhere. |
| Open path endpoints | Create phantom points by reflection (see below) |
| Collinear points | Handle gracefully, curvature becomes 0 |
| Duplicate consecutive points | Skip duplicates during parameterization, emit warning |
| Zero-length path (all coincident) | Raise `GeometryError("Path has zero length")` |
| NaN/Inf in coordinates | Raise `GeometryError("Invalid coordinate value")` |
| Bank angle outside [-180, 180] | Normalize to range, emit warning |

### Open Path Endpoint Handling

For open paths, create phantom control points at the boundaries:

```python
# At start: reflect P₁ across P₀ to create P₋₁
P_minus_1 = P_0 - (P_1 - P_0)  # = 2*P_0 - P_1

# At end: reflect P_{n-2} across P_{n-1} to create P_n
P_n = P_{n-1} + (P_{n-1} - P_{n-2})  # = 2*P_{n-1} - P_{n-2}
```

This ensures the tangent at endpoints follows the natural direction of the first/last segment.

For closed loops (junction-based), no phantom points are needed — the path wraps naturally through the junction.

### Arc Length Parameterization

1. Sample the spline at high resolution during initial computation
2. Compute cumulative chord length
3. Build lookup table for s → (segment_index, local_t)
4. Interpolate position/derivative at any arc length s

### Local Frame Calculation

Frenet-Serret frame at each point:

1. **Tangent T**: Normalized first derivative
2. **Normal N**: Normalized second derivative direction (curvature direction)
3. **Binormal B**: T × N

**Bank angle integration:**
- The bank angle rotates the frame around the tangent axis
- Applied after computing the base Frenet frame
- Results in "tilted" normal/binormal vectors used for g-force calculations

### Curvature and Slope

**Curvature:** κ = |dT/ds| = |r' × r''| / |r'|³

**Radius of curvature:** R = 1/κ (when κ > 0)

**Slope angle:** θ = arcsin(tangent_z) — angle from horizontal

### Geometry Cache

Store computed geometry with invalidation:

```python
@dataclass
class SamplePoint:
    s: float              # Arc length position
    position: Tuple[float, float, float]  # (x, y, z)
    tangent: Tuple[float, float, float]   # Unit tangent
    normal: Tuple[float, float, float]    # Unit normal (curvature direction)
    binormal: Tuple[float, float, float]  # Unit binormal
    curvature: float      # 1/meters
    radius: float         # meters (inf if straight)
    slope_deg: float      # Degrees from horizontal
    bank_deg: float       # Interpolated bank angle

@dataclass
class InterpolatedPath:
    path_id: str
    total_length: float
    samples: List[SamplePoint]  # Evenly spaced by resolution
    resolution_m: float
    validation: ValidationResult  # Unified validation result

class GeometryCache:
    """
    Manages cached geometry for a project with invalidation support.

    The cache holds a reference to the project for point lookup.
    """

    def __init__(self, project: 'Project', resolution_m: float = 0.01):
        self._project = project
        self._resolution_m: float = resolution_m
        self._paths: Dict[str, InterpolatedPath] = {}
        self._dirty: Set[str] = set()  # path_ids that need recomputation

    def get_path(self, path_id: str) -> InterpolatedPath:
        """Get cached path geometry, computing if dirty or missing."""
        ...

    def get_sample(self, path_id: str, s: float) -> SamplePoint:
        """Get sample at arc length s, interpolating between cached samples."""
        ...

    def invalidate(self, path_id: str) -> None:
        """Mark a path as needing recomputation."""
        ...

    def invalidate_points(self, point_ids: Set[str]) -> None:
        """Invalidate all paths that reference any of these points."""
        ...

    def invalidate_all(self) -> None:
        """Mark all paths as needing recomputation."""
        ...

    def compute_all(self) -> None:
        """Force computation of all paths."""
        ...

    def get_cache_status(self) -> Dict[str, Dict]:
        """Return status of each path (computed/dirty/empty)."""
        ...
```

---

## Geometry Validation

### Error Conditions (Block Operation)

| Check | Threshold | Error Message |
|-------|-----------|---------------|
| Curvature spike | κ > 0.5 m⁻¹ (R < 2m) | "Curvature too high at s=X: radius Ym" |
| Tangent discontinuity | Angle > 5° between samples | "Tangent discontinuity at s=X" |
| Invalid junction | Endpoint gap > 0.01m | "Junction X: paths not connected within tolerance" |
| Too few points | < 2 points | "Path X has insufficient points" |

### Warning Conditions (Show Only)

| Check | Threshold | Warning Message |
|-------|-----------|-----------------|
| High curvature | R < 10m | "Tight radius at s=X: Ym" |
| Bank rate change | > 10°/m | "Rapid bank transition at s=X" |
| Self-intersection | N/A | "Path may cross itself near s=X" |

### Validation API

```python
@dataclass
class ValidationIssue:
    severity: str  # "error" or "warning"
    path_id: str
    location_s: float
    message: str
    value: Optional[float] = None

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[ValidationIssue]
    warnings: List[ValidationIssue]

class GeometryValidator:
    def __init__(self, settings: SimulationSettings): ...

    def validate_path(self, path_id: str, interpolated: InterpolatedPath) -> ValidationResult
    def validate_junction(self, junction: Junction, paths: Dict[str, InterpolatedPath]) -> ValidationResult
    def validate_project(self, geometry_cache: GeometryCache, junctions: List[Junction]) -> ValidationResult
```

---

## Topology Engine

### Graph Model

The ride layout is a directed graph where:
- **Nodes** = Paths
- **Edges** = Junctions (one incoming → N outgoing)

### Junction Constraints

Junctions connect the **end** of the incoming path to the **start** of outgoing paths:

```
incoming_path.end_s (length) → outgoing_path.start_s (0)
```

This matches how roller coasters are built: track sections connected end-to-end.

### Loop Handling

A loop is modeled as a junction where a path connects to itself:

```python
# Loop junction
Junction(
    id="loop_jct",
    incoming_path_id="main_loop",
    outgoing_path_ids=["main_loop"],  # Same path
    position_s=100.0  # Must equal path length
)
```

No special case needed — routing algorithm handles it naturally.

**Validation:** For loop junctions where `incoming_path_id == outgoing_path_id`, the `position_s` must equal the incoming path's computed length. The `GeometryValidator.validate_junction` method enforces this:

```python
def validate_junction(self, junction: Junction, paths: Dict[str, InterpolatedPath]) -> ValidationResult:
    errors = []
    warnings = []

    # For loops, position_s must equal path length
    if junction.incoming_path_id in junction.outgoing_path_ids:
        incoming_path = paths.get(junction.incoming_path_id)
        if incoming_path:
            tolerance = self.settings.junction_position_tolerance_m
            if abs(junction.position_s - incoming_path.total_length) > tolerance:
                errors.append(ValidationIssue(
                    severity="error",
                    path_id=junction.incoming_path_id,
                    location_s=junction.position_s,
                    message=f"Loop junction {junction.id}: position_s must equal path length ({incoming_path.total_length}m)"
                ))
    # ... additional junction validation
    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)
```

### Path Graph API

```python
class PathNode:
    path_id: str
    length: float
    incoming_junctions: List[str]  # Junction IDs
    outgoing_junctions: List[str]  # Junction IDs

class TopologyGraph:
    def __init__(self):
        self.paths: Dict[str, PathNode] = {}
        self.junctions: Dict[str, Junction] = {}

    def build(self, paths: List[Path], junctions: List[Junction]) -> None
    def get_outgoing_paths(self, path_id: str) -> List[str]
    def get_incoming_paths(self, path_id: str) -> List[str]
    def is_connected(self) -> bool
    def get_orphan_paths(self) -> List[str]
```

---

## Routing with Switch Logic

### Route Representation

```python
@dataclass
class RouteStep:
    path_id: str
    entry_s: float  # Where train enters this path
    exit_s: float   # Where train exits (typically path length)

@dataclass
class Route:
    steps: List[RouteStep]
    switch_requirements: Dict[str, str]  # junction_id → required_alignment
    total_length: float

    def get_path_sequence(self) -> List[str]
```

### Route Finding

Dijkstra's algorithm with switch state awareness:

```python
class RouteFinder:
    def __init__(self, graph: TopologyGraph): ...

    def find_route(
        self,
        start_path: str,
        start_s: float,
        end_path: str,
        end_s: float,
        switch_states: Optional[Dict[str, str]] = None
    ) -> Optional[Route]:
        """
        Find valid route between positions.

        Args:
            start_path, start_s: Starting position
            end_path, end_s: Ending position
            switch_states: Current switch alignments (junction_id → aligned_path)
                          If None, finds all possible routes

        Returns:
            Shortest valid route, or None if no route exists
        """

    def find_all_routes(self, start_path: str, end_path: str) -> List[Route]
```

### Switch State Handling

When a switch is present at a junction:
- If `switch_states` is provided and switch is aligned to path X, only routes through X are valid
- If switch state unknown, route includes which alignment is required
- Route validation checks if required alignments are achievable

### Route Conflict Detection

```python
@dataclass
class ConflictWarning:
    train_id: str
    conflicting_train_id: str
    path_id: str
    position_s: float
    message: str

def check_route_conflicts(
    routes: Dict[str, Route],  # train_id → route
    train_positions: Dict[str, Tuple[str, float]]  # train_id → (path, s)
) -> List[ConflictWarning]:
    """
    Check for potential route conflicts between trains.

    Detects:
    - Two trains routed to same path simultaneously
    - Opposing routes on same path
    - Switch alignment conflicts
    """
```

---

## API Endpoints

### Geometry Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects/{id}/geometry/compute` | Force recompute all paths |
| GET | `/projects/{id}/geometry/status` | Cache status for all paths |
| GET | `/projects/{id}/paths/{path_id}/sample?s=50.0` | Get geometry at arc length |
| GET | `/projects/{id}/paths/{path_id}/samples?start=0&end=100` | Get sample range |
| POST | `/projects/{id}/geometry/validate` | Run validation, return results |

**Query parameters for sample endpoint:**
- `s` (required): Arc length position in meters

**Error responses:**

```json
// 400 Bad Request - s out of range
{
  "error": "arc_length_out_of_range",
  "message": "s=150.0 exceeds path length of 100.0m",
  "path_length": 100.0,
  "requested_s": 150.0
}

// 404 Not Found - path does not exist
{
  "error": "path_not_found",
  "message": "Path 'path_001' not found in project"
}

// 422 Unprocessable Entity - path has no geometry
{
  "error": "geometry_not_computed",
  "message": "Path 'path_001' has insufficient points for interpolation"
}
```

**Sample endpoint response:**

```json
{
  "s": 50.0,
  "position": [10.5, 0.0, 5.2],
  "tangent": [0.98, 0.0, 0.2],
  "normal": [-0.2, 0.0, 0.98],
  "binormal": [0.0, 1.0, 0.0],
  "curvature": 0.05,
  "radius": 20.0,
  "slope_deg": 11.5,
  "bank_deg": 15.0
}
```

### Topology Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/projects/{id}/topology/graph` | Full graph structure |
| GET | `/projects/{id}/topology/routes?from=path_1&to=path_5` | Find routes between paths |
| POST | `/projects/{id}/topology/check-conflicts` | Check route conflicts |

**Route finding response:**

```json
{
  "routes": [
    {
      "steps": [
        {"path_id": "path_1", "entry_s": 0, "exit_s": 100},
        {"path_id": "path_3", "entry_s": 0, "exit_s": 150},
        {"path_id": "path_5", "entry_s": 0, "exit_s": 50}
      ],
      "switch_requirements": {"switch_1": "path_3"},
      "total_length": 300
    }
  ]
}
```

---

## Model Updates

### SimulationSettings Extensions

```python
class SimulationSettings(BaseModel):
    # Existing
    time_step_s: float = 0.01
    gravity_mps2: float = 9.81
    drag_coefficient: float = 0.5
    rolling_resistance_coefficient: float = 0.002
    air_density_kg_m3: float = 1.225

    # Geometry settings (new)
    geometry_sample_resolution_m: float = 0.01  # 1cm default
    max_curvature_per_m: float = 0.5           # Error threshold
    curvature_warning_radius_m: float = 10.0   # Warning threshold
    tangent_discontinuity_threshold_deg: float = 5.0
    junction_position_tolerance_m: float = 0.01
    bank_rate_threshold_deg_per_m: float = 10.0
```

### Path Model Extensions

```python
class Path(BaseModel):
    id: str
    point_ids: List[str]
    length_m: Optional[float] = None  # Computed from geometry
    is_valid: bool = True
    validation_issues: List[str] = []
```

**Migration strategy:** The new fields have default values, making them backward-compatible with existing project JSON files. When loading older projects:
- `length_m` remains `None` until geometry is computed
- `is_valid` defaults to `True`
- `validation_issues` defaults to empty list

No explicit migration script is needed. The geometry computation will populate these fields on first run.

---

## Testing Strategy

### Unit Tests

- Spline interpolation with known control points
- Arc length parameterization accuracy
- Curvature calculation for known geometries (circle, helix)
- Frame orthogonality verification
- Validation threshold tests
- Graph building and traversal
- Route finding with and without switch states
- Route conflict detection

### Integration Tests

- Full geometry pipeline: points → interpolated path
- Cache invalidation and recomputation
- Graph building from paths and junctions
- Route finding across multiple paths with switches

### Test Data

Provide sample track geometries:
- Simple straight path
- Curved path with known radius
- Banked turn
- Complete loop
- Multi-path layout with junctions and switches

### Test Accuracy Requirements

| Metric | Tolerance | Notes |
|--------|-----------|-------|
| Arc length error | < 0.001m (0.1% of segment) | Measured against analytical curves |
| Curvature error | < 1% for R > 5m | Higher tolerance for tight curves |
| Frame orthogonality | |T · N| < 1e-6 | Dot product should be near zero |
| Tangent unit length | |T| = 1 ± 1e-6 | Should be exactly normalized |
| Normal unit length | |N| = 1 ± 1e-6 | Should be exactly normalized |
| Binormal = T × N | |B| = 1 ± 1e-6 | Cross product consistency |
| Bank interpolation | < 0.1° deviation | At known control points |

Test geometries should include analytical curves where expected values can be computed:
- Circular arc: constant curvature κ = 1/R
- Straight line: zero curvature
- Helix: constant curvature and torsion

---

## Performance Considerations

1. **Sampling resolution:** Configurable per project, default 1cm
2. **Cache invalidation:** Recompute when points change
3. **Lazy computation:** Compute geometry on first access
4. **Graph updates:** Incremental updates when topology changes

---

## Out of Scope for Phase 2

- Physics simulation (Phase 3)
- Equipment force behavior (Phase 4)
- Control logic execution (Phase 5)
- 3D visualization (Phase 6)
- Performance optimization with Numba (Phase 3+)

---

## Success Criteria

Phase 2 is complete when:

1. Geometry engine computes centripetal Catmull-Rom spline from points
2. Bank angle interpolated using same spline
3. Arc length parameterization works correctly
4. Curvature and frames are computed accurately
5. Geometry cache with invalidation works
6. Geometry validation catches errors and warnings
7. Path graph builds from paths and junctions
8. Route finding works with switch state awareness
9. Route conflict detection identifies potential issues
10. All tests pass
11. API endpoints return correct data