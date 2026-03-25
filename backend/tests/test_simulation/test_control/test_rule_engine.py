"""Rule engine tests"""

import pytest
from app.models.control import (
    Condition,
    Action,
    Timer,
    VisualRule,
    ConditionOperator,
    LogicGate,
)
from app.models.project import Project
from app.simulation.control.rule_engine import RuleEngine, RuleEvaluationResult


class TestRuleEngine:
    """Tests for rule engine."""

    @pytest.fixture
    def project(self):
        """Create a basic project."""
        return Project()

    @pytest.fixture
    def rule_engine(self, project):
        """Create a rule engine."""
        return RuleEngine(project)

    def test_create_rule_engine(self, rule_engine):
        """Test creating rule engine."""
        assert len(rule_engine.conditions) == 0
        assert len(rule_engine.actions) == 0
        assert len(rule_engine.rules) == 0

    def test_add_condition(self, rule_engine):
        """Test adding a condition."""
        condition = Condition(
            id="cond_1",
            entity_type="block",
            entity_id="block_1",
            property_name="occupied",
            operator=ConditionOperator.IS_FALSE
        )
        rule_engine.add_condition(condition)

        assert "cond_1" in rule_engine.conditions
        assert rule_engine.conditions["cond_1"].entity_type == "block"

    def test_add_action(self, rule_engine):
        """Test adding an action."""
        action = Action(
            id="action_1",
            target_type="lsm_launch",
            target_id="lsm_1",
            command="enable"
        )
        rule_engine.add_action(action)

        assert "action_1" in rule_engine.actions
        assert rule_engine.actions["action_1"].command == "enable"

    def test_add_timer(self, rule_engine):
        """Test adding a timer."""
        timer = Timer(
            id="timer_1",
            duration_s=5.0
        )
        rule_engine.add_timer(timer)

        assert "timer_1" in rule_engine.timers
        assert "timer_1" in rule_engine.timer_states
        assert rule_engine.timer_states["timer_1"].target_value_s == 5.0


class TestConditionEvaluation:
    """Tests for condition evaluation."""

    @pytest.fixture
    def rule_engine(self):
        """Create a rule engine with conditions."""
        engine = RuleEngine(Project())

        # Add test conditions
        engine.add_condition(Condition(
            id="block_clear",
            entity_type="block",
            entity_id="block_1",
            property_name="clear",
            operator=ConditionOperator.IS_TRUE
        ))

        engine.add_condition(Condition(
            id="train_speed",
            entity_type="train",
            entity_id="train_1",
            property_name="velocity",
            operator=ConditionOperator.LESS_THAN,
            value=10.0
        ))

        return engine

    def test_evaluate_is_true(self, rule_engine):
        """Test IS_TRUE operator."""
        condition = rule_engine.conditions["block_clear"]
        entity_states = {
            "block": {
                "block_1": {"clear": True}
            }
        }

        result = rule_engine.evaluate_condition(condition, entity_states)
        assert result is True

    def test_evaluate_is_false(self, rule_engine):
        """Test IS_FALSE operator."""
        condition = rule_engine.conditions["block_clear"]
        entity_states = {
            "block": {
                "block_1": {"clear": False}
            }
        }

        result = rule_engine.evaluate_condition(condition, entity_states)
        assert result is False

    def test_evaluate_comparison(self, rule_engine):
        """Test comparison operators."""
        condition = rule_engine.conditions["train_speed"]

        # Less than
        entity_states = {
            "train": {
                "train_1": {"velocity": 5.0}
            }
        }
        result = rule_engine.evaluate_condition(condition, entity_states)
        assert result is True

        # Greater than
        entity_states = {
            "train": {
                "train_1": {"velocity": 15.0}
            }
        }
        result = rule_engine.evaluate_condition(condition, entity_states)
        assert result is False

    def test_evaluate_missing_entity(self, rule_engine):
        """Test condition with missing entity."""
        condition = rule_engine.conditions["block_clear"]
        entity_states = {}

        result = rule_engine.evaluate_condition(condition, entity_states)
        assert result is False

    def test_evaluate_missing_property(self, rule_engine):
        """Test condition with missing property."""
        condition = rule_engine.conditions["block_clear"]
        entity_states = {
            "block": {
                "block_1": {}  # No 'clear' property
            }
        }

        result = rule_engine.evaluate_condition(condition, entity_states)
        assert result is False


