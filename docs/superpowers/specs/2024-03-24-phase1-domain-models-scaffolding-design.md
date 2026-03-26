# Phase 1: Domain Models and Project Scaffolding Design

**Date:** 2024-03-24
**Project:** Roller Coaster Simulator
**Phase:** 1 of 7

## Overview

Phase 1 establishes the project foundation: Pydantic domain models serving as the source of truth for all data structures, JSON file-based persistence, and scaffolded backend/frontend applications.

## Decisions Made

1. **Persistence:** JSON file-based for Phase 1, PostgreSQL deferred to later
2. **Repository:** Monorepo with `backend/` and `frontend/` directories
3. **Schema source of truth:** Pydantic models that auto-generate JSON Schema

## Project Structure

```
rollerCoaster/
├── PROJECT_SPEC.md
├── README.md
├── .gitignore
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Settings/configuration
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── router.py        # Main API router
│   │   │   ├── projects.py      # Project CRUD endpoints
│   │   │   ├── tracks.py        # Track/topology endpoints
│   │   │   ├── trains.py        # Train endpoints
│   │   │   ├── equipment.py     # Equipment endpoints
│   │   │   ├── control.py       # Control logic endpoints
│   │   │   └── simulation.py    # Simulation endpoints
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── common.py        # Shared types, enums
│   │   │   ├── track.py         # Path, Point, Section
│   │   │   ├── topology.py      # Junction, Block, Station
│   │   │   ├── train.py         # Vehicle, Train
│   │   │   ├── equipment.py     # LSM, Lift, Brake, Booster, TrackSwitch
│   │   │   ├── control.py       # ControlRule, ControlScript
│   │   │   └── project.py       # Project wrapper, SimulationSettings
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── project_io.py    # JSON save/load
│   │   │   └── validator.py     # Validation logic
│   │   └── simulation/          # Empty for Phase 1
│   │       └── __init__.py
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       └── test_models/
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/
│   │   ├── state/
│   │   ├── components/
│   │   └── features/
│   └── index.html
└── docs/
    └── superpowers/
        └── specs/
```

## Domain Models

### common.py - Shared Types

```python
from enum import Enum
from typing import Tuple, List, Optional
from pydantic import BaseModel

class ZoneType(str, Enum):
    LOAD = "load"
    UNLOAD = "unload"
    LAUNCH = "launch"
    BRAKE = "brake"
    HOLD = "hold"
    FREE = "free"
    MAINTENANCE = "maintenance"

class FailSafeMode(str, Enum):
    NORMALLY_OPEN = "normally_open"
    NORMALLY_CLOSED = "normally_closed"

class BrakeState(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    EMERGENCY_STOP = "emergency_stop"

class BoosterMode(str, Enum):
    DRIVE = "drive"
    BRAKE = "brake"
    IDLE = "idle"

class LoadCase(str, Enum):
    EMPTY = "empty"
    FULLY_LOADED = "fully_loaded"
    CUSTOM = "custom"

class TrainState(str, Enum):
    STOPPED = "stopped"
    MOVING = "moving"
    LOADING = "loading"
    UNLOADING = "unloading"
    IN_MAINTENANCE = "in_maintenance"

class StationType(str, Enum):
    LOAD = "load"
    UNLOAD = "unload"
    TRANSFER = "transfer"
    HOLD = "hold"

# Type alias for 3D coordinates
Position3D = Tuple[float, float, float]

# Equipment constraints for sections
class EquipmentConstraint(BaseModel):
    allowed_equipment_types: List[str] = []  # Equipment type names allowed
    min_straightness: Optional[float] = None  # For launch/brake placement
    max_curvature: Optional[float] = None
```

### track.py - Track Geometry

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from .common import ZoneType, EquipmentConstraint

class Point(BaseModel):
    id: str
    x: float  # meters
    y: float  # meters
    z: float  # meters (elevation)
    bank_deg: float = 0.0  # degrees
    editable: bool = True

class Path(BaseModel):
    id: str
    point_ids: List[str]  # Ordered list of point IDs
    length_m: Optional[float] = None  # Computed after interpolation (Phase 2)

class Section(BaseModel):
    id: str
    path_id: str
    start_s: float  # Arc length position (meters)
    end_s: float    # Arc length position (meters)
    zone_type: ZoneType
    label: Optional[str] = None
    equipment_constraints: Optional[EquipmentConstraint] = None
```

### topology.py - Track Network

```python
from pydantic import BaseModel
from typing import List, Optional
from .common import StationType

