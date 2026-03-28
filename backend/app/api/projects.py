from fastapi import APIRouter, HTTPException
from typing import Dict
from datetime import datetime, timezone
from app.models.project import Project, ProjectMetadata, SimulationSettings
from app.services.project_io import ProjectIO
import uuid

router = APIRouter()

_projects: Dict[str, Project] = {}
_project_io = ProjectIO()


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

    # Update all allowed fields
    if "metadata" in updates:
        project.metadata = ProjectMetadata(**updates["metadata"])
    if "points" in updates:
        from app.models.track import Point
        project.points = [Point(**p) for p in updates["points"]]
    if "paths" in updates:
        from app.models.track import Path
        project.paths = [Path(**p) for p in updates["paths"]]
    if "junctions" in updates:
        from app.models.topology import Junction
        project.junctions = [Junction(**j) for j in updates["junctions"]]
    if "vehicles" in updates:
        from app.models.train import Vehicle
        project.vehicles = [Vehicle(**v) for v in updates["vehicles"]]
    if "trains" in updates:
        from app.models.train import Train
        project.trains = [Train(**t) for t in updates["trains"]]
    if "equipment" in updates:
        project.equipment = updates["equipment"]
    if "blocks" in updates:
        from app.models.topology import Block
        project.blocks = [Block(**b) for b in updates["blocks"]]
    if "simulation_settings" in updates:
        project.simulation_settings = SimulationSettings(**updates["simulation_settings"])

    project.metadata.modified_at = datetime.now(timezone.utc)
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


@router.get("/{project_id}/export")
async def export_project(project_id: str):
    """Export project data as JSON for download."""
    if project_id not in _projects:
        raise HTTPException(status_code=404, detail="Project not found")
    project = _projects[project_id]
    return project.model_dump()


@router.post("/{project_id}/import")
async def import_project(project_id: str, data: dict):
    """Import project data from JSON."""
    if project_id not in _projects:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        # Validate the imported data
        imported_project = Project.model_validate(data)

        # Preserve the original project ID but update everything else
        current_project = _projects[project_id]

        # Update metadata (keep creation time from original)
        current_project.metadata = imported_project.metadata
        current_project.metadata.modified_at = datetime.now(timezone.utc)

        # Update all data
        current_project.points = imported_project.points
        current_project.paths = imported_project.paths
        current_project.junctions = imported_project.junctions
        current_project.switches = imported_project.switches
        current_project.sections = imported_project.sections
        current_project.stations = imported_project.stations
        current_project.blocks = imported_project.blocks
        current_project.vehicles = imported_project.vehicles
        current_project.trains = imported_project.trains
        current_project.equipment = imported_project.equipment
        current_project.control_rules = imported_project.control_rules
        current_project.control_scripts = imported_project.control_scripts
        current_project.simulation_settings = imported_project.simulation_settings

        _projects[project_id] = current_project

        return {"status": "imported", "id": project_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid project data: {str(e)}")


@router.post("/import/new")
async def import_new_project(data: dict, filename: str = None):
    """Import project data as a new project."""
    try:
        # Validate the imported data
        imported_project = Project.model_validate(data)

        # Create new project ID
        new_project_id = str(uuid.uuid4())

        # Update timestamps
        imported_project.metadata.created_at = datetime.now(timezone.utc)
        imported_project.metadata.modified_at = datetime.now(timezone.utc)

        if filename:
            imported_project.metadata.name = filename.replace('.json', '').replace('_', ' ')

        _projects[new_project_id] = imported_project

        return {"status": "imported", "id": new_project_id, **imported_project.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid project data: {str(e)}")