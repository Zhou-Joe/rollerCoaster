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