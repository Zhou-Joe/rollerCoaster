from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.router import api_router
from app.api.geometry import router as geometry_router
from app.api.topology import router as topology_router

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
app.include_router(geometry_router, prefix="/api")
app.include_router(topology_router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.app_version}