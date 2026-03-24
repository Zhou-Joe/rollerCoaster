from pydantic import BaseModel
from typing import Optional, List
from .common import LoadCase, TrainState


class Vehicle(BaseModel):
    id: str
    length_m: float
    dry_mass_kg: float
    capacity: int
    passenger_mass_per_person_kg: float = 75.0
    vehicle_type: Optional[str] = None


class Train(BaseModel):
    id: str
    vehicle_ids: List[str]
    coupling_gap_m: float = 0.5
    route_assignment: Optional[str] = None
    current_state: TrainState = TrainState.STOPPED
    load_case: LoadCase = LoadCase.EMPTY
    custom_occupancy_factor: Optional[float] = None
    front_position_s: float = 0.0
    current_path_id: Optional[str] = None