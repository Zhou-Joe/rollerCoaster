import json
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