class TestRuleEvaluation:
    """Tests for rule evaluation."""

    @pytest.fixture
    def rule_engine(self):
        """Create a rule engine with rules."""
        engine = RuleEngine(Project())

        # Add conditions
        engine.add_condition(Condition(
            id="cond_1",
            entity_type="block",
            entity_id="block_1",
            property_name="clear",
            operator=ConditionOperator.IS_TRUE
        ))

        engine.add_condition(Condition(
            id="cond_2",
            entity_type="station",
            entity_id="station_1",
            property_name="load_complete",
            operator=ConditionOperator.IS_TRUE
        ))

        # Add actions
        engine.add_action(Action(
            id="action_1",
            target_type="station",
            target_id="station_1",
            command="allow_dispatch"
        ))

        # Add rule
        engine.rules["rule_1"] = VisualRule(
            id="rule_1",
            name="Dispatch when ready",
            conditions=["cond_1", "cond_2"],
            condition_logic=LogicGate.AND,
            actions=["action_1"],
            enabled=True
        )

        return engine

    def test_evaluate_rule_and_logic(self, rule_engine):
        """Test rule with AND logic."""
        entity_states = {
            "block": {"block_1": {"clear": True}},
            "station": {"station_1": {"load_complete": True}}
        }

        result = rule_engine.evaluate_rule(
            rule_engine.rules["rule_1"],
            entity_states
        )

        assert result.conditions_met is True
        assert len(result.actions_to_execute) == 1

    def test_evaluate_rule_and_logic_partial(self, rule_engine):
        """Test rule with AND logic and partial conditions."""
        entity_states = {
            "block": {"block_1": {"clear": True}},
            "station": {"station_1": {"load_complete": False}}
        }

        result = rule_engine.evaluate_rule(
            rule_engine.rules["rule_1"],
            entity_states
        )

        assert result.conditions_met is False
        assert len(result.actions_to_execute) == 0

    def test_evaluate_rule_or_logic(self, rule_engine):
        """Test rule with OR logic."""
        rule_engine.rules["rule_1"].condition_logic = LogicGate.OR

        entity_states = {
            "block": {"block_1": {"clear": True}},
            "station": {"station_1": {"load_complete": False}}
        }

        result = rule_engine.evaluate_rule(
            rule_engine.rules["rule_1"],
            entity_states
        )

        assert result.conditions_met is True


class TestTimerUpdate:
    """Tests for timer updates."""

    @pytest.fixture
    def rule_engine(self):
        """Create rule engine with timer."""
        engine = RuleEngine(Project())
        engine.add_timer(Timer(id="timer_1", duration_s=5.0))
        return engine

    def test_timer_updates(self, rule_engine):
        """Test timer updates return events when complete."""
        rule_engine.timer_states["timer_1"].start()

        # Not complete yet
        events = rule_engine.update_timers(3.0)
        assert len(events) == 0

        # Complete
        events = rule_engine.update_timers(3.0)
        assert len(events) == 1
        assert events[0].entity_id == "timer_1"

    def test_start_timer(self, rule_engine):
        """Test starting timer via engine."""
        result = rule_engine.start_timer("timer_1")
        assert result is True
        assert rule_engine.timer_states["timer_1"].running is True

    def test_reset_timer(self, rule_engine):
        """Test resetting timer."""
        rule_engine.timer_states["timer_1"].current_value_s = 3.0
        rule_engine.timer_states["timer_1"].running = True

        result = rule_engine.reset_timer("timer_1")
        assert result is True
        assert rule_engine.timer_states["timer_1"].current_value_s == 0.0
        assert rule_engine.timer_states["timer_1"].running is False