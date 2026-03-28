"""Trim brake physics with electromagnetic braking (eddy current brake)

Trim brakes use electromagnetic induction (eddy currents) to provide braking force.
The braking force follows the formula: F = B² * L * V * k / R
Where:
- B = magnetic field strength (Tesla)
- L = overlap length between magnets and conductive rail
- V = train velocity
- k = geometric constant
- R = rail resistance

This provides smooth, contactless braking that increases with speed.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple

from app.models.equipment import TrimBrake


@dataclass
class TrimBrakeState:
    """Runtime state for a trim brake."""
    enabled: bool = True
    current_force_n: float = 0.0
    effective_force_n: float = 0.0
    overlap_ratio: float = 0.0  # Current overlap between train magnets and brake zone
    overlap_length_m: float = 0.0  # Actual overlap length in meters


def compute_trim_brake_force(
    trim: TrimBrake,
    state: TrimBrakeState,
    train_s: float,
    train_velocity_mps: float,
    train_length_m: float = 10.0,
    vehicle_magnet_positions: Optional[List[Tuple[float, float]]] = None,
    dt: float = 0.01
) -> float:
    """
    Compute the electromagnetic braking force from trim brake.

    Uses eddy current braking formula: F ∝ B² * L * V
    Where B is magnetic field, L is overlap length, V is velocity.

    Args:
        trim: Trim brake equipment definition
        state: Current trim brake runtime state
        train_s: Train front position (arc length)
        train_velocity_mps: Train velocity
        train_length_m: Total train length
        vehicle_magnet_positions: List of (start_s, end_s) for each vehicle's magnet relative to train front
        dt: Time step

    Returns:
        Force in Newtons (negative = braking)
    """
    if not state.enabled or not trim.enabled:
        state.current_force_n = 0.0
        state.overlap_ratio = 0.0
        state.overlap_length_m = 0.0
        return 0.0

    # Check if train is anywhere near trim zone
    train_rear_s = train_s - train_length_m
    if train_s < trim.start_s or train_rear_s > trim.end_s:
        state.current_force_n = 0.0
        state.overlap_ratio = 0.0
        state.overlap_length_m = 0.0
        return 0.0

    # Calculate overlap between vehicle magnets and trim brake zone
    trim_zone_length = trim.end_s - trim.start_s
    total_overlap_length = 0.0

    if vehicle_magnet_positions:
        # Calculate overlap for each vehicle magnet
        for magnet_start_rel, magnet_end_rel in vehicle_magnet_positions:
            # Convert magnet positions to absolute path positions
            # magnet positions are relative to train front (positive = behind front)
            magnet_end_s = train_s - magnet_start_rel  # Closer to front (higher s)
            magnet_start_s = train_s - magnet_end_rel  # Further back (lower s)

            # Calculate overlap with trim zone
            overlap_start = max(trim.start_s, magnet_start_s)
            overlap_end = min(trim.end_s, magnet_end_s)
            overlap_length = max(0.0, overlap_end - overlap_start)
            total_overlap_length += overlap_length
    else:
        # Fallback: simple overlap calculation based on train front position
        position_in_zone = max(0, min(train_s, trim.end_s) - trim.start_s)
        total_overlap_length = position_in_zone

    # Clamp overlap length
    total_overlap_length = max(0.0, min(total_overlap_length, trim_zone_length))
    state.overlap_length_m = total_overlap_length
    state.overlap_ratio = total_overlap_length / trim_zone_length if trim_zone_length > 0 else 0.0

    # No overlap = no force
    if total_overlap_length <= 0:
        state.current_force_n = 0.0
        return 0.0

    # Electromagnetic braking force: F = B² * L * V * k
    # Where:
    # - B = magnetic_field_strength (Tesla, default 1.0T)
    # - L = total_overlap_length (meters)
    # - V = train_velocity_mps (m/s)
    # - k = efficiency factor based on rail conductivity and geometry

    magnetic_field_tesla = getattr(trim, 'magnetic_field_tesla', 1.0)

    # Eddy current braking force is proportional to:
    # - B² (magnetic field squared)
    # - L (overlap length)
    # - V (velocity - eddy currents increase with speed)
    # - efficiency factor

    b_squared = magnetic_field_tesla ** 2

    # Base eddy current force coefficient (N/(T²·m·m/s))
    # Typical values for eddy current brakes: 50-200 N per T² per meter per m/s
    eddy_current_coefficient = getattr(trim, 'eddy_current_coefficient', 100.0)

    # Compute raw electromagnetic force
    # F = coefficient * B² * L * V
    raw_force = eddy_current_coefficient * b_squared * total_overlap_length * train_velocity_mps

    # Apply velocity limiting - eddy current brakes become less effective at very high speeds
    # due to saturation and heating effects
    max_effective_speed = getattr(trim, 'max_effective_speed_mps', 30.0)
    if train_velocity_mps > max_effective_speed:
        speed_factor = max_effective_speed / train_velocity_mps
        raw_force *= speed_factor

    # Clamp to maximum trim force
    max_force = trim.max_force_n if hasattr(trim, 'max_force_n') and trim.max_force_n > 0 else 5000.0
    clamped_force = min(raw_force, max_force)

    # Trim brakes typically don't aim to stop trains completely
    # They reduce speed to a target velocity
    target_velocity = getattr(trim, 'target_velocity_mps', 5.0)

    # If already at or below target velocity, reduce force
    if train_velocity_mps <= target_velocity:
        # Gradual reduction of force as we approach zero
        # This prevents oscillation near zero speed
        velocity_factor = train_velocity_mps / target_velocity if target_velocity > 0 else 0.0
        clamped_force *= velocity_factor

    state.effective_force_n = clamped_force
    # Force always opposes velocity direction (braking)
    if abs(train_velocity_mps) < 1e-6:
        # Train is essentially stopped - apply minimal holding force
        # Eddy current brakes don't work well at very low speeds
        state.current_force_n = 0.0
    else:
        state.current_force_n = -math.copysign(clamped_force, train_velocity_mps)

    return state.current_force_n


def create_trim_brake_state(trim: TrimBrake) -> TrimBrakeState:
    """Create initial runtime state for a trim brake."""
    return TrimBrakeState(
        enabled=trim.enabled,
        current_force_n=0.0,
        effective_force_n=0.0,
        overlap_ratio=0.0,
        overlap_length_m=0.0
    )
