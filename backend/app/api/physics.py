"""Physics simulation API endpoints"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List

router = APIRouter(prefix="/physics", tags=["physics"])


# In-memory simulator instances per project
_simulators: Dict[str, dict] = {}


class TrainStateResponse(BaseModel):
    train_id: str
    path_id: str
    s_front_m: float
    s_rear_m: float
    velocity_mps: float
    acceleration_mps2: float
    mass_kg: float
    forces: dict
    gforces: dict


class SimulationStateResponse(BaseModel):
    time_s: float
    running: bool
    trains: List[TrainStateResponse]


class StepRequest(BaseModel):
    dt: Optional[float] = None


class SetVelocityRequest(BaseModel):
    velocity_mps: float


class SetPositionRequest(BaseModel):
    path_id: str
    s: float


def _get_project(project_id: str):
    """Get project from in-memory store."""
    from app.api.projects import _projects
    if project_id not in _projects:
        raise HTTPException(status_code=404, detail="Project not found")
    return _projects[project_id]


def _get_or_create_simulator(project_id: str):
    """Get or create simulator for a project."""
    if project_id not in _simulators:
        from app.simulation.geometry import GeometryCache
        from app.simulation.physics import PhysicsSimulator

        project = _get_project(project_id)
        cache = GeometryCache(project)
        cache.compute_all()

        _simulators[project_id] = {
            "simulator": PhysicsSimulator(project, cache),
            "cache": cache
        }

    return _simulators[project_id]


@router.post("/projects/{project_id}/simulate/start")
async def start_simulation(project_id: str):
    """Start physics simulation."""
    data = _get_or_create_simulator(project_id)
    data["simulator"].running = True
    return {"status": "started", "time_s": data["simulator"].time_s}


@router.post("/projects/{project_id}/simulate/stop")
async def stop_simulation(project_id: str):
    """Stop physics simulation."""
    if project_id not in _simulators:
        raise HTTPException(status_code=404, detail="Simulation not found")

    _simulators[project_id]["simulator"].running = False
    return {"status": "stopped", "time_s": _simulators[project_id]["simulator"].time_s}


@router.post("/projects/{project_id}/simulate/reset")
async def reset_simulation(project_id: str):
    """Reset simulation to initial state."""
    if project_id not in _simulators:
        raise HTTPException(status_code=404, detail="Simulation not found")

    _simulators[project_id]["simulator"].reset()
    return {"status": "reset", "time_s": 0.0}


@router.get("/projects/{project_id}/simulate/state", response_model=SimulationStateResponse)
async def get_simulation_state(project_id: str):
    """Get current simulation state."""
    data = _get_or_create_simulator(project_id)
    state = data["simulator"].get_simulation_state()

    trains = [
        TrainStateResponse(
            train_id=t.train_id,
            path_id=t.path_id,
            s_front_m=t.s_front_m,
            s_rear_m=t.s_rear_m,
            velocity_mps=t.velocity_mps,
            acceleration_mps2=t.acceleration_mps2,
            mass_kg=t.mass_kg,
            forces={
                "gravity_n": t.forces.gravity_tangent_n,
                "drag_n": t.forces.drag_n,
                "rolling_resistance_n": t.forces.rolling_resistance_n,
                "total_n": t.forces.total_n
            },
            gforces={
                "normal_g": t.gforces.normal_g,
                "lateral_g": t.gforces.lateral_g,
                "vertical_g": t.gforces.vertical_g,
                "resultant_g": t.gforces.resultant_g
            }
        )
        for t in state.trains
    ]

    return SimulationStateResponse(
        time_s=state.time_s,
        running=state.running,
        trains=trains
    )


@router.post("/projects/{project_id}/simulate/step")
async def step_simulation(project_id: str, request: StepRequest = None):
    """Advance simulation by one or more steps."""
    data = _get_or_create_simulator(project_id)
    dt = request.dt if request else None

    result = data["simulator"].step(dt)

    return {
        "time_s": result.time_s,
        "dt_s": result.dt_s,
        "trains": [
            {
                "train_id": t.train_id,
                "path_id": t.path_id,
                "s_front_m": t.s_front_m,
                "velocity_mps": t.velocity_mps,
                "acceleration_mps2": t.acceleration_mps2
            }
            for t in result.trains
        ]
    }


@router.post("/projects/{project_id}/simulate/run")
async def run_simulation(project_id: str, duration_s: float, dt: Optional[float] = None):
    """Run simulation for a duration."""
    data = _get_or_create_simulator(project_id)
    results = data["simulator"].run(duration_s, dt)

    return {
        "steps": len(results),
        "final_time_s": results[-1].time_s if results else 0.0,
        "final_states": [
            {
                "train_id": t.train_id,
                "s_front_m": t.s_front_m,
                "velocity_mps": t.velocity_mps
            }
            for t in results[-1].trains
        ] if results else []
    }


@router.post("/projects/{project_id}/trains/{train_id}/velocity")
async def set_train_velocity(project_id: str, train_id: str, request: SetVelocityRequest):
    """Set a train's velocity."""
    data = _get_or_create_simulator(project_id)
    data["simulator"].set_train_velocity(train_id, request.velocity_mps)
    return {"status": "ok", "train_id": train_id, "velocity_mps": request.velocity_mps}


@router.post("/projects/{project_id}/trains/{train_id}/position")
async def set_train_position(project_id: str, train_id: str, request: SetPositionRequest):
    """Set a train's position."""
    data = _get_or_create_simulator(project_id)
    data["simulator"].set_train_position(train_id, request.path_id, request.s)
    return {"status": "ok", "train_id": train_id, "path_id": request.path_id, "s": request.s}