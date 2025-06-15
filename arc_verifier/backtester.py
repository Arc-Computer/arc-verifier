"""Backtesting engine for trading agent verification."""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import random
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn


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


class MarketDataProvider:
    """Mock market data provider for PoC."""

    def get_historical_prices(
        self, pair: str, start: datetime, end: datetime
    ) -> List[Tuple[datetime, float]]:
        """Generate mock price data with realistic patterns."""
        prices = []
        current_price = 50000  # Starting BTC price
        current = start

        # Generate hourly data
        while current <= end:
            # Add some realistic volatility
            change = random.gauss(0, 0.01)  # 1% standard deviation

            # Add trend based on date (mock bull/bear cycles)
            days_since_start = (current - start).days
            trend = 0.0001 * (1 if days_since_start % 180 < 90 else -1)

            current_price *= 1 + change + trend
            current_price = max(current_price, 1000)  # Floor price

            prices.append((current, current_price))
            current += timedelta(hours=1)

        return prices


class AgentSimulator:
    """Simulates agent trading behavior."""

    def __init__(self, strategy_type: str = "arbitrage"):
        self.strategy_type = strategy_type
        self.position = 0
        self.cash = 100000  # Starting capital
        self.trades = []

    def execute_strategy(
        self, timestamp: datetime, price: float, market_regime: MarketRegime
    ) -> Optional[Trade]:
        """Execute trading strategy based on agent type."""

        if self.strategy_type == "arbitrage":
            # Mock arbitrage: trade when price deviates from moving average
            if random.random() < 0.1:  # 10% chance to find arbitrage
                # Execute both sides
                trade = Trade(
                    timestamp=timestamp,
                    pair="BTC/USDT",
                    side="buy" if self.position <= 0 else "sell",
                    price=price,
                    amount=0.1,
                )

                # Calculate instant profit (mock 0.1-0.5% arbitrage)
                profit = trade.amount * price * random.uniform(0.001, 0.005)
                trade.pnl = profit
                self.cash += profit

                return trade

        elif self.strategy_type == "momentum":
            # Trade based on trend
            if market_regime == MarketRegime.BULL_TREND and self.position <= 0:
                # Buy in bull market
                amount = min(0.5, self.cash / price * 0.1)  # Use 10% of capital
                if amount > 0:
                    trade = Trade(timestamp, "BTC/USDT", "buy", price, amount)
                    self.position += amount
                    self.cash -= amount * price
                    return trade

            elif market_regime == MarketRegime.BEAR_MARKET and self.position > 0:
                # Sell in bear market
                trade = Trade(timestamp, "BTC/USDT", "sell", price, self.position)
                self.cash += self.position * price
                self.position = 0
                return trade

        return None


