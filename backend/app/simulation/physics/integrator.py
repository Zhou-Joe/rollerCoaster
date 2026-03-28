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

        # Debug: Log junction info
        # print(f"[DEBUG] Simulator initialized with {len(self.project.junctions)} junctions:")
        # for j in self.project.junctions:
        #     print(f"[DEBUG]   Junction {j.id}: incoming={j.incoming_path_id}, outgoing={j.outgoing_path_ids}")

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
            gforces=GForceComponents(),
            kinetic_energy_j=0.0,
            potential_energy_j=0.0,
            total_energy_j=0.0
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
            # Train not on valid geometry - this is a critical error
            print(f"[ERROR] No geometry found for train {state.train_id} on path {state.path_id} at s={state.s_front_m}")
            # Try to get the path to see if it exists
            try:
                path_data = self.geometry_cache.get_path(state.path_id)
                print(f"[ERROR] Path {state.path_id} exists with length {path_data.total_length}, samples={len(path_data.samples)}")
            except Exception as e:
                print(f"[ERROR] Path {state.path_id} not found in geometry cache: {e}")
            return

        # Compute equipment force and any velocity override (e.g., from lift)
        equipment_force_n = 0.0
        lift_velocity_override = None
        equipment_breakdown = None
        if self.equipment_manager:
            equipment_force_n, lift_velocity_override, equipment_breakdown = self.equipment_manager.compute_equipment_force(
                train_path_id=state.path_id,
                train_s=state.s_front_m,
                train_velocity_mps=state.velocity_mps,
                train_mass_kg=state.mass_kg,
                train_id=state.train_id,
                dt=dt
            )

        # If lift is engaged, it overrides velocity directly
        if lift_velocity_override is not None:
            new_velocity = lift_velocity_override
            # Position update uses lift speed
            new_s_front = state.s_front_m + new_velocity * dt

            # Get path length for boundary checking
            original_path_id = state.path_id
            try:
                path_data = self.geometry_cache.get_path(state.path_id)
                max_s = path_data.total_length
            except (ValueError, KeyError):
                max_s = float('inf')

            # Check for junction transition (forward only - lift doesn't go backward)
            if new_s_front >= max_s:
                new_s_front = self._check_junction_transition(state, new_s_front, max_s, new_velocity)
                if state.path_id == original_path_id and new_s_front >= max_s:
                    new_velocity = 0.0
                # Get geometry from new path if transition happened
                if state.path_id != original_path_id:
                    # print(f"[DEBUG] Lift mode: path changed from {original_path_id} to {state.path_id}")
                    new_sample = get_geometry_at_position(
                        self.geometry_cache,
                        state.path_id,
                        new_s_front
                    )
                    if new_sample is not None:
                        sample = new_sample
            elif new_s_front < 0:
                # Clamp to start (shouldn't happen on lift, but safety check)
                new_s_front = 0.0
                new_velocity = 0.0

            current_sample = get_geometry_at_position(
                self.geometry_cache,
                state.path_id,
                new_s_front
            )
            if current_sample is not None:
                sample = current_sample

            # Compute g-forces at new position
            gforces = compute_gforces(
                velocity_mps=new_velocity,
                curvature_per_m=sample.curvature,
                slope_deg=sample.slope_deg,
                bank_deg=sample.bank_deg,
                gravity_mps2=settings.gravity_mps2
            )

            # Energy while on lift
            height_m = sample.position[2] if hasattr(sample, 'position') and sample.position else 0.0
            kinetic_energy = 0.5 * state.mass_kg * new_velocity * new_velocity
            potential_energy = state.mass_kg * settings.gravity_mps2 * height_m

            # Update state
            state.velocity_mps = new_velocity
            state.acceleration_mps2 = 0.0  # On lift, no relative acceleration
            state.s_front_m = new_s_front
            state.s_rear_m = max(0.0, new_s_front - compute_train_length(
                next(t for t in self.project.trains if t.id == state.train_id),
                list(self.vehicle_map.values())
            ))
            state.forces = ForceComponents(
                gravity_tangent_n=0.0,
                drag_n=0.0,
                rolling_resistance_n=0.0,
                equipment_n=0.0,
                total_n=0.0
            )
            state.gforces = gforces
            state.kinetic_energy_j = kinetic_energy
            state.potential_energy_j = potential_energy
            state.total_energy_j = kinetic_energy + potential_energy

            # Update equipment force breakdown for lift mode
            if equipment_breakdown:
                from .types import EquipmentForceBreakdown
                state.equipment_forces = EquipmentForceBreakdown(
                    lsm_force_n=equipment_breakdown.lsm_force_n,
                    lift_force_n=equipment_breakdown.lift_force_n,
                    brake_force_n=equipment_breakdown.brake_force_n,
                    booster_force_n=equipment_breakdown.booster_force_n,
                    trim_force_n=equipment_breakdown.trim_force_n,
                    lsm_stators_active=equipment_breakdown.lsm_stators_active,
                    lsm_overlap_ratio=equipment_breakdown.lsm_overlap_ratio
                )

            # Skip normal physics - lift controls everything
            return

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

        # Update velocity - allow negative velocity for rollback
        new_velocity = state.velocity_mps + acceleration * dt

        # Advance distance with constant-acceleration kinematics for this step.
        new_s_front = state.s_front_m + state.velocity_mps * dt + 0.5 * acceleration * dt * dt

        # Get path length for boundary checking
        original_path_id = state.path_id
        try:
            path_data = self.geometry_cache.get_path(state.path_id)
            max_s = path_data.total_length
        except (ValueError, KeyError):
            max_s = float('inf')

        # Check for junction/switch at path boundary
        # This may update state.path_id and return adjusted position
        new_s_front = self._check_junction_transition(state, new_s_front, max_s, new_velocity)

        # After junction transition, get geometry from the NEW path
        if state.path_id != original_path_id:
            # Path changed due to junction transition - get new geometry
            # print(f"[DEBUG] Path changed from {original_path_id} to {state.path_id}, getting new geometry at s={new_s_front}")
            new_sample = get_geometry_at_position(
                self.geometry_cache,
                state.path_id,
                new_s_front
            )
            if new_sample is not None:
                sample = new_sample
            else:
                print(f"[DEBUG] WARNING: Failed to get geometry for new path {state.path_id} at s={new_s_front}")
        else:
            if new_velocity > 0 and new_s_front >= max_s:
                new_velocity = 0.0
                acceleration = 0.0
            # Check if we're stuck at a boundary with no junction
            if new_velocity < 0 and new_s_front <= 0.01:
                # Train is at start of path with backward velocity but no junction transition
                # print(f"[DEBUG] Train stuck at start of {state.path_id}, stopping backward motion")
                new_velocity = 0.0
                acceleration = 0.0

        current_sample = get_geometry_at_position(
            self.geometry_cache,
            state.path_id,
            new_s_front
        )
        if current_sample is not None:
            sample = current_sample

        # Compute g-forces
        gforces = compute_gforces(
            velocity_mps=new_velocity,
            curvature_per_m=sample.curvature,
            slope_deg=sample.slope_deg,
            bank_deg=sample.bank_deg,
            gravity_mps2=settings.gravity_mps2
        )

        # Compute energy components
        # Get height at current position (position is [x, y, z] where z=up)
        height_m = sample.position[2] if hasattr(sample, 'position') and sample.position else 0.0
        kinetic_energy = 0.5 * state.mass_kg * new_velocity * new_velocity
        potential_energy = state.mass_kg * settings.gravity_mps2 * height_m

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
        state.kinetic_energy_j = kinetic_energy
        state.potential_energy_j = potential_energy
        state.total_energy_j = kinetic_energy + potential_energy

        # Update equipment force breakdown
        if equipment_breakdown:
            from .types import EquipmentForceBreakdown
            state.equipment_forces = EquipmentForceBreakdown(
                lsm_force_n=equipment_breakdown.lsm_force_n,
                lift_force_n=equipment_breakdown.lift_force_n,
                brake_force_n=equipment_breakdown.brake_force_n,
                booster_force_n=equipment_breakdown.booster_force_n,
                trim_force_n=equipment_breakdown.trim_force_n,
                lsm_stators_active=equipment_breakdown.lsm_stators_active,
                lsm_overlap_ratio=equipment_breakdown.lsm_overlap_ratio
            )

        # Debug: Log state after junction transition
        # if state.path_id != original_path_id:
        #     print(f"[DEBUG] Train {state.train_id} state after transition: path={state.path_id}, s={state.s_front_m:.2f}, v={state.velocity_mps:.2f}")

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

    def _check_junction_transition(self, state: TrainPhysicsState, new_s_front: float, max_s: float, velocity: float) -> float:
        """
        Check if train has reached a junction and handle path transition.

        Handles both forward transitions (train reaches end of path) and
        backward transitions (train reverses past start of path).

        Returns the adjusted position (new_s_front or offset into new path).
        """
        # Get train length for position validation
        train = next((t for t in self.project.trains if t.id == state.train_id), None)
        train_length = compute_train_length(train, list(self.vehicle_map.values())) if train else 10.0

        # Check if we've passed the end of the current path (forward movement)
        if new_s_front >= max_s:
            # print(f"[DEBUG] Train {state.train_id} at end of path {state.path_id}: s={new_s_front}, max_s={max_s}")
            # Look for a junction at the end of this path
            for junction in self.project.junctions:
                if junction.incoming_path_id == state.path_id:
                    # Check if there's a track switch controlling this junction
                    switch_alignment = None
                    for equip_dict in self.project.equipment:
                        if equip_dict.get('equipment_type') == 'track_switch':
                            if equip_dict.get('junction_id') == junction.id or \
                               equip_dict.get('incoming_path_id') == state.path_id:
                                switch_alignment = equip_dict.get('current_alignment')
                                break

                    # Determine which outgoing path to take
                    outgoing_paths = junction.outgoing_path_ids
                    if not outgoing_paths:
                        # No outgoing paths, stop at boundary
                        return max_s

                    # Use switch alignment if available, otherwise take first path
                    selected_path = switch_alignment if switch_alignment and switch_alignment in outgoing_paths else outgoing_paths[0]

                    # Get new path length
                    try:
                        new_path_data = self.geometry_cache.get_path(selected_path)
                        new_path_max_s = new_path_data.total_length
                    except (ValueError, KeyError):
                        new_path_max_s = 1000.0

                    # Transition to new path - position train so all vehicles are on new path
                    overshoot = new_s_front - max_s
                    # Ensure position is at least train_length so rear is at valid position
                    new_position = max(train_length + 0.1, overshoot)

                    # print(f"[DEBUG] Forward transition: {state.path_id} -> {selected_path}, pos={new_position}")
                    state.path_id = selected_path
                    return new_position

            # No junction found, stop at boundary
            # print(f"[DEBUG] No junction found for forward transition from {state.path_id}")
            return max_s

        # Check if we've passed the start of the current path (backward movement)
        if new_s_front < 0:
            # print(f"[DEBUG] Backward junction check: train {state.train_id} at s={new_s_front} on path {state.path_id}")
            # print(f"[DEBUG] Current velocity: {velocity}")
            # print(f"[DEBUG] Looking for junction where '{state.path_id}' is an outgoing path...")
            # Look for a junction where current path is an outgoing path
            found_junction = False
            for junction in self.project.junctions:
                if state.path_id in junction.outgoing_path_ids:
                    found_junction = True
                    # Transition back to the incoming path
                    incoming_path_id = junction.incoming_path_id

                    # Get the length of the incoming path to position from its end
                    try:
                        incoming_path_data = self.geometry_cache.get_path(incoming_path_id)
                        incoming_max_s = incoming_path_data.total_length
                    except (ValueError, KeyError) as e:
                        # print(f"[DEBUG] Failed to get incoming path {incoming_path_id}: {e}")
                        incoming_max_s = 1000.0  # fallback

                    # Position at end of incoming path, ensuring train is fully on path
                    # new_s_front is negative (how far past start we went)
                    new_position = incoming_max_s + new_s_front  # near end of incoming path
                    # Ensure position doesn't go past path end
                    new_position = min(incoming_max_s - 0.1, new_position)
                    new_position = max(train_length, new_position)  # ensure rear is valid

                    # print(f"[DEBUG] Backward transition: {state.path_id} -> {incoming_path_id}, pos={new_position}, incoming_max_s={incoming_max_s}")
                    state.path_id = incoming_path_id
                    return new_position

            # No junction found, stop at boundary
            # print(f"[DEBUG] No junction found for backward transition from {state.path_id}, found_junction={found_junction}")
            return 0.0

        return new_s_front

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
