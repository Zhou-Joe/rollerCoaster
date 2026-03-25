"""Simulation analysis module

Provides tools for analyzing roller coaster projects:
- Emergency stop scenarios
- Throughput and capacity analysis
- Block timing analysis
- Load case comparison
- Project validation
"""

from .types import (
    # Enums
    ScenarioType,
    LoadCase,
    # Configs
    ScenarioConfig,
    EmergencyStopConfig,
    ThroughputConfig,
    BlockTimingConfig,
    LoadCaseConfig,
    # Results
    AnalysisResult,
    EmergencyStopResult,
    ThroughputResult,
    BlockTimingResult,
    LoadCaseResult,
    ValidationReport,
)

from .emergency_stop import EmergencyStopAnalyzer
from .throughput import ThroughputAnalyzer
from .block_timing import BlockTimingAnalyzer
from .load_case import LoadCaseAnalyzer
from .validator import (
    ProjectValidator,
    ValidationIssue,
    ValidationSeverity,
)

__all__ = [
    # Enums
    'ScenarioType',
    'LoadCase',
    # Configs
    'ScenarioConfig',
    'EmergencyStopConfig',
    'ThroughputConfig',
    'BlockTimingConfig',
    'LoadCaseConfig',
    # Results
    'AnalysisResult',
    'EmergencyStopResult',
    'ThroughputResult',
    'BlockTimingResult',
    'LoadCaseResult',
    'ValidationReport',
    # Analyzers
    'EmergencyStopAnalyzer',
    'ThroughputAnalyzer',
    'BlockTimingAnalyzer',
    'LoadCaseAnalyzer',
    # Validation
    'ProjectValidator',
    'ValidationIssue',
    'ValidationSeverity',
]