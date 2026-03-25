"""Emergency stop analysis

Simulates emergency stop scenarios to assess stopping distances,
deceleration profiles, and safety compliance.
"""

import math
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass

from app.models.common import BrakeState
from .types import (
    EmergencyStopConfig,
    EmergencyStopResult,
    ScenarioType,
)

if TYPE_CHECKING:
    from app.models.project import Project
    from app.simulation.physics.integrator import PhysicsSimulator
    from app.simulation.equipment.manager import EquipmentManager


class EmergencyStopAnalyzer:
    """
    Analyzes emergency stop scenarios.

    Simulates trains stopping from various positions and speeds
    to verify safety requirements.
    """

    def __init__(
        self,
        project: 'Project',
        physics_simulator: 'PhysicsSimulator',
        equipment_manager: Optional['EquipmentManager'] = None
    ):
        """
        Initialize emergency stop analyzer.

        Args:
            project: Project with track and equipment data
            physics_simulator: Physics simulator instance
            equipment_manager: Equipment manager for brake control
        """
        self.project = project
        self.physics_simulator = physics_simulator
        self.equipment_manager = equipment_manager

    def analyze(
        self,
        config: EmergencyStopConfig,
        scenario_id: str = ""
    ) -> EmergencyStopResult:
        """
        Run emergency stop analysis.

        Args:
            config: Emergency stop configuration
            scenario_id: Optional scenario identifier

        Returns:
            EmergencyStopResult with analysis data
        """
        import time
        start_time = time.time()

        result = EmergencyStopResult(
            scenario_id=scenario_id,
            scenario_type=ScenarioType.EMERGENCY_STOP,
        )

        try:
            # Reset simulator
            self.physics_simulator.reset()

            # Set initial conditions
            train_state = None
            for train in self.project.trains:
                train_state = self.physics_simulator.get_train_state(train.id)
                if train_state:
                    self.physics_simulator.set_train_position(
                        train.id,
                        config.initial_path_id,
                        config.initial_position_m
                    )
                    self.physics_simulator.set_train_velocity(
                        train.id,
                        config.initial_velocity_mps
                    )
                    break

            if not train_state:
                result.success = False
                result.error_message = "No trains found in project"
                return result

            # Run simulation until trigger position
            dt = self.project.simulation_settings.time_step_s
            triggered = False
            max_steps = int(config.duration_s / dt) if hasattr(config, 'duration_s') else 10000

            for _ in range(max_steps):
                state = self.physics_simulator.get_train_state(train_state.train_id)
                if not state:
                    break

                # Check if we've reached trigger position
                if not triggered and state.s_front_m >= config.trigger_position_m:
                    triggered = True
                    # Trigger emergency stop
                    self._trigger_emergency_stop()

                # Record data
                result.position_history.append({
                    'time_s': self.physics_simulator.time_s,
                    'position_m': state.s_front_m,
                    'velocity_mps': state.velocity_mps,
                })
                result.velocity_history.append({
                    'time_s': self.physics_simulator.time_s,
                    'velocity_mps': state.velocity_mps,
                })

                # Track max deceleration
                if state.acceleration_mps2 < result.max_deceleration_mps2:
                    result.max_deceleration_mps2 = state.acceleration_mps2

                # Track max G-force
                if state.gforces.resultant_g > result.max_gforce:
                    result.max_gforce = state.gforces.resultant_g

                # Check if stopped
                if triggered and state.velocity_mps < 0.01:
                    # Train has stopped
                    result.stopping_time_s = self.physics_simulator.time_s
                    result.stopping_distance_m = state.s_front_m - config.trigger_position_m
                    break

                # Step simulation
                self.physics_simulator.step(dt)

            # Calculate average G-force during stop
            if result.velocity_history:
                gforces = [v for v in result.velocity_history if triggered]
                if gforces:
                    result.avg_gforce = sum(
                        abs(v.get('velocity_mps', 0)) for v in gforces
                    ) / len(gforces) * 0.1  # Rough estimate

            # Assess safety
            result.safe_stop = self._assess_safety(result)

        except Exception as e:
            result.success = False
            result.error_message = str(e)

        result.execution_time_s = time.time() - start_time
        return result

    def _trigger_emergency_stop(self) -> None:
        """Trigger emergency stop on all brakes."""
        if self.equipment_manager:
            self.equipment_manager.apply_all_fail_safes()

        # Also trigger through control system if available
        # This would integrate with the control manager

    def _assess_safety(self, result: EmergencyStopResult) -> bool:
        """
        Assess if the emergency stop is safe.

        Args:
            result: Analysis result to assess

        Returns:
            True if stop is considered safe
        """
        safe = True

        # Check deceleration limits (typical max 2-3 G for emergency stop)
        if abs(result.max_deceleration_mps2) > 30:  # ~3 G
            safe = False
            result.warnings.append(
                f"Excessive deceleration: {abs(result.max_deceleration_mps2):.1f} m/s²"
            )

        # Check stopping distance (context-dependent)
        if result.stopping_distance_m > 100:  # Arbitrary threshold
            result.warnings.append(
                f"Long stopping distance: {result.stopping_distance_m:.1f} m"
            )

        # Check G-force limits
        if result.max_gforce > 5:
            safe = False
            result.warnings.append(f"High G-force: {result.max_gforce:.1f} G")

        return safe

    def run_multiple_stops(
        self,
        positions: List[float],
        path_id: str,
        initial_velocity: float = 10.0
    ) -> List[EmergencyStopResult]:
        """
        Run emergency stop analysis at multiple positions.

        Args:
            positions: List of trigger positions
            path_id: Path ID for initial position
            initial_velocity: Initial velocity in m/s

        Returns:
            List of results for each position
        """
        results = []

        for i, pos in enumerate(positions):
            config = EmergencyStopConfig(
                trigger_position_m=pos,
                trigger_path_id=path_id,
                initial_velocity_mps=initial_velocity,
                initial_position_m=0.0,
                initial_path_id=path_id,
            )
            result = self.analyze(config, scenario_id=f"estop_{i}")
            results.append(result)

        return results

    def find_worst_case_stop(
        self,
        path_id: str,
        velocity_range: tuple = (5.0, 25.0),
        position_step: float = 10.0
    ) -> EmergencyStopResult:
        """
        Find the worst-case emergency stop position.

        Args:
            path_id: Path to analyze
            velocity_range: (min, max) velocity to test
            position_step: Step between positions to test

        Returns:
            Worst-case result
        """
        # This would require path length from geometry cache
        # For now, use a fixed range
        positions = [i * position_step for i in range(1, 20)]
        velocities = [velocity_range[0] + i * 5 for i in range(int((velocity_range[1] - velocity_range[0]) / 5) + 1)]

        worst_result = None
        worst_metric = 0.0

        for vel in velocities:
            results = self.run_multiple_stops(positions, path_id, vel)

            for result in results:
                if not result.success:
                    continue

                # Use stopping distance as the metric
                if result.stopping_distance_m > worst_metric:
                    worst_metric = result.stopping_distance_m
                    worst_result = result

        return worst_result or EmergencyStopResult(
            scenario_id="worst_case",
            scenario_type=ScenarioType.EMERGENCY_STOP,
            success=False,
            error_message="No valid results found"
        )