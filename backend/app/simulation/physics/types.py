"""Physics types for train simulation"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ForceComponents:
    """Individual force components acting on a train."""
    gravity_tangent_n: float = 0.0
    drag_n: float = 0.0
    rolling_resistance_n: float = 0.0
    equipment_n: float = 0.0  # Launch, lift, brake, booster forces
    total_n: float = 0.0


@dataclass
class GForceComponents:
    """G-force components experienced by passengers."""
    normal_g: float = 0.0      # Perpendicular to track (into seat)
    lateral_g: float = 0.0     # Side-to-side relative to train
    vertical_g: float = 0.0    # Up-down relative to train body
    resultant_g: float = 0.0   # Magnitude of total g-force


@dataclass
class TrainPhysicsState:
    """Complete physics state for a single train."""
    train_id: str
    path_id: str
    s_front_m: float          # Front position (arc length)
    s_rear_m: float           # Rear position (arc length)
    velocity_mps: float       # Speed along track
    acceleration_mps2: float  # Current acceleration
    mass_kg: float            # Total mass (includes passengers)
    forces: ForceComponents = field(default_factory=ForceComponents)
    gforces: GForceComponents = field(default_factory=GForceComponents)
    # Energy components
    kinetic_energy_j: float = 0.0      # KE = 1/2 * m * v^2
    potential_energy_j: float = 0.0    # PE = m * g * h
    total_energy_j: float = 0.0        # Total energy


@dataclass
class PhysicsStepResult:
    """Result of a single simulation step."""
    time_s: float
    dt_s: float
    trains: List[TrainPhysicsState]


@dataclass
class SimulationState:
    """Overall simulation state."""
    time_s: float = 0.0
    running: bool = False
    trains: List[TrainPhysicsState] = field(default_factory=list)