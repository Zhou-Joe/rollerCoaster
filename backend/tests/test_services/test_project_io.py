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


def test_load_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        io = ProjectIO(tmpdir)
        project = Project(metadata=ProjectMetadata(name="Test Coaster"))
        io.save(project, "test_project.json")
        loaded = io.load("test_project.json")
        assert loaded.metadata.name == "Test Coaster"


def test_list_projects():
    with tempfile.TemporaryDirectory() as tmpdir:
        io = ProjectIO(tmpdir)
        io.save(Project(metadata=ProjectMetadata(name="C1")), "c1.json")
        io.save(Project(metadata=ProjectMetadata(name="C2")), "c2.json")
        projects = io.list_projects()
        assert len(projects) == 2


def test_delete_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        io = ProjectIO(tmpdir)
        io.save(Project(metadata=ProjectMetadata(name="Test")), "del.json")
        io.delete("del.json")
        assert not io.exists("del.json")