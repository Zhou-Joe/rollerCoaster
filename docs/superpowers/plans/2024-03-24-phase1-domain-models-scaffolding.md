# Phase 1: Domain Models and Project Scaffolding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish project foundation with Pydantic domain models, FastAPI backend, React frontend, and JSON file persistence.

**Architecture:** Monorepo with backend (FastAPI + Pydantic) and frontend (React + TypeScript + Vite). Pydantic models are the source of truth for all data structures. JSON file-based persistence for Phase 1.

**Tech Stack:** Python 3.12+, FastAPI, Pydantic v2, pytest | React 18, TypeScript, Vite, Mantine, Zustand, TanStack Query

---

## File Structure

```
rollerCoaster/
├── .gitignore
├── README.md
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── projects.py
│   │   │   ├── tracks.py
│   │   │   ├── trains.py
│   │   │   ├── equipment.py
│   │   │   ├── control.py
│   │   │   └── simulation.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── common.py
│   │   │   ├── track.py
│   │   │   ├── topology.py
│   │   │   ├── train.py
│   │   │   ├── equipment.py
│   │   │   ├── control.py
│   │   │   └── project.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── project_io.py
│   │   │   └── validator.py
│   │   └── simulation/
│   │       └── __init__.py
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       └── test_models/
│           ├── __init__.py
│           ├── test_common.py
│           ├── test_track.py
│           ├── test_topology.py
│           ├── test_train.py
│           ├── test_equipment.py
│           ├── test_control.py
│           └── test_project.py
└── frontend/
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── api/
        │   └── client.ts
        ├── state/
        │   └── projectStore.ts
        └── components/
            └── Layout.tsx
```

---

## Task 1: Backend Project Setup

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "roller-coaster-simulator"
version = "0.1.0"
description = "Professional roller coaster simulation platform"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "python-multipart>=0.0.6",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.26.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.hatch.build.targets.wheel]
packages = ["app"]
```

- [ ] **Step 2: Create app/__init__.py**

```python
"""Roller Coaster Simulator Backend"""
```

- [ ] **Step 3: Create config.py**

```python
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "Roller Coaster Simulator"
    app_version: str = "0.1.0"
    debug: bool = True

    # File storage
    projects_dir: str = "projects"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()
```

- [ ] **Step 4: Install dependencies**

Run: `cd backend && pip install -e ".[dev]"`
Expected: Successfully installed packages

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "chore: scaffold backend project structure"
```

---

## Task 2: Common Domain Models

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/common.py`
- Create: `backend/tests/test_models/__init__.py`
- Create: `backend/tests/test_models/test_common.py`

- [ ] **Step 1: Write failing test for enums**

```python
# backend/tests/test_models/test_common.py
import pytest
from app.models.common import (
    ZoneType, FailSafeMode, BrakeState, BoosterMode,
    LoadCase, TrainState, StationType, EquipmentConstraint
)


def test_zone_type_values():
    assert ZoneType.LOAD.value == "load"
    assert ZoneType.UNLOAD.value == "unload"
    assert ZoneType.LAUNCH.value == "launch"
    assert ZoneType.BRAKE.value == "brake"
    assert ZoneType.HOLD.value == "hold"
    assert ZoneType.FREE.value == "free"
    assert ZoneType.MAINTENANCE.value == "maintenance"


def test_fail_safe_mode_values():
    assert FailSafeMode.NORMALLY_OPEN.value == "normally_open"
    assert FailSafeMode.NORMALLY_CLOSED.value == "normally_closed"


def test_brake_state_values():
    assert BrakeState.OPEN.value == "open"
    assert BrakeState.CLOSED.value == "closed"
    assert BrakeState.EMERGENCY_STOP.value == "emergency_stop"


def test_booster_mode_values():
    assert BoosterMode.DRIVE.value == "drive"
    assert BoosterMode.BRAKE.value == "brake"
    assert BoosterMode.IDLE.value == "idle"


def test_load_case_values():
    assert LoadCase.EMPTY.value == "empty"
    assert LoadCase.FULLY_LOADED.value == "fully_loaded"
    assert LoadCase.CUSTOM.value == "custom"


def test_train_state_values():
    assert TrainState.STOPPED.value == "stopped"
    assert TrainState.MOVING.value == "moving"
    assert TrainState.LOADING.value == "loading"
    assert TrainState.UNLOADING.value == "unloading"
    assert TrainState.IN_MAINTENANCE.value == "in_maintenance"


def test_station_type_values():
    assert StationType.LOAD.value == "load"
    assert StationType.UNLOAD.value == "unload"
    assert StationType.TRANSFER.value == "transfer"
    assert StationType.HOLD.value == "hold"


def test_equipment_constraint_defaults():
    constraint = EquipmentConstraint()
    assert constraint.allowed_equipment_types == []
    assert constraint.min_straightness is None
    assert constraint.max_curvature is None


