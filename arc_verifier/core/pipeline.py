"""Verification pipeline coordinator that ensures proper phase ordering.

This module coordinates the verification phases to ensure LLM intelligence
informs behavioral testing, as per executive feedback.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..security import DockerScanner, TEEValidator
from ..analysis import Benchmarker, LLMJudge
from ..utils.simulator import AgentSimulator, ScenarioLibrary, SimulationScenario


class AgentStrategy(Enum):
    """Detected agent strategies from LLM analysis."""
    ARBITRAGE = "arbitrage"
    MARKET_MAKING = "market_making"
    PRICE_ORACLE = "price_oracle"
    MOMENTUM = "momentum"
    UNKNOWN = "unknown"


@dataclass
class VerificationContext:
    """Context passed between verification phases."""
    image: str
    security_result: Dict
    llm_result: Optional[Dict] = None
    detected_strategy: AgentStrategy = AgentStrategy.UNKNOWN
    risk_flags: List[str] = None
    

class VerificationPipeline:
    """Coordinates verification phases in the correct order."""
    
    def __init__(self, console=None):
        self.console = console
        self.scanner = DockerScanner()
        self.validator = TEEValidator()
        self.benchmarker = Benchmarker()
        
    def run_phase1_security(self, image: str) -> Dict:
        """Phase 1: Security & SCA (Software Composition Analysis)."""
        scan_result = self.scanner.scan(image)
        return scan_result
        
    def run_phase2_llm_intelligence(self, 
                                   scan_result: Dict, 
                                   llm_provider: str = "anthropic",
                                   tier: str = "medium") -> Tuple[Optional[Dict], AgentStrategy]:
        """Phase 2: LLM Intelligence Analysis.
        
        Returns:
            Tuple of (llm_result, detected_strategy)
        """
        try:
            llm_judge = LLMJudge(primary_provider=llm_provider)
            llm_result = llm_judge.evaluate_agent(
                image_data=scan_result,
                market_context={"tier": tier, "timestamp": scan_result.get('timestamp')}
            )
            
            # Extract detected strategy for Phase 3A
            detected_strategy = self._extract_strategy(llm_result)
            
            return llm_result, detected_strategy
        except Exception as e:
            if self.console:
                self.console.print(f"[yellow]LLM analysis failed: {e}[/yellow]")
            return None, AgentStrategy.UNKNOWN
    
    def run_phase3a_behavioral(self, 
                              image: str,
                              detected_strategy: AgentStrategy) -> Dict:
        """Phase 3A: Synthetic Behavior Tests.
        
        Uses LLM-detected strategy to select appropriate scenarios.
        """
        simulator = AgentSimulator()
        
        # Select scenarios based on detected strategy
        scenarios = self._select_scenarios_for_strategy(detected_strategy)
        
        # Run targeted simulations
        results = []
        for scenario in scenarios:
            result = simulator.run_simulation(image, scenario)
            results.append(result)
            
        # Aggregate behavioral score
        behavior_score = self._calculate_behavior_score(results)
        
        return {
            "simulation_results": results,
            "behavior_score": behavior_score,
            "scenarios_tested": len(scenarios)
        }
    
    def run_phase3b_performance(self, 
                               image: str,
                               detected_strategy: AgentStrategy) -> Dict:
        """Phase 3B: Historical Capability Replay.
        
        To be implemented with real data integration.
        """
        # Placeholder for Phase 3B implementation
        return {
            "performance_score": 0,
            "strategy_verified": False,
            "regime_performance": {},
            "percentile_rank": 50
        }
    
    def _extract_strategy(self, llm_result) -> AgentStrategy:
        """Extract detected strategy from LLM analysis."""
        if not llm_result:
            return AgentStrategy.UNKNOWN
            
        intent = llm_result.intent_classification
        strategy_map = {
            "arbitrage": AgentStrategy.ARBITRAGE,
            "market_making": AgentStrategy.MARKET_MAKING,
            "price_oracle": AgentStrategy.PRICE_ORACLE,
            "momentum": AgentStrategy.MOMENTUM,
        }
        
        primary_strategy = intent.primary_strategy.lower()
        return strategy_map.get(primary_strategy, AgentStrategy.UNKNOWN)
    
    def _select_scenarios_for_strategy(self, 
                                      strategy: AgentStrategy) -> List[SimulationScenario]:
        """Select appropriate test scenarios based on detected strategy."""
        if strategy == AgentStrategy.ARBITRAGE:
            return ScenarioLibrary.get_arbitrage_scenarios()
        elif strategy == AgentStrategy.PRICE_ORACLE:
            return ScenarioLibrary.get_price_oracle_scenarios()
        elif strategy == AgentStrategy.MARKET_MAKING:
            # TODO: Add market making scenarios
            return ScenarioLibrary.get_arbitrage_scenarios()[:1]  # Use subset for now
        else:
            # Unknown strategy - run basic scenarios from each type
            scenarios = []
            scenarios.extend(ScenarioLibrary.get_price_oracle_scenarios()[:1])
            scenarios.extend(ScenarioLibrary.get_arbitrage_scenarios()[:1])
            return scenarios
    
    def _calculate_behavior_score(self, results: List) -> float:
        """Calculate aggregate behavior score from simulation results."""
        if not results:
            return 0.0
            
        passed = sum(1 for r in results if r.passed)
        total = len(results)
        
        # Basic scoring: percentage passed with bonus for consistency
        base_score = (passed / total) * 30  # Max 30 points
        
        # Consistency bonus
        if passed == total:
            base_score += 5
            
        return base_score