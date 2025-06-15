"""Strategy verification module for detecting and analyzing trading strategies."""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass

import numpy as np
import pandas as pd
from pydantic import BaseModel
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..data.backtester import RealBacktester, BacktestResult, MarketRegime
from ..data.registry import DataRegistry
from ..security.audit import AuditLogger


class StrategyType(Enum):
    """Classification of trading strategy types."""
    
    ARBITRAGE = "arbitrage"
    MARKET_MAKING = "market_making"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    STATISTICAL_ARB = "statistical_arbitrage"
    HIGH_FREQUENCY = "high_frequency"
    UNKNOWN = "unknown"


@dataclass
class StrategySignature:
    """Signature patterns that identify a strategy type."""
    
    keywords: List[str]
    indicators: List[str]
    trading_patterns: List[str]
    risk_profile: Dict[str, str]


class StrategyProfile(BaseModel):
    """Complete profile of a detected strategy."""
    
    strategy_type: StrategyType
    confidence: float  # 0-1 confidence in classification
    detected_patterns: List[str]
    expected_behavior: Dict[str, str]
    optimal_conditions: List[str]
    risk_factors: List[str]
    capital_requirements: Dict[str, float]
    
    
class StrategyVerificationResult(BaseModel):
    """Result of strategy verification."""
    
    agent_id: str
    detected_strategy: str  # Changed from StrategyType to str for JSON serialization
    classification_confidence: float
    backtest_results: Dict[str, Any]  # Simplified BacktestResult
    performance_by_regime: Dict[str, Dict[str, float]]
    strategy_effectiveness: float  # 0-100 score
    verification_status: str  # "verified", "partial", "failed"
    warnings: List[str]
    recommendations: List[str]
    risk_score: float  # 0-100, higher is riskier
    