def test_equipment_constraint_with_values():
    constraint = EquipmentConstraint(
        allowed_equipment_types=["lsm_launch", "booster"],
        min_straightness=0.95,
        max_curvature=0.01
    )
    assert constraint.allowed_equipment_types == ["lsm_launch", "booster"]
    assert constraint.min_straightness == 0.95
    assert constraint.max_curvature == 0.01
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_models/test_common.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.models.common'"

- [ ] **Step 3: Create models/__init__.py**

```python
"""Domain models for roller coaster simulator"""
```

- [ ] **Step 4: Create models/common.py**

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


Position3D = Tuple[float, float, float]


class EquipmentConstraint(BaseModel):
    allowed_equipment_types: List[str] = []
    min_straightness: Optional[float] = None
    max_curvature: Optional[float] = None
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && pytest tests/test_models/test_common.py -v`
Expected: All tests PASS

- [ ] **Step 6: Create tests/__init__.py and tests/test_models/__init__.py**

```python
# backend/tests/__init__.py
"""Tests for roller coaster simulator backend"""

# backend/tests/test_models/__init__.py
"""Tests for domain models"""
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/ backend/tests/
git commit -m "feat: add common domain models (enums, EquipmentConstraint)"
```

---

## Task 3: Track Models

**Files:**
- Create: `backend/app/models/track.py`
- Create: `backend/tests/test_models/test_track.py`

- [ ] **Step 1: Write failing test for track models**

```python
# backend/tests/test_models/test_track.py
import pytest
from app.models.track import Point, Path, Section
from app.models.common import ZoneType, EquipmentConstraint


def test_point_creation():
    point = Point(id="pt_001", x=0.0, y=0.0, z=10.0)
    assert point.id == "pt_001"
    assert point.x == 0.0
    assert point.y == 0.0
    assert point.z == 10.0
    assert point.bank_deg == 0.0
    assert point.editable is True


def test_point_with_bank():
    point = Point(id="pt_002", x=10.0, y=0.0, z=15.0, bank_deg=45.0, editable=False)
    assert point.bank_deg == 45.0
    assert point.editable is False


def test_path_creation():
    path = Path(id="path_001", point_ids=["pt_001", "pt_002", "pt_003"])
    assert path.id == "path_001"
    assert len(path.point_ids) == 3
    assert path.length_m is None


def test_path_with_length():
    path = Path(id="path_001", point_ids=["pt_001", "pt_002"], length_m=100.5)
    assert path.length_m == 100.5


def test_section_creation():
    section = Section(
        id="sec_001",
        path_id="path_001",
        start_s=0.0,
        end_s=50.0,
        zone_type=ZoneType.LAUNCH
    )
    assert section.id == "sec_001"
    assert section.path_id == "path_001"
    assert section.zone_type == ZoneType.LAUNCH
    assert section.label is None


