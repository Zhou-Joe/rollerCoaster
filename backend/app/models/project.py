from pydantic import BaseModel, Field, ConfigDict
from typing import List
from datetime import datetime, timezone
from .track import Point, Path, Section
from .topology import Junction, Block, Station
from .train import Vehicle, Train
from .control import VisualRule, ControlScript


class ProjectMetadata(BaseModel):
    name: str = "Untitled Project"
    units: str = "metric"
    version: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    modified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SimulationSettings(BaseModel):
    time_step_s: float = 0.01
    gravity_mps2: float = 9.81
    drag_coefficient: float = 0.5
    rolling_resistance_coefficient: float = 0.002
    air_density_kg_m3: float = 1.225

    # Geometry settings
    geometry_sample_resolution_m: float = 0.01
    max_curvature_per_m: float = 0.5
    curvature_warning_radius_m: float = 10.0
    tangent_discontinuity_threshold_deg: float = 5.0
    junction_position_tolerance_m: float = 0.01
    bank_rate_threshold_deg_per_m: float = 10.0


class Project(BaseModel):
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    metadata: ProjectMetadata = Field(default_factory=ProjectMetadata)
    points: List[Point] = []
    paths: List[Path] = []
    junctions: List[Junction] = []
    switches: List[dict] = []
    sections: List[Section] = []
    stations: List[Station] = []
    blocks: List[Block] = []
    vehicles: List[Vehicle] = []
    trains: List[Train] = []
    equipment: List[dict] = []
    control_rules: List[VisualRule] = []
    control_scripts: List[ControlScript] = []
    simulation_settings: SimulationSettings = Field(default_factory=SimulationSettings)