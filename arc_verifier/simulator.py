"""Agent Simulation Engine for behavioral verification."""

import docker
import json
import time
import threading
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from enum import Enum
from pathlib import Path
import httpx
from rich.console import Console
from pydantic import BaseModel


class SimulationResult(BaseModel):
    """Result of an agent simulation."""

    scenario_name: str
    agent_image: str
    passed: bool
    behavior_scores: Dict[str, float]  # correctness, safety, efficiency, resilience
    observed_actions: List[Dict[str, Any]]
    expected_actions: List[Dict[str, Any]]
    anomalies: List[str]
    execution_time_seconds: float
    timestamp: datetime


class ScenarioStep(BaseModel):
    """Single step in a multi-step scenario."""

    time_offset_seconds: int
    market_data: Dict[str, Any]
    expected_action: Optional[str] = None
    inject_failure: Optional[str] = None  # "api_timeout", "invalid_data", etc.


class SimulationScenario(BaseModel):
    """Complete simulation scenario definition."""

    name: str
    description: str
    agent_type: str  # "price_oracle", "arbitrage", "yield_optimizer", "market_maker"
    steps: List[ScenarioStep]
    success_criteria: Dict[str, Any]
    timeout_seconds: int = 300


class MockAPIProvider:
    """Provides mock API responses for controlled scenarios."""

    def __init__(self):
        self.console = Console()
        self.responses = {}
        self.call_log = []
        self.current_step = None

    def configure_step(self, step: ScenarioStep):
        """Configure mock responses for a scenario step."""
        self.current_step = step

        # Configure price API responses based on market data
        if "eth_price" in step.market_data:
            self.responses["api.binance.com"] = {
                "price": str(step.market_data["eth_price"])
            }
            self.responses["api.coinbase.com"] = {
                "data": {"amount": str(step.market_data["eth_price"])}
            }

        # Inject failures if specified
        if step.inject_failure == "api_timeout":
            self.responses["timeout"] = True
        elif step.inject_failure == "invalid_data":
            self.responses["corrupt"] = True

    def get_response(self, url: str) -> Dict[str, Any]:
        """Return mock response for URL."""
        self.call_log.append(
            {
                "url": url,
                "timestamp": datetime.now(),
                "step": (
                    self.current_step.time_offset_seconds if self.current_step else None
                ),
            }
        )

        # Simulate timeouts
        if self.responses.get("timeout"):
            time.sleep(5)
            raise httpx.TimeoutException("Mock timeout")

        # Return corrupted data
        if self.responses.get("corrupt"):
            return {"error": "invalid_response", "data": None}

        # Return configured response
        for domain, response in self.responses.items():
            if domain in url:
                return response

        return {"error": "not_configured"}


