"""Train dynamics calculations"""

from typing import List, Optional, TYPE_CHECKING
from app.models.train import Train, Vehicle
from app.models.common import LoadCase

if TYPE_CHECKING:
    from app.simulation.geometry import GeometryCache, SamplePoint


def compute_train_mass(
    train: Train,
    vehicles: List[Vehicle],
    load_case: LoadCase = LoadCase.EMPTY,
    custom_occupancy: Optional[float] = None
) -> float:
    """
    Compute total train mass including passengers.

    Args:
        train: Train model with vehicle IDs and load case
        vehicles: List of vehicle definitions
        load_case: Loading condition (empty, fully loaded, custom)
        custom_occupancy: Custom occupancy factor (0.0 to 1.0)

    Returns:
        Total mass in kilograms
    """
    # Build vehicle lookup
    vehicle_map = {v.id: v for v in vehicles}

    total_dry_mass = 0.0
    total_passenger_mass = 0.0

    for vehicle_id in train.vehicle_ids:
        if vehicle_id not in vehicle_map:
            continue
        vehicle = vehicle_map[vehicle_id]

        total_dry_mass += vehicle.dry_mass_kg

        # Add passenger mass based on load case
        if load_case == LoadCase.FULLY_LOADED:
            occupancy = 1.0
        elif load_case == LoadCase.CUSTOM and custom_occupancy is not None:
            occupancy = custom_occupancy
        else:
            occupancy = 0.0

        passenger_count = vehicle.capacity * occupancy
        total_passenger_mass += passenger_count * vehicle.passenger_mass_per_person_kg

    return total_dry_mass + total_passenger_mass


def compute_train_length(train: Train, vehicles: List[Vehicle]) -> float:
    """
    Compute total train length including coupling gaps.

    Args:
        train: Train model with vehicle IDs and coupling gap
        vehicles: List of vehicle definitions

    Returns:
        Total length in meters
    """
    vehicle_map = {v.id: v for v in vehicles}

    total_length = 0.0
    vehicle_count = 0

    for vehicle_id in train.vehicle_ids:
        if vehicle_id not in vehicle_map:
            continue
        vehicle = vehicle_map[vehicle_id]
        total_length += vehicle.length_m
        vehicle_count += 1

    # Add coupling gaps between vehicles
    if vehicle_count > 1:
        total_length += (vehicle_count - 1) * train.coupling_gap_m

    return total_length


def get_geometry_at_position(
    geometry_cache: 'GeometryCache',
    path_id: str,
    s: float
) -> Optional['SamplePoint']:
    """
    Get geometry sample at a specific arc length position.

    Args:
        geometry_cache: Cache with computed path geometry
        path_id: Path identifier
        s: Arc length position in meters

    Returns:
        SamplePoint if available, None otherwise
    """
    try:
        path_data = geometry_cache.get_path(path_id)
        if not path_data or not path_data.samples:
            return None

        # Clamp s to path bounds
        s = max(0.0, min(s, path_data.total_length))

        # O(1) index calculation - samples are evenly spaced by resolution_m
        idx = int(s / path_data.resolution_m)
        if idx >= len(path_data.samples):
            idx = len(path_data.samples) - 1

        return path_data.samples[idx]

    except (ValueError, KeyError):
        return None


def get_rear_position(s_front: float, train_length: float) -> float:
    """
    Compute rear train position from front position and length.

    Args:
        s_front: Front position (arc length)
        train_length: Total train length

    Returns:
        Rear position (arc length), always <= s_front
    """
    return max(0.0, s_front - train_length)


def is_train_on_path(
    s_front: float,
    s_rear: float,
    path_start: float,
    path_end: float
) -> bool:
    """
    Check if any part of the train is on a path segment.

    Args:
        s_front: Train front position
        s_rear: Train rear position
        path_start: Path start arc length
        path_end: Path end arc length

    Returns:
        True if train overlaps with path segment
    """
    # Train overlaps with path if its interval intersects
    return not (s_front < path_start or s_rear > path_end)


def compute_occupancy_fraction(
    s_front: float,
    s_rear: float,
    segment_start: float,
    segment_end: float
) -> float:
    """
    Compute fraction of a segment occupied by the train.

    Args:
        s_front: Train front position
        s_rear: Train rear position
        segment_start: Segment start arc length
        segment_end: Segment end arc length

    Returns:
        Fraction of segment occupied (0.0 to 1.0)
    """
    # Compute overlap
    overlap_start = max(s_rear, segment_start)
    overlap_end = min(s_front, segment_end)

    if overlap_start >= overlap_end:
        return 0.0

    overlap_length = overlap_end - overlap_start
    segment_length = segment_end - segment_start

    if segment_length <= 0:
        return 0.0

    return overlap_length / segment_length