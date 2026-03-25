"""Python runtime tests"""

import pytest
from app.models.control import ControlScript
from app.models.project import Project
from app.simulation.control.python_runtime import RestrictedPythonRuntime, ScriptResult
from app.simulation.control.manager import ControlManager


class TestRestrictedPythonRuntime:
    """Tests for restricted Python runtime."""

    @pytest.fixture
    def control_manager(self):
        """Create a control manager."""
        return ControlManager(Project())

    @pytest.fixture
    def runtime(self, control_manager):
        """Create a Python runtime."""
        return RestrictedPythonRuntime(control_manager)

    def test_create_runtime(self, runtime):
        """Test creating runtime."""
        assert len(runtime.scripts) == 0
        assert len(runtime.ALLOWED_BUILTINS) > 0

    def test_register_script(self, runtime):
        """Test registering a script."""
        script = ControlScript(
            id="script_1",
            name="Test Script",
            script_content="x = 1 + 1"
        )
        runtime.register_script(script)

        assert "script_1" in runtime.scripts

    def test_validate_simple_script(self, runtime):
        """Test validating a simple script."""
        script = ControlScript(
            id="script_1",
            name="Test",
            script_content="x = 1 + 1"
        )

        errors = runtime.validate_script(script)
        assert len(errors) == 0

    def test_validate_syntax_error(self, runtime):
        """Test validating script with syntax error."""
        script = ControlScript(
            id="script_1",
            name="Bad Script",
            script_content="x = 1 +"  # Syntax error
        )

        errors = runtime.validate_script(script)
        assert len(errors) > 0
        assert "Syntax error" in errors[0]

    def test_validate_forbidden_import(self, runtime):
        """Test validating script with forbidden import."""
        script = ControlScript(
            id="script_1",
            name="Bad Import",
            script_content="import os"
        )

        errors = runtime.validate_script(script)
        assert len(errors) > 0

    def test_validate_forbidden_function(self, runtime):
        """Test validating script with forbidden function."""
        script = ControlScript(
            id="script_1",
            name="Bad Function",
            script_content="exec('print(1)')"
        )

        errors = runtime.validate_script(script)
        assert len(errors) > 0

    def test_execute_simple_script(self, runtime):
        """Test executing a simple script."""
        script = ControlScript(
            id="script_1",
            name="Simple",
            script_content="result = 2 + 2",
            enabled=True
        )
        runtime.register_script(script)

        result = runtime.execute_script("script_1", simulation_time=0.0)

        assert result.success is True
        assert result.error_message is None

    def test_execute_disabled_script(self, runtime):
        """Test executing a disabled script."""
        script = ControlScript(
            id="script_1",
            name="Disabled",
            script_content="x = 1 / 0",  # Would fail if executed
            enabled=False
        )
        runtime.register_script(script)

        result = runtime.execute_script("script_1", simulation_time=0.0)

        assert result.success is True
        assert len(result.commands_issued) == 0

    def test_execute_nonexistent_script(self, runtime):
        """Test executing a script that doesn't exist."""
        result = runtime.execute_script("nonexistent", simulation_time=0.0)

        assert result.success is False
        assert "not found" in result.error_message

    def test_script_has_simulation_time(self, runtime):
        """Test that script has access to simulation_time."""
        script = ControlScript(
            id="script_1",
            name="Time Check",
            script_content="t = simulation_time"
        )
        runtime.register_script(script)

        result = runtime.execute_script("script_1", simulation_time=10.5)
        assert result.success is True


class TestScriptAPI:
    """Tests for script API functions."""

    @pytest.fixture
    def control_manager(self):
        """Create a control manager with some state."""
        manager = ControlManager(Project())
        manager.update_block_state("block_1", occupied=False)
        manager.update_train_state("train_1", {"position": 100.0, "velocity": 5.0})
        return manager

    @pytest.fixture
    def runtime(self, control_manager):
        """Create a Python runtime."""
        return RestrictedPythonRuntime(control_manager)

    def test_api_is_block_clear(self, runtime, control_manager):
        """Test is_block_clear API."""
        script = ControlScript(
            id="script_1",
            name="Block Check",
            script_content="""
clear = is_block_clear("block_1")
""",
            allowed_apis=["is_block_clear"]
        )
        runtime.register_script(script)

        result = runtime.execute_script("script_1", simulation_time=0.0)
        assert result.success is True

    def test_api_get_train(self, runtime, control_manager):
        """Test get_train API."""
        script = ControlScript(
            id="script_1",
            name="Train Check",
            script_content="""
train = get_train("train_1")
if train:
    pos = train.get("position")
""",
            allowed_apis=["get_train"]
        )
        runtime.register_script(script)

        result = runtime.execute_script("script_1", simulation_time=0.0)
        assert result.success is True

    def test_api_get_timer(self, runtime, control_manager):
        """Test get_timer API."""
        from app.models.control import Timer
        control_manager.register_timer(Timer(id="timer_1", duration_s=10.0))

        script = ControlScript(
            id="script_1",
            name="Timer Check",
            script_content="""
t = get_timer("timer_1")
""",
            allowed_apis=["get_timer"]
        )
        runtime.register_script(script)

        result = runtime.execute_script("script_1", simulation_time=0.0)
        assert result.success is True


class TestAllowedBuiltins:
    """Tests for allowed built-in functions."""

    @pytest.fixture
    def runtime(self):
        """Create a Python runtime."""
        return RestrictedPythonRuntime(ControlManager(Project()))

    def test_math_operations(self, runtime):
        """Test math operations work."""
        script = ControlScript(
            id="script_1",
            name="Math",
            script_content="""
x = abs(-5)
y = min(1, 2, 3)
z = max(1, 2, 3)
"""
        )
        runtime.register_script(script)

        result = runtime.execute_script("script_1", simulation_time=0.0)
        assert result.success is True

    def test_list_operations(self, runtime):
        """Test list operations work."""
        script = ControlScript(
            id="script_1",
            name="Lists",
            script_content="""
items = [1, 2, 3, 4, 5]
total = sum(items)
count = len(items)
first = items[0]
"""
        )
        runtime.register_script(script)

        result = runtime.execute_script("script_1", simulation_time=0.0)
        assert result.success is True

    def test_private_attribute_blocked(self, runtime):
        """Test that private attributes are blocked."""
        script = ControlScript(
            id="script_1",
            name="Private",
            script_content="""
obj = object()
x = obj.__class__
"""
        )
        runtime.register_script(script)

        errors = runtime.validate_script(script)
        assert len(errors) > 0
        assert "private" in errors[0].lower()