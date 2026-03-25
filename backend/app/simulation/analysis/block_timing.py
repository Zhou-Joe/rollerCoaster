"""Block timing analysis

Analyzes block occupancy timing, sequencing, and safety margins.
"""

from typing import List, Dict, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass
from collections import defaultdict

from .types import (
    BlockTimingConfig,
    BlockTimingResult,
    ScenarioType,
)

if TYPE_CHECKING:
    from app.models.project import Project
    from app.simulation.physics.integrator import PhysicsSimulator


class BlockTimingAnalyzer:
    """
    Analyzes block timing and sequencing.

    Measures occupancy times, calculates safety margins,
    and identifies timing conflicts.
    """

    def __init__(
        self,
        project: 'Project',
        physics_simulator: Optional['PhysicsSimulator'] = None
    ):
        """
        Initialize block timing analyzer.

        Args:
            project: Project with block definitions
            physics_simulator: Optional physics simulator
        """
        self.project = project
        self.physics_simulator = physics_simulator

    def analyze(
        self,
        config: BlockTimingConfig,
        scenario_id: str = ""
    ) -> BlockTimingResult:
        """
        Run block timing analysis.

        Args:
            config: Block timing configuration
            scenario_id: Optional scenario identifier

        Returns:
            BlockTimingResult with timing data
        """
        import time
        start_time = time.time()

        result = BlockTimingResult(
            scenario_id=scenario_id,
            scenario_type=ScenarioType.BLOCK_TIMING,
        )

        try:
            # Determine which blocks to analyze
            blocks_to_analyze = config.block_ids or [b.id for b in self.project.blocks]

            if not blocks_to_analyze:
                result.success = False
                result.error_message = "No blocks defined in project"
                return result

            # Analyze timing
            if self.physics_simulator:
                result = self._analyze_with_simulation(config, result)
            else:
                result = self._analyze_static(config, result)

            # Calculate safety margins
            result.min_separation_s, result.min_separation_blocks = self._calculate_min_separation(result)

            # Check for timing issues
            result.timing_warnings = self._check_timing_issues(result)

        except Exception as e:
            result.success = False
            result.error_message = str(e)

        result.execution_time_s = time.time() - start_time
        return result

    def _analyze_with_simulation(
        self,
        config: BlockTimingConfig,
        result: BlockTimingResult
    ) -> BlockTimingResult:
        """Analyze timing using physics simulation."""
        dt = self.project.simulation_settings.time_step_s
        elapsed_time = 0.0

        # Track block entry/exit times
        block_entry_times: Dict[str, float] = {}
        block_exit_times: Dict[str, float] = {}
        block_occupancy: Dict[str, bool] = defaultdict(bool)

        # Reset simulator
        self.physics_simulator.reset()

        # Run simulation
        while elapsed_time < config.duration_s:
            # Step simulation
            self.physics_simulator.step(dt)
            elapsed_time = self.physics_simulator.time_s

            # Check train positions against blocks
            for train_state in self.physics_simulator.get_all_states():
                for block in self.project.blocks:
                    if block.path_id != train_state.path_id:
                        continue

                    # Check if train is in block
                    train_front = train_state.s_front_m
                    train_rear = train_state.s_rear_m

                    in_block = (
                        train_front >= block.start_s and
                        train_rear <= block.end_s
                    )

                    # Track transitions
                    was_in_block = block_occupancy[block.id]

                    if in_block and not was_in_block:
                        # Entered block
                        block_entry_times[block.id] = elapsed_time
                        block_occupancy[block.id] = True
                    elif not in_block and was_in_block:
                        # Exited block
                        block_exit_times[block.id] = elapsed_time
                        block_occupancy[block.id] = False

        # Calculate occupancy times
        for block_id in block_entry_times:
            if block_id in block_exit_times:
                result.block_occupancy_times[block_id] = (
                    block_exit_times[block_id] - block_entry_times[block_id]
                )
            else:
                # Still in block at end of simulation
                result.block_occupancy_times[block_id] = (
                    config.duration_s - block_entry_times[block_id]
                )

        # Set sequence
        result.block_sequence = sorted(
            block_entry_times.keys(),
            key=lambda x: block_entry_times[x]
        )

        return result

    def _analyze_static(
        self,
        config: BlockTimingConfig,
        result: BlockTimingResult
    ) -> BlockTimingResult:
        """Analyze timing without simulation (static estimation)."""
        # Estimate based on block lengths and typical train speed
        typical_speed = 10.0  # m/s

        for block in self.project.blocks:
            if block.id not in config.block_ids and config.block_ids:
                continue

            # Estimate occupancy time
            block_length = block.end_s - block.start_s if hasattr(block, 'end_s') else 20.0
            occupancy_time = block_length / typical_speed

            result.block_occupancy_times[block.id] = occupancy_time

        # Create sequence based on block positions
        result.block_sequence = sorted(
            result.block_occupancy_times.keys(),
            key=lambda x: next(
                (b.start_s for b in self.project.blocks if b.id == x), 0
            )
        )

        return result

    def _calculate_min_separation(
        self,
        result: BlockTimingResult
    ) -> tuple:
        """Calculate minimum separation between blocks."""
        min_sep = float('inf')
        min_blocks = ("", "")

        block_times = list(result.block_occupancy_times.items())

        for i, (block1, time1) in enumerate(block_times):
            for block2, time2 in block_times[i+1:]:
                # Estimate separation (would need more detailed analysis)
                sep = abs(time1 - time2)
                if sep < min_sep:
                    min_sep = sep
                    min_blocks = (block1, block2)

        if min_sep == float('inf'):
            min_sep = 0.0

        return min_sep, min_blocks

    def _check_timing_issues(self, result: BlockTimingResult) -> List[str]:
        """Check for timing issues and conflicts."""
        warnings = []

        # Check for very short occupancy times (train passing too fast)
        for block_id, time_s in result.block_occupancy_times.items():
            if time_s < 1.0:
                warnings.append(
                    f"Block {block_id} has very short occupancy: {time_s:.2f}s"
                )

        # Check for very long occupancy times (potential blockage)
        for block_id, time_s in result.block_occupancy_times.items():
            if time_s > 60.0:
                warnings.append(
                    f"Block {block_id} has long occupancy: {time_s:.1f}s"
                )

        # Check for insufficient separation
        if result.min_separation_s < 5.0:
            warnings.append(
                f"Low separation ({result.min_separation_s:.1f}s) between "
                f"{result.min_separation_blocks[0]} and {result.min_separation_blocks[1]}"
            )

        return warnings

    def generate_timing_report(self, config: BlockTimingConfig) -> Dict[str, Any]:
        """
        Generate a comprehensive timing report.

        Args:
            config: Block timing configuration

        Returns:
            Dict with detailed timing information
        """
        result = self.analyze(config, "timing_report")

        report = {
            'blocks': {},
            'summary': {
                'total_blocks': len(result.block_occupancy_times),
                'total_time_s': result.total_block_time_s,
                'min_separation_s': result.min_separation_s,
                'warnings_count': len(result.timing_warnings),
            },
            'warnings': result.timing_warnings,
        }

        for block in self.project.blocks:
            if block.id in result.block_occupancy_times:
                report['blocks'][block.id] = {
                    'occupancy_time_s': result.block_occupancy_times[block.id],
                    'clear_time_s': result.block_clear_times.get(block.id, 0),
                    'path_id': block.path_id,
                    'start_s': block.start_s if hasattr(block, 'start_s') else 0,
                    'end_s': block.end_s if hasattr(block, 'end_s') else 0,
                }

        return report