def test_section_with_constraints():
    constraint = EquipmentConstraint(allowed_equipment_types=["lsm_launch"])
    section = Section(
        id="sec_001",
        path_id="path_001",
        start_s=0.0,
        end_s=100.0,
        zone_type=ZoneType.BRAKE,
        label="Final Brake Run",
        equipment_constraints=constraint
    )
    assert section.label == "Final Brake Run"
    assert section.equipment_constraints.allowed_equipment_types == ["lsm_launch"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_models/test_track.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.models.track'"

- [ ] **Step 3: Create models/track.py**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_models/test_track.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/track.py backend/tests/test_models/test_track.py
git commit -m "feat: add track domain models (Point, Path, Section)"
```

---

## Task 4: Topology Models

**Files:**
- Create: `backend/app/models/topology.py`
- Create: `backend/tests/test_models/test_topology.py`

- [ ] **Step 1: Write failing test for topology models**

```python
# backend/tests/test_models/test_topology.py
import pytest
from app.models.topology import Junction, BlockPathInterval, Block, Station
from app.models.common import StationType


def test_junction_creation():
    junction = Junction(
        id="jct_001",
        incoming_path_id="path_001",
        outgoing_path_ids=["path_002", "path_003"],
        position_s=100.0
    )
    assert junction.id == "jct_001"
    assert junction.incoming_path_id == "path_001"
    assert len(junction.outgoing_path_ids) == 2


def test_block_path_interval():
    interval = BlockPathInterval(path_id="path_001", start_s=0.0, end_s=50.0)
    assert interval.path_id == "path_001"
    assert interval.start_s == 0.0
    assert interval.end_s == 50.0


def test_block_creation():
    block = Block(
        id="block_001",
        path_intervals=[
            BlockPathInterval(path_id="path_001", start_s=0.0, end_s=100.0)
        ]
    )
    assert block.id == "block_001"
    assert block.occupied is False
    assert block.reserved_by is None


def test_block_occupied():
    block = Block(
        id="block_001",
        path_intervals=[
            BlockPathInterval(path_id="path_001", start_s=0.0, end_s=100.0)
        ],
        occupied=True,
        reserved_by="train_001"
    )
    assert block.occupied is True
    assert block.reserved_by == "train_001"


def test_station_creation():
    station = Station(
        id="station_001",
        name="Main Station",
        station_type=StationType.LOAD,
        associated_block_ids=["block_001"],
        position_path_id="path_001",
        position_s=50.0
    )
    assert station.id == "station_001"
    assert station.name == "Main Station"
    assert station.station_type == StationType.LOAD
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_models/test_topology.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create models/topology.py**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_models/test_topology.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/topology.py backend/tests/test_models/test_topology.py
git commit -m "feat: add topology domain models (Junction, Block, Station)"
```

---

## Task 5: Train Models

**Files:**
- Create: `backend/app/models/train.py`
- Create: `backend/tests/test_models/test_train.py`

- [ ] **Step 1: Write failing test for train models**

```python
# backend/tests/test_models/test_train.py
import pytest
from app.models.train import Vehicle, Train
from app.models.common import LoadCase, TrainState


def test_vehicle_creation():
    vehicle = Vehicle(
        id="veh_001",
        length_m=2.5,
        dry_mass_kg=500.0,
        capacity=4
    )
    assert vehicle.id == "veh_001"
    assert vehicle.length_m == 2.5
    assert vehicle.dry_mass_kg == 500.0
    assert vehicle.capacity == 4
    assert vehicle.passenger_mass_per_person_kg == 75.0


def test_vehicle_with_type():
    vehicle = Vehicle(
        id="veh_001",
        length_m=3.0,
        dry_mass_kg=600.0,
        capacity=6,
        passenger_mass_per_person_kg=80.0,
        vehicle_type="passenger_car"
    )
    assert vehicle.vehicle_type == "passenger_car"
    assert vehicle.passenger_mass_per_person_kg == 80.0


def test_train_creation():
    train = Train(
        id="train_001",
        vehicle_ids=["veh_001", "veh_002", "veh_003"]
    )
    assert train.id == "train_001"
    assert len(train.vehicle_ids) == 3
    assert train.coupling_gap_m == 0.5
    assert train.current_state == TrainState.STOPPED
    assert train.load_case == LoadCase.EMPTY


def test_train_with_route():
    train = Train(
        id="train_001",
        vehicle_ids=["veh_001"],
        route_assignment="route_main",
        current_state=TrainState.MOVING,
        load_case=LoadCase.FULLY_LOADED,
        front_position_s=150.0,
        current_path_id="path_001"
    )
    assert train.route_assignment == "route_main"
    assert train.current_state == TrainState.MOVING
    assert train.load_case == LoadCase.FULLY_LOADED
    assert train.front_position_s == 150.0


def test_train_custom_occupancy():
    train = Train(
        id="train_001",
        vehicle_ids=["veh_001"],
        load_case=LoadCase.CUSTOM,
        custom_occupancy_factor=0.75
    )
    assert train.load_case == LoadCase.CUSTOM
    assert train.custom_occupancy_factor == 0.75
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_models/test_train.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create models/train.py**

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
    vehicle_ids: List[str]
    coupling_gap_m: float = 0.5
    route_assignment: Optional[str] = None
    current_state: TrainState = TrainState.STOPPED
    load_case: LoadCase = LoadCase.EMPTY
    custom_occupancy_factor: Optional[float] = None
    front_position_s: float = 0.0
    current_path_id: Optional[str] = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_models/test_train.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/train.py backend/tests/test_models/test_train.py
git commit -m "feat: add train domain models (Vehicle, Train)"
```

---

## Task 6: Equipment Models

**Files:**
- Create: `backend/app/models/equipment.py`
- Create: `backend/tests/test_models/test_equipment.py`

- [ ] **Step 1: Write failing test for equipment models**

```python
# backend/tests/test_models/test_equipment.py
import pytest
from app.models.equipment import (
    EquipmentType, LSMLaunch, Lift, PneumaticBrake,
    TrimBrake, Booster, TrackSwitch
)
from app.models.common import FailSafeMode, BrakeState, BoosterMode


def test_equipment_type_values():
    assert EquipmentType.LSM_LAUNCH.value == "lsm_launch"
    assert EquipmentType.LIFT.value == "lift"
    assert EquipmentType.PNEUMATIC_BRAKE.value == "pneumatic_brake"
    assert EquipmentType.TRIM_BRAKE.value == "trim_brake"
    assert EquipmentType.BOOSTER.value == "booster"
    assert EquipmentType.TRACK_SWITCH.value == "track_switch"


def test_lsm_launch_creation():
    lsm = LSMLaunch(
        id="lsm_001",
        path_id="path_001",
        start_s=0.0,
        end_s=100.0,
        stator_count=10,
        magnetic_field_strength=1.5,
        max_force_n=50000.0
    )
    assert lsm.id == "lsm_001"
    assert lsm.equipment_type == EquipmentType.LSM_LAUNCH
    assert lsm.stator_count == 10
    assert lsm.enabled is True


def test_lift_creation():
    lift = Lift(
        id="lift_001",
        path_id="path_001",
        start_s=0.0,
        end_s=50.0,
        lift_speed_mps=2.0,
        max_pull_force_n=30000.0,
        engagement_point_s=5.0,
        release_point_s=45.0
    )
    assert lift.id == "lift_001"
    assert lift.equipment_type == EquipmentType.LIFT
    assert lift.lift_speed_mps == 2.0


def test_pneumatic_brake_creation():
    brake = PneumaticBrake(
        id="brake_001",
        path_id="path_001",
        start_s=0.0,
        end_s=20.0,
        max_brake_force_n=40000.0,
        response_time_s=0.3,
        air_pressure=6.0,
        fail_safe_mode=FailSafeMode.NORMALLY_CLOSED
    )
    assert brake.id == "brake_001"
    assert brake.equipment_type == EquipmentType.PNEUMATIC_BRAKE
    assert brake.fail_safe_mode == FailSafeMode.NORMALLY_CLOSED
    assert brake.state == BrakeState.OPEN


def test_trim_brake_creation():
    trim = TrimBrake(
        id="trim_001",
        path_id="path_001",
        start_s=50.0,
        end_s=60.0,
        max_trim_force_n=15000.0
    )
    assert trim.id == "trim_001"
    assert trim.equipment_type == EquipmentType.TRIM_BRAKE
    assert trim.enabled is True


def test_booster_creation():
    booster = Booster(
        id="booster_001",
        path_id="path_001",
        start_s=0.0,
        end_s=10.0,
        wheel_count=4,
        max_drive_force_n=5000.0,
        max_drive_speed_mps=2.0,
        brake_friction_force_n=2000.0
    )
    assert booster.id == "booster_001"
    assert booster.equipment_type == EquipmentType.BOOSTER
    assert booster.mode == BoosterMode.IDLE


def test_track_switch_creation():
    switch = TrackSwitch(
        id="switch_001",
        junction_id="jct_001",
        incoming_path_id="path_001",
        outgoing_path_ids=["path_002", "path_003"],
        current_alignment="path_002"
    )
    assert switch.id == "switch_001"
    assert switch.equipment_type == EquipmentType.TRACK_SWITCH
    assert switch.actuation_time_s == 2.0
    assert switch.locked_when_occupied is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_models/test_equipment.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create models/equipment.py**

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


ForceCurvePoint = Dict[str, Any]
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


Equipment = Union[LSMLaunch, Lift, PneumaticBrake, TrimBrake, Booster, TrackSwitch]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_models/test_equipment.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/equipment.py backend/tests/test_models/test_equipment.py
git commit -m "feat: add equipment domain models (LSM, Lift, Brakes, Booster, Switch)"
```

---

## Task 7: Control Models

**Files:**
- Create: `backend/app/models/control.py`
- Create: `backend/tests/test_models/test_control.py`

- [ ] **Step 1: Write failing test for control models**

```python
# backend/tests/test_models/test_control.py
import pytest
from app.models.control import (
    ConditionOperator, Condition, LogicGate, Action, Timer,
    VisualRule, ControlScript
)


def test_condition_operator_values():
    assert ConditionOperator.EQUALS.value == "=="
    assert ConditionOperator.NOT_EQUALS.value == "!="
    assert ConditionOperator.GREATER_THAN.value == ">"
    assert ConditionOperator.LESS_THAN.value == "<"
    assert ConditionOperator.IS_TRUE.value == "is_true"
    assert ConditionOperator.IS_FALSE.value == "is_false"


def test_condition_creation():
    cond = Condition(
        id="cond_001",
        entity_type="block",
        entity_id="block_001",
        property_name="occupied",
        operator=ConditionOperator.IS_FALSE
    )
    assert cond.id == "cond_001"
    assert cond.entity_type == "block"
    assert cond.operator == ConditionOperator.IS_FALSE


def test_condition_with_value():
    cond = Condition(
        id="cond_002",
        entity_type="train",
        entity_id="train_001",
        property_name="front_s",
        operator=ConditionOperator.GREATER_THAN,
        value=100.0
    )
    assert cond.value == 100.0


def test_action_creation():
    action = Action(
        id="act_001",
        target_type="brake",
        target_id="brake_001",
        command="set_state",
        parameters={"state": "closed"}
    )
    assert action.id == "act_001"
    assert action.target_type == "brake"
    assert action.parameters == {"state": "closed"}


def test_timer_creation():
    timer = Timer(
        id="timer_001",
        duration_s=30.0
    )
    assert timer.id == "timer_001"
    assert timer.duration_s == 30.0
    assert timer.current_value_s == 0.0
    assert timer.running is False


def test_visual_rule_creation():
    rule = VisualRule(
        id="rule_001",
        name="Dispatch when block clear",
        conditions=["cond_001"],
        actions=["act_001"]
    )
    assert rule.id == "rule_001"
    assert rule.name == "Dispatch when block clear"
    assert rule.condition_logic == LogicGate.AND
    assert rule.enabled is True


def test_control_script_creation():
    script = ControlScript(
        id="script_001",
        name="Main dispatch logic",
        script_content="if is_block_clear('block_001'):\n    allow_dispatch('station_001')"
    )
    assert script.id == "script_001"
    assert "is_block_clear" in script.script_content
    assert "allow_dispatch" in script.allowed_apis
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_models/test_control.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create models/control.py**

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


class LogicGate(str, Enum):
    AND = "and"
    OR = "or"


class Condition(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    property_name: str
    operator: ConditionOperator
    value: Optional[Any] = None


class Action(BaseModel):
    id: str
    target_type: str
    target_id: str
    command: str
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
    conditions: List[str]
    condition_logic: LogicGate = LogicGate.AND
    actions: List[str]
    timers: List[str] = []
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

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_models/test_control.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/control.py backend/tests/test_models/test_control.py
git commit -m "feat: add control domain models (Condition, Action, Rule, Script)"
```

---

## Task 8: Project Model

**Files:**
- Create: `backend/app/models/project.py`
- Create: `backend/tests/test_models/test_project.py`

- [ ] **Step 1: Write failing test for project model**

```python
# backend/tests/test_models/test_project.py
import pytest
from datetime import datetime
from app.models.project import Project, ProjectMetadata, SimulationSettings
from app.models.track import Point, Path, Section
from app.models.common import ZoneType


def test_project_metadata_defaults():
    meta = ProjectMetadata()
    assert meta.name == "Untitled Project"
    assert meta.units == "metric"
    assert meta.version == 1


def test_project_metadata_custom():
    meta = ProjectMetadata(name="My Coaster", units="metric", version=2)
    assert meta.name == "My Coaster"


def test_simulation_settings_defaults():
    settings = SimulationSettings()
    assert settings.time_step_s == 0.01
    assert settings.gravity_mps2 == 9.81
    assert settings.drag_coefficient == 0.5


def test_project_creation():
    project = Project()
    assert project.metadata.name == "Untitled Project"
    assert project.points == []
    assert project.paths == []
    assert project.trains == []


def test_project_with_data():
    project = Project(
        metadata=ProjectMetadata(name="Test Coaster"),
        points=[
            Point(id="pt_001", x=0.0, y=0.0, z=0.0),
            Point(id="pt_002", x=10.0, y=0.0, z=5.0),
        ],
        paths=[
            Path(id="path_001", point_ids=["pt_001", "pt_002"])
        ]
    )
    assert project.metadata.name == "Test Coaster"
    assert len(project.points) == 2
    assert len(project.paths) == 1


def test_project_json_serialization():
    project = Project(metadata=ProjectMetadata(name="JSON Test"))
    json_str = project.model_dump_json()
    assert '"name":"JSON Test"' in json_str

    # Deserialize
    loaded = Project.model_validate_json(json_str)
    assert loaded.metadata.name == "JSON Test"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_models/test_project.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create models/project.py**

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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_models/test_project.py -v`
Expected: All tests PASS

- [ ] **Step 5: Update models/__init__.py**

```python
"""Domain models for roller coaster simulator"""

from .common import (
    ZoneType, FailSafeMode, BrakeState, BoosterMode,
    LoadCase, TrainState, StationType, EquipmentConstraint
)
from .track import Point, Path, Section
from .topology import Junction, BlockPathInterval, Block, Station
from .train import Vehicle, Train
from .equipment import (
    EquipmentType, LSMLaunch, Lift, PneumaticBrake,
    TrimBrake, Booster, TrackSwitch, Equipment
)
from .control import (
    ConditionOperator, Condition, LogicGate, Action, Timer,
    VisualRule, ControlScript
)
from .project import Project, ProjectMetadata, SimulationSettings

__all__ = [
    "ZoneType", "FailSafeMode", "BrakeState", "BoosterMode",
    "LoadCase", "TrainState", "StationType", "EquipmentConstraint",
    "Point", "Path", "Section",
    "Junction", "BlockPathInterval", "Block", "Station",
    "Vehicle", "Train",
    "EquipmentType", "LSMLaunch", "Lift", "PneumaticBrake",
    "TrimBrake", "Booster", "TrackSwitch", "Equipment",
    "ConditionOperator", "Condition", "LogicGate", "Action", "Timer",
    "VisualRule", "ControlScript",
    "Project", "ProjectMetadata", "SimulationSettings",
]
```

- [ ] **Step 6: Run all model tests**

Run: `cd backend && pytest tests/test_models/ -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/ backend/tests/test_models/
git commit -m "feat: add Project model and export all models from __init__"
```

---

## Task 9: FastAPI Application Setup

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/router.py`
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: Create main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.router import api_router

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.app_version}
```

- [ ] **Step 2: Create api/__init__.py**

```python
"""API endpoints"""
```

- [ ] **Step 3: Create api/router.py**

```python
from fastapi import APIRouter

api_router = APIRouter()

# Routers will be added in subsequent tasks
# from .projects import router as projects_router
# api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
```

- [ ] **Step 4: Create tests/conftest.py**

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)
```

- [ ] **Step 5: Test the application starts**

Run: `cd backend && python -c "from app.main import app; print('OK')"`
Expected: OK

- [ ] **Step 6: Test health endpoint**

Run: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 &`
Then: `curl http://localhost:8000/health`
Expected: `{"status": "healthy", "version": "0.1.0"}`

Kill the server: `pkill -f "uvicorn app.main:app"`

- [ ] **Step 7: Commit**

```bash
git add backend/app/main.py backend/app/api/ backend/tests/conftest.py
git commit -m "feat: add FastAPI application with health check endpoint"
```

---

## Task 10: Project Service (JSON I/O)

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/project_io.py`
- Create: `backend/tests/test_services/__init__.py`
- Create: `backend/tests/test_services/test_project_io.py`

- [ ] **Step 1: Write failing test for project I/O**

```python
# backend/tests/test_services/test_project_io.py
import pytest
import tempfile
import os
from app.services.project_io import ProjectIO
from app.models.project import Project, ProjectMetadata


def test_save_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        io = ProjectIO(tmpdir)
        project = Project(metadata=ProjectMetadata(name="Test Coaster"))

        filepath = io.save(project, "test_project.json")

        assert os.path.exists(filepath)
        assert filepath.endswith("test_project.json")


def test_load_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        io = ProjectIO(tmpdir)
        project = Project(metadata=ProjectMetadata(name="Test Coaster"))

        filepath = io.save(project, "test_project.json")
        loaded = io.load("test_project.json")

        assert loaded.metadata.name == "Test Coaster"


def test_list_projects():
    with tempfile.TemporaryDirectory() as tmpdir:
        io = ProjectIO(tmpdir)

        project1 = Project(metadata=ProjectMetadata(name="Coaster 1"))
        project2 = Project(metadata=ProjectMetadata(name="Coaster 2"))

        io.save(project1, "coaster1.json")
        io.save(project2, "coaster2.json")

        projects = io.list_projects()

        assert len(projects) == 2
        assert "coaster1.json" in projects
        assert "coaster2.json" in projects


def test_delete_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        io = ProjectIO(tmpdir)
        project = Project(metadata=ProjectMetadata(name="Test"))

        filepath = io.save(project, "delete_me.json")
        assert os.path.exists(filepath)

        io.delete("delete_me.json")
        assert not os.path.exists(filepath)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_services/test_project_io.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create services/__init__.py**

```python
"""Business logic services"""
```

- [ ] **Step 4: Create services/project_io.py**

```python
import json
import os
from typing import List
from pathlib import Path
from app.models.project import Project


class ProjectIO:
    def __init__(self, projects_dir: str = "projects"):
        self.projects_dir = Path(projects_dir)
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def save(self, project: Project, filename: str) -> str:
        filepath = self.projects_dir / filename
        with open(filepath, "w") as f:
            f.write(project.model_dump_json(indent=2))
        return str(filepath)

    def load(self, filename: str) -> Project:
        filepath = self.projects_dir / filename
        with open(filepath, "r") as f:
            data = json.load(f)
        return Project.model_validate(data)

    def list_projects(self) -> List[str]:
        return [f.name for f in self.projects_dir.glob("*.json")]

    def delete(self, filename: str) -> None:
        filepath = self.projects_dir / filename
        if filepath.exists():
            filepath.unlink()

    def exists(self, filename: str) -> bool:
        return (self.projects_dir / filename).exists()
```

- [ ] **Step 5: Create tests/test_services/__init__.py**

```python
"""Tests for services"""
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd backend && pytest tests/test_services/test_project_io.py -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/ backend/tests/test_services/
git commit -m "feat: add ProjectIO service for JSON file persistence"
```

---

## Task 11: Project API Endpoints

**Files:**
- Create: `backend/app/api/projects.py`
- Create: `backend/tests/test_api/__init__.py`
- Create: `backend/tests/test_api/test_projects.py`

- [ ] **Step 1: Write failing test for project API**

```python
# backend/tests/test_api/test_projects.py
import pytest
from fastapi.testclient import TestClient


def test_create_project(client):
    response = client.post("/api/projects", json={"name": "New Coaster"})
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["name"] == "New Coaster"


def test_get_project(client):
    # Create a project first
    create_resp = client.post("/api/projects", json={"name": "Test"})
    project_id = create_resp.json()["id"]

    response = client.get(f"/api/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["metadata"]["name"] == "Test"


def test_update_project(client):
    create_resp = client.post("/api/projects", json={"name": "Original"})
    project_id = create_resp.json()["id"]

    response = client.put(f"/api/projects/{project_id}", json={
        "metadata": {"name": "Updated"}
    })
    assert response.status_code == 200
    assert response.json()["metadata"]["name"] == "Updated"


def test_delete_project(client):
    create_resp = client.post("/api/projects", json={"name": "To Delete"})
    project_id = create_resp.json()["id"]

    response = client.delete(f"/api/projects/{project_id}")
    assert response.status_code == 200

    # Verify it's gone
    get_resp = client.get(f"/api/projects/{project_id}")
    assert get_resp.status_code == 404


def test_list_projects(client):
    client.post("/api/projects", json={"name": "Coaster 1"})
    client.post("/api/projects", json={"name": "Coaster 2"})

    response = client.get("/api/projects")
    assert response.status_code == 200
    assert len(response.json()) >= 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_api/test_projects.py -v`
Expected: FAIL with 404 or route not found

- [ ] **Step 3: Create tests/test_api/__init__.py**

```python
"""Tests for API endpoints"""
```

- [ ] **Step 4: Create api/projects.py**

```python
from fastapi import APIRouter, HTTPException
from typing import Dict, List
from datetime import datetime
from app.models.project import Project, ProjectMetadata
from app.services.project_io import ProjectIO
import uuid

router = APIRouter()

# In-memory store for Phase 1 (will be replaced with proper persistence)
_projects: Dict[str, Project] = {}
_project_io = ProjectIO()


def get_project_io():
    return _project_io


@router.post("/")
async def create_project(metadata: ProjectMetadata = None):
    if metadata is None:
        metadata = ProjectMetadata()
    project = Project(metadata=metadata)
    project_id = str(uuid.uuid4())
    _projects[project_id] = project
    return {"id": project_id, **project.model_dump()}


@router.get("/")
async def list_projects():
    return [
        {"id": pid, "metadata": p.metadata.model_dump()}
        for pid, p in _projects.items()
    ]


@router.get("/{project_id}")
async def get_project(project_id: str):
    if project_id not in _projects:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"id": project_id, **_projects[project_id].model_dump()}


@router.put("/{project_id}")
async def update_project(project_id: str, updates: Dict):
    if project_id not in _projects:
        raise HTTPException(status_code=404, detail="Project not found")

    project = _projects[project_id]

    if "metadata" in updates:
        project.metadata = ProjectMetadata(**updates["metadata"])

    project.metadata.modified_at = datetime.utcnow()
    _projects[project_id] = project

    return {"id": project_id, **project.model_dump()}


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    if project_id not in _projects:
        raise HTTPException(status_code=404, detail="Project not found")
    del _projects[project_id]
    return {"status": "deleted"}


@router.post("/{project_id}/save")
async def save_project(project_id: str, filename: str = None):
    if project_id not in _projects:
        raise HTTPException(status_code=404, detail="Project not found")

    project = _projects[project_id]
    fname = filename or f"{project.metadata.name.replace(' ', '_')}.json"
    filepath = _project_io.save(project, fname)

    return {"status": "saved", "filepath": filepath}
```

- [ ] **Step 5: Update api/router.py**

```python
from fastapi import APIRouter
from .projects import router as projects_router

api_router = APIRouter()
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd backend && pytest tests/test_api/test_projects.py -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/api/ backend/tests/test_api/
git commit -m "feat: add project CRUD API endpoints"
```

---

## Task 12: Frontend Project Setup

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`

- [ ] **Step 1: Create package.json**

```json
{
  "name": "roller-coaster-frontend",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint src --ext ts,tsx"
  },
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
    "@vitejs/plugin-react": "^4.2.0",
    "eslint": "^8.55.0",
    "@typescript-eslint/eslint-plugin": "^6.13.0",
    "@typescript-eslint/parser": "^6.13.0"
  }
}
```

- [ ] **Step 2: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 3: Create tsconfig.node.json**

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 4: Create vite.config.ts**

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

- [ ] **Step 5: Create index.html**

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Roller Coaster Simulator</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 6: Install dependencies**

Run: `cd frontend && npm install`
Expected: Dependencies installed successfully

- [ ] **Step 7: Commit**

```bash
git add frontend/package.json frontend/tsconfig.json frontend/tsconfig.node.json frontend/vite.config.ts frontend/index.html
git commit -m "chore: scaffold frontend project with Vite, React, TypeScript"
```

---

## Task 13: Frontend Core Files

**Files:**
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/state/projectStore.ts`