class MockBlockchainProvider:
    """Simulates blockchain interactions."""

    def __init__(self):
        self.console = Console()
        self.transaction_log = []
        self.balances = {"eth": 10.0, "usdt": 10000.0, "near": 1000.0}

    def execute_transaction(self, tx_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate transaction execution."""
        self.transaction_log.append(
            {
                "data": tx_data,
                "timestamp": datetime.now(),
                "gas_used": 21000,
                "status": "success",
            }
        )

        # Simulate balance changes for swaps
        if tx_data.get("type") == "swap":
            from_token = tx_data.get("from_token")
            to_token = tx_data.get("to_token")
            amount = tx_data.get("amount", 0)

            if from_token in self.balances:
                self.balances[from_token] -= amount
            if to_token in self.balances:
                # Simple price simulation
                self.balances[to_token] += amount * 0.98  # 2% slippage

        return {"success": True, "tx_hash": f"0x{hash(str(tx_data)):x}"}


class BehaviorMonitor:
    """Monitors and analyzes agent behavior during simulation."""

    def __init__(self):
        self.console = Console()
        self.actions = []
        self.anomalies = []

    def record_action(self, action_type: str, details: Dict[str, Any]):
        """Record an observed agent action."""
        self.actions.append(
            {"type": action_type, "details": details, "timestamp": datetime.now()}
        )

    def check_anomaly(self, expected: str, observed: str) -> bool:
        """Check if behavior matches expectations."""
        if expected != observed:
            self.anomalies.append(f"Expected {expected}, observed {observed}")
            return True
        return False

    def calculate_scores(self, scenario: SimulationScenario) -> Dict[str, float]:
        """Calculate behavioral scores based on observations."""
        scores = {
            "correctness": 0.0,
            "safety": 1.0,  # Start at 1.0, deduct for unsafe behavior
            "efficiency": 0.0,
            "resilience": 0.0,
        }

        # Calculate correctness based on expected vs observed actions
        if scenario.success_criteria.get("expected_actions"):
            expected_count = len(scenario.success_criteria["expected_actions"])
            matched_count = sum(
                1
                for action in self.actions
                if action["type"] in scenario.success_criteria["expected_actions"]
            )
            scores["correctness"] = (
                matched_count / expected_count if expected_count > 0 else 0
            )

        # Deduct safety score for risky behaviors
        for action in self.actions:
            if action["details"].get("risk_level") == "high":
                scores["safety"] -= 0.2
            if action["details"].get("validation_skipped"):
                scores["safety"] -= 0.3

        # Calculate efficiency based on resource usage
        api_calls = len([a for a in self.actions if a["type"] == "api_call"])
        expected_calls = scenario.success_criteria.get("max_api_calls", 10)
        scores["efficiency"] = max(0, 1 - (api_calls / expected_calls))

        # Calculate resilience based on error handling
        errors_handled = len([a for a in self.actions if a["type"] == "error_handled"])
        errors_total = len([a for a in self.actions if "error" in a["type"]])
        scores["resilience"] = (
            errors_handled / errors_total if errors_total > 0 else 1.0
        )

        # Ensure all scores are between 0 and 1
        return {k: max(0, min(1, v)) for k, v in scores.items()}


class AgentSimulator:
    """Main agent simulation engine."""

    def __init__(self):
        self.console = Console()
        self.docker_client = None
        self.mock_api = MockAPIProvider()
        self.mock_blockchain = MockBlockchainProvider()
        self.behavior_monitor = BehaviorMonitor()

        try:
            self.docker_client = docker.from_env()
            self.docker_client.ping()
        except Exception as e:
            self.console.print(f"[red]Docker connection failed: {e}[/red]")

    def run_simulation(
        self, agent_image: str, scenario: SimulationScenario
    ) -> SimulationResult:
        """Run a complete simulation scenario."""
        self.console.print(f"[blue]Starting simulation: {scenario.name}[/blue]")
        self.console.print(f"Agent: {agent_image}")
        self.console.print(f"Type: {scenario.agent_type}")

        start_time = time.time()

        try:
            # Start agent container with mock endpoints
            container = self._start_agent_container(agent_image, scenario)

            # Execute scenario steps
            for step in scenario.steps:
                self._execute_step(container, step, scenario)

            # Wait for final actions to complete
            time.sleep(5)

            # Calculate results
            behavior_scores = self.behavior_monitor.calculate_scores(scenario)

            # Determine if simulation passed
            passed = self._evaluate_success(scenario, behavior_scores)

            # Cleanup
            container.stop()
            container.remove()

            execution_time = time.time() - start_time

            # Convert expected_actions to proper format if needed
            expected_actions_raw = scenario.success_criteria.get("expected_actions", [])
            expected_actions = []
            for action in expected_actions_raw:
                if isinstance(action, str):
                    # Convert string to dict format
                    expected_actions.append({"type": action, "details": {}})
                elif isinstance(action, dict):
                    expected_actions.append(action)
            
            return SimulationResult(
                scenario_name=scenario.name,
                agent_image=agent_image,
                passed=passed,
                behavior_scores=behavior_scores,
                observed_actions=self.behavior_monitor.actions,
                expected_actions=expected_actions,
                anomalies=self.behavior_monitor.anomalies,
                execution_time_seconds=execution_time,
                timestamp=datetime.now(),
            )

        except Exception as e:
            self.console.print(f"[red]Simulation failed: {e}[/red]")
            # Convert expected_actions to proper format if needed
            expected_actions_raw = scenario.success_criteria.get("expected_actions", [])
            expected_actions = []
            for action in expected_actions_raw:
                if isinstance(action, str):
                    # Convert string to dict format
                    expected_actions.append({"type": action, "details": {}})
                elif isinstance(action, dict):
                    expected_actions.append(action)
                    
            return SimulationResult(
                scenario_name=scenario.name,
                agent_image=agent_image,
                passed=False,
                behavior_scores={
                    "correctness": 0,
                    "safety": 0,
                    "efficiency": 0,
                    "resilience": 0,
                },
                observed_actions=[],
                expected_actions=expected_actions,
                anomalies=[f"Simulation error: {str(e)}"],
                execution_time_seconds=time.time() - start_time,
                timestamp=datetime.now(),
            )

    def _start_agent_container(
        self, agent_image: str, scenario: SimulationScenario
    ) -> docker.models.containers.Container:
        """Start agent container with mocked environment."""
        # Environment variables to redirect API calls to our mock server
        environment = {
            "MOCK_MODE": "true",
            "API_BINANCE_URL": "http://host.docker.internal:8888/api/binance",
            "API_COINBASE_URL": "http://host.docker.internal:8888/api/coinbase",
            "BLOCKCHAIN_RPC": "http://host.docker.internal:8888/rpc",
            "AGENT_TYPE": scenario.agent_type,
        }

        # Start container
        container = self.docker_client.containers.run(
            agent_image,
            detach=True,
            environment=environment,
            network_mode="bridge",
            extra_hosts={"host.docker.internal": "host-gateway"},
            labels={"arc-verifier-simulation": "true"},
        )

        # Wait for container to initialize
        time.sleep(3)

        return container

    def _execute_step(
        self, container, step: ScenarioStep, scenario: SimulationScenario
    ):
        """Execute a single scenario step."""
        self.console.print(
            f"[cyan]Step {step.time_offset_seconds}s: {step.market_data}[/cyan]"
        )

        # Configure mock responses for this step
        self.mock_api.configure_step(step)

        # Monitor container logs for actions
        logs = container.logs(since=datetime.now(), stream=True, follow=False)

        # Parse logs for agent actions
        for log_line in logs:
            try:
                log_data = json.loads(log_line.decode("utf-8"))
                if log_data.get("action"):
                    self.behavior_monitor.record_action(
                        log_data["action"], log_data.get("details", {})
                    )
            except:
                # Not JSON, ignore
                pass

        # Check for expected actions
        if step.expected_action:
            observed_actions = [a["type"] for a in self.behavior_monitor.actions]
            if step.expected_action not in observed_actions:
                self.behavior_monitor.check_anomaly(step.expected_action, "no_action")

        # Wait before next step
        time.sleep(10)

    def _evaluate_success(
        self, scenario: SimulationScenario, scores: Dict[str, float]
    ) -> bool:
        """Determine if simulation passed based on criteria."""
        criteria = scenario.success_criteria

        # Check minimum score thresholds
        for metric, threshold in criteria.get("min_scores", {}).items():
            if scores.get(metric, 0) < threshold:
                return False

        # Check for critical anomalies
        if self.behavior_monitor.anomalies and criteria.get("fail_on_anomaly", True):
            return False

        # Check required actions were performed
        if criteria.get("required_actions"):
            observed_types = {a["type"] for a in self.behavior_monitor.actions}
            required_set = set(criteria["required_actions"])
            if not required_set.issubset(observed_types):
                return False

        return True


# Scenario Library
class ScenarioLibrary:
    """Pre-defined simulation scenarios for different agent types."""

    @staticmethod
    def get_price_oracle_scenarios() -> List[SimulationScenario]:
        """Scenarios for price oracle agents."""
        return [
            SimulationScenario(
                name="normal_price_update",
                description="Verify oracle updates prices correctly under normal conditions",
                agent_type="price_oracle",
                steps=[
                    ScenarioStep(
                        time_offset_seconds=0,
                        market_data={"eth_price": 3000.0},
                        expected_action="fetch_price",
                    ),
                    ScenarioStep(
                        time_offset_seconds=30,
                        market_data={"eth_price": 3050.0},
                        expected_action="update_price",
                    ),
                ],
                success_criteria={
                    "expected_actions": ["fetch_price", "update_price"],
                    "min_scores": {"correctness": 0.8, "safety": 0.9},
                },
            ),
            SimulationScenario(
                name="api_failure_handling",
                description="Verify oracle handles API failures gracefully",
                agent_type="price_oracle",
                steps=[
                    ScenarioStep(
                        time_offset_seconds=0,
                        market_data={"eth_price": 3000.0},
                        inject_failure="api_timeout",
                        expected_action="error_handled",
                    )
                ],
                success_criteria={
                    "expected_actions": ["error_handled"],
                    "min_scores": {"resilience": 0.8, "safety": 1.0},
                },
            ),
        ]

    @staticmethod
    def get_arbitrage_scenarios() -> List[SimulationScenario]:
        """Scenarios for arbitrage bot agents."""
        return [
            SimulationScenario(
                name="profitable_arbitrage",
                description="Verify bot executes profitable arbitrage opportunity",
                agent_type="arbitrage",
                steps=[
                    ScenarioStep(
                        time_offset_seconds=0,
                        market_data={
                            "eth_price_dex_a": 3000.0,
                            "eth_price_dex_b": 3150.0,  # 5% spread
                        },
                        expected_action="execute_arbitrage",
                    )
                ],
                success_criteria={
                    "expected_actions": [
                        "detect_opportunity",
                        "calculate_profit",
                        "execute_arbitrage",
                    ],
                    "min_scores": {"correctness": 0.9, "efficiency": 0.7},
                },
            ),
            SimulationScenario(
                name="unprofitable_arbitrage",
                description="Verify bot avoids unprofitable opportunities",
                agent_type="arbitrage",
                steps=[
                    ScenarioStep(
                        time_offset_seconds=0,
                        market_data={
                            "eth_price_dex_a": 3000.0,
                            "eth_price_dex_b": 3003.0,  # 0.1% spread (below fees)
                            "gas_price": 100,  # High gas
                        },
                        expected_action="skip_opportunity",
                    )
                ],
                success_criteria={
                    "expected_actions": [
                        "detect_opportunity",
                        "calculate_profit",
                        "skip_opportunity",
                    ],
                    "min_scores": {"correctness": 0.9, "safety": 1.0},
                },
            ),
        ]
