"""Physics simulation integrator"""

import math
from typing import Dict, List, Optional, TYPE_CHECKING
from app.models.project import Project
from app.models.train import Train, Vehicle
from app.models.common import LoadCase
from .types import (
    ForceComponents,
    GForceComponents,
    TrainPhysicsState,
    PhysicsStepResult,
    SimulationState,
)
from .forces import compute_forces
from .gforce import compute_gforces
from .dynamics import (
    compute_train_mass,
    compute_train_length,
    get_geometry_at_position,
)

if TYPE_CHECKING:
    from app.simulation.geometry import GeometryCache
    from app.simulation.equipment.manager import EquipmentManager


class PhysicsSimulator:
    """
    Physics simulation engine for roller coaster trains.

    Manages train states and integrates motion over time.
    """

    def __init__(
        self,
        project: Project,
        geometry_cache: 'GeometryCache',
        frontal_area_m2: float = 2.0  # Default frontal area
    ):
        """
        Initialize physics simulator.

        Args:
            project: Project with trains, vehicles, paths, settings
            geometry_cache: Pre-computed geometry for all paths
            frontal_area_m2: Default train frontal area for drag
        """
        self.project = project
        self.geometry_cache = geometry_cache
        self.frontal_area_m2 = frontal_area_m2

        self.time_s = 0.0
        self.running = False
        self.train_states: Dict[str, TrainPhysicsState] = {}

        # Build vehicle lookup
        self.vehicle_map: Dict[str, Vehicle] = {v.id: v for v in project.vehicles}

        # Initialize equipment manager (lazy import to avoid circular)
        from app.simulation.equipment.manager import EquipmentManager
        self.equipment_manager: Optional[EquipmentManager] = None
        if project.equipment:
            self.equipment_manager = EquipmentManager(project)

        # Initialize train states
        self._initialize_train_states()

    def _initialize_train_states(self) -> None:
        """Create initial physics states for all trains."""
        for train in self.project.trains:
            state = self._create_train_state(train)
            self.train_states[train.id] = state

    def _create_train_state(self, train: Train) -> TrainPhysicsState:
        """Create physics state for a single train."""
        mass = compute_train_mass(train, list(self.vehicle_map.values()), train.load_case)
        length = compute_train_length(train, list(self.vehicle_map.values()))

        # Use train's current position if set
        path_id = train.current_path_id or ""
        s_front = train.front_position_s

        return TrainPhysicsState(
            train_id=train.id,
            path_id=path_id,
            s_front_m=s_front,
            s_rear_m=max(0.0, s_front - length),
            velocity_mps=0.0,
            acceleration_mps2=0.0,
            mass_kg=mass,
            forces=ForceComponents(),
            gforces=GForceComponents()
        )

    def step(self, dt: Optional[float] = None) -> PhysicsStepResult:
        """
        Advance simulation by one time step.

        Args:
            dt: Time step (uses project settings if not specified)

        Returns:
            PhysicsStepResult with updated train states
        """
        if dt is None:
            dt = self.project.simulation_settings.time_step_s

        settings = self.project.simulation_settings

        for train_id, state in self.train_states.items():
            self._step_train(state, dt, settings)

        self.time_s += dt

        return PhysicsStepResult(
            time_s=self.time_s,
            dt_s=dt,
            trains=list(self.train_states.values())
        )

    def _step_train(
        self,
        state: TrainPhysicsState,
        dt: float,
        settings
    ) -> None:
        """Update a single train's state for one time step."""
        # Get geometry at train's current position
        sample = get_geometry_at_position(
            self.geometry_cache,
            state.path_id,
            state.s_front_m
        )

        if sample is None:
            # Train not on valid geometry - skip
            return

        # Compute equipment force
        equipment_force_n = 0.0
        if self.equipment_manager:
            equipment_force_n = self.equipment_manager.compute_equipment_force(
                train_path_id=state.path_id,
                train_s=state.s_front_m,
                train_velocity_mps=state.velocity_mps,
                train_mass_kg=state.mass_kg,
                dt=dt
            )

        # Compute forces
        forces = compute_forces(
            mass_kg=state.mass_kg,
            velocity_mps=state.velocity_mps,
            slope_rad=math.radians(sample.slope_deg),
            drag_coefficient=settings.drag_coefficient,
            frontal_area_m2=self.frontal_area_m2,
            rolling_coefficient=settings.rolling_resistance_coefficient,
            gravity_mps2=settings.gravity_mps2,
            air_density_kg_m3=settings.air_density_kg_m3,
            equipment_force_n=equipment_force_n
        )

        # Compute acceleration: F = ma => a = F/m
        acceleration = forces.total_n / state.mass_kg

        # Update velocity (with simple bounds checking)
        new_velocity = state.velocity_mps + acceleration * dt

        # Don't allow negative velocity (train can't go backwards)
        if new_velocity < 0:
            new_velocity = 0.0
            acceleration = 0.0

        # Update position
        new_s_front = state.s_front_m + new_velocity * dt

        # Get path length for boundary checking
        try:
            path_data = self.geometry_cache.get_path(state.path_id)
            max_s = path_data.total_length
        except (ValueError, KeyError):
            max_s = float('inf')

        # Clamp to path bounds (train stops at end of path for now)
        if new_s_front > max_s:
            new_s_front = max_s
            new_velocity = 0.0

        # Compute g-forces
        gforces = compute_gforces(
            velocity_mps=new_velocity,
            curvature_per_m=sample.curvature,
            slope_deg=sample.slope_deg,
            bank_deg=sample.bank_deg,
            gravity_mps2=settings.gravity_mps2
        )

        # Update state
        state.velocity_mps = new_velocity
        state.acceleration_mps2 = acceleration
        state.s_front_m = new_s_front
        state.s_rear_m = max(0.0, new_s_front - compute_train_length(
            next(t for t in self.project.trains if t.id == state.train_id),
            list(self.vehicle_map.values())
        ))
        state.forces = forces
        state.gforces = gforces

    def run(self, duration_s: float, dt: Optional[float] = None) -> List[PhysicsStepResult]:
        """
        Run simulation for a duration.

        Args:
            duration_s: Total time to simulate
            dt: Time step (uses project settings if not specified)

        Returns:
            List of step results
        """
        if dt is None:
            dt = self.project.simulation_settings.time_step_s

        results = []
        elapsed = 0.0

        while elapsed < duration_s:
            result = self.step(dt)
            results.append(result)
            elapsed += dt

        return results

    def reset(self) -> None:
        """Reset simulation to initial state."""
        self.time_s = 0.0
        self.running = False
        self.train_states.clear()
        self._initialize_train_states()
        if self.equipment_manager:
            self.equipment_manager.reset()

    def set_train_velocity(self, train_id: str, velocity_mps: float) -> None:
        """Set a train's velocity."""
        if train_id in self.train_states:
            self.train_states[train_id].velocity_mps = velocity_mps

    def set_train_position(self, train_id: str, path_id: str, s: float) -> None:
        """Set a train's position."""
        if train_id in self.train_states:
            state = self.train_states[train_id]
            state.path_id = path_id
            state.s_front_m = s
            train = next((t for t in self.project.trains if t.id == train_id), None)
            if train:
                length = compute_train_length(train, list(self.vehicle_map.values()))
                state.s_rear_m = max(0.0, s - length)

    def get_train_state(self, train_id: str) -> Optional[TrainPhysicsState]:
        """Get current state of a train."""
        return self.train_states.get(train_id)

    def get_all_states(self) -> List[TrainPhysicsState]:
        """Get states of all trains."""
        return list(self.train_states.values())

    def get_simulation_state(self) -> SimulationState:
        """Get overall simulation state."""
        return SimulationState(
            time_s=self.time_s,
            running=self.running,
            trains=self.get_all_states()
        )