class StrategyClassifier:
    """Classifies trading strategies based on behavior patterns."""
    
    def __init__(self):
        self.console = Console()
        self.signatures = self._build_strategy_signatures()
        
    def _build_strategy_signatures(self) -> Dict[StrategyType, StrategySignature]:
        """Build signature patterns for each strategy type."""
        return {
            StrategyType.ARBITRAGE: StrategySignature(
                keywords=["arbitrage", "spread", "cross-exchange", "price difference"],
                indicators=["price_diff", "spread_calc", "exchange_price"],
                trading_patterns=["simultaneous_buy_sell", "quick_reversal", "neutral_position"],
                risk_profile={
                    "market_risk": "low",
                    "execution_risk": "high",
                    "capital_efficiency": "medium"
                }
            ),
            StrategyType.MARKET_MAKING: StrategySignature(
                keywords=["bid", "ask", "spread", "liquidity", "order book"],
                indicators=["bid_ask_spread", "order_depth", "volume_profile"],
                trading_patterns=["limit_orders", "both_sides", "inventory_management"],
                risk_profile={
                    "market_risk": "medium",
                    "inventory_risk": "high",
                    "capital_efficiency": "high"
                }
            ),
            StrategyType.MOMENTUM: StrategySignature(
                keywords=["trend", "momentum", "breakout", "continuation"],
                indicators=["SMA", "EMA", "MACD", "RSI", "volume"],
                trading_patterns=["trend_following", "position_scaling", "trailing_stop"],
                risk_profile={
                    "market_risk": "high",
                    "whipsaw_risk": "high",
                    "capital_efficiency": "low"
                }
            ),
            StrategyType.MEAN_REVERSION: StrategySignature(
                keywords=["reversion", "overbought", "oversold", "bollinger"],
                indicators=["BB", "RSI", "standard_deviation", "z_score"],
                trading_patterns=["counter_trend", "fade_extreme", "range_bound"],
                risk_profile={
                    "market_risk": "medium",
                    "breakout_risk": "high",
                    "capital_efficiency": "medium"
                }
            )
        }
        
    def analyze_trading_behavior(self, backtest_result: BacktestResult) -> Dict[str, Any]:
        """Analyze actual trading behavior from backtest."""
        behavior = {
            "trade_frequency": len(backtest_result.trades) / 
                              ((datetime.fromisoformat(backtest_result.end_date) - 
                                datetime.fromisoformat(backtest_result.start_date)).days + 1),
            "avg_holding_period": backtest_result.metrics.avg_trade_duration,
            "position_reversal_rate": 0,
            "uses_both_sides": False,
            "trade_clustering": 0,
            "signal_patterns": []
        }
        
        # Analyze trade patterns
        trades = backtest_result.trades
        if len(trades) > 1:
            # Check for position reversals (characteristic of mean reversion/arbitrage)
            reversals = 0
            for i in range(1, len(trades)):
                if trades[i]["side"] != trades[i-1]["side"]:
                    reversals += 1
            behavior["position_reversal_rate"] = reversals / (len(trades) - 1)
            
            # Check if uses both buy and sell
            sides = set(t["side"] for t in trades)
            behavior["uses_both_sides"] = len(sides) == 2
            
            # Extract unique signal patterns
            signals = set(t.get("signal", "") for t in trades if t.get("signal"))
            behavior["signal_patterns"] = list(signals)
            
        return behavior
        
    def classify_strategy(self, 
                         backtest_result: BacktestResult,
                         agent_metadata: Optional[Dict] = None) -> Tuple[StrategyType, float]:
        """Classify strategy type based on trading behavior and patterns."""
        
        behavior = self.analyze_trading_behavior(backtest_result)
        scores = {}
        
        # Score each strategy type based on behavior
        for strategy_type, signature in self.signatures.items():
            score = 0.0
            matches = []
            
            # Check signal patterns
            if behavior["signal_patterns"]:
                for signal in behavior["signal_patterns"]:
                    signal_lower = signal.lower()
                    # Check keywords
                    for keyword in signature.keywords:
                        if keyword in signal_lower:
                            score += 0.2
                            matches.append(f"keyword:{keyword}")
                    # Check indicators
                    for indicator in signature.indicators:
                        if indicator.lower() in signal_lower:
                            score += 0.3
                            matches.append(f"indicator:{indicator}")
                            
            # Behavioral scoring
            if strategy_type == StrategyType.ARBITRAGE:
                if behavior["avg_holding_period"] < 1:  # Very short holding
                    score += 0.3
                if behavior["position_reversal_rate"] > 0.7:
                    score += 0.2
                if "arbitrage" in str(behavior["signal_patterns"]):
                    score += 0.5
                    
            elif strategy_type == StrategyType.MARKET_MAKING:
                if behavior["uses_both_sides"]:
                    score += 0.3
                if behavior["trade_frequency"] > 10:  # High frequency
                    score += 0.2
                if "market_making" in str(behavior["signal_patterns"]):
                    score += 0.5
                    
            elif strategy_type == StrategyType.MOMENTUM:
                if behavior["avg_holding_period"] > 5:  # Longer holding
                    score += 0.2
                if behavior["position_reversal_rate"] < 0.3:  # Trend following
                    score += 0.2
                if any("momentum" in s or "trend" in s for s in behavior["signal_patterns"]):
                    score += 0.4
                    
            elif strategy_type == StrategyType.MEAN_REVERSION:
                if behavior["position_reversal_rate"] > 0.5:
                    score += 0.3
                if any("oversold" in s or "overbought" in s for s in behavior["signal_patterns"]):
                    score += 0.4
                    
            scores[strategy_type] = min(score, 1.0)  # Cap at 1.0
            
        # Find best match
        if scores:
            best_match = max(scores.items(), key=lambda x: x[1])
            if best_match[1] > 0.3:  # Minimum confidence threshold
                return best_match[0], best_match[1]
                
        return StrategyType.UNKNOWN, 0.0
        

