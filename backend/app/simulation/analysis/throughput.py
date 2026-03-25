"""Throughput analysis

Calculates ride capacity, dispatch efficiency, and block utilization.
"""

import math
from typing import List, Dict, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass
from collections import defaultdict

from .types import (
    ThroughputConfig,
    ThroughputResult,
    ScenarioType,
)

if TYPE_CHECKING:
    from app.models.project import Project
    from app.simulation.physics.integrator import PhysicsSimulator


class ThroughputAnalyzer:
    """
    Analyzes ride throughput and capacity.

    Calculates theoretical and actual capacity, dispatch timing,
    and block utilization.
    """

    def __init__(
        self,
        project: 'Project',
        physics_simulator: Optional['PhysicsSimulator'] = None
    ):
        """
        Initialize throughput analyzer.

        Args:
            project: Project with track and train data
            physics_simulator: Optional physics simulator for detailed analysis
        """
        self.project = project
        self.physics_simulator = physics_simulator

    def analyze(
        self,
        config: ThroughputConfig,
        scenario_id: str = ""
    ) -> ThroughputResult:
        """
        Run throughput analysis.

        Args:
            config: Throughput configuration
            scenario_id: Optional scenario identifier

        Returns:
            ThroughputResult with capacity metrics
        """
        import time
        start_time = time.time()

        result = ThroughputResult(
            scenario_id=scenario_id,
            scenario_type=ScenarioType.THROUGHPUT,
        )

        try:
            # Calculate theoretical capacity
            result.theoretical_capacity_pph = self._calculate_theoretical_capacity(config)

            # Simulate dispatches
            if self.physics_simulator:
                result.actual_capacity_pph = self._simulate_dispatches(config, result)
            else:
                # Estimate without full simulation
                result.actual_capacity_pph = int(result.theoretical_capacity_pph * 0.85)

            # Calculate efficiency
            if result.theoretical_capacity_pph > 0:
                result.dispatch_efficiency = result.actual_capacity_pph / result.theoretical_capacity_pph

            # Calculate block utilization
            result.block_utilization = self._calculate_block_utilization(config)

            # Calculate total riders
            total_capacity = sum(
                sum(v.capacity for v in self.project.vehicles if v.id in t.vehicle_ids)
                for t in self.project.trains
            )
            result.total_riders = result.actual_capacity_pph

        except Exception as e:
            result.success = False
            result.error_message = str(e)

        result.execution_time_s = time.time() - start_time
        return result

    def _calculate_theoretical_capacity(self, config: ThroughputConfig) -> int:
        """
        Calculate theoretical maximum capacity.

        Theoretical capacity = (trains * capacity per train * 3600) / cycle time

        Args:
            config: Throughput configuration

        Returns:
            Theoretical capacity in passengers per hour
        """
        # Get train capacity
        total_capacity = 0
        for train in self.project.trains[:config.num_trains]:
            train_capacity = sum(
                v.capacity for v in self.project.vehicles
                if v.id in train.vehicle_ids
            )
            total_capacity += train_capacity

        if total_capacity == 0:
            total_capacity = 20  # Default assumption

        # Estimate cycle time (would need actual simulation for accurate value)
        # Use dispatch interval as minimum cycle time
        cycle_time = max(config.dispatch_interval_s, 120)  # At least 2 minutes

        # Theoretical capacity
        capacity_pph = int((config.num_trains * total_capacity * 3600) / cycle_time)

        return capacity_pph

    def _simulate_dispatches(
        self,
        config: ThroughputConfig,
        result: ThroughputResult
    ) -> int:
        """
        Simulate actual dispatches to measure capacity.

        Args:
            config: Throughput configuration
            result: Result object to update with timing data

        Returns:
            Actual capacity in passengers per hour
        """
        if not self.physics_simulator:
            return 0

        dt = self.project.simulation_settings.time_step_s
        elapsed_time = 0.0
        dispatches = 0
        cycle_times = []

        last_dispatch_time = 0.0
        max_dispatches = int(config.duration_s / config.dispatch_interval_s) + 1

        # Simplified simulation - just count potential dispatches
        while elapsed_time < config.duration_s and dispatches < max_dispatches:
            elapsed_time += dt

            # Check if it's time to dispatch
            if elapsed_time - last_dispatch_time >= config.dispatch_interval_s:
                dispatches += 1
                if last_dispatch_time > 0:
                    cycle_times.append(elapsed_time - last_dispatch_time)
                last_dispatch_time = elapsed_time

        result.total_dispatches = dispatches

        # Calculate timing metrics
        if cycle_times:
            result.avg_cycle_time_s = sum(cycle_times) / len(cycle_times)
            result.min_cycle_time_s = min(cycle_times)
            result.max_cycle_time_s = max(cycle_times)

        result.avg_dispatch_interval_s = config.dispatch_interval_s

        # Calculate actual capacity
        train_capacity = sum(
            sum(v.capacity for v in self.project.vehicles if v.id in t.vehicle_ids)
            for t in self.project.trains
        ) or 20

        # Scale to hourly
        actual_pph = int((dispatches * train_capacity * 3600) / config.duration_s)

        return actual_pph

    def _calculate_block_utilization(self, config: ThroughputConfig) -> Dict[str, float]:
        """
        Calculate block utilization percentages.

        Args:
            config: Throughput configuration

        Returns:
            Dict of block_id -> utilization percentage
        """
        utilization = {}

        # Simplified calculation based on block lengths and train count
        total_track_length = 0.0
        for path in self.project.paths:
            # Estimate path length (would need actual geometry)
            total_track_length += 100  # Placeholder

        train_length = 15.0  # Default train length

        for block in self.project.blocks:
            block_length = block.end_s - block.start_s if hasattr(block, 'end_s') else 20
            # Simplified: assume trains pass through each block once per cycle
            occupancy_time = config.dispatch_interval_s * (train_length / block_length)
            utilization[block.id] = min(1.0, occupancy_time / config.dispatch_interval_s)

        return utilization

    def optimize_dispatch_interval(
        self,
        min_interval: float = 30.0,
        max_interval: float = 180.0,
        step: float = 5.0
    ) -> Dict[str, Any]:
        """
        Find optimal dispatch interval.

        Args:
            min_interval: Minimum dispatch interval to test
            max_interval: Maximum dispatch interval to test
            step: Step size for testing

        Returns:
            Dict with optimal interval and capacity
        """
        best_capacity = 0
        best_interval = min_interval

        for interval in range(int(min_interval), int(max_interval) + 1, int(step)):
            config = ThroughputConfig(
                dispatch_interval_s=float(interval),
                num_trains=len(self.project.trains) or 1,
                duration_s=3600.0,
            )
            result = self.analyze(config, f"optimize_{interval}")

            if result.actual_capacity_pph > best_capacity:
                best_capacity = result.actual_capacity_pph
                best_interval = float(interval)

        return {
            'optimal_interval_s': best_interval,
            'max_capacity_pph': best_capacity,
        }

    def calculate_efficiency_metrics(self, config: ThroughputConfig) -> Dict[str, float]:
        """
        Calculate various efficiency metrics.

        Args:
            config: Throughput configuration

        Returns:
            Dict of metric name -> value
        """
        result = self.analyze(config, "efficiency_metrics")

        return {
            'dispatch_efficiency': result.dispatch_efficiency,
            'theoretical_capacity_pph': result.theoretical_capacity_pph,
            'actual_capacity_pph': result.actual_capacity_pph,
            'avg_cycle_time_s': result.avg_cycle_time_s,
            'avg_dispatch_interval_s': result.avg_dispatch_interval_s,
        }