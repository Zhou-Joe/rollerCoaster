"""Physics simulation module"""

from .types import (
    ForceComponents,
    GForceComponents,
    TrainPhysicsState,
    PhysicsStepResult,
    SimulationState,
)
from .forces import (
    gravity_force,
    drag_force,
    rolling_resistance_force,
    compute_forces,
)
from .gforce import (
    normal_acceleration,
    compute_gforces,
)
from .dynamics import (
    compute_train_mass,
    compute_train_length,
    get_geometry_at_position,
)
from .integrator import PhysicsSimulator

__all__ = [
    'ForceComponents',
    'GForceComponents',
    'TrainPhysicsState',
    'PhysicsStepResult',
    'SimulationState',
    'gravity_force',
    'drag_force',
    'rolling_resistance_force',
    'compute_forces',
    'normal_acceleration',
    'compute_gforces',
    'compute_train_mass',
    'compute_train_length',
    'get_geometry_at_position',
    'PhysicsSimulator',
]