"""Tests for analysis types."""

import pytest
from datetime import datetime

from app.simulation.analysis.types import (
    ScenarioType,
    LoadCase,
    ScenarioConfig,
    EmergencyStopConfig,
    ThroughputConfig,
    BlockTimingConfig,
    LoadCaseConfig,
    AnalysisResult,
    EmergencyStopResult,
    ThroughputResult,
    BlockTimingResult,
    LoadCaseResult,
    ValidationReport,
)


class TestScenarioType:
    """Test ScenarioType enum."""

    def test_scenario_types_exist(self):
        """All expected scenario types exist."""
        assert ScenarioType.EMERGENCY_STOP == "emergency_stop"
        assert ScenarioType.THROUGHPUT == "throughput"
        assert ScenarioType.BLOCK_TIMING == "block_timing"
        assert ScenarioType.LOAD_CASE == "load_case"
        assert ScenarioType.CUSTOM == "custom"


class TestLoadCase:
    """Test LoadCase enum."""

    def test_load_cases_exist(self):
        """All expected load cases exist."""
        assert LoadCase.EMPTY == "empty"
        assert LoadCase.LOADED == "loaded"
        assert LoadCase.CUSTOM == "custom"


class TestConfigs:
    """Test configuration dataclasses."""

    def test_scenario_config_defaults(self):
        """ScenarioConfig has expected defaults."""
        config = ScenarioConfig(
            scenario_id="test",
            name="Test Scenario",
            scenario_type=ScenarioType.CUSTOM,
        )
        assert config.duration_s == 60.0
        assert config.time_step_s == 0.01
        assert config.load_case == LoadCase.LOADED

    def test_emergency_stop_config(self):
        """EmergencyStopConfig stores values correctly."""
        config = EmergencyStopConfig(
            trigger_position_m=100.0,
            trigger_path_id="path_1",
            initial_velocity_mps=10.0,
            initial_position_m=0.0,
            initial_path_id="path_1",
        )
        assert config.trigger_position_m == 100.0
        assert config.trigger_path_id == "path_1"

    def test_throughput_config_defaults(self):
        """ThroughputConfig has expected defaults."""
        config = ThroughputConfig()
        assert config.dispatch_interval_s == 60.0
        assert config.num_trains == 1
        assert config.duration_s == 3600.0

    def test_block_timing_config_defaults(self):
        """BlockTimingConfig has expected defaults."""
        config = BlockTimingConfig()
        assert config.block_ids == []
        assert config.duration_s == 300.0

    def test_load_case_config_defaults(self):
        """LoadCaseConfig has expected defaults."""
        config = LoadCaseConfig()
        assert config.cases == [LoadCase.EMPTY, LoadCase.LOADED]
        assert config.duration_s == 60.0


class TestResults:
    """Test result dataclasses."""

    def test_analysis_result_defaults(self):
        """AnalysisResult has expected defaults."""
        result = AnalysisResult(
            scenario_id="test",
            scenario_type=ScenarioType.CUSTOM,
        )
        assert result.success is True
        assert result.error_message is None
        assert result.execution_time_s == 0.0

    def test_emergency_stop_result_defaults(self):
        """EmergencyStopResult has expected defaults."""
        result = EmergencyStopResult(
            scenario_id="test",
        )
        assert result.stopping_distance_m == 0.0
        assert result.safe_stop is True
        assert result.warnings == []

    def test_throughput_result_defaults(self):
        """ThroughputResult has expected defaults."""
        result = ThroughputResult(
            scenario_id="test",
        )
        assert result.theoretical_capacity_pph == 0
        assert result.actual_capacity_pph == 0
        assert result.dispatch_efficiency == 0.0

    def test_block_timing_result_defaults(self):
        """BlockTimingResult has expected defaults."""
        result = BlockTimingResult(
            scenario_id="test",
        )
        assert result.block_occupancy_times == {}
        assert result.block_sequence == []
        assert result.timing_warnings == []

    def test_load_case_result_defaults(self):
        """LoadCaseResult has expected defaults."""
        result = LoadCaseResult(
            scenario_id="test",
        )
        assert result.case_results == {}
        assert result.worst_case == LoadCase.LOADED
        assert result.critical_metrics == []


class TestValidationReport:
    """Test ValidationReport."""

    def test_validation_report_defaults(self):
        """ValidationReport has expected defaults."""
        report = ValidationReport(project_id="test_project")
        assert report.overall_valid is True
        assert report.emergency_stop_results == []
        assert report.critical_issues == []