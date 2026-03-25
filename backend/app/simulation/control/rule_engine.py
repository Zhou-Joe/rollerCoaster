"""Visual rule evaluation engine"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, TYPE_CHECKING

from app.models.control import (
    Condition,
    Action,
    Timer,
    VisualRule,
    ConditionOperator,
    LogicGate,
)
from .events import TimerState, ControlEvent, EventType

if TYPE_CHECKING:
    from app.models.project import Project


@dataclass
class RuleEvaluationResult:
    """Result of evaluating a visual rule."""
    rule_id: str
    conditions_met: bool
    condition_results: Dict[str, bool]
    actions_to_execute: List[str]


class RuleEngine:
    """
    Evaluates visual rules against current system state.

    The rule engine:
    - Evaluates conditions against entity states
    - Combines conditions using AND/OR logic
    - Manages timer states
    - Returns actions to execute when rules trigger
    """

    def __init__(self, project: 'Project'):
        """
        Initialize rule engine.

        Args:
            project: Project containing rules, conditions, actions, timers
        """
        self.project = project

        # Build lookup maps
        self.conditions: Dict[str, Condition] = {}
        self.actions: Dict[str, Action] = {}
        self.timers: Dict[str, Timer] = {}
        self.rules: Dict[str, VisualRule] = {}

        self.timer_states: Dict[str, TimerState] = {}

        self._build_lookups()

    def _build_lookups(self) -> None:
        """Build lookup maps from project data."""
        # Build from control_rules which are VisualRule objects
        for rule in self.project.control_rules:
            self.rules[rule.id] = rule

            # Build conditions referenced by this rule
            for cond_id in rule.conditions:
                # Conditions are stored by ID, need to find in data
                pass  # Will be populated from external condition data

            # Build actions
            for action_id in rule.actions:
                pass  # Will be populated from external action data

            # Build timers
            for timer_id in rule.timers:
                pass  # Will be populated from external timer data

    def add_condition(self, condition: Condition) -> None:
        """Add a condition to the engine."""
        self.conditions[condition.id] = condition

    def add_action(self, action: Action) -> None:
        """Add an action to the engine."""
        self.actions[action.id] = action

    def add_timer(self, timer: Timer) -> None:
        """Add a timer to the engine."""
        self.timers[timer.id] = timer
        self.timer_states[timer.id] = TimerState(
            timer_id=timer.id,
            target_value_s=timer.duration_s,
            running=timer.running,
            current_value_s=timer.current_value_s
        )

    def evaluate_condition(
        self,
        condition: Condition,
        entity_states: Dict[str, Dict[str, Any]]
    ) -> bool:
        """
        Evaluate a single condition.

        Args:
            condition: Condition to evaluate
            entity_states: Current states of all entities {entity_type: {entity_id: state}}

        Returns:
            True if condition is met
        """
        # Get entity state
        entity_type_states = entity_states.get(condition.entity_type, {})
        entity_state = entity_type_states.get(condition.entity_id, {})

        if not entity_state:
            return False

        # Get property value
        property_value = entity_state.get(condition.property_name)
        if property_value is None:
            return False

        # Evaluate based on operator
        return self._compare(property_value, condition.operator, condition.value)

    def _compare(self, actual: Any, operator: ConditionOperator, expected: Any) -> bool:
        """Compare actual value with expected using operator."""
        try:
            if operator == ConditionOperator.EQUALS:
                return actual == expected
            elif operator == ConditionOperator.NOT_EQUALS:
                return actual != expected
            elif operator == ConditionOperator.GREATER_THAN:
                return actual > expected
            elif operator == ConditionOperator.LESS_THAN:
                return actual < expected
            elif operator == ConditionOperator.GREATER_OR_EQUAL:
                return actual >= expected
            elif operator == ConditionOperator.LESS_OR_EQUAL:
                return actual <= expected
            elif operator == ConditionOperator.IS_TRUE:
                return bool(actual) is True
            elif operator == ConditionOperator.IS_FALSE:
                return bool(actual) is False
        except (TypeError, ValueError):
            return False

        return False

    def evaluate_rule(
        self,
        rule: VisualRule,
        entity_states: Dict[str, Dict[str, Any]]
    ) -> RuleEvaluationResult:
        """
        Evaluate a visual rule.

        Args:
            rule: Rule to evaluate
            entity_states: Current states of all entities

        Returns:
            RuleEvaluationResult with condition results and actions
        """
        condition_results: Dict[str, bool] = {}

        for condition_id in rule.conditions:
            condition = self.conditions.get(condition_id)
            if condition:
                result = self.evaluate_condition(condition, entity_states)
                condition_results[condition_id] = result
            else:
                condition_results[condition_id] = False

        # Combine results using logic gate
        if rule.condition_logic == LogicGate.AND:
            all_met = all(condition_results.values())
        else:  # OR
            all_met = any(condition_results.values())

        return RuleEvaluationResult(
            rule_id=rule.id,
            conditions_met=all_met,
            condition_results=condition_results,
            actions_to_execute=list(rule.actions) if all_met else []
        )

    def evaluate_all_rules(
        self,
        entity_states: Dict[str, Dict[str, Any]]
    ) -> List[RuleEvaluationResult]:
        """
        Evaluate all enabled rules.

        Args:
            entity_states: Current states of all entities

        Returns:
            List of evaluation results for rules that triggered
        """
        results = []

        for rule in self.rules.values():
            if not rule.enabled:
                continue

            result = self.evaluate_rule(rule, entity_states)
            if result.conditions_met:
                results.append(result)

        # Sort by priority (higher priority first)
        results.sort(key=lambda r: self.rules[r.rule_id].priority, reverse=True)

        return results

    def update_timers(self, dt: float) -> List[ControlEvent]:
        """
        Update all timers and return events for completed timers.

        Args:
            dt: Time step in seconds

        Returns:
            List of TIMER_EXPIRED events
        """
        events = []

        for timer_id, timer_state in self.timer_states.items():
            if timer_state.update(dt):
                events.append(ControlEvent(
                    event_type=EventType.TIMER_EXPIRED,
                    timestamp=0.0,  # Will be set by caller
                    entity_type="timer",
                    entity_id=timer_id
                ))

        return events

    def start_timer(self, timer_id: str) -> bool:
        """Start a timer."""
        if timer_id in self.timer_states:
            self.timer_states[timer_id].start()
            return True
        return False

    def reset_timer(self, timer_id: str) -> bool:
        """Reset a timer."""
        if timer_id in self.timer_states:
            self.timer_states[timer_id].reset()
            return True
        return False

    def get_action(self, action_id: str) -> Optional[Action]:
        """Get an action by ID."""
        return self.actions.get(action_id)

    def reset(self) -> None:
        """Reset all timers to initial state."""
        for timer_state in self.timer_states.values():
            timer_state.reset()