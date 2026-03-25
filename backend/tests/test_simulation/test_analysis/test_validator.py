"""Tests for project validator."""

import pytest

from app.simulation.analysis.validator import (
    ProjectValidator,
    ValidationIssue,
    ValidationSeverity,
)
from app.models.project import Project, ProjectMetadata, SimulationSettings
from app.models.track import Point, Path
from app.models.train import Vehicle, Train
from app.models.topology import Block


class TestValidationIssue:
    """Test ValidationIssue."""

    def test_create_issue(self):
        """Can create validation issue."""
        issue = ValidationIssue(
            severity=ValidationSeverity.ERROR,
            category="test",
            message="Test issue",
        )
        assert issue.severity == ValidationSeverity.ERROR
        assert issue.category == "test"
        assert issue.message == "Test issue"

    def test_issue_with_location(self):
        """Can create issue with location."""
        issue = ValidationIssue(
            severity=ValidationSeverity.WARNING,
            category="points",
            message="Point has extreme bank",
            location="point_1",
        )
        assert issue.location == "point_1"


class TestProjectValidator:
    """Test ProjectValidator."""

    @pytest.fixture
    def minimal_project(self):
        """Create minimal valid project."""
        return Project(
            metadata=ProjectMetadata(
                id="test_project",
                name="Test Project",
                version=1,
            ),
            simulation_settings=SimulationSettings(),
            points=[
                Point(id="p1", x=0, y=0, z=0),
                Point(id="p2", x=10, y=0, z=0),
            ],
            paths=[
                Path(id="path_1", point_ids=["p1", "p2"]),
            ],
            vehicles=[
                Vehicle(
                    id="v1",
                    length_m=2.0,
                    dry_mass_kg=500.0,
                    capacity=4,
                ),
            ],
            trains=[
                Train(id="train_1", vehicle_ids=["v1"]),
            ],
        )

    def test_validate_minimal_project(self, minimal_project):
        """Minimal valid project passes validation."""
        validator = ProjectValidator(minimal_project)
        report = validator.validate()

        assert report.overall_valid is True
        assert report.total_failures == 0

    def test_validate_missing_name(self, minimal_project):
        """Project without name fails validation."""
        minimal_project.metadata.name = ""
        validator = ProjectValidator(minimal_project)
        report = validator.validate()

        assert report.overall_valid is False
        assert any("name" in issue.lower() for issue in report.critical_issues)

    def test_validate_no_points(self, minimal_project):
        """Project without points fails validation."""
        minimal_project.points = []
        validator = ProjectValidator(minimal_project)
        report = validator.validate()

        assert report.overall_valid is False

    def test_validate_no_paths(self, minimal_project):
        """Project without paths fails validation."""
        minimal_project.paths = []
        validator = ProjectValidator(minimal_project)
        report = validator.validate()

        assert report.overall_valid is False

    def test_validate_duplicate_point_ids(self, minimal_project):
        """Duplicate point IDs cause error."""
        minimal_project.points.append(Point(id="p1", x=20, y=0, z=0))
        validator = ProjectValidator(minimal_project)
        report = validator.validate()

        assert report.overall_valid is False
        assert any("duplicate" in issue.lower() for issue in report.critical_issues)

    def test_validate_path_missing_point(self, minimal_project):
        """Path referencing missing point causes error."""
        minimal_project.paths[0].point_ids.append("nonexistent")
        validator = ProjectValidator(minimal_project)
        report = validator.validate()

        assert report.overall_valid is False

    def test_validate_train_missing_vehicle(self, minimal_project):
        """Train referencing missing vehicle causes error."""
        minimal_project.trains[0].vehicle_ids.append("nonexistent")
        validator = ProjectValidator(minimal_project)
        report = validator.validate()

        assert report.overall_valid is False

    def test_validate_invalid_vehicle_length(self, minimal_project):
        """Vehicle with invalid length causes error."""
        minimal_project.vehicles[0].length_m = -1.0
        validator = ProjectValidator(minimal_project)
        report = validator.validate()

        assert report.overall_valid is False

    def test_validate_extreme_bank_angle(self, minimal_project):
        """Point with extreme bank angle causes warning."""
        minimal_project.points[0].bank_deg = 95.0
        validator = ProjectValidator(minimal_project)
        report = validator.validate()

        # Should be valid but have warning
        assert report.overall_valid is True
        assert len(report.recommendations) > 0

    def test_get_summary(self, minimal_project):
        """Can get validation summary."""
        validator = ProjectValidator(minimal_project)
        validator.validate()
        summary = validator.get_summary()

        assert 'total_issues' in summary
        assert 'by_severity' in summary
        assert 'by_category' in summary

    def test_validate_for_simulation(self, minimal_project):
        """Can validate for simulation readiness."""
        validator = ProjectValidator(minimal_project)
        issues = validator.validate_for_simulation()

        assert len(issues) == 0  # No errors

    def test_validate_for_simulation_no_trains(self, minimal_project):
        """Missing trains cause simulation validation error."""
        minimal_project.trains = []
        validator = ProjectValidator(minimal_project)
        issues = validator.validate_for_simulation()

        assert len(issues) > 0
        assert all(i.severity == ValidationSeverity.ERROR for i in issues)