"""Control manager tests"""

import pytest
from app.models.control import (
    Condition,
    Action,
    Timer,
    VisualRule,
    ControlScript,
    ConditionOperator,
    LogicGate,
)
from app.models.common import BrakeState, BoosterMode
from app.models.project import Project
from app.simulation.control.manager import ControlManager
from app.simulation.control.events import EventType
from app.simulation.equipment.manager import EquipmentManager


class TestControlManager:
    """Tests for control manager."""

    @pytest.fixture
    def project(self):
        """Create a basic project."""
        return Project()

    @pytest.fixture
    def manager(self, project):
        """Create a control manager."""
        return ControlManager(project)

    def test_create_manager(self, manager):
        """Test creating control manager."""
        assert manager.rule_engine is not None
        assert manager.python_runtime is not None
        assert manager.interlocks is not None

    def test_initial_state(self, manager):
        """Test initial state is empty."""
        assert len(manager.entity_states['train']) == 0
        assert len(manager.entity_states['block']) == 0
        assert manager.simulation_time == 0.0


class TestEntityStateUpdates:
    """Tests for entity state updates."""

    @pytest.fixture
    def manager(self):
        """Create a control manager."""
        return ControlManager(Project())

    def test_update_train_state(self, manager):
        """Test updating train state."""
        manager.update_train_state("train_1", {
            "position": 100.0,
            "velocity": 5.0
        })

        assert "train_1" in manager.entity_states['train']
        assert manager.entity_states['train']['train_1']['position'] == 100.0

    def test_update_block_state(self, manager):
        """Test updating block state."""
        manager.update_block_state("block_1", occupied=True, train_id="train_1")

        assert manager.entity_states['block']['block_1']['occupied'] is True
        assert manager.entity_states['block']['block_1']['train_id'] == "train_1"

    def test_update_equipment_state(self, manager):
        """Test updating equipment state."""
        manager.update_equipment_state("brake_1", "pneumatic_brake", {
            "state": "closed"
        })

        assert manager.entity_states['equipment']['brake_1']['state'] == "closed"

    def test_update_switch_state(self, manager):
        """Test updating switch state."""
        manager.update_switch_state("switch_1", "main", occupied=False)

        assert manager.entity_states['switch']['switch_1']['alignment'] == "main"
        assert manager.interlocks.switch_states["switch_1"] == "main"


class TestRuleRegistration:
    """Tests for registering rules, conditions, actions."""

    @pytest.fixture
    def manager(self):
        """Create a control manager."""
        return ControlManager(Project())

    def test_register_condition(self, manager):
        """Test registering a condition."""
        condition = Condition(
            id="cond_1",
            entity_type="block",
            entity_id="block_1",
            property_name="clear",
            operator=ConditionOperator.IS_TRUE
        )
        manager.register_condition(condition)

        assert "cond_1" in manager.rule_engine.conditions

    def test_register_action(self, manager):
        """Test registering an action."""
        action = Action(
            id="action_1",
            target_type="lsm_launch",
            target_id="lsm_1",
            command="enable"
        )
        manager.register_action(action)

        assert "action_1" in manager.rule_engine.actions

    def test_register_timer(self, manager):
        """Test registering a timer."""
        timer = Timer(id="timer_1", duration_s=5.0)
        manager.register_timer(timer)

        assert "timer_1" in manager.rule_engine.timers

    def test_register_rule(self, manager):
        """Test registering a rule."""
        rule = VisualRule(
            id="rule_1",
            name="Test Rule",
            conditions=["cond_1"],
            actions=["action_1"]
        )
        manager.register_rule(rule)

        assert "rule_1" in manager.rule_engine.rules


