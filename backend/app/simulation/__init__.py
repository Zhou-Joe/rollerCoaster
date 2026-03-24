"""Simulation engine for roller coaster dynamics"""

from .geometry import (
    GeometryError,
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
from .physics import (
    ForceComponents,
    GForceComponents,
    TrainPhysicsState,
    PhysicsStepResult,
    SimulationState,
    PhysicsSimulator,
    compute_train_mass,
    compute_train_length,
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
    'ForceComponents',
    'GForceComponents',
    'TrainPhysicsState',
    'PhysicsStepResult',
    'SimulationState',
    'PhysicsSimulator',
    'compute_train_mass',
    'compute_train_length',
]