class Junction(BaseModel):
    """A passive topological connection between paths."""
    id: str
    incoming_path_id: str
    outgoing_path_ids: List[str]
    position_s: float  # Position on incoming path

class BlockPathInterval(BaseModel):
    path_id: str
    start_s: float
    end_s: float

class Block(BaseModel):
    id: str
    path_intervals: List[BlockPathInterval]
    occupied: bool = False
    reserved_by: Optional[str] = None  # Train ID
    linked_station_id: Optional[str] = None

class Station(BaseModel):
    id: str
    name: str
    station_type: StationType
    associated_block_ids: List[str]
    position_path_id: str
    position_s: float
```

**Note:** Switches are modeled as equipment (see `TrackSwitch` in equipment.py). This design treats switches as controllable devices with force/routing behavior, consistent with the PROJECT_SPEC which places switches under equipment (Section 12.6).

### train.py - Vehicle and Train

```python
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
    vehicle_ids: List[str]  # Ordered list of vehicle IDs
    coupling_gap_m: float = 0.5  # Gap between vehicles
    route_assignment: Optional[str] = None  # Current route ID
    current_state: TrainState = TrainState.STOPPED
    load_case: LoadCase = LoadCase.EMPTY
    custom_occupancy_factor: Optional[float] = None  # 0.0 to 1.0
    front_position_s: float = 0.0  # Current position on path
    current_path_id: Optional[str] = None

# Note: total_length_m and total_dry_mass_kg are computed in the service layer
# when vehicles are resolved from the project context. This avoids circular
# dependencies and allows for proper validation.
```

### equipment.py - Equipment Types

```python
from pydantic import BaseModel
from typing import List, Optional, Union, Dict, Any
from .common import FailSafeMode, BrakeState, BoosterMode
from enum import Enum

class EquipmentType(str, Enum):
    LSM_LAUNCH = "lsm_launch"
    LIFT = "lift"
    PNEUMATIC_BRAKE = "pneumatic_brake"
    TRIM_BRAKE = "trim_brake"
    BOOSTER = "booster"
    TRACK_SWITCH = "track_switch"

# Force curve representation - flexible for Phase 4
ForceCurvePoint = Dict[str, Any]  # {local_s, speed, force_factor}
ForceCurve = List[ForceCurvePoint]

class LSMLaunch(BaseModel):
    equipment_type: EquipmentType = EquipmentType.LSM_LAUNCH
    id: str
    path_id: str
    start_s: float
    end_s: float
    stator_count: int
    magnetic_field_strength: float
    max_force_n: float
    force_curve: Optional[ForceCurve] = None
    enabled: bool = True

class Lift(BaseModel):
    equipment_type: EquipmentType = EquipmentType.LIFT
    id: str
    path_id: str
    start_s: float
    end_s: float
    lift_speed_mps: float
    max_pull_force_n: float
    engagement_point_s: float
    release_point_s: float
    enabled: bool = True

class PneumaticBrake(BaseModel):
    equipment_type: EquipmentType = EquipmentType.PNEUMATIC_BRAKE
    id: str
    path_id: str
    start_s: float
    end_s: float
    max_brake_force_n: float
    response_time_s: float
    air_pressure: float
    fail_safe_mode: FailSafeMode
    force_curve: Optional[ForceCurve] = None
    state: BrakeState = BrakeState.OPEN

class TrimBrake(BaseModel):
    equipment_type: EquipmentType = EquipmentType.TRIM_BRAKE
    id: str
    path_id: str
    start_s: float
    end_s: float
    max_trim_force_n: float
    force_curve: Optional[ForceCurve] = None
    enabled: bool = True

class Booster(BaseModel):
    equipment_type: EquipmentType = EquipmentType.BOOSTER
    id: str
    path_id: str
    start_s: float
    end_s: float
    wheel_count: int
    max_drive_force_n: float
    max_drive_speed_mps: float
    brake_friction_force_n: float
    mode: BoosterMode = BoosterMode.IDLE

class TrackSwitch(BaseModel):
    equipment_type: EquipmentType = EquipmentType.TRACK_SWITCH
    id: str
    junction_id: str
    incoming_path_id: str
    outgoing_path_ids: List[str]
    current_alignment: str
    actuation_time_s: float = 2.0
    locked_when_occupied: bool = True

