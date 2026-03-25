"""Topology API endpoints"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List

router = APIRouter(prefix="/topology", tags=["topology"])


class PathNodeResponse(BaseModel):
    path_id: str
    length: float
    incoming_junctions: list[str]
    outgoing_junctions: list[str]


class TopologyGraphResponse(BaseModel):
    paths: Dict[str, PathNodeResponse]
    junctions: Dict[str, dict]
    is_connected: bool
    orphan_paths: list[str]


class RouteStepResponse(BaseModel):
    path_id: str
    entry_s: float
    exit_s: float


class RouteResponse(BaseModel):
    steps: list[RouteStepResponse]
    switch_requirements: Dict[str, str]
    total_length: float


class RouteRequest(BaseModel):
    from_path: str
    to_path: str
    switch_states: Optional[Dict[str, str]] = None


def _get_project(project_id: str):
    """Get project from in-memory store."""
    from app.api.projects import _projects
    if project_id not in _projects:
        raise HTTPException(status_code=404, detail="Project not found")
    return _projects[project_id]


@router.get("/projects/{project_id}/topology/graph", response_model=TopologyGraphResponse)
async def get_topology_graph(project_id: str):
    """Get full topology graph."""
    from app.simulation.topology import TopologyGraph
    from app.simulation.geometry import GeometryCache

    project = _get_project(project_id)
    cache = GeometryCache(project, resolution_m=project.simulation_settings.geometry_sample_resolution_m)
    cache.compute_all()

    for path in project.paths:
        path_data = cache.get_path(path.id)
        if path_data:
            path.length_m = path_data.total_length

    graph = TopologyGraph()
    graph.build(project.paths, project.junctions)

    paths = {pid: PathNodeResponse(
        path_id=node.path_id,
        length=node.length,
        incoming_junctions=node.incoming_junctions,
        outgoing_junctions=node.outgoing_junctions
    ) for pid, node in graph.paths.items()}

    return TopologyGraphResponse(
        paths=paths,
        junctions={j.id: j.model_dump() for j in project.junctions},
        is_connected=graph.is_connected(),
        orphan_paths=graph.get_orphan_paths()
    )


@router.post("/projects/{project_id}/topology/routes", response_model=list[RouteResponse])
async def find_routes(project_id: str, request: RouteRequest):
    """Find routes between paths."""
    from app.simulation.topology import TopologyGraph, RouteFinder
    from app.simulation.geometry import GeometryCache

    project = _get_project(project_id)
    cache = GeometryCache(project, resolution_m=project.simulation_settings.geometry_sample_resolution_m)
    cache.compute_all()

    for path in project.paths:
        path_data = cache.get_path(path.id)
        if path_data:
            path.length_m = path_data.total_length

    graph = TopologyGraph()
    graph.build(project.paths, project.junctions)
    finder = RouteFinder(graph)

    route = finder.find_route(
        start_path=request.from_path,
        start_s=0.0,
        end_path=request.to_path,
        end_s=0.0,
        switch_states=request.switch_states
    )

    if not route:
        return []

    return [RouteResponse(
        steps=[RouteStepResponse(path_id=s.path_id, entry_s=s.entry_s, exit_s=s.exit_s) for s in route.steps],
        switch_requirements=route.switch_requirements,
        total_length=route.total_length
    )]