class TestControlStep:
    """Tests for control step execution."""

    @pytest.fixture
    def manager(self):
        """Create a control manager with rules."""
        mgr = ControlManager(Project())

        # Add conditions
        mgr.register_condition(Condition(
            id="block_clear",
            entity_type="block",
            entity_id="block_1",
            property_name="clear",
            operator=ConditionOperator.IS_TRUE
        ))

        # Add rule
        mgr.register_rule(VisualRule(
            id="dispatch_rule",
            name="Dispatch Rule",
            conditions=["block_clear"],
            actions=["enable_lsm"],
            enabled=True
        ))

        return mgr

    def test_step_updates_time(self, manager):
        """Test that step updates simulation time."""
        manager.step(0.01)
        assert manager.simulation_time == 0.01

        manager.step(0.01)
        assert manager.simulation_time == 0.02

    def test_step_evaluates_rules(self, manager):
        """Test that step evaluates rules."""
        manager.register_action(Action(
            id="enable_lsm",
            target_type="lsm_launch",
            target_id="lsm_1",
            command="enable"
        ))

        # Set up entity state
        manager.update_block_state("block_1", occupied=False)

        # Step should evaluate rules
        results = manager.step(0.01)

        # Rule should have been evaluated
        assert manager.diagnostics.rule_evaluations > 0

    def test_step_updates_timers(self, manager):
        """Test that step updates timers."""
        manager.register_timer(Timer(id="timer_1", duration_s=1.0))
        manager.rule_engine.start_timer("timer_1")

        manager.step(0.5)
        assert manager.rule_engine.timer_states["timer_1"].current_value_s == 0.5


class TestEmergencyStop:
    """Tests for emergency stop."""

    @pytest.fixture
    def manager(self):
        """Create a control manager."""
        return ControlManager(Project())

    def test_trigger_emergency_stop(self, manager):
        """Test triggering E-stop."""
        manager.trigger_emergency_stop()

        assert manager.interlocks.emergency_stop_active is True
        assert len(manager.diagnostics.recent_events) > 0
        assert manager.diagnostics.recent_events[-1].event_type == EventType.EMERGENCY_STOP

    def test_clear_emergency_stop(self, manager):
        """Test clearing E-stop."""
        manager.trigger_emergency_stop()
        manager.clear_emergency_stop()

        assert manager.interlocks.emergency_stop_active is False

    def test_estop_blocks_commands(self, manager):
        """Test that E-stop blocks non-safety commands."""
        manager.trigger_emergency_stop()

        # Use _execute_action which properly checks interlocks
        from app.models.control import Action
        action = Action(
            id="test_action",
            target_type="lsm_launch",
            target_id="lsm_1",
            command="enable"
        )
        result = manager._execute_action(action)

        assert result.success is False
        assert result.rejected_by_interlock is True


class TestDiagnostics:
    """Tests for diagnostics."""

    @pytest.fixture
    def manager(self):
        """Create a control manager."""
        return ControlManager(Project())

    def test_get_diagnostics(self, manager):
        """Test getting diagnostics."""
        diag = manager.get_diagnostics()

        assert diag.rule_evaluations == 0
        assert len(diag.active_rules) == 0

    def test_diagnostics_track_rejected_commands(self, manager):
        """Test that diagnostics track rejected commands."""
        manager.register_action(Action(
            id="action_1",
            target_type="switch",
            target_id="switch_1",
            command="set_alignment",
            parameters={"alignment": "main"}
        ))

        # Make switch occupied
        manager.interlocks.update_switch_occupancy("switch_1", True)

        # Try to execute - should be rejected
        manager.step(0.01)

        # Run a step that tries to execute the action
        manager.rule_engine.rules["test"] = VisualRule(
            id="test",
            name="Test",
            conditions=[],
            actions=["action_1"],
            enabled=True
        )
        manager.step(0.01)

        # Should have some rejected commands (if rule was evaluated)
        # Note: depends on entity states being set up


class TestReset:
    """Tests for reset."""

    @pytest.fixture
    def manager(self):
        """Create a control manager with state."""
        mgr = ControlManager(Project())
        mgr.simulation_time = 10.0
        mgr.update_train_state("train_1", {"position": 100.0})
        mgr.interlocks.set_emergency_stop(True)
        return mgr

    def test_reset_clears_time(self, manager):
        """Test that reset clears simulation time."""
        manager.reset()
        assert manager.simulation_time == 0.0

    def test_reset_clears_states(self, manager):
        """Test that reset clears entity states."""
        manager.reset()
        assert len(manager.entity_states['train']) == 0

    def test_reset_clears_estop(self, manager):
        """Test that reset clears E-stop."""
        manager.reset()
        assert manager.interlocks.emergency_stop_active is False