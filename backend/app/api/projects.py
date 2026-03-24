from fastapi import APIRouter, HTTPException
from typing import Dict
from datetime import datetime
from app.models.project import Project, ProjectMetadata
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