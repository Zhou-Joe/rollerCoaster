"""Control system types and events"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime


class EventType(str, Enum):
    """Types of control events."""
    TRAIN_POSITION = "train_position"
    TRAIN_ENTERED_ZONE = "train_entered_zone"
    TRAIN_EXITED_ZONE = "train_exited_zone"
    BLOCK_OCCUPIED = "block_occupied"
    BLOCK_CLEARED = "block_cleared"
    EQUIPMENT_STATE_CHANGED = "equipment_state_changed"
    SWITCH_STATE_CHANGED = "switch_state_changed"
    TIMER_EXPIRED = "timer_expired"
    TIMER_STARTED = "timer_started"
    DISPATCH_REQUESTED = "dispatch_requested"
    EMERGENCY_STOP = "emergency_stop"
    EMERGENCY_CLEAR = "emergency_clear"
    STATION_READY = "station_ready"
    LOAD_COMPLETE = "load_complete"
    UNLOAD_COMPLETE = "unload_complete"


@dataclass
class ControlEvent:
    """A control system event."""
    event_type: EventType
    timestamp: float  # Simulation time in seconds
    entity_type: str
    entity_id: str
    data: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"[{self.timestamp:.3f}s] {self.event_type.value}: {self.entity_type}/{self.entity_id}"


@dataclass
class TimerState:
    """Runtime state of a timer."""
    timer_id: str
    current_value_s: float = 0.0
    target_value_s: float = 0.0
    running: bool = False
    completed: bool = False

    def update(self, dt: float) -> bool:
        """
        Update timer by dt seconds.

        Returns True if timer just completed.
        """
        if not self.running or self.completed:
            return False

        self.current_value_s += dt

        if self.current_value_s >= self.target_value_s:
            self.completed = True
            self.running = False
            return True

        return False

    def start(self) -> None:
        """Start the timer."""
        self.running = True
        self.completed = False

    def reset(self) -> None:
        """Reset the timer."""
        self.current_value_s = 0.0
        self.running = False
        self.completed = False

    def stop(self) -> None:
        """Stop the timer."""
        self.running = False


@dataclass
class ControlDiagnostics:
    """Diagnostic information for control system."""
    active_rules: List[str] = field(default_factory=list)
    active_timers: List[str] = field(default_factory=list)
    recent_events: List[ControlEvent] = field(default_factory=list)
    rejected_commands: List[Dict[str, Any]] = field(default_factory=list)
    rule_evaluations: int = 0
    last_evaluation_time: float = 0.0


@dataclass
class CommandResult:
    """Result of a control command execution."""
    success: bool
    command: str
    target_type: str
    target_id: str
    message: str = ""
    rejected_by_interlock: bool = False
    rejection_reason: Optional[str] = None