from app.models.control import (
    ConditionOperator, Condition, LogicGate, Action, Timer,
    VisualRule, ControlScript
)


def test_condition_operator_values():
    assert ConditionOperator.EQUALS.value == "=="
    assert ConditionOperator.IS_TRUE.value == "is_true"


def test_condition_creation():
    cond = Condition(
        id="cond_001", entity_type="block", entity_id="block_001",
        property_name="occupied", operator=ConditionOperator.IS_FALSE
    )
    assert cond.id == "cond_001"


def test_action_creation():
    action = Action(
        id="act_001", target_type="brake", target_id="brake_001",
        command="set_state", parameters={"state": "closed"}
    )
    assert action.target_type == "brake"


def test_timer_creation():
    timer = Timer(id="timer_001", duration_s=30.0)
    assert timer.duration_s == 30.0
    assert timer.running is False


def test_visual_rule_creation():
    rule = VisualRule(
        id="rule_001", name="Dispatch when block clear",
        conditions=["cond_001"], actions=["act_001"]
    )
    assert rule.condition_logic == LogicGate.AND
    assert rule.enabled is True


def test_control_script_creation():
    script = ControlScript(
        id="script_001", name="Main dispatch logic",
        script_content="if is_block_clear('block_001'):\n    allow_dispatch('station_001')"
    )
    assert "allow_dispatch" in script.allowed_apis