"""Analysis types and scenarios"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime


class ScenarioType(str, Enum):
    """Types of analysis scenarios."""
    EMERGENCY_STOP = "emergency_stop"
    THROUGHPUT = "throughput"
    BLOCK_TIMING = "block_timing"
    LOAD_CASE = "load_case"
    CUSTOM = "custom"


class LoadCase(str, Enum):
    """Train load cases for analysis."""
    EMPTY = "empty"
    LOADED = "loaded"
    CUSTOM = "custom"


@dataclass
class ScenarioConfig:
    """Configuration for an analysis scenario."""
    scenario_id: str
    name: str
    scenario_type: ScenarioType
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    # Simulation parameters
    duration_s: float = 60.0
    time_step_s: float = 0.01

    # Load case settings
    load_case: LoadCase = LoadCase.LOADED

    # Custom parameters
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EmergencyStopConfig:
    """Configuration for emergency stop analysis."""
    trigger_position_m: float  # Position to trigger E-stop
    trigger_path_id: str
    initial_velocity_mps: float = 0.0
    initial_position_m: float = 0.0
    initial_path_id: str = ""


@dataclass
class ThroughputConfig:
    """Configuration for throughput analysis."""
    dispatch_interval_s: float = 60.0
    num_trains: int = 1
    station_id: str = ""
    duration_s: float = 3600.0  # 1 hour default


@dataclass
class BlockTimingConfig:
    """Configuration for block timing analysis."""
    block_ids: List[str] = field(default_factory=list)
    duration_s: float = 300.0


@dataclass
class LoadCaseConfig:
    """Configuration for load case comparison."""
    cases: List[LoadCase] = field(default_factory=lambda: [LoadCase.EMPTY, LoadCase.LOADED])
    initial_position_m: float = 0.0
    initial_path_id: str = ""
    initial_velocity_mps: float = 0.0
    duration_s: float = 60.0


@dataclass
class AnalysisResult:
    """Base class for analysis results."""
    scenario_id: str
    scenario_type: ScenarioType
    executed_at: datetime = field(default_factory=datetime.now)
    execution_time_s: float = 0.0
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class EmergencyStopResult(AnalysisResult):
    """Results from emergency stop analysis."""
    scenario_type: ScenarioType = ScenarioType.EMERGENCY_STOP

    # Stopping results
    stopping_distance_m: float = 0.0
    stopping_time_s: float = 0.0
    max_deceleration_mps2: float = 0.0

    # Position tracking
    position_history: List[Dict[str, float]] = field(default_factory=list)
    velocity_history: List[Dict[str, float]] = field(default_factory=list)

    # G-forces during stop
    max_gforce: float = 0.0
    avg_gforce: float = 0.0

    # Safety assessment
    safe_stop: bool = True
    warnings: List[str] = field(default_factory=list)


@dataclass
class ThroughputResult(AnalysisResult):
    """Results from throughput analysis."""
    scenario_type: ScenarioType = ScenarioType.THROUGHPUT

    # Throughput metrics
    total_dispatches: int = 0
    total_riders: int = 0
    theoretical_capacity_pph: int = 0  # Passengers per hour
    actual_capacity_pph: int = 0

    # Timing metrics
    avg_cycle_time_s: float = 0.0
    min_cycle_time_s: float = 0.0
    max_cycle_time_s: float = 0.0
    avg_dispatch_interval_s: float = 0.0

    # Efficiency
    dispatch_efficiency: float = 0.0  # Actual vs theoretical
    block_utilization: Dict[str, float] = field(default_factory=dict)


@dataclass
class BlockTimingResult(AnalysisResult):
    """Results from block timing analysis."""
    scenario_type: ScenarioType = ScenarioType.BLOCK_TIMING

    # Per-block timing
    block_occupancy_times: Dict[str, float] = field(default_factory=dict)  # block_id -> time_s
    block_clear_times: Dict[str, float] = field(default_factory=dict)

    # Sequence timing
    block_sequence: List[str] = field(default_factory=list)
    total_block_time_s: float = 0.0

    # Safety margins
    min_separation_s: float = 0.0
    min_separation_blocks: tuple = ("", "")

    # Warnings
    timing_warnings: List[str] = field(default_factory=list)


@dataclass
class LoadCaseResult(AnalysisResult):
    """Results from load case comparison."""
    scenario_type: ScenarioType = ScenarioType.LOAD_CASE

    # Per-case results
    case_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Comparisons
    velocity_difference_mps: float = 0.0
    position_difference_m: float = 0.0
    time_difference_s: float = 0.0

    # Energy comparison
    kinetic_energy_difference_j: float = 0.0

    # Worst case assessment
    worst_case: LoadCase = LoadCase.LOADED
    critical_metrics: List[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    """Complete validation report for a project."""
    project_id: str
    generated_at: datetime = field(default_factory=datetime.now)

    # Overall status
    overall_valid: bool = True

    # Individual results
    emergency_stop_results: List[EmergencyStopResult] = field(default_factory=list)
    throughput_results: List[ThroughputResult] = field(default_factory=list)
    block_timing_results: List[BlockTimingResult] = field(default_factory=list)
    load_case_results: List[LoadCaseResult] = field(default_factory=list)

    # Summary
    total_scenarios_run: int = 0
    total_failures: int = 0
    critical_issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)