class StrategyAnalyzer:
    """Analyzes strategy effectiveness and risk profile."""
    
    def __init__(self):
        self.console = Console()
        self.optimal_conditions = {
            StrategyType.ARBITRAGE: {
                "market_regimes": [MarketRegime.SIDEWAYS, MarketRegime.HIGH_VOLATILITY],
                "min_capital": 10000,
                "ideal_capital": 50000,
                "risk_tolerance": "low"
            },
            StrategyType.MARKET_MAKING: {
                "market_regimes": [MarketRegime.SIDEWAYS],
                "min_capital": 25000,
                "ideal_capital": 100000,
                "risk_tolerance": "medium"
            },
            StrategyType.MOMENTUM: {
                "market_regimes": [MarketRegime.BULL_TREND],
                "min_capital": 5000,
                "ideal_capital": 25000,
                "risk_tolerance": "high"
            },
            StrategyType.MEAN_REVERSION: {
                "market_regimes": [MarketRegime.SIDEWAYS, MarketRegime.HIGH_VOLATILITY],
                "min_capital": 10000,
                "ideal_capital": 50000,
                "risk_tolerance": "medium"
            }
        }
        
    def calculate_effectiveness_score(self,
                                    strategy_type: StrategyType,
                                    backtest_result: BacktestResult,
                                    regime_performance: Dict) -> float:
        """Calculate how effectively the strategy performs its intended function."""
        
        score = 50.0  # Base score
        
        # Performance metrics contribution (0-30 points)
        metrics = backtest_result.metrics
        if metrics.sharpe_ratio > 2:
            score += 15
        elif metrics.sharpe_ratio > 1:
            score += 10
        elif metrics.sharpe_ratio > 0.5:
            score += 5
            
        if metrics.win_rate > 0.6:
            score += 10
        elif metrics.win_rate > 0.5:
            score += 7
        elif metrics.win_rate > 0.4:
            score += 3
            
        if abs(metrics.max_drawdown) < 0.1:
            score += 5
        elif abs(metrics.max_drawdown) < 0.2:
            score += 3
            
        # Strategy-specific effectiveness (0-20 points)
        if strategy_type != StrategyType.UNKNOWN:
            optimal = self.optimal_conditions.get(strategy_type, {})
            optimal_regimes = optimal.get("market_regimes", [])
            
            # Check if performs well in expected regimes
            regime_scores = []
            for regime_name, stats in regime_performance.items():
                if stats["hours"] > 0:
                    regime = MarketRegime(regime_name)
                    if regime in optimal_regimes:
                        # Should perform well in optimal regimes
                        if stats.get("annualized_return", 0) > 0.1:
                            regime_scores.append(10)
                        elif stats.get("annualized_return", 0) > 0:
                            regime_scores.append(5)
                    else:
                        # Should at least not lose money in other regimes
                        if stats.get("annualized_return", 0) > -0.05:
                            regime_scores.append(5)
                            
            if regime_scores:
                score += sum(regime_scores) / len(regime_scores)
                
        return min(score, 100)  # Cap at 100
        
    def calculate_risk_score(self,
                           strategy_type: StrategyType,
                           backtest_result: BacktestResult) -> float:
        """Calculate risk score (0-100, higher is riskier)."""
        
        risk_score = 0.0
        metrics = backtest_result.metrics
        
        # Drawdown risk (0-30 points)
        drawdown_risk = abs(metrics.max_drawdown) * 100
        risk_score += min(drawdown_risk, 30)
        
        # Volatility risk (0-20 points)
        if metrics.sharpe_ratio > 0:
            volatility_risk = 20 / metrics.sharpe_ratio
        else:
            volatility_risk = 20
        risk_score += min(volatility_risk, 20)
        
        # Win rate risk (0-20 points)
        win_rate_risk = (1 - metrics.win_rate) * 20
        risk_score += win_rate_risk
        
        # Strategy-specific risks (0-30 points)
        strategy_risks = {
            StrategyType.MOMENTUM: 30,  # High market risk
            StrategyType.MARKET_MAKING: 20,  # Inventory risk
            StrategyType.ARBITRAGE: 10,  # Execution risk
            StrategyType.MEAN_REVERSION: 15,  # Breakout risk
            StrategyType.UNKNOWN: 30  # Unknown strategy is risky
        }
        risk_score += strategy_risks.get(strategy_type, 20)
        
        return min(risk_score, 100)
        
    def generate_recommendations(self,
                               strategy_type: StrategyType,
                               backtest_result: BacktestResult,
                               effectiveness_score: float,
                               risk_score: float) -> List[str]:
        """Generate actionable recommendations."""
        
        recommendations = []
        metrics = backtest_result.metrics
        
        # Capital recommendations
        if strategy_type in self.optimal_conditions:
            optimal = self.optimal_conditions[strategy_type]
            recommendations.append(
                f"Recommended capital: ${optimal['ideal_capital']:,} "
                f"(minimum: ${optimal['min_capital']:,})"
            )
            
        # Performance recommendations
        if metrics.sharpe_ratio < 1:
            recommendations.append("Consider improving risk-adjusted returns through better entry/exit timing")
            
        if metrics.win_rate < 0.4:
            recommendations.append("Low win rate detected - review strategy logic and market conditions")
            
        if abs(metrics.max_drawdown) > 0.2:
            recommendations.append("High drawdown risk - implement better risk management and position sizing")
            
        # Strategy-specific recommendations
        if strategy_type == StrategyType.MOMENTUM:
            recommendations.append("Best suited for trending markets - consider pausing during sideways periods")
        elif strategy_type == StrategyType.ARBITRAGE:
            recommendations.append("Monitor execution latency closely - profits depend on speed")
        elif strategy_type == StrategyType.MARKET_MAKING:
            recommendations.append("Ensure adequate capital for inventory management")
            
        # Risk recommendations
        if risk_score > 70:
            recommendations.append("HIGH RISK: Consider reducing position sizes or adding hedging")
        elif risk_score > 50:
            recommendations.append("MODERATE RISK: Monitor closely and set strict stop losses")
            
        return recommendations
        

