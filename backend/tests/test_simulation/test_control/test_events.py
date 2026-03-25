"""Control event tests"""

import pytest
from app.simulation.control.events import (
    EventType,
    ControlEvent,
    TimerState,
    ControlDiagnostics,
    CommandResult,
)


class TestEventType:
    """Tests for event types."""

    def test_event_types_exist(self):
        """Test that all expected event types exist."""
        assert EventType.TRAIN_POSITION == "train_position"
        assert EventType.BLOCK_OCCUPIED == "block_occupied"
        assert EventType.BLOCK_CLEARED == "block_cleared"
        assert EventType.EQUIPMENT_STATE_CHANGED == "equipment_state_changed"
        assert EventType.TIMER_EXPIRED == "timer_expired"
        assert EventType.EMERGENCY_STOP == "emergency_stop"
        assert EventType.DISPATCH_REQUESTED == "dispatch_requested"


class TestControlEvent:
    """Tests for control events."""

    def test_create_event(self):
        """Test creating a control event."""
        event = ControlEvent(
            event_type=EventType.BLOCK_OCCUPIED,
            timestamp=1.5,
            entity_type="block",
            entity_id="block_1",
            data={"train_id": "train_1"}
        )

        assert event.event_type == EventType.BLOCK_OCCUPIED
        assert event.timestamp == 1.5
        assert event.entity_type == "block"
        assert event.entity_id == "block_1"
        assert event.data["train_id"] == "train_1"

    def test_event_str(self):
        """Test event string representation."""
        event = ControlEvent(
            event_type=EventType.TIMER_EXPIRED,
            timestamp=10.0,
            entity_type="timer",
            entity_id="timer_1"
        )

        s = str(event)
        assert "10.000s" in s
        assert "timer_expired" in s
        assert "timer/timer_1" in s


class TestTimerState:
    """Tests for timer state."""

    def test_create_timer_state(self):
        """Test creating timer state."""
        timer = TimerState(
            timer_id="timer_1",
            target_value_s=5.0
        )

        assert timer.timer_id == "timer_1"
        assert timer.current_value_s == 0.0
        assert timer.target_value_s == 5.0
        assert timer.running is False
        assert timer.completed is False

    def test_timer_start(self):
        """Test starting timer."""
        timer = TimerState(timer_id="timer_1", target_value_s=5.0)
        timer.start()

        assert timer.running is True
        assert timer.completed is False

    def test_timer_update(self):
        """Test updating timer."""
        timer = TimerState(timer_id="timer_1", target_value_s=5.0)
        timer.start()

        completed = timer.update(2.0)

        assert timer.current_value_s == 2.0
        assert timer.running is True
        assert completed is False

    def test_timer_complete(self):
        """Test timer completion."""
        timer = TimerState(timer_id="timer_1", target_value_s=5.0)
        timer.start()

        completed1 = timer.update(3.0)
        completed2 = timer.update(3.0)

        assert completed1 is False
        assert completed2 is True
        assert timer.completed is True
        assert timer.running is False

    def test_timer_reset(self):
        """Test timer reset."""
        timer = TimerState(
            timer_id="timer_1",
            target_value_s=5.0,
            current_value_s=3.0,
            running=True
        )
        timer.reset()

        assert timer.current_value_s == 0.0
        assert timer.running is False
        assert timer.completed is False

    def test_timer_stop(self):
        """Test stopping timer."""
        timer = TimerState(timer_id="timer_1", target_value_s=5.0)
        timer.start()
        timer.update(2.0)
        timer.stop()

        assert timer.running is False
        assert timer.current_value_s == 2.0  # Preserves current value


class TestControlDiagnostics:
    """Tests for control diagnostics."""

    def test_empty_diagnostics(self):
        """Test creating empty diagnostics."""
        diag = ControlDiagnostics()

        assert len(diag.active_rules) == 0
        assert len(diag.active_timers) == 0
        assert len(diag.recent_events) == 0
        assert len(diag.rejected_commands) == 0
        assert diag.rule_evaluations == 0


class TestCommandResult:
    """Tests for command results."""

    def test_success_result(self):
        """Test successful command result."""
        result = CommandResult(
            success=True,
            command="enable",
            target_type="lsm_launch",
            target_id="lsm_1"
        )

        assert result.success is True
        assert result.rejected_by_interlock is False

    def test_rejected_result(self):
        """Test rejected command result."""
        result = CommandResult(
            success=False,
            command="set_alignment",
            target_type="switch",
            target_id="switch_1",
            rejected_by_interlock=True,
            rejection_reason="Switch is occupied"
        )

        assert result.success is False
        assert result.rejected_by_interlock is True
        assert result.rejection_reason == "Switch is occupied"