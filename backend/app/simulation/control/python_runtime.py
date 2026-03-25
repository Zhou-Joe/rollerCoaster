"""Sandboxed Python control script runtime"""

import ast
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Callable, TYPE_CHECKING

from app.models.control import ControlScript

if TYPE_CHECKING:
    from app.simulation.control.manager import ControlManager


@dataclass
class ScriptResult:
    """Result of script execution."""
    script_id: str
    success: bool
    error_message: Optional[str] = None
    commands_issued: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.commands_issued is None:
            self.commands_issued = []


class RestrictedPythonRuntime:
    """
    A restricted Python runtime for control scripts.

    Provides a sandboxed environment where scripts can only
    access whitelisted APIs and cannot perform dangerous operations.
    """

    # Allowed built-in functions
    ALLOWED_BUILTINS = {
        'abs': abs,
        'min': min,
        'max': max,
        'round': round,
        'len': len,
        'range': range,
        'enumerate': enumerate,
        'zip': zip,
        'map': map,
        'filter': filter,
        'sum': sum,
        'any': any,
        'all': all,
        'sorted': sorted,
        'list': list,
        'dict': dict,
        'tuple': tuple,
        'set': set,
        'bool': bool,
        'int': int,
        'float': float,
        'str': str,
        'print': print,  # For debugging
    }

    # Allowed modules (none by default - very restricted)
    ALLOWED_MODULES = {
        'math': math,
    }

    def __init__(self, control_manager: 'ControlManager'):
        """
        Initialize the Python runtime.

        Args:
            control_manager: ControlManager providing API access
        """
        self.control_manager = control_manager
        self.scripts: Dict[str, ControlScript] = {}
        self.script_results: Dict[str, ScriptResult] = {}

    def register_script(self, script: ControlScript) -> None:
        """Register a control script."""
        self.scripts[script.id] = script

    def validate_script(self, script: ControlScript) -> List[str]:
        """
        Validate a script for safety.

        Returns list of validation errors (empty if valid).
        """
        errors = []

        try:
            tree = ast.parse(script.script_content)
        except SyntaxError as e:
            errors.append(f"Syntax error: {e}")
            return errors

        # Check for forbidden operations
        for node in ast.walk(tree):
            # No imports
            if isinstance(node, ast.Import):
                # For 'import os', node.names contains the modules
                for alias in node.names:
                    if alias.name not in self.ALLOWED_MODULES:
                        errors.append(f"Import of '{alias.name}' is not allowed")
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module not in self.ALLOWED_MODULES:
                    errors.append(f"Import from '{node.module}' is not allowed")

            # No exec/eval
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ('exec', 'eval', 'compile', 'open', 'input'):
                        errors.append(f"Function '{node.func.id}' is not allowed")

            # No attribute access on dangerous names
            if isinstance(node, ast.Attribute):
                if node.attr.startswith('_'):
                    errors.append(f"Access to private attributes is not allowed")

        return errors

    def create_api_context(self, script: ControlScript) -> Dict[str, Any]:
        """
        Create the API context for script execution.

        This provides the allowed APIs that scripts can call.
        """
        context: Dict[str, Any] = {}

        # Build API functions based on allowed_apis
        if 'get_train' in script.allowed_apis:
            context['get_train'] = self.control_manager.api_get_train

        if 'is_block_clear' in script.allowed_apis:
            context['is_block_clear'] = self.control_manager.api_is_block_clear

        if 'set_switch' in script.allowed_apis:
            context['set_switch'] = self.control_manager.api_set_switch

        if 'set_equipment_state' in script.allowed_apis:
            context['set_equipment_state'] = self.control_manager.api_set_equipment_state

        if 'allow_dispatch' in script.allowed_apis:
            context['allow_dispatch'] = self.control_manager.api_allow_dispatch

        if 'get_timer' in script.allowed_apis:
            context['get_timer'] = self.control_manager.api_get_timer

        if 'start_timer' in script.allowed_apis:
            context['start_timer'] = self.control_manager.api_start_timer

        if 'reset_timer' in script.allowed_apis:
            context['reset_timer'] = self.control_manager.api_reset_timer

        if 'get_train_position' in script.allowed_apis:
            context['get_train_position'] = self.control_manager.api_get_train_position

        if 'get_train_velocity' in script.allowed_apis:
            context['get_train_velocity'] = self.control_manager.api_get_train_velocity

        return context

    def execute_script(
        self,
        script_id: str,
        simulation_time: float
    ) -> ScriptResult:
        """
        Execute a control script.

        Args:
            script_id: ID of script to execute
            simulation_time: Current simulation time

        Returns:
            ScriptResult with execution outcome
        """
        script = self.scripts.get(script_id)
        if not script:
            return ScriptResult(
                script_id=script_id,
                success=False,
                error_message=f"Script '{script_id}' not found"
            )

        if not script.enabled:
            return ScriptResult(
                script_id=script_id,
                success=True,
                commands_issued=[]
            )

        # Validate script
        errors = self.validate_script(script)
        if errors:
            return ScriptResult(
                script_id=script_id,
                success=False,
                error_message="; ".join(errors)
            )

        # Create execution context
        context = self.create_api_context(script)
        context.update(self.ALLOWED_BUILTINS)
        context['__builtins__'] = self.ALLOWED_BUILTINS

        # Add math module if allowed
        if any(module in script.allowed_apis for module in ['math']):
            context.update({name: getattr(math, name) for name in dir(math) if not name.startswith('_')})

        # Add simulation time
        context['simulation_time'] = simulation_time

        # Track commands issued
        commands_issued: List[Dict[str, Any]] = []
        context['_commands'] = commands_issued

        try:
            # Execute the script
            exec(script.script_content, context)
            result = ScriptResult(
                script_id=script_id,
                success=True,
                commands_issued=commands_issued
            )
        except Exception as e:
            result = ScriptResult(
                script_id=script_id,
                success=False,
                error_message=str(e)
            )

        self.script_results[script_id] = result
        return result

    def execute_all_scripts(self, simulation_time: float) -> List[ScriptResult]:
        """
        Execute all registered scripts.

        Args:
            simulation_time: Current simulation time

        Returns:
            List of execution results
        """
        results = []
        for script_id in self.scripts:
            result = self.execute_script(script_id, simulation_time)
            results.append(result)
        return results

    def reset(self) -> None:
        """Reset script results."""
        self.script_results.clear()