class StrategyVerifier:
    """Main strategy verification orchestrator."""
    
    def __init__(self):
        self.console = Console()
        self.classifier = StrategyClassifier()
        self.analyzer = StrategyAnalyzer()
        self.backtester = RealBacktester()
        self.audit_logger = AuditLogger()
        self.registry = DataRegistry()
        
    def verify_strategy(self,
                       agent_image: str,
                       start_date: Optional[str] = None,
                       end_date: Optional[str] = None,
                       use_regime: Optional[str] = None) -> StrategyVerificationResult:
        """Perform complete strategy verification."""
        
        self.console.print(f"\n[blue]Starting strategy verification for {agent_image}[/blue]")
        
        # Run backtests with different strategies to find best match
        strategy_results = {}
        
        with self.console.status("[cyan]Testing different strategy types..."):
            for strategy in ["arbitrage", "momentum", "market_making"]:
                try:
                    result = self.backtester.run(
                        agent_image,
                        start_date=start_date or "2024-10-01",
                        end_date=end_date or "2024-10-07",
                        strategy_type=strategy,
                        use_cached_regime=use_regime
                    )
                    strategy_results[strategy] = result
                except Exception as e:
                    self.console.print(f"[yellow]Warning: Failed to test {strategy}: {e}[/yellow]")
                    
        if not strategy_results:
            raise ValueError("Failed to run any strategy backtests")
            
        # Find best performing strategy
        best_strategy = max(
            strategy_results.items(),
            key=lambda x: x[1].metrics.sharpe_ratio
        )
        strategy_name, backtest_result = best_strategy
        
        # Classify strategy
        detected_type, confidence = self.classifier.classify_strategy(backtest_result)
        
        # If classification doesn't match backtest strategy, use backtest
        if detected_type == StrategyType.UNKNOWN:
            detected_type = StrategyType(strategy_name)
            confidence = 0.8  # High confidence since it performed well
            
        self.console.print(f"Detected strategy: [green]{detected_type.value}[/green] "
                          f"(confidence: {confidence:.1%})")
        
        # Calculate effectiveness and risk
        effectiveness_score = self.analyzer.calculate_effectiveness_score(
            detected_type,
            backtest_result,
            backtest_result.regime_performance
        )
        
        risk_score = self.analyzer.calculate_risk_score(detected_type, backtest_result)
        
        # Generate recommendations
        recommendations = self.analyzer.generate_recommendations(
            detected_type,
            backtest_result,
            effectiveness_score,
            risk_score
        )
        
        # Determine verification status
        if effectiveness_score > 70 and confidence > 0.7:
            verification_status = "verified"
        elif effectiveness_score > 50 or confidence > 0.5:
            verification_status = "partial"
        else:
            verification_status = "failed"
            
        # Build warnings
        warnings = []
        if risk_score > 70:
            warnings.append("High risk strategy - exercise caution")
        if backtest_result.metrics.max_drawdown < -0.3:
            warnings.append("Significant drawdown risk detected")
        if backtest_result.metrics.total_trades < 10:
            warnings.append("Limited trading data - results may not be representative")
            
        # Create result
        result = StrategyVerificationResult(
            agent_id=agent_image,
            detected_strategy=detected_type.value,  # Convert enum to string
            classification_confidence=confidence,
            backtest_results={
                "metrics": backtest_result.metrics.dict(),
                "total_return": backtest_result.metrics.total_return,
                "sharpe_ratio": backtest_result.metrics.sharpe_ratio,
                "max_drawdown": backtest_result.metrics.max_drawdown
            },
            performance_by_regime=backtest_result.regime_performance,
            strategy_effectiveness=effectiveness_score,
            verification_status=verification_status,
            warnings=warnings,
            recommendations=recommendations,
            risk_score=risk_score
        )
        
        # Log for audit trail
        self.audit_logger.log_action(
            action="strategy_verification",
            details={
                "agent_id": agent_image,
                "detected_strategy": detected_type.value,
                "confidence": confidence,
                "effectiveness_score": effectiveness_score,
                "risk_score": risk_score,
                "status": verification_status
            }
        )
        
        return result
        
    def display_verification_report(self, result: StrategyVerificationResult):
        """Display comprehensive verification report."""
        
        # Main results panel
        status_color = {
            "verified": "green",
            "partial": "yellow", 
            "failed": "red"
        }[result.verification_status]
        
        panel_content = f"""
[bold]Strategy Type:[/bold] {result.detected_strategy}
[bold]Classification Confidence:[/bold] {result.classification_confidence:.1%}
[bold]Effectiveness Score:[/bold] {result.strategy_effectiveness:.0f}/100
[bold]Risk Score:[/bold] {result.risk_score:.0f}/100
[bold]Verification Status:[/bold] [{status_color}]{result.verification_status.upper()}[/{status_color}]
"""
        
        self.console.print(Panel(
            panel_content,
            title=f"Strategy Verification Report - {result.agent_id}",
            border_style="blue"
        ))
        
        # Performance summary
        if result.backtest_results:
            perf_table = Table(title="Backtest Performance")
            perf_table.add_column("Metric", style="cyan")
            perf_table.add_column("Value", style="green")
            
            perf_table.add_row("Total Return", f"{result.backtest_results['total_return']:.1%}")
            perf_table.add_row("Sharpe Ratio", f"{result.backtest_results['sharpe_ratio']:.2f}")
            perf_table.add_row("Max Drawdown", f"{result.backtest_results['max_drawdown']:.1%}")
            
            self.console.print(perf_table)
            
        # Regime performance
        regime_table = Table(title="Performance by Market Regime")
        regime_table.add_column("Regime", style="cyan")
        regime_table.add_column("Hours", style="yellow")
        regime_table.add_column("Trades", style="yellow")
        regime_table.add_column("Return", style="green")
        
        for regime, stats in result.performance_by_regime.items():
            if stats["hours"] > 0:
                regime_table.add_row(
                    regime.replace("_", " ").title(),
                    str(stats["hours"]),
                    str(stats["trades"]),
                    f"{stats.get('annualized_return', 0):.1%}"
                )
                
        self.console.print(regime_table)
        
        # Warnings
        if result.warnings:
            self.console.print("\n[bold yellow]⚠️  Warnings:[/bold yellow]")
            for warning in result.warnings:
                self.console.print(f"  • {warning}")
                
        # Recommendations
        if result.recommendations:
            self.console.print("\n[bold cyan]💡 Recommendations:[/bold cyan]")
            for rec in result.recommendations:
                self.console.print(f"  • {rec}")
                
    def compare_strategies(self, results: List[StrategyVerificationResult]) -> Table:
        """Compare multiple strategy verification results."""
        
        table = Table(title="Strategy Comparison")
        table.add_column("Agent", style="cyan")
        table.add_column("Strategy", style="yellow")
        table.add_column("Effectiveness", style="green")
        table.add_column("Risk", style="red")
        table.add_column("Sharpe", style="blue")
        table.add_column("Status", style="bold")
        
        # Sort by effectiveness score
        sorted_results = sorted(
            results,
            key=lambda x: x.strategy_effectiveness,
            reverse=True
        )
        
        for result in sorted_results:
            status_style = {
                "verified": "green",
                "partial": "yellow",
                "failed": "red"
            }[result.verification_status]
            
            table.add_row(
                result.agent_id[:20] + "..." if len(result.agent_id) > 20 else result.agent_id,
                result.detected_strategy,
                f"{result.strategy_effectiveness:.0f}",
                f"{result.risk_score:.0f}",
                f"{result.backtest_results.get('sharpe_ratio', 0):.2f}",
                f"[{status_style}]{result.verification_status}[/{status_style}]"
            )
            
        return table