- [ ] **Step 1: Create src/main.tsx**

```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { MantineProvider, createTheme } from '@mantine/core'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import '@mantine/core/styles.css'

const queryClient = new QueryClient()

const theme = createTheme({
  primaryColor: 'blue',
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <MantineProvider theme={theme}>
        <App />
      </MantineProvider>
    </QueryClientProvider>
  </React.StrictMode>,
)
```

- [ ] **Step 2: Create src/App.tsx**

```tsx
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import { AppShell, Navbar, Header, Text, Button, Group } from '@mantine/core'
import { useQuery } from '@tanstack/react-query'
import { healthCheck } from './api/client'

function App() {
  const { data: health, isLoading } = useQuery({
    queryKey: ['health'],
    queryFn: healthCheck,
  })

  return (
    <BrowserRouter>
      <AppShell
        padding="md"
        navbar={
          <Navbar width={{ base: 240 }} p="xs">
            <Text fw={700} mb="md">Roller Coaster Simulator</Text>
            <Text size="sm" c="dimmed">Phase 1 - Domain Models</Text>
            <Group mt="xl">
              <Button variant="subtle" component={Link} to="/">Dashboard</Button>
            </Group>
          </Navbar>
        }
        header={
          <Header height={60} p="xs">
            <Group position="apart">
              <Text fw={600}>Roller Coaster Simulator</Text>
              <Text size="sm" c={health ? 'green' : 'red'}>
                {isLoading ? 'Connecting...' : health ? 'Backend: Connected' : 'Backend: Disconnected'}
              </Text>
            </Group>
          </Header>
        }
      >
        <Routes>
          <Route path="/" element={
            <div>
              <Text size="xl" fw={700} mb="md">Welcome to Roller Coaster Simulator</Text>
              <Text c="dimmed">Phase 1: Domain models and project scaffolding complete.</Text>
              <Text c="dimmed" mt="sm">Backend API available at /api/projects</Text>
            </div>
          } />
        </Routes>
      </AppShell>
    </BrowserRouter>
  )
}

export default App
```

