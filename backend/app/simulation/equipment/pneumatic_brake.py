"""Pneumatic brake physics with overlap calculation

Pneumatic brakes use compressed air to apply braking force.
They support two fail-safe modes:
- normally_open: Brake is open when no air pressure (freewheeling)
- normally_closed: Brake is closed when no air pressure (emergency stop)

Force is calculated based on overlap between vehicle magnets and brake zone,
similar to LSM launch system. Actual braking force = max_force * overlap_ratio.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from app.models.equipment import PneumaticBrake
from app.models.common import FailSafeMode, BrakeState


@dataclass
class PneumaticBrakeState:
    """Runtime state for a pneumatic brake."""
    state: BrakeState = BrakeState.OPEN
    current_force_n: float = 0.0
    response_progress: float = 1.0  # 1.0 = fully responded
    effective_brake_force_n: float = 0.0
    overlap_ratio: float = 0.0  # Current overlap between train and brake zone


def compute_pneumatic_brake_force(
    brake: PneumaticBrake,
    state: PneumaticBrakeState,
    train_s: float,
    train_velocity_mps: float,
    train_length_m: float = 10.0,
    vehicle_magnet_positions: Optional[List[Tuple[float, float]]] = None,
    dt: float = 0.01
) -> float:
    """
    Compute the force applied by a pneumatic brake based on vehicle overlap.

    The brake applies force proportional to the overlap between vehicle magnets
    and the brake zone. This is similar to LSM launch system calculation.

    Args:
        brake: Pneumatic brake equipment definition
        state: Current brake runtime state
        train_s: Train front position (arc length)
        train_velocity_mps: Train velocity
        train_length_m: Total train length
        vehicle_magnet_positions: List of (start_s, end_s) for each vehicle's magnet relative to train front
        dt: Time step for response time simulation

    Returns:
        Force in Newtons (negative = braking)
    """
    # Check if train is anywhere near brake zone
    train_rear_s = train_s - train_length_m
    if train_s < brake.start_s or train_rear_s > brake.end_s:
        state.current_force_n = 0.0
        state.overlap_ratio = 0.0
        return 0.0

    # If brake is open, no force regardless of overlap
    if state.state == BrakeState.OPEN:
        state.current_force_n = 0.0
        state.overlap_ratio = 0.0
        return 0.0

    # Calculate overlap between vehicle magnets and brake zone
    brake_zone_length = brake.end_s - brake.start_s
    total_overlap_ratio = 0.0

    if vehicle_magnet_positions:
        # Calculate overlap for each vehicle magnet
        for magnet_start_rel, magnet_end_rel in vehicle_magnet_positions:
            # Convert magnet positions to absolute path positions
            # magnet positions are relative to train front (positive = behind front)
            magnet_end_s = train_s - magnet_start_rel  # Closer to front (higher s)
            magnet_start_s = train_s - magnet_end_rel  # Further back (lower s)

            # Calculate overlap with brake zone
            overlap_start = max(brake.start_s, magnet_start_s)
            overlap_end = min(brake.end_s, magnet_end_s)
            overlap_length = max(0.0, overlap_end - overlap_start)

            # Add to total overlap (as ratio of brake zone)
            if brake_zone_length > 0:
                total_overlap_ratio += overlap_length / brake_zone_length
    else:
        # Fallback: simple overlap calculation based on train front position
        position_in_zone = max(0, min(train_s, brake.end_s) - brake.start_s)
        total_overlap_ratio = position_in_zone / brake_zone_length if brake_zone_length > 0 else 0.0

    # Clamp overlap ratio to 0-1 range
    total_overlap_ratio = min(1.0, max(0.0, total_overlap_ratio))
    state.overlap_ratio = total_overlap_ratio

    # Determine target brake force based on state
    target_force_magnitude = _compute_target_brake_force(
        brake, state.state, train_velocity_mps
    )

    # Apply overlap ratio - force proportional to overlap
    target_force_magnitude *= total_overlap_ratio

    # Simulate response time (pneumatic actuation delay)
    response_rate = 1.0 / brake.response_time_s if brake.response_time_s > 0 else float('inf')
    current_force_magnitude = abs(state.effective_brake_force_n)
    force_diff = target_force_magnitude - current_force_magnitude
    max_change = response_rate * dt * brake.max_brake_force_n

    if abs(force_diff) <= max_change:
        new_force_magnitude = target_force_magnitude
        state.response_progress = 1.0
    else:
        new_force_magnitude = current_force_magnitude + math.copysign(max_change, force_diff)
        state.response_progress = 0.5  # In transition

    # Apply force curve if defined
    if brake.force_curve:
        new_force_magnitude = _apply_brake_force_curve(
            brake.force_curve,
            new_force_magnitude,
            train_velocity_mps
        )

    state.effective_brake_force_n = new_force_magnitude
    # Force always opposes velocity direction (braking)
    if abs(train_velocity_mps) < 1e-6:
        # Train is essentially stopped - apply holding brake force
        # When velocity is essentially zero, we need to check the direction we want to oppose
        # If there's any motion tendency, brakes should oppose it
        # For now, apply force in direction that opposes any motion
        # Use the sign of the previous force or default to opposing forward
        state.current_force_n = -new_force_magnitude  # Hold against forward by default
    else:
        state.current_force_n = -math.copysign(new_force_magnitude, train_velocity_mps)

    return state.current_force_n


def _compute_target_brake_force(
    brake: PneumaticBrake,
    brake_state: BrakeState,
    velocity_mps: float
) -> float:
    """
    Compute target brake force magnitude based on state.

    Args:
        brake: Pneumatic brake equipment definition
        brake_state: Current commanded brake state
        velocity_mps: Train velocity

    Returns:
        Target brake force magnitude (positive value)
    """
    if brake_state == BrakeState.OPEN:
        return 0.0

    elif brake_state == BrakeState.CLOSED:
        # Closed = full braking capability
        return _compute_velocity_dependent_force(
            brake.max_brake_force_n,
            velocity_mps,
            brake.air_pressure
        )

    elif brake_state == BrakeState.EMERGENCY_STOP:
        # Emergency stop = maximum braking
        return brake.max_brake_force_n

    return 0.0


def _compute_velocity_dependent_force(
    max_force_n: float,
    velocity_mps: float,
    air_pressure: float
) -> float:
    """
    Compute brake force considering velocity and pressure.

    Pneumatic brakes have:
    - Force proportional to air pressure
    - Full effectiveness across speed range (can stop completely)
    """
    # Air pressure factor (normalized to 1.0 at typical pressure)
    # Typical pneumatic system: 6-8 bar
    typical_pressure = 7.0
    pressure_factor = min(air_pressure / typical_pressure, 1.5)

    # Pneumatic brakes maintain effectiveness at all speeds, including near zero
    # This allows them to bring the train to a complete stop
    speed_factor = 1.0

    return max_force_n * pressure_factor * speed_factor


def _apply_brake_force_curve(
    force_curve: List[Dict[str, Any]],
    base_force: float,
    velocity_mps: float
) -> float:
    """
    Apply a force curve to modify brake force.

    Force curve format:
    [
        {"velocity": 0, "force_factor": 1.0},
        {"velocity": 10, "force_factor": 0.9},
        {"velocity": 20, "force_factor": 0.8},
    ]
    """
    if not force_curve:
        return base_force

    # Sort by velocity
    sorted_curve = sorted(force_curve, key=lambda p: p.get("velocity", 0))

    # Find surrounding points
    for i, point in enumerate(sorted_curve):
        if point.get("velocity", 0) >= velocity_mps:
            if i == 0:
                factor = float(point.get("force_factor", 1.0))
                return base_force * factor
            prev = sorted_curve[i - 1]
            prev_v = prev.get("velocity", 0)
            curr_v = point.get("velocity", 0)
            prev_f = float(prev.get("force_factor", 1.0))
            curr_f = float(point.get("force_factor", 1.0))

            # Linear interpolation
            t = (velocity_mps - prev_v) / (curr_v - prev_v) if curr_v > prev_v else 0
            factor = prev_f + t * (curr_f - prev_f)
            return base_force * factor

    # Return last point's factor if velocity is beyond all points
    factor = float(sorted_curve[-1].get("force_factor", 1.0))
    return base_force * factor


def set_brake_state(
    brake: PneumaticBrake,
    state: PneumaticBrakeState,
    new_state: BrakeState
) -> None:
    """
    Set the brake state, respecting fail-safe behavior.

    Args:
        brake: Pneumatic brake equipment definition
        state: Current brake runtime state
        new_state: Desired brake state
    """
    state.state = new_state
    state.response_progress = 0.0  # Start response transition


def apply_fail_safe(
    brake: PneumaticBrake,
    state: PneumaticBrakeState
) -> None:
    """
    Apply fail-safe behavior (e.g., when power is lost).

    Args:
        brake: Pneumatic brake equipment definition
        state: Current brake runtime state
    """
    if brake.fail_safe_mode == FailSafeMode.NORMALLY_OPEN:
        # Loss of air pressure = brake stays open
        state.state = BrakeState.OPEN
    else:  # normally_closed
        # Loss of air pressure = spring applies brake
        state.state = BrakeState.CLOSED


def create_pneumatic_brake_state(brake: PneumaticBrake) -> PneumaticBrakeState:
    """Create initial runtime state for a pneumatic brake."""
    return PneumaticBrakeState(
        state=brake.state,
        current_force_n=0.0,
        response_progress=1.0,
        effective_brake_force_n=0.0,
        overlap_ratio=0.0
    )
