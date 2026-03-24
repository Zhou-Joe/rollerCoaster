"""Force models for train physics"""

import math
from typing import Optional
from .types import ForceComponents


def gravity_force(mass_kg: float, slope_rad: float, gravity_mps2: float = 9.81) -> float:
    """
    Compute gravitational force component along track tangent.

    Positive force is in direction of travel (downhill).
    Negative force opposes travel (uphill).

    Args:
        mass_kg: Total train mass
        slope_rad: Slope angle (positive = uphill)
        gravity_mps2: Gravitational acceleration

    Returns:
        Force in Newtons (positive = accelerating, negative = decelerating)
    """
    # Force = m * g * sin(slope)
    # Positive slope (uphill) => negative force (decelerating)
    return -mass_kg * gravity_mps2 * math.sin(slope_rad)


def drag_force(
    velocity_mps: float,
    drag_coefficient: float,
    frontal_area_m2: float,
    air_density_kg_m3: float = 1.225
) -> float:
    """
    Compute aerodynamic drag force.

    Drag always opposes motion.

    Args:
        velocity_mps: Train speed (positive = forward)
        drag_coefficient: Drag coefficient Cd
        frontal_area_m2: Frontal cross-sectional area
        air_density_kg_m3: Air density

    Returns:
        Force in Newtons (always opposes velocity)
    """
    # F_drag = 0.5 * rho * Cd * A * v^2
    # Direction opposes velocity
    drag_magnitude = 0.5 * air_density_kg_m3 * drag_coefficient * frontal_area_m2 * velocity_mps ** 2
    return -math.copysign(drag_magnitude, velocity_mps)


def rolling_resistance_force(
    mass_kg: float,
    rolling_coefficient: float,
    gravity_mps2: float = 9.81,
    velocity_mps: float = 0.0
) -> float:
    """
    Compute rolling resistance force.

    Rolling resistance opposes motion when moving.
    When stationary, it acts as static friction holding the train.

    Args:
        mass_kg: Total train mass
        rolling_coefficient: Rolling resistance coefficient Crr
        gravity_mps2: Gravitational acceleration
        velocity_mps: Current velocity (to determine direction)

    Returns:
        Force in Newtons (opposes motion or prevents sliding)
    """
    # F_rr = Crr * m * g * cos(slope) ≈ Crr * m * g for small slopes
    # We approximate by ignoring slope effect on normal force
    resistance_magnitude = rolling_coefficient * mass_kg * gravity_mps2

    if abs(velocity_mps) < 1e-6:
        # Static - doesn't apply force when stationary
        return 0.0

    # Dynamic - opposes motion
    return -math.copysign(resistance_magnitude, velocity_mps)


def compute_forces(
    mass_kg: float,
    velocity_mps: float,
    slope_rad: float,
    drag_coefficient: float,
    frontal_area_m2: float,
    rolling_coefficient: float,
    gravity_mps2: float = 9.81,
    air_density_kg_m3: float = 1.225,
    equipment_force_n: float = 0.0
) -> ForceComponents:
    """
    Compute all forces acting on a train.

    Args:
        mass_kg: Total train mass
        velocity_mps: Current speed
        slope_rad: Track slope angle at train position
        drag_coefficient: Aerodynamic drag coefficient
        frontal_area_m2: Train frontal area
        rolling_coefficient: Rolling resistance coefficient
        gravity_mps2: Gravitational acceleration
        air_density_kg_m3: Air density
        equipment_force_n: Force from equipment (launch, lift, brake, etc.)

    Returns:
        ForceComponents with individual forces and total
    """
    gravity_n = gravity_force(mass_kg, slope_rad, gravity_mps2)
    drag_n = drag_force(velocity_mps, drag_coefficient, frontal_area_m2, air_density_kg_m3)
    rolling_n = rolling_resistance_force(mass_kg, rolling_coefficient, gravity_mps2, velocity_mps)

    total_n = gravity_n + drag_n + rolling_n + equipment_force_n

    return ForceComponents(
        gravity_tangent_n=gravity_n,
        drag_n=drag_n,
        rolling_resistance_n=rolling_n,
        equipment_n=equipment_force_n,
        total_n=total_n
    )