- [ ] **Step 3: Create src/api/client.ts**

```typescript
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface Project {
  id: string
  metadata: {
    name: string
    units: string
    version: number
  }
}

export const healthCheck = async () => {
  const response = await axios.get('/health')
  return response.data
}

export const createProject = async (name: string): Promise<Project> => {
  const response = await api.post('/projects', { name })
  return response.data
}

export const getProject = async (id: string): Promise<Project> => {
  const response = await api.get(`/projects/${id}`)
  return response.data
}

export const listProjects = async (): Promise<Project[]> => {
  const response = await api.get('/projects')
  return response.data
}

export default api
```

- [ ] **Step 4: Create src/state/projectStore.ts**

```typescript
import { create } from 'zustand'
import { Project } from '../api/client'

interface ProjectState {
  currentProject: Project | null
  projects: Project[]
  setCurrentProject: (project: Project | null) => void
  setProjects: (projects: Project[]) => void
}

export const useProjectStore = create<ProjectState>((set) => ({
  currentProject: null,
  projects: [],
  setCurrentProject: (project) => set({ currentProject: project }),
  setProjects: (projects) => set({ projects }),
}))
```

- [ ] **Step 5: Create src/vite-env.d.ts**

```typescript
/// <reference types="vite/client" />
```

- [ ] **Step 6: Test frontend builds and runs**

