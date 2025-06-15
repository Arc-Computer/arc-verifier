"""Tests for Agent Simulation Engine."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from arc_verifier.simulator import (
    AgentSimulator, SimulationScenario, ScenarioStep,
    SimulationResult, MockAPIProvider, BehaviorMonitor,
    ScenarioLibrary
)


class TestMockAPIProvider:
    """Test mock API provider functionality."""
    
    def test_configure_step(self):
        """Test scenario step configuration."""
        provider = MockAPIProvider()
        step = ScenarioStep(
            time_offset_seconds=0,
            market_data={"eth_price": 3500.0},
            inject_failure=None
        )
        
        provider.configure_step(step)
        
        assert provider.current_step == step
        assert "api.binance.com" in provider.responses
        assert provider.responses["api.binance.com"]["price"] == "3500.0"
        
    def test_api_timeout_injection(self):
        """Test API timeout failure injection."""
        provider = MockAPIProvider()
        step = ScenarioStep(
            time_offset_seconds=0,
            market_data={"eth_price": 3000.0},
            inject_failure="api_timeout"
        )
        
        provider.configure_step(step)
        assert provider.responses.get("timeout") is True
        
    def test_invalid_data_injection(self):
        """Test invalid data failure injection."""
        provider = MockAPIProvider()
        step = ScenarioStep(
            time_offset_seconds=0,
            market_data={"eth_price": 3000.0},
            inject_failure="invalid_data"
        )
        
        provider.configure_step(step)
        assert provider.responses.get("corrupt") is True
        
    def test_call_logging(self):
        """Test API call logging."""
        provider = MockAPIProvider()
        provider.configure_step(ScenarioStep(
            time_offset_seconds=0,
            market_data={"eth_price": 3000.0}
        ))
        
        response = provider.get_response("https://api.binance.com/price")
        
        assert len(provider.call_log) == 1
        assert provider.call_log[0]["url"] == "https://api.binance.com/price"
        assert "timestamp" in provider.call_log[0]


class TestBehaviorMonitor:
    """Test behavior monitoring functionality."""
    
    def test_record_action(self):
        """Test action recording."""
        monitor = BehaviorMonitor()
        
        monitor.record_action("fetch_price", {"source": "binance", "price": 3000})
        
        assert len(monitor.actions) == 1
        assert monitor.actions[0]["type"] == "fetch_price"
        assert monitor.actions[0]["details"]["price"] == 3000
        
    def test_anomaly_detection(self):
        """Test anomaly detection."""
        monitor = BehaviorMonitor()
        
        result = monitor.check_anomaly("execute_trade", "skip_trade")
        
        assert result is True
        assert len(monitor.anomalies) == 1
        assert "Expected execute_trade, observed skip_trade" in monitor.anomalies[0]
        
    def test_score_calculation(self):
        """Test behavioral score calculation."""
        monitor = BehaviorMonitor()
        scenario = SimulationScenario(
            name="test",
            description="Test scenario",
            agent_type="test",
            steps=[],
            success_criteria={
                "expected_actions": ["fetch_price", "update_price"],
                "max_api_calls": 10
            }
        )
        
        # Record matching actions
        monitor.record_action("fetch_price", {})
        monitor.record_action("update_price", {})
        monitor.record_action("api_call", {})
        
        scores = monitor.calculate_scores(scenario)
        
        assert scores["correctness"] == 1.0  # All expected actions performed
        assert scores["efficiency"] == 0.9   # 1 API call out of 10 max
        assert scores["resilience"] == 1.0   # No errors
        assert 0 <= scores["safety"] <= 1.0


class TestScenarioLibrary:
    """Test pre-defined scenarios."""
    
    def test_price_oracle_scenarios(self):
        """Test price oracle scenario definitions."""
        scenarios = ScenarioLibrary.get_price_oracle_scenarios()
        
        assert len(scenarios) >= 2
        assert any(s.name == "normal_price_update" for s in scenarios)
        assert any(s.name == "api_failure_handling" for s in scenarios)
        
        # Check scenario structure
        for scenario in scenarios:
            assert scenario.agent_type == "price_oracle"
            assert len(scenario.steps) > 0
            assert "expected_actions" in scenario.success_criteria
            
    def test_arbitrage_scenarios(self):
        """Test arbitrage bot scenario definitions."""
        scenarios = ScenarioLibrary.get_arbitrage_scenarios()
        
        assert len(scenarios) >= 2
        assert any(s.name == "profitable_arbitrage" for s in scenarios)
        assert any(s.name == "unprofitable_arbitrage" for s in scenarios)
        
        # Check scenario structure
        for scenario in scenarios:
            assert scenario.agent_type == "arbitrage"
            assert len(scenario.steps) > 0
            assert "min_scores" in scenario.success_criteria


class TestAgentSimulator:
    """Test main agent simulator."""
    
    @patch('docker.from_env')
    def test_simulator_initialization(self, mock_docker):
        """Test simulator initialization."""
        mock_client = MagicMock()
        mock_docker.return_value = mock_client
        
        simulator = AgentSimulator()
        
        assert simulator.docker_client is not None
        mock_client.ping.assert_called_once()
        
    @patch('docker.from_env')
    def test_docker_unavailable(self, mock_docker):
        """Test handling when Docker is unavailable."""
        mock_docker.side_effect = Exception("Docker not found")
        
        simulator = AgentSimulator()
        
        assert simulator.docker_client is None
        
    @patch('docker.from_env')
    def test_run_simulation_success(self, mock_docker):
        """Test successful simulation run."""
        # Mock Docker client and container
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_docker.return_value = mock_client
        mock_client.containers.run.return_value = mock_container
        mock_container.logs.return_value = []
        
        simulator = AgentSimulator()
        scenario = SimulationScenario(
            name="test_scenario",
            description="Test",
            agent_type="test",
            steps=[
                ScenarioStep(
                    time_offset_seconds=0,
                    market_data={"test": True}
                )
            ],
            success_criteria={"expected_actions": []}
        )
        
        result = simulator.run_simulation("test:latest", scenario)
        
        assert isinstance(result, SimulationResult)
        assert result.scenario_name == "test_scenario"
        assert result.agent_image == "test:latest"
        assert isinstance(result.behavior_scores, dict)
        
    @patch('docker.from_env')
    def test_container_startup_failure(self, mock_docker):
        """Test handling of container startup failure."""
        mock_client = MagicMock()
        mock_docker.return_value = mock_client
        mock_client.containers.run.side_effect = Exception("Container failed")
        
        simulator = AgentSimulator()
        scenario = SimulationScenario(
            name="test_scenario",
            description="Test",
            agent_type="test",
            steps=[],
            success_criteria={}
        )
        
        result = simulator.run_simulation("test:latest", scenario)
        
        assert result.passed is False
        assert "Simulation error" in result.anomalies[0]
        
    def test_evaluate_success_criteria(self):
        """Test success evaluation logic."""
        simulator = AgentSimulator()
        
        # Test passing criteria
        scenario = SimulationScenario(
            name="test",
            description="Test",
            agent_type="test",
            steps=[],
            success_criteria={
                "min_scores": {"correctness": 0.7, "safety": 0.8}
            }
        )
        
        scores = {"correctness": 0.8, "safety": 0.9, "efficiency": 0.6}
        assert simulator._evaluate_success(scenario, scores) is True
        
        # Test failing criteria
        scores = {"correctness": 0.6, "safety": 0.9, "efficiency": 0.6}
        assert simulator._evaluate_success(scenario, scores) is False


class TestSimulationResult:
    """Test simulation result model."""
    
    def test_result_creation(self):
        """Test creating simulation result."""
        result = SimulationResult(
            scenario_name="test",
            agent_image="test:latest",
            passed=True,
            behavior_scores={"correctness": 0.9},
            observed_actions=[{"type": "test"}],
            expected_actions=[{"type": "test"}],
            anomalies=[],
            execution_time_seconds=10.5,
            timestamp=datetime.now()
        )
        
        assert result.scenario_name == "test"
        assert result.passed is True
        assert result.behavior_scores["correctness"] == 0.9
        
    def test_result_serialization(self):
        """Test result serialization to JSON."""
        result = SimulationResult(
            scenario_name="test",
            agent_image="test:latest",
            passed=True,
            behavior_scores={"correctness": 0.9},
            observed_actions=[],
            expected_actions=[],
            anomalies=[],
            execution_time_seconds=10.5,
            timestamp=datetime.now()
        )
        
        json_data = result.model_dump(mode='json')
        
        assert json_data["scenario_name"] == "test"
        assert json_data["passed"] is True
        assert isinstance(json_data["timestamp"], str)  # Datetime serialized to string