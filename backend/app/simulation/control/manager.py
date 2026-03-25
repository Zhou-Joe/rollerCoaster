"""Control system manager

Coordinates rule engine, Python runtime, and interlocks.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from app.models.control import Condition, Action, Timer, VisualRule, ControlScript
from app.models.common import BrakeState, BoosterMode
from .events import (
    ControlEvent,
    EventType,
    TimerState,
    ControlDiagnostics,
    CommandResult,
)
from .rule_engine import RuleEngine, RuleEvaluationResult
from .python_runtime import RestrictedPythonRuntime, ScriptResult
from .interlocks import InterlockSystem, InterlockResult

if TYPE_CHECKING:
    from app.models.project import Project
    from app.simulation.equipment.manager import EquipmentManager


class ControlManager:
    """
    Central control system manager.

    Coordinates:
    - Visual rule evaluation
    - Python script execution
    - Safety interlocks
    - Timer management
    - Event processing
    """

    def __init__(
        self,
        project: 'Project',
        equipment_manager: Optional['EquipmentManager'] = None
    ):
        """
        Initialize control manager.

        Args:
            project: Project containing control configuration
            equipment_manager: Optional equipment manager for commands
        """
        self.project = project
        self.equipment_manager = equipment_manager

        self.rule_engine = RuleEngine(project)
        self.python_runtime = RestrictedPythonRuntime(self)
        self.interlocks = InterlockSystem()

        self.diagnostics = ControlDiagnostics()
        self.simulation_time = 0.0

        # Entity states for rule evaluation
        self.entity_states: Dict[str, Dict[str, Any]] = {
            'train': {},
            'block': {},
            'station': {},
            'equipment': {},
            'switch': {},
            'timer': {},
        }

        self._initialize_from_project()

    def _initialize_from_project(self) -> None:
        """Initialize from project configuration."""
        # Register control scripts
        for script in self.project.control_scripts:
            self.python_runtime.register_script(script)

    def register_condition(self, condition: Condition) -> None:
        """Register a condition with the rule engine."""
        self.rule_engine.add_condition(condition)

    def register_action(self, action: Action) -> None:
        """Register an action with the rule engine."""
        self.rule_engine.add_action(action)

    def register_timer(self, timer: Timer) -> None:
        """Register a timer with the rule engine."""
        self.rule_engine.add_timer(timer)

    def register_rule(self, rule: VisualRule) -> None:
        """Register a visual rule."""
        self.rule_engine.rules[rule.id] = rule

    def register_script(self, script: ControlScript) -> None:
        """Register a control script."""
        self.python_runtime.register_script(script)

    def update_train_state(
        self,
        train_id: str,
        state: Dict[str, Any]
    ) -> None:
        """Update train state for rule evaluation."""
        self.entity_states['train'][train_id] = state

    def update_block_state(
        self,
        block_id: str,
        occupied: bool,
        train_id: Optional[str] = None
    ) -> None:
        """Update block state for rule evaluation and interlocks."""
        self.entity_states['block'][block_id] = {
            'occupied': occupied,
            'train_id': train_id,
            'clear': not occupied
        }
        self.interlocks.update_block_occupancy(
            block_id,
            train_id if occupied else None
        )

    def update_station_state(
        self,
        station_id: str,
        state: Dict[str, Any]
    ) -> None:
        """Update station state for rule evaluation."""
        self.entity_states['station'][station_id] = state

    def update_equipment_state(
        self,
        equipment_id: str,
        equipment_type: str,
        state: Dict[str, Any]
    ) -> None:
        """Update equipment state for rule evaluation."""
        self.entity_states['equipment'][equipment_id] = {
            'type': equipment_type,
            **state
        }

    def update_switch_state(
        self,
        switch_id: str,
        alignment: str,
        occupied: bool = False
    ) -> None:
        """Update switch state for rule evaluation and interlocks."""
        self.entity_states['switch'][switch_id] = {
            'alignment': alignment,
            'occupied': occupied
        }
        self.interlocks.update_switch_state(switch_id, alignment)
        self.interlocks.update_switch_occupancy(switch_id, occupied)

    def step(self, dt: float) -> List[CommandResult]:
        """
        Execute one control step.

        Args:
            dt: Time step in seconds

        Returns:
            List of command results from executed actions
        """
        self.simulation_time += dt
        results = []

        # Update timers
        timer_events = self.rule_engine.update_timers(dt)
        self.diagnostics.recent_events.extend(timer_events)
        self.diagnostics.active_timers = [
            tid for tid, ts in self.rule_engine.timer_states.items()
            if ts.running
        ]

        # Evaluate visual rules
        rule_results = self.rule_engine.evaluate_all_rules(self.entity_states)
        self.diagnostics.rule_evaluations += len(self.rule_engine.rules)
        self.diagnostics.last_evaluation_time = self.simulation_time

        for rule_result in rule_results:
            if rule_result.conditions_met:
                self.diagnostics.active_rules.append(rule_result.rule_id)

                # Execute actions
                for action_id in rule_result.actions_to_execute:
                    action = self.rule_engine.get_action(action_id)
                    if action:
                        result = self._execute_action(action)
                        results.append(result)
                        if not result.success:
                            self.diagnostics.rejected_commands.append({
                                'action_id': action_id,
                                'reason': result.rejection_reason,
                                'time': self.simulation_time
                            })

        # Execute Python scripts
        script_results = self.python_runtime.execute_all_scripts(self.simulation_time)

        for script_result in script_results:
            if script_result.success and script_result.commands_issued:
                for cmd in script_result.commands_issued:
                    # Process commands from scripts
                    pass  # Commands are executed through API calls

        # Trim recent events
        if len(self.diagnostics.recent_events) > 100:
            self.diagnostics.recent_events = self.diagnostics.recent_events[-100:]

        return results

    def _execute_action(self, action: Action) -> CommandResult:
        """
        Execute an action with interlock checking.

        Args:
            action: Action to execute

        Returns:
            CommandResult with outcome
        """
        # Check interlock
        interlock_result = self.interlocks.check_equipment_command(
            action.target_id,
            action.target_type,
            action.command,
            action.parameters
        )

        if not interlock_result.allowed:
            return CommandResult(
                success=False,
                command=action.command,
                target_type=action.target_type,
                target_id=action.target_id,
                rejected_by_interlock=True,
                rejection_reason=interlock_result.reason
            )

        # Execute command
        return self._dispatch_command(
            action.target_type,
            action.target_id,
            action.command,
            action.parameters
        )

    def _dispatch_command(
        self,
        target_type: str,
        target_id: str,
        command: str,
        parameters: Dict[str, Any]
    ) -> CommandResult:
        """Dispatch a command to the appropriate handler."""
        if not self.equipment_manager:
            return CommandResult(
                success=False,
                command=command,
                target_type=target_type,
                target_id=target_id,
                message="No equipment manager configured"
            )

        if target_type == "lsm_launch":
            if command == "enable":
                success = self.equipment_manager.set_lsm_enabled(target_id, True)
                return CommandResult(success=success, command=command, target_type=target_type, target_id=target_id)
            elif command == "disable":
                success = self.equipment_manager.set_lsm_enabled(target_id, False)
                return CommandResult(success=success, command=command, target_type=target_type, target_id=target_id)

        elif target_type == "pneumatic_brake":
            if command == "open":
                success = self.equipment_manager.set_brake_state(target_id, BrakeState.OPEN)
                return CommandResult(success=success, command=command, target_type=target_type, target_id=target_id)
            elif command == "close":
                success = self.equipment_manager.set_brake_state(target_id, BrakeState.CLOSED)
                return CommandResult(success=success, command=command, target_type=target_type, target_id=target_id)
            elif command == "emergency_stop":
                success = self.equipment_manager.set_brake_state(target_id, BrakeState.EMERGENCY_STOP)
                return CommandResult(success=success, command=command, target_type=target_type, target_id=target_id)

        elif target_type == "booster":
            if command == "drive":
                success = self.equipment_manager.set_booster_mode(target_id, BoosterMode.DRIVE)
                return CommandResult(success=success, command=command, target_type=target_type, target_id=target_id)
            elif command == "brake":
                success = self.equipment_manager.set_booster_mode(target_id, BoosterMode.BRAKE)
                return CommandResult(success=success, command=command, target_type=target_type, target_id=target_id)
            elif command == "idle":
                success = self.equipment_manager.set_booster_mode(target_id, BoosterMode.IDLE)
                return CommandResult(success=success, command=command, target_type=target_type, target_id=target_id)

        elif target_type == "lift":
            if command == "enable":
                success = self.equipment_manager.set_lift_enabled(target_id, True)
                return CommandResult(success=success, command=command, target_type=target_type, target_id=target_id)
            elif command == "disable":
                success = self.equipment_manager.set_lift_enabled(target_id, False)
                return CommandResult(success=success, command=command, target_type=target_type, target_id=target_id)

        elif target_type == "trim_brake":
            if command == "enable":
                success = self.equipment_manager.set_trim_enabled(target_id, True)
                return CommandResult(success=success, command=command, target_type=target_type, target_id=target_id)
            elif command == "disable":
                success = self.equipment_manager.set_trim_enabled(target_id, False)
                return CommandResult(success=success, command=command, target_type=target_type, target_id=target_id)

        elif target_type == "station":
            if command == "allow_dispatch":
                self.interlocks.set_dispatch_permit(target_id, True)
                return CommandResult(success=True, command=command, target_type=target_type, target_id=target_id)
            elif command == "block_dispatch":
                self.interlocks.set_dispatch_permit(target_id, False)
                return CommandResult(success=True, command=command, target_type=target_type, target_id=target_id)

        elif target_type == "switch":
            alignment = parameters.get("alignment")
            if alignment:
                interlock_result = self.interlocks.check_switch_change(target_id, alignment)
                if not interlock_result.allowed:
                    return CommandResult(
                        success=False,
                        command=command,
                        target_type=target_type,
                        target_id=target_id,
                        rejected_by_interlock=True,
                        rejection_reason=interlock_result.reason
                    )
                self.interlocks.update_switch_state(target_id, alignment)
                return CommandResult(success=True, command=command, target_type=target_type, target_id=target_id)

        return CommandResult(
            success=False,
            command=command,
            target_type=target_type,
            target_id=target_id,
            message=f"Unknown command '{command}' for target type '{target_type}'"
        )

    # API methods for Python scripts
    def api_get_train(self, train_id: str) -> Optional[Dict[str, Any]]:
        """Get train state for script API."""
        return self.entity_states['train'].get(train_id)

    def api_is_block_clear(self, block_id: str) -> bool:
        """Check if block is clear for script API."""
        block_state = self.entity_states['block'].get(block_id, {})
        return block_state.get('clear', False)

    def api_set_switch(self, switch_id: str, alignment: str) -> bool:
        """Set switch alignment for script API."""
        result = self._dispatch_command("switch", switch_id, "set_alignment", {"alignment": alignment})
        return result.success

    def api_set_equipment_state(
        self,
        equipment_id: str,
        equipment_type: str,
        state: str
    ) -> bool:
        """Set equipment state for script API."""
        result = self._dispatch_command(equipment_type, equipment_id, state, {})
        return result.success

    def api_allow_dispatch(self, station_id: str, allow: bool) -> bool:
        """Set dispatch permission for script API."""
        command = "allow_dispatch" if allow else "block_dispatch"
        result = self._dispatch_command("station", station_id, command, {})
        return result.success

    def api_get_timer(self, timer_id: str) -> Optional[float]:
        """Get timer value for script API."""
        timer_state = self.rule_engine.timer_states.get(timer_id)
        if timer_state:
            return timer_state.current_value_s
        return None

    def api_start_timer(self, timer_id: str) -> bool:
        """Start timer for script API."""
        return self.rule_engine.start_timer(timer_id)

    def api_reset_timer(self, timer_id: str) -> bool:
        """Reset timer for script API."""
        return self.rule_engine.reset_timer(timer_id)

    def api_get_train_position(self, train_id: str) -> Optional[float]:
        """Get train position for script API."""
        train_state = self.entity_states['train'].get(train_id, {})
        return train_state.get('position')

    def api_get_train_velocity(self, train_id: str) -> Optional[float]:
        """Get train velocity for script API."""
        train_state = self.entity_states['train'].get(train_id, {})
        return train_state.get('velocity')

    def trigger_emergency_stop(self) -> None:
        """Trigger emergency stop."""
        self.interlocks.set_emergency_stop(True)
        self.diagnostics.recent_events.append(ControlEvent(
            event_type=EventType.EMERGENCY_STOP,
            timestamp=self.simulation_time,
            entity_type="system",
            entity_id="control"
        ))

        # Apply all fail-safes
        if self.equipment_manager:
            self.equipment_manager.apply_all_fail_safes()

    def clear_emergency_stop(self) -> None:
        """Clear emergency stop."""
        self.interlocks.set_emergency_stop(False)
        self.diagnostics.recent_events.append(ControlEvent(
            event_type=EventType.EMERGENCY_CLEAR,
            timestamp=self.simulation_time,
            entity_type="system",
            entity_id="control"
        ))

    def reset(self) -> None:
        """Reset control system to initial state."""
        self.simulation_time = 0.0
        self.entity_states = {
            'train': {},
            'block': {},
            'station': {},
            'equipment': {},
            'switch': {},
            'timer': {},
        }
        self.rule_engine.reset()
        self.python_runtime.reset()
        self.interlocks.reset()
        self.diagnostics = ControlDiagnostics()

    def get_diagnostics(self) -> ControlDiagnostics:
        """Get current diagnostics."""
        return self.diagnostics