class Backtester:
    """Main backtesting engine."""

    def __init__(self):
        self.console = Console()
        self.data_provider = MarketDataProvider()

    def detect_market_regime(
        self, prices: List[float], window: int = 24
    ) -> MarketRegime:
        """Simple regime detection based on price movements."""
        if len(prices) < window:
            return MarketRegime.SIDEWAYS

        recent = prices[-window:]
        returns = [
            (recent[i] - recent[i - 1]) / recent[i - 1] for i in range(1, len(recent))
        ]

        avg_return = sum(returns) / len(returns)
        volatility = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5

        # Classify regime
        if volatility > 0.02:  # 2% hourly volatility
            return MarketRegime.HIGH_VOLATILITY
        elif avg_return > 0.001:  # 0.1% hourly = strong trend
            return MarketRegime.BULL_TREND
        elif avg_return < -0.001:
            return MarketRegime.BEAR_MARKET
        else:
            return MarketRegime.SIDEWAYS

    def calculate_metrics(
        self,
        trades: List[Trade],
        initial_capital: float,
        final_capital: float,
        duration_days: int,
    ) -> PerformanceMetrics:
        """Calculate standard performance metrics."""

        total_return = (final_capital - initial_capital) / initial_capital
        annualized_return = (1 + total_return) ** (365 / duration_days) - 1

        # Calculate trade statistics
        winning_trades = [t for t in trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl and t.pnl < 0]

        win_rate = len(winning_trades) / len(trades) if trades else 0

        total_profit = sum(t.pnl for t in winning_trades if t.pnl)
        total_loss = abs(sum(t.pnl for t in losing_trades if t.pnl))
        profit_factor = total_profit / total_loss if total_loss > 0 else float("inf")

        # Mock other metrics for PoC
        sharpe_ratio = (
            annualized_return / 0.15 if annualized_return > 0 else 0
        )  # Assume 15% volatility

        return PerformanceMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sharpe_ratio * 1.2,  # Mock
            max_drawdown=-0.12,  # Mock 12% drawdown
            calmar_ratio=annualized_return / 0.12 if annualized_return > 0 else 0,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=len(trades),
            avg_trade_duration=4.5,  # Mock 4.5 hours average
        )

    def run(
        self,
        agent_image: str,
        start_date: str = "2024-01-01",
        end_date: str = "2024-12-31",
        strategy_type: str = "arbitrage",
    ) -> BacktestResult:
        """Run backtest simulation."""

        self.console.print(f"[blue]Starting backtest for {agent_image}[/blue]")

        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)

        # Initialize agent simulator
        agent = AgentSimulator(strategy_type)
        initial_capital = agent.cash

        # Get market data
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("[cyan]Fetching market data...", total=None)
            price_data = self.data_provider.get_historical_prices(
                "BTC/USDT", start, end
            )
            progress.update(task, description="[cyan]Running simulation...")

            # Track regime performance
            regime_performance = {
                regime.value: {"trades": 0, "pnl": 0, "hours": 0}
                for regime in MarketRegime
            }

            # Run simulation
            price_history = []
            for timestamp, price in price_data:
                price_history.append(price)

                # Detect current regime
                regime = self.detect_market_regime(
                    price_history[-168:]
                )  # 1 week window
                regime_performance[regime.value]["hours"] += 1

                # Execute strategy
                trade = agent.execute_strategy(timestamp, price, regime)
                if trade:
                    agent.trades.append(trade)
                    regime_performance[regime.value]["trades"] += 1
                    if trade.pnl:
                        regime_performance[regime.value]["pnl"] += trade.pnl

            progress.update(task, description="[cyan]Calculating metrics...")

        # Calculate final capital (close all positions at end price)
        final_price = price_data[-1][1]
        if agent.position > 0:
            agent.cash += agent.position * final_price

        # Calculate metrics
        duration_days = (end - start).days
        metrics = self.calculate_metrics(
            agent.trades, initial_capital, agent.cash, duration_days
        )

        # Calculate regime-specific returns
        for regime, stats in regime_performance.items():
            if stats["hours"] > 0:
                # Annualized return for this regime
                regime_return = (stats["pnl"] / initial_capital) * (
                    8760 / stats["hours"]
                )
                stats["annualized_return"] = regime_return

        return BacktestResult(
            agent_id=agent_image,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            final_capital=agent.cash,
            metrics=metrics,
            regime_performance=regime_performance,
            trades=[
                {
                    "timestamp": t.timestamp.isoformat(),
                    "pair": t.pair,
                    "side": t.side,
                    "price": t.price,
                    "amount": t.amount,
                    "pnl": t.pnl,
                }
                for t in agent.trades[:100]
            ],  # Limit to first 100 trades for output
        )

    def display_results(self, result: BacktestResult):
        """Display backtest results in terminal."""

        # Performance table
        table = Table(title="Backtest Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        metrics = result.metrics
        table.add_row("Total Return", f"{metrics.total_return:.1%}")
        table.add_row("Annualized Return", f"{metrics.annualized_return:.1%}")
        table.add_row("Sharpe Ratio", f"{metrics.sharpe_ratio:.2f}")
        table.add_row("Max Drawdown", f"{metrics.max_drawdown:.1%}")
        table.add_row("Win Rate", f"{metrics.win_rate:.1%}")
        table.add_row("Profit Factor", f"{metrics.profit_factor:.2f}")
        table.add_row("Total Trades", str(metrics.total_trades))

        self.console.print(table)

        # Regime performance table
        regime_table = Table(title="Performance by Market Regime")
        regime_table.add_column("Regime", style="cyan")
        regime_table.add_column("Hours", style="yellow")
        regime_table.add_column("Trades", style="yellow")
        regime_table.add_column("Annualized Return", style="green")

        for regime, stats in result.regime_performance.items():
            if stats["hours"] > 0:
                regime_table.add_row(
                    regime.replace("_", " ").title(),
                    str(stats["hours"]),
                    str(stats["trades"]),
                    f"{stats.get('annualized_return', 0):.1%}",
                )

        self.console.print(regime_table)
