"""LSM Launch system physics

LSM (Linear Synchronous Motor) launch systems use electromagnetic
stators to accelerate trains along a launch track.

The force is calculated based on:
1. Overlap between vehicle magnets and track stators
2. Electromagnetic parameters (B, I, L)
3. Speed-dependent effects (back-EMF)
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple

from app.models.equipment import LSMLaunch


@dataclass
class StatorState:
    """State of a single stator segment."""
    position_s: float  # Center position on path
    active: bool = False  # Currently covered by a vehicle magnet
    overlap_ratio: float = 0.0  # 0.0 to 1.0 - how much of stator is covered
    current_force_n: float = 0.0


@dataclass
class LSMState:
    """Runtime state for an LSM launch system."""
    enabled: bool = True
    current_force_n: float = 0.0
    stators_active: int = 0
    total_overlap_ratio: float = 0.0  # Sum of all stator overlaps
    stator_states: List[StatorState] = field(default_factory=list)


def compute_lsm_force(
    lsm: LSMLaunch,
    state: LSMState,
    train_s: float,
    train_velocity_mps: float,
    train_mass_kg: float,
    train_length_m: float = 10.0,
    vehicle_magnet_positions: Optional[List[Tuple[float, float]]] = None,
    dt: float = 0.01
) -> float:
    """
    Compute the force applied by an LSM launch system.

    The force is based on the electromagnetic interaction between
    track stators and vehicle magnets, considering overlap.

    Args:
        lsm: LSM launch equipment definition
        state: Current LSM runtime state
        train_s: Train front position (arc length)
        train_velocity_mps: Train velocity
        train_mass_kg: Total train mass
        train_length_m: Total train length
        vehicle_magnet_positions: List of (start_s, end_s) for each vehicle's magnet relative to train front
        dt: Time step for force ramping

    Returns:
        Force in Newtons (positive = accelerating)
    """
    if not state.enabled or not lsm.enabled:
        return 0.0

    # Check if train is in the launch zone
    if not (lsm.start_s <= train_s <= lsm.end_s):
        return 0.0

    # Initialize stator positions if not done
    if not state.stator_states:
        state.stator_states = _create_stator_states(lsm)

    # Use default magnet positions if not provided (backward compatibility)
    if vehicle_magnet_positions is None:
        # Default: assume magnets cover entire train length
        # Use simpler model where force is based on position in zone
        zone_length = lsm.end_s - lsm.start_s
        position_ratio = (train_s - lsm.start_s) / zone_length if zone_length > 0 else 0.0

        # Use legacy force calculation
        force = _legacy_lsm_force_model(lsm, position_ratio, train_velocity_mps)

        # Update state
        state.current_force_n = force
        state.stators_active = int(lsm.stator_count * (1.0 - position_ratio))
        state.total_overlap_ratio = position_ratio

        return force

    # Calculate train rear position
    train_rear_s = train_s - train_length_m

    # Calculate which stators are covered by vehicle magnets
    total_force = 0.0
    active_count = 0
    total_overlap = 0.0

    for stator in state.stator_states:
        stator_start = stator.position_s - lsm.stator_length_m / 2
        stator_end = stator.position_s + lsm.stator_length_m / 2

        # Calculate overlap with any vehicle magnet
        max_overlap = 0.0
        for magnet_start_rel, magnet_end_rel in vehicle_magnet_positions:
            # Convert magnet positions to absolute path positions
            # magnet positions are relative to train front (positive = behind front)
            magnet_start_s = train_s - magnet_start_rel
            magnet_end_s = train_s - magnet_end_rel

            # Calculate overlap
            overlap_start = max(stator_start, magnet_start_s)
            overlap_end = min(stator_end, magnet_end_s)
            overlap = max(0.0, overlap_end - overlap_start)
            overlap_ratio = overlap / lsm.stator_length_m
            max_overlap = max(max_overlap, overlap_ratio)

        stator.overlap_ratio = max_overlap
        stator.active = max_overlap > 0.0

        if stator.active:
            active_count += 1
            total_overlap += max_overlap

            # Calculate force for this stator based on overlap and electromagnetic params
            force = _compute_stator_force(lsm, max_overlap, train_velocity_mps)
            stator.current_force_n = force
            total_force += force
        else:
            stator.current_force_n = 0.0

    # Update state
    state.current_force_n = total_force
    state.stators_active = active_count
    state.total_overlap_ratio = total_overlap

    # If no overlap detected (train params may not match stator layout),
    # fall back to legacy model for backward compatibility
    if total_force == 0.0:
        zone_length = lsm.end_s - lsm.start_s
        position_ratio = (train_s - lsm.start_s) / zone_length if zone_length > 0 else 0.0
        return _legacy_lsm_force_model(lsm, position_ratio, train_velocity_mps)

    return total_force


def _interpolate_force_curve(
    force_curve: List[Dict[str, Any]],
    position_ratio: float,
    velocity_mps: float
) -> float:
    """
    Interpolate force from a force curve definition.

    Force curve format:
    [
        {"position": 0.0, "velocity_min": 0, "velocity_max": 10, "force": 50000},
        {"position": 0.5, "velocity_min": 0, "velocity_max": 20, "force": 45000},
        ...
    ]
    """
    if not force_curve:
        return 0.0

    # Filter points by velocity range
    valid_points = [
        p for p in force_curve
        if p.get("velocity_min", 0) <= velocity_mps <= p.get("velocity_max", float('inf'))
    ]

    if not valid_points:
        return 0.0

    # Sort by position
    valid_points.sort(key=lambda p: p.get("position", 0))

    # Find surrounding points for interpolation
    for i, point in enumerate(valid_points):
        if point.get("position", 0) >= position_ratio:
            if i == 0:
                return float(point.get("force", 0))
            prev = valid_points[i - 1]
            prev_pos = prev.get("position", 0)
            curr_pos = point.get("position", 0)
            prev_force = float(prev.get("force", 0))
            curr_force = float(point.get("force", 0))

            # Linear interpolation
            t = (position_ratio - prev_pos) / (curr_pos - prev_pos) if curr_pos > prev_pos else 0
            return prev_force + t * (curr_force - prev_force)

    # Return last point's force if position is beyond all points
    return float(valid_points[-1].get("force", 0))


def _legacy_lsm_force_model(
    lsm: LSMLaunch,
    position_ratio: float,
    velocity_mps: float
) -> float:
    """
    Legacy LSM force model for backward compatibility.

    Uses the original simple model where force is based on position
    in the launch zone and speed, without detailed magnet/stator overlap.

    Args:
        lsm: LSM equipment definition
        position_ratio: Position within launch zone (0.0 to 1.0)
        velocity_mps: Current velocity

    Returns:
        Force in Newtons
    """
    # If force curve is defined, use it directly
    if lsm.force_curve:
        return _interpolate_force_curve(lsm.force_curve, position_ratio, velocity_mps)

    # Speed-dependent factor (force decreases at high speeds)
    design_speed_mps = lsm.max_speed_mps if lsm.max_speed_mps > 0 else 30.0
    speed_factor = 1.0 / (1.0 + velocity_mps / design_speed_mps)

    # Position factor (force may vary along launch track)
    position_factor = 1.0 - 0.2 * position_ratio

    # Magnetic field factor (legacy parameter)
    if lsm.magnetic_field_strength is not None:
        field_factor = min(lsm.magnetic_field_strength, 1.0)
    else:
        field_factor = 1.0

    # Stator efficiency factor
    stator_factor = min(lsm.stator_count / 10.0, 1.0)

    # Base max force
    if lsm.max_force_n is not None:
        max_force = lsm.max_force_n
    else:
        # Calculate from electromagnetic parameters
        max_force = (
            lsm.magnetic_field_tesla *
            lsm.max_current_amps *
            lsm.active_length_m *
            lsm.efficiency *
            lsm.stator_count
        )

    return max_force * speed_factor * position_factor * field_factor * stator_factor


def _compute_stator_force(lsm: LSMLaunch, overlap_ratio: float, velocity_mps: float) -> float:
    """
    Compute force from a single stator based on overlap and speed.

    F = B * I * L * efficiency * overlap_ratio * speed_factor
    Or uses legacy max_force_n if electromagnetic params not set.

    Args:
        lsm: LSM equipment definition
        overlap_ratio: How much of the stator is covered (0.0 to 1.0)
        velocity_mps: Current train velocity

    Returns:
        Force in Newtons from this stator
    """
    # Speed factor: force decreases as speed approaches max speed
    # This models the back-EMF effect: V_back_emf = k * v
    # As back-EMF approaches supply voltage, current (and thus force) drops
    if lsm.max_speed_mps > 0:
        # Linear decrease model: force = max_force * (1 - v/v_max)
        speed_factor = max(0.0, 1.0 - velocity_mps / lsm.max_speed_mps)
    else:
        speed_factor = 1.0

    # Check if using legacy parameters (max_force_n set directly)
    if lsm.max_force_n is not None:
        # Legacy mode: max_force_n is total force, divide by stator count
        max_force_per_stator = lsm.max_force_n / max(1, lsm.stator_count)
    elif lsm.max_force_per_stator_n is not None:
        max_force_per_stator = lsm.max_force_per_stator_n
    else:
        # Calculate from electromagnetic parameters: F = B * I * L * efficiency
        max_force_per_stator = (
            lsm.magnetic_field_tesla *
            lsm.max_current_amps *
            lsm.active_length_m *
            lsm.efficiency
        )

    # Force is proportional to overlap (magnetic coverage)
    force = max_force_per_stator * overlap_ratio * speed_factor

    return force


def _create_stator_states(lsm: LSMLaunch) -> List[StatorState]:
    """
    Create stator states based on LSM configuration.

    Stators are evenly distributed along the launch zone.
    """
    stators = []

    # Calculate spacing if not provided
    zone_length = lsm.end_s - lsm.start_s
    if lsm.stator_spacing_m is not None:
        spacing = lsm.stator_spacing_m
    else:
        # Auto-calculate spacing to evenly distribute stators
        if lsm.stator_count > 1:
            spacing = zone_length / (lsm.stator_count - 1) if lsm.stator_count > 1 else zone_length
        else:
            spacing = zone_length

    # Create stator positions
    for i in range(lsm.stator_count):
        if lsm.stator_count == 1:
            position = (lsm.start_s + lsm.end_s) / 2
        else:
            position = lsm.start_s + i * spacing

        stators.append(StatorState(position_s=position))

    return stators


def compute_vehicle_magnet_positions(
    vehicle_lengths: List[float],
    vehicle_magnet_lengths: List[Optional[float]],
    vehicle_magnet_offsets: List[float],
    coupling_gaps: float = 0.5
) -> List[Tuple[float, float]]:
    """
    Calculate magnet positions relative to train front for all vehicles.

    Args:
        vehicle_lengths: Length of each vehicle in order (front to back)
        vehicle_magnet_lengths: Length of magnet on each vehicle (or None for full vehicle length)
        vehicle_magnet_offsets: Offset from vehicle front to magnet start
        coupling_gaps: Gap between vehicles

    Returns:
        List of (start_distance_from_front, end_distance_from_front) for each magnet
        Positive distance means behind the train front
    """
    magnet_positions = []
    current_distance = 0.0  # Distance from train front

    for i, (v_length, mag_length, mag_offset) in enumerate(
        zip(vehicle_lengths, vehicle_magnet_lengths, vehicle_magnet_offsets)
    ):
        # Use vehicle length if magnet length not specified
        actual_mag_length = mag_length if mag_length is not None else v_length

        # Magnet start is at current_distance + mag_offset from train front
        mag_start = current_distance + mag_offset
        mag_end = mag_start + actual_mag_length

        magnet_positions.append((mag_start, mag_end))

        # Move to next vehicle (add vehicle length + coupling gap)
        current_distance += v_length + coupling_gaps

    return magnet_positions


def get_train_magnet_positions_from_project(
    project,
    train_id: str,
    train_front_s: float
) -> Tuple[float, List[Tuple[float, float]]]:
    """
    Get train length and magnet positions from project data.

    Args:
        project: Project containing vehicles and trains
        train_id: ID of the train

    Returns:
        Tuple of (train_length_m, magnet_positions relative to train front)
    """
    # Find the train
    train = None
    for t in project.trains:
        if t.id == train_id:
            train = t
            break

    if train is None:
        return 0.0, []

    # Build vehicle data
    vehicle_lengths = []
    magnet_lengths = []
    magnet_offsets = []

    for v_id in train.vehicle_ids:
        vehicle = None
        for v in project.vehicles:
            if v.id == v_id:
                vehicle = v
                break

        if vehicle:
            vehicle_lengths.append(vehicle.length_m)
            magnet_lengths.append(vehicle.magnet_length_m)
            magnet_offsets.append(vehicle.magnet_offset_m)

    if not vehicle_lengths:
        return 0.0, []

    # Calculate train length
    train_length = sum(vehicle_lengths) + (len(vehicle_lengths) - 1) * train.coupling_gap_m

    # Calculate magnet positions
    magnet_positions = compute_vehicle_magnet_positions(
        vehicle_lengths, magnet_lengths, magnet_offsets, train.coupling_gap_m
    )

    return train_length, magnet_positions


def create_lsm_state(lsm: LSMLaunch) -> LSMState:
    """Create initial runtime state for an LSM."""
    return LSMState(
        enabled=lsm.enabled,
        current_force_n=0.0,
        stators_active=0,
        total_overlap_ratio=0.0,
        stator_states=[]  # Will be initialized on first use
    )