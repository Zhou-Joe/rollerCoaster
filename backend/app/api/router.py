from fastapi import APIRouter
from .projects import router as projects_router
from .geometry import router as geometry_router
from .topology import router as topology_router
from .physics import router as physics_router
from .analysis import router as analysis_router

api_router = APIRouter()
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
api_router.include_router(geometry_router, tags=["geometry"])
api_router.include_router(topology_router, tags=["topology"])
api_router.include_router(physics_router, tags=["physics"])
api_router.include_router(analysis_router, tags=["analysis"])