# Union type for all equipment
Equipment = Union[LSMLaunch, Lift, PneumaticBrake, TrimBrake, Booster, TrackSwitch]
```

### control.py - Ride Control System

```python
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from enum import Enum

class ConditionOperator(str, Enum):
    EQUALS = "=="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_OR_EQUAL = ">="
    LESS_OR_EQUAL = "<="
    IS_TRUE = "is_true"
    IS_FALSE = "is_false"

class Condition(BaseModel):
    id: str
    entity_type: str  # e.g., "block", "train", "switch", "timer"
    entity_id: str
    property_name: str  # e.g., "occupied", "front_s", "current_alignment"
    operator: ConditionOperator
    value: Optional[Any] = None

class LogicGate(str, Enum):
    AND = "and"
    OR = "or"

class Action(BaseModel):
    id: str
    target_type: str  # e.g., "brake", "launch", "switch", "dispatch"
    target_id: str
    command: str  # e.g., "set_state", "enable", "set_alignment"
    parameters: Dict[str, Any] = {}

class Timer(BaseModel):
    id: str
    duration_s: float
    start_condition_id: Optional[str] = None
    reset_condition_id: Optional[str] = None
    current_value_s: float = 0.0
    running: bool = False

class VisualRule(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    conditions: List[str]  # Condition IDs
    condition_logic: LogicGate = LogicGate.AND
    actions: List[str]  # Action IDs
    timers: List[str] = []  # Timer IDs
    priority: int = 0
    enabled: bool = True

class ControlScript(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    script_content: str
    allowed_apis: List[str] = [
        "get_train", "is_block_clear", "set_switch",
        "set_equipment_state", "allow_dispatch", "get_timer"
    ]
    enabled: bool = True
```

### project.py - Project Wrapper

```python
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from .track import Point, Path, Section
from .topology import Junction, Block, Station
from .train import Vehicle, Train
from .equipment import Equipment
from .control import VisualRule, ControlScript

class ProjectMetadata(BaseModel):
    name: str = "Untitled Project"
    units: str = "metric"
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    modified_at: datetime = Field(default_factory=datetime.utcnow)

class SimulationSettings(BaseModel):
    time_step_s: float = 0.01
    gravity_mps2: float = 9.81
    drag_coefficient: float = 0.5
    rolling_resistance_coefficient: float = 0.002
    air_density_kg_m3: float = 1.225

class Project(BaseModel):
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    metadata: ProjectMetadata = Field(default_factory=ProjectMetadata)
    points: List[Point] = []
    paths: List[Path] = []
    junctions: List[Junction] = []
    switches: List[dict] = []  # TrackSwitch equipment with type discriminator
    sections: List[Section] = []
    stations: List[Station] = []
    blocks: List[Block] = []
    vehicles: List[Vehicle] = []
    trains: List[Train] = []
    equipment: List[dict] = []  # Equipment with type discriminator
    control_rules: List[VisualRule] = []
    control_scripts: List[ControlScript] = []
    simulation_settings: SimulationSettings = Field(default_factory=SimulationSettings)
```

## API Design

### Project APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects` | Create new project |
| GET | `/projects/{id}` | Get project by ID |
| PUT | `/projects/{id}` | Update project |
| DELETE | `/projects/{id}` | Delete project |
| POST | `/projects/{id}/save` | Save project to JSON file |
| POST | `/projects/load` | Load project from uploaded JSON file |

### Track and Topology APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects/{id}/points` | Create point |
| PUT | `/projects/{id}/points/{point_id}` | Update point |
| DELETE | `/projects/{id}/points/{point_id}` | Delete point |
| POST | `/projects/{id}/paths` | Create path |
| PUT | `/projects/{id}/paths/{path_id}` | Update path |
| DELETE | `/projects/{id}/paths/{path_id}` | Delete path |
| POST | `/projects/{id}/junctions` | Create junction |
| POST | `/projects/{id}/switches` | Create switch |
| POST | `/projects/{id}/sections` | Create section |
| POST | `/projects/{id}/blocks` | Create block |
| POST | `/projects/{id}/stations` | Create station |

### Train APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects/{id}/vehicles` | Create vehicle |
| PUT | `/projects/{id}/vehicles/{vehicle_id}` | Update vehicle |
| DELETE | `/projects/{id}/vehicles/{vehicle_id}` | Delete vehicle |
| POST | `/projects/{id}/trains` | Create train |
| PUT | `/projects/{id}/trains/{train_id}` | Update train |
| DELETE | `/projects/{id}/trains/{train_id}` | Delete train |

### Equipment APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects/{id}/equipment` | Create equipment |
| PUT | `/projects/{id}/equipment/{equipment_id}` | Update equipment |
| DELETE | `/projects/{id}/equipment/{equipment_id}` | Delete equipment |

### Control APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects/{id}/control/rules` | Create visual rule |
| PUT | `/projects/{id}/control/rules/{rule_id}` | Update visual rule |
| DELETE | `/projects/{id}/control/rules/{rule_id}` | Delete visual rule |
| POST | `/projects/{id}/control/scripts` | Create control script |
| PUT | `/projects/{id}/control/scripts/{script_id}` | Update control script |
| DELETE | `/projects/{id}/control/scripts/{script_id}` | Delete control script |
| POST | `/projects/{id}/control/validate` | Validate control logic |
| POST | `/projects/{id}/control/compile` | Compile rules/scripts to executable form |

### Simulation APIs (Placeholder)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects/{id}/simulate/start` | Start simulation |
| POST | `/projects/{id}/simulate/stop` | Stop simulation |
| POST | `/projects/{id}/simulate/reset` | Reset simulation |
| GET | `/projects/{id}/simulate/state` | Get simulation state |
| WS | `/projects/{id}/simulate/stream` | WebSocket for live updates |

## Frontend Scaffolding

### Dependencies

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@react-three/fiber": "^8.15.0",
    "@react-three/drei": "^9.88.0",
    "three": "^0.159.0",
    "@mantine/core": "^7.2.0",
    "@mantine/hooks": "^7.2.0",
    "@mantine/notifications": "^7.2.0",
    "@tabler/icons-react": "^2.42.0",
    "plotly.js": "^2.27.0",
    "react-plotly.js": "^2.6.0",
    "@monaco-editor/react": "^4.6.0",
    "zustand": "^4.4.0",
    "@tanstack/react-query": "^5.8.0",
    "axios": "^1.6.0",
    "react-router-dom": "^6.20.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@types/three": "^0.159.0",
    "@types/react-plotly.js": "^2.6.0",
    "eslint": "^8.55.0",
    "@typescript-eslint/eslint-plugin": "^6.13.0",
    "@typescript-eslint/parser": "^6.13.0"
  }
}
```

### Directory Structure

```
frontend/src/
├── main.tsx              # Entry point
├── App.tsx               # Root component with routing
├── api/
│   ├── client.ts         # Axios instance with base URL
│   ├── projects.ts       # Project API functions
│   ├── tracks.ts         # Track/topology API functions
│   ├── trains.ts         # Train API functions
│   ├── equipment.ts      # Equipment API functions
│   └── control.ts        # Control API functions
├── state/
│   ├── projectStore.ts   # Current project state (Zustand)
│   └── uiStore.ts        # UI state (selections, panels)
├── components/
│   ├── Layout.tsx        # App shell with Mantine AppShell
│   └── Navbar.tsx        # Navigation sidebar
└── features/             # Empty placeholders for Phase 6
    ├── track-editor/
    ├── topology-editor/
    ├── train-editor/
    ├── equipment-editor/
    ├── control-editor/
    ├── simulation-player/
    └── analytics/
```

## Validation Rules (Phase 1)

### Geometry Validation
- Path has at least 2 points for interpolation
- Section extents are within path bounds
- Banking values within reasonable limits (±90°)

### Equipment Validation
- Equipment lies fully within path bounds
- Equipment is placed in compatible zone types
- No overlapping equipment of incompatible types

### Operational Validation
- Junctions connect to existing paths
- Switches reference valid junctions
- Trains reference existing vehicles

### Control Validation
- Visual rules reference existing entities
- Python scripts use only allowed APIs

## Out of Scope for Phase 1

- Database integration (PostgreSQL)
- 3D rendering (Phase 2/6)
- Physics simulation (Phase 3)
- Equipment force behavior (Phase 4)
- Control rule execution (Phase 5)
- Advanced validation (Phase 7)

## Success Criteria

Phase 1 is complete when:

1. Backend runs with `uvicorn app.main:app --reload`
2. All Pydantic models are defined and validated
3. API endpoints return proper OpenAPI documentation
4. Projects can be created, saved, and loaded as JSON files
5. Frontend runs with `npm run dev`
6. Frontend can call backend health check endpoint
7. Basic test coverage for domain models
8. JSON Schema is auto-generated and accessible via `/openapi.json` for frontend TypeScript type generation