Run: `cd frontend && npm run dev`
Expected: Vite server starts on port 5173
Visit: http://localhost:5173
Expected: Page loads with "Backend: Connected" in header

Kill server: Ctrl+C

- [ ] **Step 7: Commit**

```bash
git add frontend/src/
git commit -m "feat: add frontend App, API client, and Zustand store"
```

---

## Task 14: Integration Test and Final Cleanup

**Files:**
- Create: `backend/app/simulation/__init__.py`
- Create: `backend/app/services/validator.py`
- Create: `.gitignore`
- Create: `README.md`

- [ ] **Step 1: Create simulation/__init__.py**

```python
"""Simulation engine - Phase 3"""
```

- [ ] **Step 2: Create services/validator.py (placeholder)**

```python
"""Validation logic - Phase 7"""

def validate_project(project):
    """Placeholder for project validation"""
    return {"valid": True, "errors": []}
```

- [ ] **Step 3: Create .gitignore**

```
# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
*.egg-info/
dist/
build/

# Node
node_modules/
frontend/dist/

# IDE
.idea/
.vscode/
*.swp

# Project files
projects/
*.json
!.vscode/launch.json

# OS
.DS_Store
Thumbs.db

# Testing
.coverage
htmlcov/
.pytest_cache/
```

- [ ] **Step 4: Create README.md**

