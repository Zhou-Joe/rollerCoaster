from pydantic import BaseModel
from typing import List, Optional
from .common import StationType


class Junction(BaseModel):
    id: str
    incoming_path_id: str
    outgoing_path_ids: List[str]
    position_s: float


class BlockPathInterval(BaseModel):
    path_id: str
    start_s: float
    end_s: float


class Block(BaseModel):
    id: str
    path_intervals: List[BlockPathInterval]
    occupied: bool = False
    reserved_by: Optional[str] = None
    linked_station_id: Optional[str] = None


class Station(BaseModel):
    id: str
    name: str
    station_type: StationType
    associated_block_ids: List[str]
    position_path_id: str
    position_s: float