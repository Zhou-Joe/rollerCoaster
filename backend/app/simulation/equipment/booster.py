"""Booster physics

Boosters are tire-driven propulsion devices used in stations,
hold zones, and maintenance areas to move trains at low speeds.
They can also apply braking when in brake mode.
"""

import math
from dataclasses import dataclass
from typing import Optional

from app.models.equipment import Booster
from app.models.common import BoosterMode


@dataclass
class BoosterState:
    """Runtime state for a booster."""
    mode: BoosterMode = BoosterMode.IDLE
    current_force_n: float = 0.0
    current_speed_mps: float = 0.0
    wheels_engaged: bool = True


def compute_booster_force(
    booster: Booster,
    state: BoosterState,
    train_s: float,
    train_velocity_mps: float,
    dt: float = 0.01
) -> float:
    """
    Compute the force applied by a booster.

    Boosters have three modes:
    - drive: Propel train forward at controlled speed
    - brake: Apply friction braking
    - idle: No force applied

    Boosters are typically used for:
    - Station dispatch
    - Transfer track movement
    - Maintenance bay operations
    - Low-speed positioning

    Args:
        booster: Booster equipment definition
        state: Current booster runtime state
        train_s: Train front position (arc length)
        train_velocity_mps: Train velocity
        dt: Time step

    Returns:
        Force in Newtons (positive = driving, negative = braking)
    """
    # Check if train is in booster zone
    if not (booster.start_s <= train_s <= booster.end_s):
        state.current_force_n = 0.0
        return 0.0

    if state.mode == BoosterMode.IDLE:
        state.current_force_n = 0.0
        return 0.0

    elif state.mode == BoosterMode.DRIVE:
        return _compute_drive_force(booster, state, train_velocity_mps)

    elif state.mode == BoosterMode.BRAKE:
        return _compute_booster_brake_force(booster, state, train_velocity_mps)

    return 0.0


def _compute_drive_force(
    booster: Booster,
    state: BoosterState,
    train_velocity_mps: float
) -> float:
    """
    Compute driving force when booster is in drive mode.

    The booster tries to accelerate the train to its drive speed.
    Force is applied proportional to how far below target speed the train is.
    """
    if train_velocity_mps >= booster.max_drive_speed_mps:
        # Train at or above target speed - no driving force
        state.current_force_n = 0.0
        return 0.0

    # Calculate force needed to reach target speed
    velocity_deficit = booster.max_drive_speed_mps - train_velocity_mps

    # Apply proportional force (simplified - no PID for now)
    force_ratio = velocity_deficit / booster.max_drive_speed_mps
    force = booster.max_drive_force_n * min(force_ratio, 1.0)

    # Account for wheel count efficiency
    wheel_factor = min(booster.wheel_count / 4.0, 1.0)  # Normalized to 4 wheels
    force *= wheel_factor

    state.current_force_n = force
    state.current_speed_mps = train_velocity_mps

    return force


def _compute_booster_brake_force(
    booster: Booster,
    state: BoosterState,
    train_velocity_mps: float
) -> float:
    """
    Compute braking force when booster is in brake mode.

    When in brake mode, the wheels apply friction against the train.
    Force always opposes velocity direction.
    """
    force = booster.brake_friction_force_n

    # Account for wheel count
    wheel_factor = min(booster.wheel_count / 4.0, 1.0)
    force *= wheel_factor

    # Force always opposes velocity direction
    state.current_force_n = -math.copysign(force, train_velocity_mps)

    return state.current_force_n


def set_booster_mode(
    booster: Booster,
    state: BoosterState,
    mode: BoosterMode
) -> None:
    """
    Set the booster mode.

    Args:
        booster: Booster equipment definition
        state: Current booster runtime state
        mode: Desired mode
    """
    state.mode = mode
    state.current_force_n = 0.0


def create_booster_state(booster: Booster) -> BoosterState:
    """Create initial runtime state for a booster."""
    return BoosterState(
        mode=booster.mode,
        current_force_n=0.0,
        current_speed_mps=0.0,
        wheels_engaged=True
    )