"""Type definitions for topology and routing"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class RouteStep:
    """A single step in a route through one path."""
    path_id: str
    entry_s: float  # Arc length where train enters this path
    exit_s: float   # Arc length where train exits this path

    @property
    def length(self) -> float:
        """Length of this step."""
        return self.exit_s - self.entry_s


@dataclass
class Route:
    """Complete route through the track network."""
    steps: List[RouteStep]
    switch_requirements: Dict[str, str] = field(default_factory=dict)

    @property
    def total_length(self) -> float:
        """Total route length."""
        return sum(step.length for step in self.steps)

    def get_path_sequence(self) -> List[str]:
        """Get ordered list of path IDs in route."""
        return [step.path_id for step in self.steps]

    def is_empty(self) -> bool:
        """Check if route has no steps."""
        return len(self.steps) == 0


@dataclass
class ConflictWarning:
    """Warning about potential route conflict."""
    train_id: str
    conflicting_train_id: str
    path_id: str
    position_s: float
    message: str


@dataclass
class RouteConflict:
    """Detected conflict between train routes."""
    conflict_type: str  # "path_overlap", "opposing_direction", "switch_conflict"
    train_ids: List[str]
    path_id: str
    details: str
