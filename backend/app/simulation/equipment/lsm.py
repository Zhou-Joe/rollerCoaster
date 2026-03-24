"""LSM Launch system physics

LSM (Linear Synchronous Motor) launch systems use electromagnetic
stators to accelerate trains along a launch track.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

from app.models.equipment import LSMLaunch


@dataclass
class LSMState:
    """Runtime state for an LSM launch system."""
    enabled: bool = True
    current_force_n: float = 0.0
    stators_active: int = 0


def compute_lsm_force(
    lsm: LSMLaunch,
    state: LSMState,
    train_s: float,
    train_velocity_mps: float,
    train_mass_kg: float,
    dt: float = 0.01
) -> float:
    """
    Compute the force applied by an LSM launch system.

    The LSM applies force based on:
    - Whether it's enabled
    - The train's position relative to the launch zone
    - The train's velocity (force typically decreases at high speeds)
    - The force curve if defined

    Args:
        lsm: LSM launch equipment definition
        state: Current LSM runtime state
        train_s: Train front position (arc length)
        train_velocity_mps: Train velocity
        train_mass_kg: Total train mass
        dt: Time step for force ramping

    Returns:
        Force in Newtons (positive = accelerating)
    """
    if not state.enabled or not lsm.enabled:
        return 0.0

    # Check if train is in the launch zone
    if not (lsm.start_s <= train_s <= lsm.end_s):
        return 0.0

    # Calculate position within launch zone (0.0 to 1.0)
    zone_length = lsm.end_s - lsm.start_s
    position_ratio = (train_s - lsm.start_s) / zone_length if zone_length > 0 else 0.0

    # Calculate base force from force curve or default model
    if lsm.force_curve:
        force = _interpolate_force_curve(lsm.force_curve, position_ratio, train_velocity_mps)
    else:
        force = _default_lsm_force_model(
            lsm.max_force_n,
            lsm.stator_count,
            lsm.magnetic_field_strength,
            position_ratio,
            train_velocity_mps
        )

    # Clamp to maximum force
    force = min(force, lsm.max_force_n)

    # Update state
    state.current_force_n = force
    state.stators_active = int(lsm.stator_count * (1.0 - position_ratio))

    return force


def _default_lsm_force_model(
    max_force_n: float,
    stator_count: int,
    magnetic_field_strength: float,
    position_ratio: float,
    velocity_mps: float
) -> float:
    """
    Default LSM force model.

    LSM force characteristics:
    - Maximum force at low speeds
    - Force decreases as speed increases (back-EMF effect)
    - Force may vary along the launch track
    """
    # Speed-dependent factor (force decreases at high speeds)
    # Typical LSM: force ~ 1 / (1 + v/v_max) where v_max is motor design speed
    design_speed_mps = 30.0  # Typical LSM design speed
    speed_factor = 1.0 / (1.0 + velocity_mps / design_speed_mps)

    # Position factor (typically constant or slightly decreasing)
    # Some LSMs have stronger acceleration near the end
    position_factor = 1.0 - 0.2 * position_ratio

    # Magnetic field strength factor (0.0 to 1.0 typically)
    field_factor = min(magnetic_field_strength, 1.0)

    # Stator efficiency factor
    stator_factor = min(stator_count / 10.0, 1.0)  # Normalized to 10 stators

    return max_force_n * speed_factor * position_factor * field_factor * stator_factor


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


def create_lsm_state(lsm: LSMLaunch) -> LSMState:
    """Create initial runtime state for an LSM."""
    return LSMState(
        enabled=lsm.enabled,
        current_force_n=0.0,
        stators_active=0
    )