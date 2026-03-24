"""Trim brake physics

Trim brakes are used to reduce train speed without bringing
the train to a complete stop. They apply a controlled braking
force over a defined interval.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

from app.models.equipment import TrimBrake


@dataclass
class TrimBrakeState:
    """Runtime state for a trim brake."""
    enabled: bool = True
    current_force_n: float = 0.0
    effective_force_n: float = 0.0


def compute_trim_brake_force(
    trim: TrimBrake,
    state: TrimBrakeState,
    train_s: float,
    train_velocity_mps: float,
    dt: float = 0.01
) -> float:
    """
    Compute the force applied by a trim brake.

    Trim brakes apply a gentler braking force compared to
    pneumatic brakes. They're typically used for:
    - Mid-course speed adjustment
    - Section-to-section speed control
    - Fine-tuning ride dynamics

    Args:
        trim: Trim brake equipment definition
        state: Current trim brake runtime state
        train_s: Train front position (arc length)
        train_velocity_mps: Train velocity
        dt: Time step

    Returns:
        Force in Newtons (negative = braking)
    """
    if not state.enabled or not trim.enabled:
        return 0.0

    # Check if train is in trim zone
    if not (trim.start_s <= train_s <= trim.end_s):
        state.current_force_n = 0.0
        return 0.0

    # Compute base trim force
    base_force = trim.max_trim_force_n

    # Apply force curve if defined
    if trim.force_curve:
        base_force = _apply_trim_force_curve(
            trim.force_curve,
            base_force,
            train_velocity_mps,
            train_s - trim.start_s,
            trim.end_s - trim.start_s
        )

    # Trim brakes typically don't stop trains completely
    # If velocity is very low, reduce force to avoid stopping
    min_velocity_mps = 2.0  # Don't trim below this speed
    if train_velocity_mps < min_velocity_mps:
        # Reduce force proportionally
        reduction = train_velocity_mps / min_velocity_mps
        base_force *= reduction

    state.current_force_n = -abs(base_force)
    state.effective_force_n = base_force

    return state.current_force_n


def _apply_trim_force_curve(
    force_curve: List[Dict[str, Any]],
    base_force: float,
    velocity_mps: float,
    local_s: float,
    zone_length: float
) -> float:
    """
    Apply a force curve to modify trim force.

    Force curve can depend on:
    - Velocity (speed-dependent trim)
    - Position within trim zone (entry/exit profile)

    Force curve format:
    [
        {"velocity": 10, "position": 0.0, "force_factor": 0.5},
        {"velocity": 10, "position": 1.0, "force_factor": 0.8},
        ...
    ]
    """
    if not force_curve:
        return base_force

    position_ratio = local_s / zone_length if zone_length > 0 else 0.0

    # Filter points by velocity (closest match)
    best_points = []
    min_velocity_diff = float('inf')

    for point in force_curve:
        point_velocity = point.get("velocity", 0)
        velocity_diff = abs(point_velocity - velocity_mps)
        if velocity_diff < min_velocity_diff:
            min_velocity_diff = velocity_diff
            best_points = [point]
        elif velocity_diff == min_velocity_diff:
            best_points.append(point)

    if not best_points:
        return base_force

    # Sort by position
    best_points.sort(key=lambda p: p.get("position", 0))

    # Find surrounding points for position interpolation
    for i, point in enumerate(best_points):
        if point.get("position", 0) >= position_ratio:
            if i == 0:
                factor = float(point.get("force_factor", 1.0))
                return base_force * factor
            prev = best_points[i - 1]
            prev_pos = prev.get("position", 0)
            curr_pos = point.get("position", 0)
            prev_f = float(prev.get("force_factor", 1.0))
            curr_f = float(point.get("force_factor", 1.0))

            t = (position_ratio - prev_pos) / (curr_pos - prev_pos) if curr_pos > prev_pos else 0
            factor = prev_f + t * (curr_f - prev_f)
            return base_force * factor

    factor = float(best_points[-1].get("force_factor", 1.0))
    return base_force * factor


def create_trim_brake_state(trim: TrimBrake) -> TrimBrakeState:
    """Create initial runtime state for a trim brake."""
    return TrimBrakeState(
        enabled=trim.enabled,
        current_force_n=0.0,
        effective_force_n=0.0
    )