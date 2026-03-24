from pydantic import BaseModel, Field
from typing import Optional, List
from .common import ZoneType, EquipmentConstraint


class Point(BaseModel):
    id: str
    x: float
    y: float
    z: float
    bank_deg: float = 0.0
    editable: bool = True


class Path(BaseModel):
    id: str
    point_ids: List[str]
    length_m: Optional[float] = None


class Section(BaseModel):
    id: str
    path_id: str
    start_s: float
    end_s: float
    zone_type: ZoneType
    label: Optional[str] = None
    equipment_constraints: Optional[EquipmentConstraint] = None