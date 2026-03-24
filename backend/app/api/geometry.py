"""Geometry API endpoints"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/geometry", tags=["geometry"])


class SamplePointResponse(BaseModel):
    s: float
    position: list[float]
    tangent: list[float]
    normal: list[float]
    binormal: list[float]
    curvature: float
    radius: float
    slope_deg: float
    bank_deg: float


class CacheStatusResponse(BaseModel):
    path_id: str
    computed: bool
    total_length: Optional[float] = None
    sample_count: Optional[int] = None


class GeometryStatusResponse(BaseModel):
    paths: list[CacheStatusResponse]


class ValidationResultResponse(BaseModel):
    is_valid: bool
    errors: list[dict]
    warnings: list[dict]


@router.post("/projects/{project_id}/compute")
async def compute_geometry(project_id: str):
    """Compute geometry for all paths."""
    from app.simulation.geometry import GeometryCache
    from app.services.project_io import ProjectIO

    project = ProjectIO.load(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    cache = GeometryCache(project, resolution_m=project.simulation_settings.geometry_sample_resolution_m)
    cache.compute_all()

    return {"status": "computed", "paths_computed": len(cache._paths)}


@router.get("/projects/{project_id}/geometry/status")
async def get_geometry_status(project_id: str):
    """Get cache status."""
    from app.simulation.geometry import GeometryCache
    from app.services.project_io import ProjectIO

    project = ProjectIO.load(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    cache = GeometryCache(project, resolution_m=project.simulation_settings.geometry_sample_resolution_m)
    status = cache.get_cache_status()

    paths = []
    for path_id, info in status.items():
        paths.append(CacheStatusResponse(
            path_id=path_id,
            computed=info.get("status") == "computed",
            total_length=info.get("length"),
            sample_count=info.get("sample_count")
        ))

    return GeometryStatusResponse(paths=paths)


@router.get("/projects/{project_id}/paths/{path_id}/sample", response_model=SamplePointResponse)
async def get_path_sample(project_id: str, path_id: str, s: float = Query(...)):
    """Get sample at arc length."""
    from app.simulation.geometry import GeometryCache
    from app.services.project_io import ProjectIO

    project = ProjectIO.load(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    cache = GeometryCache(project, resolution_m=project.simulation_settings.geometry_sample_resolution_m)

    try:
        path_data = cache.get_path(path_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if not path_data or not path_data.samples:
        raise HTTPException(status_code=422, detail="Path has no geometry")

    if s < 0 or s > path_data.total_length:
        raise HTTPException(status_code=400, detail=f"s={s} exceeds path length {path_data.total_length}m")

    sample = min(path_data.samples, key=lambda sp: abs(sp.s - s))

    return SamplePointResponse(
        s=sample.s,
        position=list(sample.position),
        tangent=list(sample.tangent),
        normal=list(sample.normal),
        binormal=list(sample.binormal),
        curvature=sample.curvature,
        radius=sample.radius,
        slope_deg=sample.slope_deg,
        bank_deg=sample.bank_deg
    )


@router.post("/projects/{project_id}/geometry/validate", response_model=ValidationResultResponse)
async def validate_geometry(project_id: str):
    """Validate all geometry."""
    from app.simulation.geometry import GeometryCache, GeometryValidator
    from app.services.project_io import ProjectIO

    project = ProjectIO.load(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    cache = GeometryCache(project, resolution_m=project.simulation_settings.geometry_sample_resolution_m)
    cache.compute_all()

    validator = GeometryValidator(project.simulation_settings)
    result = validator.validate_project(cache, project.junctions)

    return ValidationResultResponse(
        is_valid=result.is_valid,
        errors=[{"severity": e.severity, "path_id": e.path_id, "location_s": e.location_s, "message": e.message} for e in result.errors],
        warnings=[{"severity": w.severity, "path_id": w.path_id, "location_s": w.location_s, "message": w.message} for w in result.warnings]
    )