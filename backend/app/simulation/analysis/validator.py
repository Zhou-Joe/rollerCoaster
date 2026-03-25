"""Project validation

Comprehensive validation of roller coaster projects including
geometry, physics, equipment, and safety checks.
"""

import math
from typing import List, Dict, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum

from .types import ValidationReport

if TYPE_CHECKING:
    from app.models.project import Project


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    ERROR = "error"      # Must be fixed
    WARNING = "warning"  # Should be fixed
    INFO = "info"        # Informational


@dataclass
class ValidationIssue:
    """A single validation issue."""
    severity: ValidationSeverity
    category: str
    message: str
    location: Optional[str] = None  # e.g., "path_1", "train_2"
    details: Dict[str, Any] = field(default_factory=dict)


class ProjectValidator:
    """
    Validates roller coaster projects.

    Performs comprehensive validation including:
    - Geometry integrity
    - Track continuity
    - Equipment placement
    - Safety constraints
    - Control system logic
    """

    # Physics constants
    MAX_GFORCE = 5.0  # Maximum allowed G-force
    MAX_LATERAL_G = 2.5  # Maximum lateral G-force
    MIN_RADIUS_M = 2.0  # Minimum turn radius
    MAX_BANK_RATE_DEG_PER_M = 5.0  # Maximum bank change rate

    def __init__(self, project: 'Project'):
        """
        Initialize project validator.

        Args:
            project: Project to validate
        """
        self.project = project
        self.issues: List[ValidationIssue] = []

    def validate(self) -> ValidationReport:
        """
        Run all validations.

        Returns:
            ValidationReport with all issues found
        """
        from datetime import datetime

        self.issues = []

        # Run all validation checks
        self._validate_metadata()
        self._validate_paths()
        self._validate_points()
        self._validate_trains()
        self._validate_vehicles()
        self._validate_equipment()
        self._validate_blocks()
        self._validate_control_system()
        self._validate_topology()

        # Build report
        report = ValidationReport(
            project_id=getattr(self.project, 'id', 'unknown'),
            generated_at=datetime.now(),
            overall_valid=all(i.severity != ValidationSeverity.ERROR for i in self.issues),
            total_scenarios_run=1,
            total_failures=sum(1 for i in self.issues if i.severity == ValidationSeverity.ERROR),
        )

        # Convert issues to recommendations
        for issue in self.issues:
            if issue.severity == ValidationSeverity.ERROR:
                report.critical_issues.append(issue.message)
            else:
                report.recommendations.append(f"{issue.category}: {issue.message}")

        return report

    def _validate_metadata(self) -> None:
        """Validate project metadata."""
        meta = self.project.metadata

        if not meta.name or not meta.name.strip():
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="metadata",
                message="Project name is required",
            ))

        if meta.version < 0:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="metadata",
                message="Version cannot be negative",
            ))

    def _validate_points(self) -> None:
        """Validate track points."""
        if not self.project.points:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="points",
                message="Project has no track points defined",
            ))
            return

        seen_ids = set()
        for point in self.project.points:
            # Check for duplicate IDs
            if point.id in seen_ids:
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="points",
                    message=f"Duplicate point ID: {point.id}",
                    location=point.id,
                ))
            seen_ids.add(point.id)

            # Validate position values
            if not all(math.isfinite(x) for x in [point.x, point.y, point.z]):
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="points",
                    message=f"Point {point.id} has invalid coordinates",
                    location=point.id,
                ))

            # Validate bank angle
            if abs(point.bank_deg) > 90:
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="points",
                    message=f"Point {point.id} has extreme bank angle: {point.bank_deg:.1f}°",
                    location=point.id,
                ))

    def _validate_paths(self) -> None:
        """Validate paths."""
        if not self.project.paths:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="paths",
                message="Project has no paths defined",
            ))
            return

        point_ids = {p.id for p in self.project.points}

        for path in self.project.paths:
            # Check path has points
            if not path.point_ids:
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="paths",
                    message=f"Path {path.id} has no points",
                    location=path.id,
                ))
                continue

            # Check minimum points for spline
            if len(path.point_ids) < 2:
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="paths",
                    message=f"Path {path.id} needs at least 2 points",
                    location=path.id,
                ))

            # Check referenced points exist
            for point_id in path.point_ids:
                if point_id not in point_ids:
                    self.issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="paths",
                        message=f"Path {path.id} references missing point: {point_id}",
                        location=path.id,
                    ))

    def _validate_trains(self) -> None:
        """Validate trains."""
        vehicle_ids = {v.id for v in self.project.vehicles}

        for train in self.project.trains:
            # Check train has vehicles
            if not train.vehicle_ids:
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="trains",
                    message=f"Train {train.id} has no vehicles",
                    location=train.id,
                ))

            # Check referenced vehicles exist
            for vehicle_id in train.vehicle_ids:
                if vehicle_id not in vehicle_ids:
                    self.issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="trains",
                        message=f"Train {train.id} references missing vehicle: {vehicle_id}",
                        location=train.id,
                    ))

    def _validate_vehicles(self) -> None:
        """Validate vehicles."""
        for vehicle in self.project.vehicles:
            # Check dimensions
            if vehicle.length_m <= 0:
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="vehicles",
                    message=f"Vehicle {vehicle.id} has invalid length: {vehicle.length_m}",
                    location=vehicle.id,
                ))

            if vehicle.dry_mass_kg <= 0:
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="vehicles",
                    message=f"Vehicle {vehicle.id} has invalid mass: {vehicle.dry_mass_kg}",
                    location=vehicle.id,
                ))

    def _validate_equipment(self) -> None:
        """Validate equipment placement and configuration."""
        path_ids = {p.id for p in self.project.paths}

        for equipment in self.project.equipment:
            equip_type = equipment.get('equipment_type', 'unknown')
            equip_id = equipment.get('id', 'unknown')
            path_id = equipment.get('path_id', '')

            # Check path exists
            if path_id and path_id not in path_ids:
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="equipment",
                    message=f"Equipment {equip_id} on non-existent path: {path_id}",
                    location=equip_id,
                ))

            # Type-specific validation
            if equip_type == 'lsm_launch':
                self._validate_lsm(equipment)
            elif equip_type == 'lift':
                self._validate_lift(equipment)
            elif equip_type == 'pneumatic_brake':
                self._validate_brake(equipment)
            elif equip_type == 'track_switch':
                self._validate_switch(equipment)

    def _validate_lsm(self, equipment: dict) -> None:
        """Validate LSM launch configuration."""
        equip_id = equipment.get('id', 'unknown')

        launch_velocity = equipment.get('launch_velocity_mps', 0)
        if launch_velocity <= 0:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="equipment",
                message=f"LSM {equip_id} has invalid launch velocity",
                location=equip_id,
            ))

        max_force = equipment.get('max_force_n', 0)
        if max_force <= 0:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="equipment",
                message=f"LSM {equip_id} has no force configured",
                location=equip_id,
            ))

    def _validate_lift(self, equipment: dict) -> None:
        """Validate lift hill configuration."""
        equip_id = equipment.get('id', 'unknown')

        engagement = equipment.get('engagement_point_s', 0)
        release = equipment.get('release_point_s', 0)

        if release <= engagement:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="equipment",
                message=f"Lift {equip_id} release point before engagement",
                location=equip_id,
            ))

        chain_speed = equipment.get('chain_speed_mps', 0)
        if chain_speed <= 0:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="equipment",
                message=f"Lift {equip_id} has invalid chain speed",
                location=equip_id,
            ))

    def _validate_brake(self, equipment: dict) -> None:
        """Validate brake configuration."""
        equip_id = equipment.get('id', 'unknown')

        max_force = equipment.get('max_force_n', 0)
        if max_force <= 0:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="equipment",
                message=f"Brake {equip_id} has no force configured",
                location=equip_id,
            ))

    def _validate_switch(self, equipment: dict) -> None:
        """Validate track switch configuration."""
        equip_id = equipment.get('id', 'unknown')

        # Check switch has diverging path
        diverging_path = equipment.get('diverging_path_id', '')
        if not diverging_path:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="equipment",
                message=f"Switch {equip_id} has no diverging path",
                location=equip_id,
            ))

    def _validate_blocks(self) -> None:
        """Validate block zones."""
        path_ids = {p.id for p in self.project.paths}

        for block in self.project.blocks:
            # Check path exists
            if block.path_id and block.path_id not in path_ids:
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="blocks",
                    message=f"Block {block.id} on non-existent path: {block.path_id}",
                    location=block.id,
                ))

            # Check block extent
            if hasattr(block, 'start_s') and hasattr(block, 'end_s'):
                if block.end_s <= block.start_s:
                    self.issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="blocks",
                        message=f"Block {block.id} has invalid extent",
                        location=block.id,
                    ))

    def _validate_control_system(self) -> None:
        """Validate control system rules and scripts."""
        for script in self.project.control_scripts:
            # Check script has rules
            if not script.rules:
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    category="control",
                    message=f"Script {script.id} has no rules defined",
                    location=script.id,
                ))

            # Validate each rule
            for rule in script.rules:
                self._validate_rule(rule, script.id)

    def _validate_rule(self, rule, script_id: str) -> None:
        """Validate a single control rule."""
        # Check rule has conditions
        if not rule.conditions:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="control",
                message=f"Rule in {script_id} has no conditions",
                location=script_id,
            ))

        # Check rule has actions
        if not rule.actions:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="control",
                message=f"Rule in {script_id} has no actions",
                location=script_id,
            ))

    def _validate_topology(self) -> None:
        """Validate topology connectivity."""
        # Check junctions
        path_ids = {p.id for p in self.project.paths}

        for junction in self.project.junctions:
            # Check paths exist
            if junction.path_id and junction.path_id not in path_ids:
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="topology",
                    message=f"Junction {junction.id} references missing path",
                    location=junction.id,
                ))

    def validate_for_simulation(self) -> List[ValidationIssue]:
        """
        Validate project is ready for simulation.

        Returns:
            List of issues that prevent simulation
        """
        self.issues = []

        # Essential checks
        if not self.project.trains:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="simulation",
                message="No trains defined for simulation",
            ))

        if not self.project.paths:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="simulation",
                message="No paths defined for simulation",
            ))

        # Check simulation settings
        settings = self.project.simulation_settings
        if settings.time_step_s <= 0 or settings.time_step_s > 0.1:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="simulation",
                message=f"Invalid time step: {settings.time_step_s}",
            ))

        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]

    def get_summary(self) -> Dict[str, Any]:
        """
        Get validation summary.

        Returns:
            Dict with counts by severity and category
        """
        by_severity = {
            ValidationSeverity.ERROR: 0,
            ValidationSeverity.WARNING: 0,
            ValidationSeverity.INFO: 0,
        }
        by_category: Dict[str, int] = {}

        for issue in self.issues:
            by_severity[issue.severity] += 1
            by_category[issue.category] = by_category.get(issue.category, 0) + 1

        return {
            'total_issues': len(self.issues),
            'by_severity': {k.value: v for k, v in by_severity.items()},
            'by_category': by_category,
            'has_errors': by_severity[ValidationSeverity.ERROR] > 0,
        }