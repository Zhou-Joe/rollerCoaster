"""Load case analysis

Compares train behavior under different load conditions:
empty trains, fully loaded, and custom configurations.
"""

import math
from typing import List, Dict, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass

from .types import (
    LoadCaseConfig,
    LoadCaseResult,
    LoadCase,
    ScenarioType,
)

if TYPE_CHECKING:
    from app.models.project import Project
    from app.simulation.physics.integrator import PhysicsSimulator


class LoadCaseAnalyzer:
    """
    Analyzes different train load cases.

    Compares empty vs loaded train behavior including:
    - Velocity profiles
    - Position tracking
    - G-force differences
    - Energy analysis
    """

    def __init__(
        self,
        project: 'Project',
        physics_simulator: 'PhysicsSimulator'
    ):
        """
        Initialize load case analyzer.

        Args:
            project: Project with train and vehicle data
            physics_simulator: Physics simulator instance
        """
        self.project = project
        self.physics_simulator = physics_simulator

    def analyze(
        self,
        config: LoadCaseConfig,
        scenario_id: str = ""
    ) -> LoadCaseResult:
        """
        Run load case comparison analysis.

        Args:
            config: Load case configuration
            scenario_id: Optional scenario identifier

        Returns:
            LoadCaseResult with comparison data
        """
        import time
        start_time = time.time()

        result = LoadCaseResult(
            scenario_id=scenario_id,
            scenario_type=ScenarioType.LOAD_CASE,
        )

        try:
            # Run simulation for each load case
            for load_case in config.cases:
                case_result = self._run_load_case(
                    load_case,
                    config
                )
                result.case_results[load_case.value] = case_result

            # Compare results
            if len(result.case_results) >= 2:
                result = self._compare_cases(result)

            # Identify worst case
            result.worst_case = self._identify_worst_case(result)

        except Exception as e:
            result.success = False
            result.error_message = str(e)

        result.execution_time_s = time.time() - start_time
        return result

    def _run_load_case(
        self,
        load_case: LoadCase,
        config: LoadCaseConfig
    ) -> Dict[str, Any]:
        """
        Run simulation for a single load case.

        Args:
            load_case: Load case to run
            config: Configuration

        Returns:
            Dict with simulation results
        """
        # Reset simulator
        self.physics_simulator.reset()

        # Set load case
        self._apply_load_case(load_case)

        # Set initial conditions
        train = self.project.trains[0] if self.project.trains else None
        if not train:
            return {'error': 'No trains in project'}

        self.physics_simulator.set_train_position(
            train.id,
            config.initial_path_id,
            config.initial_position_m
        )
        self.physics_simulator.set_train_velocity(
            train.id,
            config.initial_velocity_mps
        )

        # Run simulation
        dt = self.project.simulation_settings.time_step_s
        elapsed_time = 0.0

        positions = []
        velocities = []
        accelerations = []
        gforces = []
        max_velocity = 0.0
        min_velocity = float('inf')
        max_gforce = 0.0

        while elapsed_time < config.duration_s:
            state = self.physics_simulator.get_train_state(train.id)
            if not state:
                break

            # Record data
            positions.append({
                'time_s': elapsed_time,
                'position_m': state.s_front_m,
            })
            velocities.append({
                'time_s': elapsed_time,
                'velocity_mps': state.velocity_mps,
            })
            accelerations.append({
                'time_s': elapsed_time,
                'acceleration_mps2': state.acceleration_mps2,
            })
            gforces.append({
                'time_s': elapsed_time,
                'gforce_g': state.gforces.resultant_g,
            })

            # Track extremes
            max_velocity = max(max_velocity, state.velocity_mps)
            min_velocity = min(min_velocity, state.velocity_mps)
            max_gforce = max(max_gforce, state.gforces.resultant_g)

            # Step simulation
            self.physics_simulator.step(dt)
            elapsed_time = self.physics_simulator.time_s

        # Calculate energy at end
        final_state = self.physics_simulator.get_train_state(train.id)
        kinetic_energy = 0.0
        if final_state:
            kinetic_energy = 0.5 * final_state.mass_kg * (final_state.velocity_mps ** 2)

        return {
            'load_case': load_case.value,
            'positions': positions,
            'velocities': velocities,
            'accelerations': accelerations,
            'gforces': gforces,
            'max_velocity_mps': max_velocity,
            'min_velocity_mps': min_velocity if min_velocity != float('inf') else 0.0,
            'max_gforce_g': max_gforce,
            'final_position_m': positions[-1]['position_m'] if positions else 0,
            'kinetic_energy_j': kinetic_energy,
            'mass_kg': final_state.mass_kg if final_state else 0,
        }

    def _apply_load_case(self, load_case: LoadCase) -> None:
        """
        Apply load case to trains.

        Args:
            load_case: Load case to apply
        """
        # This would modify train mass based on load case
        # For now, we adjust via the physics simulator
        for train in self.project.trains:
            if load_case == LoadCase.EMPTY:
                # Empty train - no passenger mass
                self.physics_simulator.set_train_load(train.id, 0.0)
            elif load_case == LoadCase.LOADED:
                # Fully loaded - max capacity
                capacity = sum(
                    v.capacity for v in self.project.vehicles
                    if v.id in train.vehicle_ids
                )
                # Assume 70kg per passenger
                passenger_mass = capacity * 70
                self.physics_simulator.set_train_load(train.id, passenger_mass)
            elif load_case == LoadCase.CUSTOM:
                # Custom load - use configured value
                self.physics_simulator.set_train_load(train.id, 0.0)

    def _compare_cases(self, result: LoadCaseResult) -> LoadCaseResult:
        """
        Compare results between load cases.

        Args:
            result: Result with case data

        Returns:
            Updated result with comparisons
        """
        cases = list(result.case_results.values())
        if len(cases) < 2:
            return result

        # Compare empty vs loaded
        empty = result.case_results.get(LoadCase.EMPTY.value, {})
        loaded = result.case_results.get(LoadCase.LOADED.value, {})

        if empty and loaded:
            # Velocity difference
            result.velocity_difference_mps = abs(
                empty.get('max_velocity_mps', 0) -
                loaded.get('max_velocity_mps', 0)
            )

            # Position difference at end
            result.position_difference_m = abs(
                empty.get('final_position_m', 0) -
                loaded.get('final_position_m', 0)
            )

            # Energy difference
            result.kinetic_energy_difference_j = abs(
                empty.get('kinetic_energy_j', 0) -
                loaded.get('kinetic_energy_j', 0)
            )

        # Identify critical metrics
        if result.velocity_difference_mps > 2.0:
            result.critical_metrics.append('velocity_difference')
        if result.position_difference_m > 50.0:
            result.critical_metrics.append('position_difference')
        if result.kinetic_energy_difference_j > 10000:
            result.critical_metrics.append('energy_difference')

        return result

    def _identify_worst_case(self, result: LoadCaseResult) -> LoadCase:
        """
        Identify the worst case load scenario.

        Args:
            result: Analysis result

        Returns:
            LoadCase that is most critical
        """
        worst_case = LoadCase.LOADED
        max_gforce = 0.0

        for case_name, case_data in result.case_results.items():
            case_gforce = case_data.get('max_gforce_g', 0)
            if case_gforce > max_gforce:
                max_gforce = case_gforce
                worst_case = LoadCase(case_name)

        return worst_case

    def compare_energy_profiles(
        self,
        config: LoadCaseConfig
    ) -> Dict[str, Any]:
        """
        Compare energy profiles across load cases.

        Args:
            config: Load case configuration

        Returns:
            Dict with energy comparison data
        """
        result = self.analyze(config, "energy_comparison")

        energy_data = {}
        for case_name, case_result in result.case_results.items():
            energy_data[case_name] = {
                'kinetic_energy_j': case_result.get('kinetic_energy_j', 0),
                'mass_kg': case_result.get('mass_kg', 0),
                'max_velocity_mps': case_result.get('max_velocity_mps', 0),
            }

        return {
            'cases': energy_data,
            'difference_j': result.kinetic_energy_difference_j,
            'worst_case': result.worst_case.value,
        }

    def find_optimal_dispatch(
        self,
        load_cases: List[LoadCase] = None
    ) -> Dict[str, Any]:
        """
        Find optimal dispatch timing considering load cases.

        Args:
            load_cases: Load cases to consider

        Returns:
            Dict with dispatch recommendations
        """
        if load_cases is None:
            load_cases = [LoadCase.EMPTY, LoadCase.LOADED]

        # Analyze each load case
        results = {}
        for load_case in load_cases:
            config = LoadCaseConfig(
                cases=[load_case],
                duration_s=120.0,
            )
            result = self.analyze(config, f"dispatch_{load_case.value}")
            results[load_case.value] = result

        # Find the worst case timing
        max_cycle_time = 0.0
        worst_load = LoadCase.LOADED

        for load_name, result in results.items():
            if result.case_results:
                case_data = result.case_results.get(load_name, {})
                cycle_time = case_data.get('cycle_time_s', 0)
                if cycle_time > max_cycle_time:
                    max_cycle_time = cycle_time
                    worst_load = LoadCase(load_name)

        return {
            'recommended_dispatch_interval_s': max_cycle_time * 1.1,  # 10% margin
            'worst_case_load': worst_load.value,
            'cycle_times': {
                name: r.case_results.get(name, {}).get('cycle_time_s', 0)
                for name, r in results.items()
            },
        }