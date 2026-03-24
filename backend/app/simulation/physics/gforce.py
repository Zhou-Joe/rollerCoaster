"""G-force calculations from track geometry"""

import math
from .types import GForceComponents


def normal_acceleration(velocity_mps: float, curvature_per_m: float) -> float:
    """
    Compute centripetal acceleration due to track curvature.

    a_n = v^2 * κ = v^2 / R

    Args:
        velocity_mps: Train speed
        curvature_per_m: Track curvature (1/radius)

    Returns:
        Normal acceleration in m/s^2
    """
    return velocity_mps ** 2 * curvature_per_m


def compute_gforces(
    velocity_mps: float,
    curvature_per_m: float,
    slope_deg: float,
    bank_deg: float,
    gravity_mps2: float = 9.81
) -> GForceComponents:
    """
    Compute g-forces experienced by passengers.

    The g-force frame is relative to the train body:
    - Normal: perpendicular to track, into the seat
    - Lateral: side-to-side in the train
    - Vertical: up-down in the train body

    Bank angle affects how the normal acceleration is perceived.

    Args:
        velocity_mps: Train speed
        curvature_per_m: Track curvature at position
        slope_deg: Track slope angle
        bank_deg: Track bank angle
        gravity_mps2: Gravitational acceleration

    Returns:
        GForceComponents with normal, lateral, vertical, and resultant g-forces
    """
    # Normal acceleration from curvature
    a_normal = normal_acceleration(velocity_mps, curvature_per_m)

    # Convert angles to radians
    slope_rad = math.radians(slope_deg)
    bank_rad = math.radians(bank_deg)

    # Gravity component perpendicular to track (into seat)
    # When level, this is 1g. On slope, it's reduced.
    g_normal_base = math.cos(slope_rad)  # Gravity component normal to track

    # The normal acceleration adds to this
    # In the track frame, normal acceleration points toward center of curvature
    a_normal_g = a_normal / gravity_mps2

    # Bank angle rotates the normal force into lateral component
    # When banked, some of the normal force becomes lateral in the train frame
    # Normal to passenger = (g_normal + a_normal) * cos(bank)
    g_normal = (g_normal_base + a_normal_g) * math.cos(bank_rad)

    # Lateral force = (normal acceleration) * sin(bank)
    # This is the "pushed into the side" feeling
    g_lateral = a_normal_g * math.sin(bank_rad)

    # Vertical in train frame = gravity component along slope * cos(bank)
    # Plus small component from normal acceleration
    g_vertical = math.sin(slope_rad) * math.cos(bank_rad)

    # Resultant magnitude
    g_resultant = math.sqrt(g_normal ** 2 + g_lateral ** 2 + g_vertical ** 2)

    return GForceComponents(
        normal_g=g_normal,
        lateral_g=g_lateral,
        vertical_g=g_vertical,
        resultant_g=g_resultant
    )


def compute_vertical_gforce(
    velocity_mps: float,
    curvature_per_m: float,
    slope_deg: float,
    gravity_mps2: float = 9.81
) -> float:
    """
    Compute vertical g-force (alias for simple cases without banking).

    This is the "airtime" or "negative g" that riders feel on hills.

    Args:
        velocity_mps: Train speed
        curvature_per_m: Track curvature
        slope_deg: Track slope
        gravity_mps2: Gravitational acceleration

    Returns:
        Vertical g-force component
    """
    gforces = compute_gforces(velocity_mps, curvature_per_m, slope_deg, 0.0, gravity_mps2)
    return gforces.normal_g