```markdown
# Roller Coaster Simulator

Professional roller coaster simulation platform for ride development, engineering analysis, and operational logic testing.

## Quick Start

### Backend

```bash
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

API available at http://localhost:8000

### Frontend

```bash
cd frontend
npm install
npm run dev
```

UI available at http://localhost:5173

## Architecture

See [PROJECT_SPEC.md](./PROJECT_SPEC.md) for full requirements.

- **Backend**: FastAPI + Pydantic v2
- **Frontend**: React + TypeScript + Vite + Mantine
- **Persistence**: JSON files (Phase 1)

## Development Status

Phase 1: Domain Models and Project Scaffolding - **Complete**
```

- [ ] **Step 5: Run all backend tests**

Run: `cd backend && pytest -v`
Expected: All tests PASS

- [ ] **Step 6: Run full integration test**

Terminal 1:
```bash
cd backend && uvicorn app.main:app --reload
```

Terminal 2:
```bash
cd frontend && npm run dev
```

Visit http://localhost:5173
Expected: Dashboard loads with "Backend: Connected"

Create a project via API:
```bash
curl -X POST http://localhost:8000/api/projects -H "Content-Type: application/json" -d '{"name": "Test Coaster"}'
```

Expected: Project created with ID returned

- [ ] **Step 7: Final commit**

```bash
git add .
git commit -m "chore: add simulation placeholder, validator, .gitignore, README"
```

---

## Completion Checklist

- [ ] Backend runs with `uvicorn app.main:app --reload`
- [ ] All Pydantic models are defined and tested
- [ ] API endpoints return proper OpenAPI documentation (`/docs`)
- [ ] Projects can be created, saved, and loaded as JSON files
- [ ] Frontend runs with `npm run dev`
- [ ] Frontend displays backend connection status
- [ ] All model tests pass (`pytest tests/test_models/ -v`)
- [ ] JSON Schema accessible via `/openapi.json`