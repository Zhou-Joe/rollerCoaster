"""Lift hill physics

Lift systems pull trains uphill using a chain or tire drive mechanism.
The train is mechanically engaged and forced to move at lift speed.
"""

import math
from dataclasses import dataclass
from typing import Optional, Tuple

from app.models.equipment import Lift


@dataclass
class LiftState:
    """Runtime state for a lift system."""
    enabled: bool = True
    engaged: bool = False
    current_force_n: float = 0.0
    engagement_progress: float = 0.0  # 0.0 to 1.0


def compute_lift_effect(
    lift: Lift,
    state: LiftState,
    train_s: float,
    train_velocity_mps: float,
    dt: float = 0.01
) -> Tuple[float, float]:
    """
    Compute the effect of a lift system on a train.

    When engaged, the lift mechanically drives the train at a constant speed,
    overriding the train's natural physics. This is how real lift hills work -
    the chain dog engages and pulls the train at the chain speed.

    Args:
        lift: Lift equipment definition
        state: Current lift runtime state
        train_s: Train front position (arc length)
        train_velocity_mps: Train velocity
        dt: Time step for engagement smoothing

    Returns:
        Tuple of (force_n, target_velocity_mps)
        - If engaged: returns (0, lift_speed) - velocity is overridden
        - If not engaged: returns (0, train_velocity) - no effect
    """
    if not state.enabled or not lift.enabled:
        state.engaged = False
        return 0.0, train_velocity_mps

    # Get engagement and release points
    engagement_point = lift.engagement_point_s if lift.engagement_point_s is not None else lift.start_s
    release_point = lift.release_point_s if lift.release_point_s is not None else lift.end_s

    # Check if train is in the engagement zone
    in_engagement_zone = engagement_point <= train_s <= release_point

    if not in_engagement_zone:
        state.engaged = False
        state.engagement_progress = 0.0
        return 0.0, train_velocity_mps

    # Smooth engagement over 0.5s
    state.engagement_progress = min(1.0, state.engagement_progress + dt * 2.0)
    state.engaged = True

    # Lift mechanically drives train at constant speed
    # The train velocity is overridden to match lift speed
    return 0.0, lift.lift_speed_mps


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