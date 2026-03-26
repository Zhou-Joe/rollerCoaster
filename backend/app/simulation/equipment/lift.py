"""Lift hill physics

Lift systems pull trains uphill using a chain or tire drive mechanism.
"""

import math
from dataclasses import dataclass
from typing import Optional

from app.models.equipment import Lift


@dataclass
class LiftState:
    """Runtime state for a lift system."""
    enabled: bool = True
    engaged: bool = False
    current_force_n: float = 0.0
    engagement_progress: float = 0.0  # 0.0 to 1.0


def compute_lift_force(
    lift: Lift,
    state: LiftState,
    train_s: float,
    train_velocity_mps: float,
    dt: float = 0.01
) -> float:
    """
    Compute the force applied by a lift system.

    The lift applies force when:
    - It's enabled
    - The train is within the engagement/release zone
    - The train is moving slower than lift speed (or stopped)

    The lift maintains a constant speed when engaged, applying
    whatever force is needed (up to max) to maintain that speed.

    Args:
        lift: Lift equipment definition
        state: Current lift runtime state
        train_s: Train front position (arc length)
        train_velocity_mps: Train velocity
        dt: Time step for engagement smoothing

    Returns:
        Force in Newtons (positive = pulling uphill)
    """
    if not state.enabled or not lift.enabled:
        state.engaged = False
        return 0.0

    # Get engagement and release points, defaulting to start_s and end_s
    engagement_point = lift.engagement_point_s if lift.engagement_point_s is not None else lift.start_s
    release_point = lift.release_point_s if lift.release_point_s is not None else lift.end_s

    # Check if train is in the engagement zone (between engagement and release points)
    in_engagement_zone = engagement_point <= train_s <= release_point

    if not in_engagement_zone:
        state.engaged = False
        state.engagement_progress = 0.0
        return 0.0

    # Smooth engagement
    state.engagement_progress = min(1.0, state.engagement_progress + dt * 2.0)  # 0.5s engagement
    state.engaged = True

    if not state.engaged:
        return 0.0

    # Compute force needed to maintain lift speed
    # If train is slower than lift speed, apply force to accelerate
    # If train is faster, apply no force (freewheeling)

    velocity_diff = lift.lift_speed_mps - train_velocity_mps

    if velocity_diff <= 0:
        # Train is at or above lift speed - no force needed
        # (In reality, lift would disengage or allow slip)
        state.current_force_n = 0.0
        return 0.0

    # Apply force to accelerate train to lift speed
    # Force proportional to how much below lift speed we are
    engagement_factor = state.engagement_progress

    # Simple model: constant force to maintain speed
    # More sophisticated: PID controller simulation
    force = lift.max_pull_force_n * engagement_factor * min(velocity_diff / lift.lift_speed_mps, 1.0)

    # Clamp to max
    force = min(force, lift.max_pull_force_n)

    state.current_force_n = force
    return force


def check_lift_release(
    lift: Lift,
    state: LiftState,
    train_s: float
) -> bool:
    """
    Check if train has reached the release point.

    Args:
        lift: Lift equipment definition
        state: Current lift runtime state
        train_s: Train front position

    Returns:
        True if train should be released from lift
    """
    release_point = lift.release_point_s if lift.release_point_s is not None else lift.end_s
    if train_s >= release_point:
        state.engaged = False
        state.engagement_progress = 0.0
        return True
    return False


def create_lift_state(lift: Lift) -> LiftState:
    """Create initial runtime state for a lift."""
    return LiftState(
        enabled=lift.enabled,
        engaged=False,
        current_force_n=0.0,
        engagement_progress=0.0
    )