"""Container-based backtesting engine using real market data and actual agent containers."""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .fetcher import MarketDataManager
from .registry import DataRegistry
from .container_backtester import ContainerBacktester
import docker


class MarketRegime(Enum):
    """Market condition classifications."""

    BULL_TREND = "bull_trend"
    BEAR_MARKET = "bear_market"
    HIGH_VOLATILITY = "high_volatility"
    SIDEWAYS = "sideways"


@dataclass
class Trade:
    """Individual trade record."""

    timestamp: datetime
    pair: str
    side: str  # 'buy' or 'sell'
    price: float
    amount: float
    pnl: Optional[float] = None
    strategy_signal: Optional[str] = None  # What triggered the trade


class PerformanceMetrics(BaseModel):
    """Standard trading performance metrics."""

    total_return: float
    annualized_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    calmar_ratio: float
    win_rate: float
    profit_factor: float
    total_trades: int
    avg_trade_duration: float  # in hours
    risk_adjusted_return: float  # New: Sharpe * Win Rate


class BacktestResult(BaseModel):
    """Complete backtest results."""

    agent_id: str
    start_date: str
    end_date: str
    initial_capital: float
    final_capital: float
    metrics: PerformanceMetrics
    regime_performance: Dict[str, Dict[str, float]]
    trades: List[Dict]  # Simplified for JSON serialization
    strategy_type: str
    data_quality: Dict[str, Any]  # New: Track data coverage




class RealBacktester:
    """Container-only backtesting engine using real market data and actual agent containers."""

    def __init__(self):
        self.console = Console()
        self.container_backtester = ContainerBacktester()
        self.docker_client = None
        
    def _verify_docker_image(self, agent_image: str) -> bool:
        """Verify that the Docker image exists."""
        try:
            if not self.docker_client:
                self.docker_client = docker.from_env()
            # Try to get the image
            self.docker_client.images.get(agent_image)
            return True
        except docker.errors.ImageNotFound:
            self.console.print(f"[red]Error: Docker image '{agent_image}' not found[/red]")
            self.console.print("[yellow]Please build or pull the agent image first[/yellow]")
            return False
        except Exception as e:
            self.console.print(f"[red]Docker error: {e}[/red]")
            return False

    def run(
        self,
        agent_image: str,
        start_date: str = "2024-05-01",
        end_date: str = "2024-05-31",
        strategy_type: str = "arbitrage",
        use_cached_regime: Optional[str] = None
    ) -> BacktestResult:
        """Run container-based backtest with real market data."""
        
        # Verify Docker image exists
        if not self._verify_docker_image(agent_image):
            raise ValueError(f"Cannot run backtest: Docker image '{agent_image}' not found")
        
        # Always use container-based backtesting for realistic results
        self.console.print(f"[blue]Starting container-based backtest for {agent_image}[/blue]")
        
        # Delegate to container backtester
        return self.container_backtester.run(
            agent_image,
            start_date=start_date,
            end_date=end_date,
            strategy_type=strategy_type
        )

    def display_results(self, result: BacktestResult):
        """Display container-based backtest results."""
        
        # Performance table
        table = Table(title=f"Container Backtest Results - {result.strategy_type.title()} Strategy")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        metrics = result.metrics
        table.add_row("Total Return", f"{metrics.total_return:.1%}")
        table.add_row("Annualized Return", f"{metrics.annualized_return:.1%}")
        table.add_row("Sharpe Ratio", f"{metrics.sharpe_ratio:.2f}")
        table.add_row("Sortino Ratio", f"{metrics.sortino_ratio:.2f}")
        table.add_row("Max Drawdown", f"{metrics.max_drawdown:.1%}")
        table.add_row("Calmar Ratio", f"{metrics.calmar_ratio:.2f}")
        table.add_row("Win Rate", f"{metrics.win_rate:.1%}")
        table.add_row("Profit Factor", f"{metrics.profit_factor:.2f}")
        table.add_row("Total Trades", str(metrics.total_trades))
        table.add_row("Avg Trade Duration", f"{metrics.avg_trade_duration:.1f} hours")
        table.add_row("Risk-Adjusted Return", f"{metrics.risk_adjusted_return:.2f}")
        
        self.console.print(table)
        
        # Trade summary
        if result.trades:
            self.console.print(f"\n[dim]Showing first {min(5, len(result.trades))} trades from actual agent execution:[/dim]")
            for i, trade in enumerate(result.trades[:5]):
                self.console.print(f"  {i+1}. {trade['timestamp']} - {trade['side']} {trade['amount']} @ ${trade['price']:.2f}")
        
        # Data quality info
        self.console.print(f"\n[dim]Data Quality: {result.data_quality['data_coverage']:.1%} coverage "
                          f"({result.data_quality['total_hours']} hours)[/dim]")
        
        # Note about container execution
        self.console.print("\n[green]✓ Results from actual agent container execution[/green]")