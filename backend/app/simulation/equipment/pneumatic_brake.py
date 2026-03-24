"""Pneumatic brake physics

Pneumatic brakes use compressed air to apply braking force.
They support two fail-safe modes:
- normally_open: Brake is open when no air pressure (freewheeling)
- normally_closed: Brake is closed when no air pressure (emergency stop)
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
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


def compute_pneumatic_brake_force(
    brake: PneumaticBrake,
    state: PneumaticBrakeState,
    train_s: float,
    train_velocity_mps: float,
    dt: float = 0.01
) -> float:
    """
    Compute the force applied by a pneumatic brake.

    The brake applies force based on:
    - Current brake state (open, closed, emergency_stop)
    - Fail-safe mode (determines behavior when state changes)
    - Response time for actuation
    - Air pressure
    - Train velocity (braking force may be speed-dependent)

    Args:
        brake: Pneumatic brake equipment definition
        state: Current brake runtime state
        train_s: Train front position (arc length)
        train_velocity_mps: Train velocity
        dt: Time step for response time simulation

    Returns:
        Force in Newtons (negative = braking)
    """
    # Check if train is in brake zone
    if not (brake.start_s <= train_s <= brake.end_s):
        state.current_force_n = 0.0
        return 0.0

    # Determine target brake state based on command and fail-safe mode
    target_force = _compute_target_brake_force(
        brake, state.state, train_velocity_mps
    )

    # Simulate response time
    response_rate = 1.0 / brake.response_time_s if brake.response_time_s > 0 else float('inf')

    # Smooth transition to target force
    current_force = state.effective_brake_force_n
    force_diff = target_force - current_force
    max_change = response_rate * dt * brake.max_brake_force_n

    if abs(force_diff) <= max_change:
        new_force = target_force
        state.response_progress = 1.0
    else:
        new_force = current_force + math.copysign(max_change, force_diff)
        state.response_progress = 0.5  # In transition

    # Apply force curve if defined
    if brake.force_curve:
        new_force = _apply_brake_force_curve(
            brake.force_curve,
            new_force,
            train_velocity_mps
        )

    state.effective_brake_force_n = new_force
    state.current_force_n = -abs(new_force)  # Always negative (braking)

    return state.current_force_n


def _compute_target_brake_force(
    brake: PneumaticBrake,
    brake_state: BrakeState,
    velocity_mps: float
) -> float:
    """
    Compute target brake force based on state and fail-safe mode.

    Args:
        brake: Pneumatic brake equipment definition
        brake_state: Current commanded brake state
        velocity_mps: Train velocity

    Returns:
        Target brake force magnitude (positive)
    """
    if brake_state == BrakeState.OPEN:
        # Open = no braking (unless fail-safe mode overrides)
        if brake.fail_safe_mode == FailSafeMode.NORMALLY_OPEN:
            return 0.0
        else:  # normally_closed
            # Normally closed means default is closed
            # Open requires air pressure - so open = no force
            return 0.0

    elif brake_state == BrakeState.CLOSED:
        # Closed = full braking
        return _compute_velocity_dependent_force(
            brake.max_brake_force_n,
            velocity_mps,
            brake.air_pressure
        )

    elif brake_state == BrakeState.EMERGENCY_STOP:
        # Emergency stop = maximum braking
        # Apply max force regardless of normal settings
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
    - May have speed-dependent efficiency
    """
    # Air pressure factor (normalized to 1.0 at typical pressure)
    # Typical pneumatic system: 6-8 bar
    typical_pressure = 7.0
    pressure_factor = min(air_pressure / typical_pressure, 1.5)

    # Speed factor (brakes may be less effective at very low speeds)
    # But generally pneumatic brakes are effective across speed range
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
        effective_brake_force_n=0.0
    )