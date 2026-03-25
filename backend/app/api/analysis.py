"""Analysis API endpoints

Provides endpoints for running various analysis scenarios on projects.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.services.project_io import ProjectIO
from app.simulation.geometry.cache import GeometryCache
from app.simulation.physics.integrator import PhysicsSimulator
from app.simulation.equipment.manager import EquipmentManager
from app.simulation.analysis import (
    # Types
    ScenarioType,
    LoadCase,
    EmergencyStopConfig,
    ThroughputConfig,
    BlockTimingConfig,
    LoadCaseConfig,
    # Analyzers
    EmergencyStopAnalyzer,
    ThroughputAnalyzer,
    BlockTimingAnalyzer,
    LoadCaseAnalyzer,
    ProjectValidator,
    ValidationReport,
)

router = APIRouter(prefix="/projects/{project_id}/analysis", tags=["analysis"])


# Request models
class EmergencyStopRequest(BaseModel):
    """Request for emergency stop analysis."""
    trigger_position_m: float = Field(..., description="Position to trigger E-stop")
    trigger_path_id: str = Field(..., description="Path ID for trigger position")
    initial_velocity_mps: float = Field(10.0, description="Initial velocity")
    initial_position_m: float = Field(0.0, description="Initial position")
    initial_path_id: str = Field("", description="Initial path ID")


class ThroughputRequest(BaseModel):
    """Request for throughput analysis."""
    dispatch_interval_s: float = Field(60.0, description="Dispatch interval")
    num_trains: int = Field(1, description="Number of trains")
    station_id: str = Field("", description="Station ID")
    duration_s: float = Field(3600.0, description="Analysis duration")


class BlockTimingRequest(BaseModel):
    """Request for block timing analysis."""
    block_ids: List[str] = Field(default_factory=list, description="Block IDs to analyze")
    duration_s: float = Field(300.0, description="Analysis duration")


class LoadCaseRequest(BaseModel):
    """Request for load case analysis."""
    cases: List[str] = Field(
        default=["empty", "loaded"],
        description="Load cases to analyze"
    )
    initial_position_m: float = Field(0.0)
    initial_path_id: str = Field("")
    initial_velocity_mps: float = Field(0.0)
    duration_s: float = Field(60.0)


class MultiPositionEstopRequest(BaseModel):
    """Request for multi-position emergency stop analysis."""
    positions: List[float] = Field(..., description="Positions to test")
    path_id: str = Field(..., description="Path ID")
    initial_velocity_mps: float = Field(10.0)


def get_project(project_id: str):
    """Load project by ID from memory or disk."""
    # First check in-memory projects
    from app.api.projects import _projects
    if project_id in _projects:
        return _projects[project_id]

    # Fall back to disk storage
    project_io = ProjectIO()
    try:
        return project_io.load(project_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")


def create_simulator(project, geometry_cache=None):
    """Create physics simulator for project."""
    if geometry_cache is None:
        geometry_cache = GeometryCache(project)

    equipment_manager = EquipmentManager(project)
    simulator = PhysicsSimulator(project, geometry_cache, equipment_manager)
    return simulator, equipment_manager, geometry_cache


@router.post("/validate")
async def validate_project(project_id: str) -> ValidationReport:
    """
    Validate project for errors and warnings.

    Returns a comprehensive validation report.
    """
    project = get_project(project_id)
    validator = ProjectValidator(project)
    return validator.validate()


@router.post("/emergency-stop")
async def analyze_emergency_stop(
    project_id: str,
    request: EmergencyStopRequest,
) -> dict:
    """
    Run emergency stop analysis.

    Simulates a train stopping from the given conditions.
    """
    project = get_project(project_id)
    simulator, equipment_manager, geometry_cache = create_simulator(project)

    config = EmergencyStopConfig(
        trigger_position_m=request.trigger_position_m,
        trigger_path_id=request.trigger_path_id,
        initial_velocity_mps=request.initial_velocity_mps,
        initial_position_m=request.initial_position_m,
        initial_path_id=request.initial_path_id or request.trigger_path_id,
    )

    analyzer = EmergencyStopAnalyzer(
        project,
        simulator,
        equipment_manager
    )

    result = analyzer.analyze(config)

    return {
        'success': result.success,
        'error_message': result.error_message,
        'stopping_distance_m': result.stopping_distance_m,
        'stopping_time_s': result.stopping_time_s,
        'max_deceleration_mps2': result.max_deceleration_mps2,
        'max_gforce': result.max_gforce,
        'safe_stop': result.safe_stop,
        'warnings': result.warnings,
        'execution_time_s': result.execution_time_s,
    }


@router.post("/emergency-stop/multi")
async def analyze_multi_position_estop(
    project_id: str,
    request: MultiPositionEstopRequest,
) -> dict:
    """
    Run emergency stop analysis at multiple positions.

    Identifies worst-case stopping scenarios.
    """
    project = get_project(project_id)
    simulator, equipment_manager, geometry_cache = create_simulator(project)

    analyzer = EmergencyStopAnalyzer(
        project,
        simulator,
        equipment_manager
    )

    results = analyzer.run_multiple_stops(
        positions=request.positions,
        path_id=request.path_id,
        initial_velocity=request.initial_velocity_mps,
    )

    return {
        'results': [
            {
                'position_m': pos,
                'stopping_distance_m': r.stopping_distance_m,
                'stopping_time_s': r.stopping_time_s,
                'max_gforce': r.max_gforce,
                'safe_stop': r.safe_stop,
            }
            for pos, r in zip(request.positions, results)
            if r.success
        ],
        'total_scenarios': len(results),
    }


@router.post("/throughput")
async def analyze_throughput(
    project_id: str,
    request: ThroughputRequest,
) -> dict:
    """
    Run throughput analysis.

    Calculates ride capacity and dispatch efficiency.
    """
    project = get_project(project_id)
    simulator, equipment_manager, geometry_cache = create_simulator(project)

    config = ThroughputConfig(
        dispatch_interval_s=request.dispatch_interval_s,
        num_trains=request.num_trains,
        station_id=request.station_id,
        duration_s=request.duration_s,
    )

    analyzer = ThroughputAnalyzer(project, simulator)
    result = analyzer.analyze(config)

    return {
        'success': result.success,
        'error_message': result.error_message,
        'theoretical_capacity_pph': result.theoretical_capacity_pph,
        'actual_capacity_pph': result.actual_capacity_pph,
        'dispatch_efficiency': result.dispatch_efficiency,
        'total_dispatches': result.total_dispatches,
        'avg_cycle_time_s': result.avg_cycle_time_s,
        'block_utilization': result.block_utilization,
        'execution_time_s': result.execution_time_s,
    }


@router.post("/throughput/optimize")
async def optimize_throughput(
    project_id: str,
    min_interval: float = 30.0,
    max_interval: float = 180.0,
    step: float = 5.0,
) -> dict:
    """
    Find optimal dispatch interval for maximum throughput.

    Tests various dispatch intervals and returns the best.
    """
    project = get_project(project_id)
    simulator, equipment_manager, geometry_cache = create_simulator(project)

    analyzer = ThroughputAnalyzer(project, simulator)
    result = analyzer.optimize_dispatch_interval(
        min_interval=min_interval,
        max_interval=max_interval,
        step=step,
    )

    return result


@router.post("/block-timing")
async def analyze_block_timing(
    project_id: str,
    request: BlockTimingRequest,
) -> dict:
    """
    Run block timing analysis.

    Analyzes block occupancy and sequencing.
    """
    project = get_project(project_id)
    simulator, equipment_manager, geometry_cache = create_simulator(project)

    config = BlockTimingConfig(
        block_ids=request.block_ids,
        duration_s=request.duration_s,
    )

    analyzer = BlockTimingAnalyzer(project, simulator)
    result = analyzer.analyze(config)

    return {
        'success': result.success,
        'error_message': result.error_message,
        'block_occupancy_times': result.block_occupancy_times,
        'block_sequence': result.block_sequence,
        'min_separation_s': result.min_separation_s,
        'min_separation_blocks': result.min_separation_blocks,
        'timing_warnings': result.timing_warnings,
        'execution_time_s': result.execution_time_s,
    }


@router.post("/load-case")
async def analyze_load_case(
    project_id: str,
    request: LoadCaseRequest,
) -> dict:
    """
    Run load case comparison analysis.

    Compares train behavior under different loading conditions.
    """
    project = get_project(project_id)
    simulator, equipment_manager, geometry_cache = create_simulator(project)

    # Parse load cases
    cases = []
    for case_str in request.cases:
        try:
            cases.append(LoadCase(case_str.lower()))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid load case: {case_str}"
            )

    config = LoadCaseConfig(
        cases=cases,
        initial_position_m=request.initial_position_m,
        initial_path_id=request.initial_path_id,
        initial_velocity_mps=request.initial_velocity_mps,
        duration_s=request.duration_s,
    )

    analyzer = LoadCaseAnalyzer(project, simulator)
    result = analyzer.analyze(config)

    return {
        'success': result.success,
        'error_message': result.error_message,
        'case_results': result.case_results,
        'velocity_difference_mps': result.velocity_difference_mps,
        'position_difference_m': result.position_difference_m,
        'kinetic_energy_difference_j': result.kinetic_energy_difference_j,
        'worst_case': result.worst_case.value,
        'critical_metrics': result.critical_metrics,
        'execution_time_s': result.execution_time_s,
    }


@router.post("/comprehensive")
async def run_comprehensive_analysis(
    project_id: str,
    include_estop: bool = True,
    include_throughput: bool = True,
    include_block_timing: bool = True,
    include_load_case: bool = True,
) -> dict:
    """
    Run comprehensive analysis suite.

    Runs all analysis types and returns combined results.
    """
    project = get_project(project_id)
    simulator, equipment_manager, geometry_cache = create_simulator(project)

    results = {
        'project_id': project_id,
        'validation': None,
        'emergency_stop': None,
        'throughput': None,
        'block_timing': None,
        'load_case': None,
    }

    # Validate first
    validator = ProjectValidator(project)
    validation_report = validator.validate()
    results['validation'] = {
        'valid': validation_report.overall_valid,
        'critical_issues': validation_report.critical_issues,
        'recommendations': validation_report.recommendations,
    }

    # Only proceed with analysis if validation passes
    if not validation_report.overall_valid:
        return results

    # Emergency stop analysis
    if include_estop and project.paths:
        estop_analyzer = EmergencyStopAnalyzer(
            project, simulator, equipment_manager
        )
        # Find worst case
        worst = estop_analyzer.find_worst_case_stop(
            project.paths[0].id,
            velocity_range=(5.0, 25.0),
            position_step=50.0,
        )
        results['emergency_stop'] = {
            'worst_case_stopping_distance_m': worst.stopping_distance_m,
            'worst_case_stopping_time_s': worst.stopping_time_s,
            'max_gforce': worst.max_gforce,
            'safe_stop': worst.safe_stop,
            'warnings': worst.warnings,
        }

    # Throughput analysis
    if include_throughput and project.trains:
        throughput_analyzer = ThroughputAnalyzer(project, simulator)
        config = ThroughputConfig(
            dispatch_interval_s=60.0,
            num_trains=len(project.trains),
            duration_s=3600.0,
        )
        throughput_result = throughput_analyzer.analyze(config)
        results['throughput'] = {
            'theoretical_capacity_pph': throughput_result.theoretical_capacity_pph,
            'actual_capacity_pph': throughput_result.actual_capacity_pph,
            'dispatch_efficiency': throughput_result.dispatch_efficiency,
        }

    # Block timing analysis
    if include_block_timing and project.blocks:
        timing_analyzer = BlockTimingAnalyzer(project, simulator)
        config = BlockTimingConfig(
            block_ids=[b.id for b in project.blocks],
            duration_s=300.0,
        )
        timing_result = timing_analyzer.analyze(config)
        results['block_timing'] = {
            'block_occupancy_times': timing_result.block_occupancy_times,
            'min_separation_s': timing_result.min_separation_s,
            'timing_warnings': timing_result.timing_warnings,
        }

    # Load case analysis
    if include_load_case and project.trains:
        load_analyzer = LoadCaseAnalyzer(project, simulator)
        config = LoadCaseConfig(
            cases=[LoadCase.EMPTY, LoadCase.LOADED],
            duration_s=60.0,
        )
        load_result = load_analyzer.analyze(config)
        results['load_case'] = {
            'velocity_difference_mps': load_result.velocity_difference_mps,
            'position_difference_m': load_result.position_difference_m,
            'worst_case': load_result.worst_case.value,
            'critical_metrics': load_result.critical_metrics,
        }

    return results