"""Enhanced backtesting engine using real market data."""

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


class RealMarketDataProvider:
    """Market data provider using real Binance data."""

    def __init__(self):
        self.console = Console()
        self.data_manager = MarketDataManager()
        self.registry = DataRegistry()
        
    def get_historical_prices(
        self, pair: str, start: datetime, end: datetime, interval: str = "1h"
    ) -> pd.DataFrame:
        """Get real historical price data."""
        # Convert datetime to string format
        start_str = start.strftime("%Y-%m-%d")
        end_str = end.strftime("%Y-%m-%d")
        
        # Fetch real data
        symbol = pair.replace("/", "")  # Convert BTC/USDT to BTCUSDT
        data = self.data_manager.fetch_market_data(
            symbols=[symbol],
            start_date=start_str,
            end_date=end_str,
            interval=interval
        )
        
        # Extract the dataframe for this symbol
        df = data.get(symbol, pd.DataFrame())
        
        return df
        
    def get_multiple_pairs(
        self, pairs: List[str], start: datetime, end: datetime
    ) -> Dict[str, pd.DataFrame]:
        """Get data for multiple trading pairs."""
        data = {}
        for pair in pairs:
            try:
                data[pair] = self.get_historical_prices(pair, start, end)
            except Exception as e:
                self.console.print(f"[yellow]Warning: Failed to load {pair}: {e}[/yellow]")
        return data


class StrategyEngine:
    """Enhanced strategy engine with real indicators."""
    
    def __init__(self, strategy_type: str = "arbitrage"):
        self.strategy_type = strategy_type
        self.position = {}  # Track positions per pair
        self.cash = 100000  # Starting capital
        self.trades = []
        self.indicators = {}  # Cache for technical indicators
        
    def calculate_indicators(self, df: pd.DataFrame, pair: str):
        """Calculate technical indicators for the strategy."""
        # Simple Moving Averages
        df['SMA_20'] = df['close'].rolling(window=20).mean()
        df['SMA_50'] = df['close'].rolling(window=50).mean()
        
        # Exponential Moving Average
        df['EMA_12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['EMA_26'] = df['close'].ewm(span=26, adjust=False).mean()
        
        # MACD
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['BB_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
        df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
        
        # Volume indicators
        df['volume_SMA'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_SMA']
        
        # Store in cache
        self.indicators[pair] = df
        
        return df
        
    def execute_arbitrage_strategy(
        self, row: pd.Series, pair: str, market_regime: MarketRegime
    ) -> Optional[Trade]:
        """Execute arbitrage strategy using real market inefficiencies."""
        
        # Simple cross-exchange arbitrage simulation
        # In reality, this would compare prices across exchanges
        
        # Look for price deviations from Bollinger Bands
        if pd.notna(row.get('BB_upper')) and pd.notna(row.get('BB_lower')):
            price = row['close']
            
            # Oversold - potential buy
            if price < row['BB_lower'] and row.get('RSI', 50) < 30:
                amount = min(0.1, self.cash / price * 0.02)  # 2% of capital
                if amount > 0:
                    trade = Trade(
                        timestamp=row.name,
                        pair=pair,
                        side="buy",
                        price=price,
                        amount=amount,
                        strategy_signal="BB_oversold"
                    )
                    self.cash -= amount * price * 1.001  # Include fees
                    self.position[pair] = self.position.get(pair, 0) + amount
                    return trade
                    
            # Overbought - potential sell
            elif price > row['BB_upper'] and row.get('RSI', 50) > 70:
                if self.position.get(pair, 0) > 0:
                    amount = min(0.1, self.position[pair])
                    trade = Trade(
                        timestamp=row.name,
                        pair=pair,
                        side="sell",
                        price=price,
                        amount=amount,
                        strategy_signal="BB_overbought"
                    )
                    self.cash += amount * price * 0.999  # Include fees
                    self.position[pair] -= amount
                    # Calculate PnL (simplified)
                    trade.pnl = amount * price * 0.002  # Mock 0.2% profit
                    return trade
                    
        return None
        
    def execute_momentum_strategy(
        self, row: pd.Series, pair: str, market_regime: MarketRegime
    ) -> Optional[Trade]:
        """Execute momentum/trend following strategy."""
        
        # Check if we have enough data
        if pd.isna(row.get('SMA_50')) or pd.isna(row.get('MACD')):
            return None
            
        price = row['close']
        
        # Bull signal: price above SMA50, MACD positive, increasing volume
        if (price > row['SMA_50'] and 
            row['MACD'] > row['MACD_signal'] and 
            row.get('volume_ratio', 1) > 1.2):
            
            # Enter position
            if self.position.get(pair, 0) == 0:
                amount = min(1.0, self.cash / price * 0.1)  # 10% of capital
                if amount > 0:
                    trade = Trade(
                        timestamp=row.name,
                        pair=pair,
                        side="buy",
                        price=price,
                        amount=amount,
                        strategy_signal="momentum_bull"
                    )
                    self.cash -= amount * price * 1.001
                    self.position[pair] = amount
                    return trade
                    
        # Exit signal: MACD crosses below signal line
        elif (row['MACD'] < row['MACD_signal'] and 
              self.position.get(pair, 0) > 0):
            
            amount = self.position[pair]
            trade = Trade(
                timestamp=row.name,
                pair=pair,
                side="sell",
                price=price,
                amount=amount,
                strategy_signal="momentum_exit"
            )
            self.cash += amount * price * 0.999
            self.position[pair] = 0
            return trade
            
        return None
        
    def execute_market_making_strategy(
        self, row: pd.Series, pair: str, market_regime: MarketRegime
    ) -> Optional[Trade]:
        """Execute market making strategy."""
        
        # Market makers profit from bid-ask spread
        # Simulate by placing orders around the mid price
        
        if pd.notna(row.get('BB_middle')):
            price = row['close']
            spread_pct = 0.001  # 0.1% spread
            
            # Only make markets in low volatility
            if market_regime == MarketRegime.SIDEWAYS:
                spread_pct = 0.0005  # Tighter spread in calm markets
            elif market_regime == MarketRegime.HIGH_VOLATILITY:
                spread_pct = 0.002  # Wider spread in volatile markets
                
            # Simulate filled orders (simplified)
            if np.random.random() < 0.3:  # 30% chance of fill
                # Randomly choose buy or sell
                if np.random.random() < 0.5:
                    # Buy order filled
                    amount = 0.05
                    trade = Trade(
                        timestamp=row.name,
                        pair=pair,
                        side="buy",
                        price=price * (1 - spread_pct),
                        amount=amount,
                        strategy_signal="market_making_bid"
                    )
                    self.cash -= trade.price * amount * 1.0001
                    self.position[pair] = self.position.get(pair, 0) + amount
                else:
                    # Sell order filled
                    if self.position.get(pair, 0) > 0:
                        amount = min(0.05, self.position[pair])
                        trade = Trade(
                            timestamp=row.name,
                            pair=pair,
                            side="sell",
                            price=price * (1 + spread_pct),
                            amount=amount,
                            strategy_signal="market_making_ask"
                        )
                        self.cash += trade.price * amount * 0.9999
                        self.position[pair] -= amount
                        # Profit from spread
                        trade.pnl = amount * price * spread_pct * 2
                        return trade
                        
        return None


class RealBacktester:
    """Enhanced backtesting engine with real market data."""

    def __init__(self):
        self.console = Console()
        self.data_provider = RealMarketDataProvider()

    def detect_market_regime(self, df: pd.DataFrame, lookback: int = 168) -> MarketRegime:
        """Detect market regime using real price data."""
        
        if len(df) < lookback:
            return MarketRegime.SIDEWAYS
            
        recent = df.tail(lookback)
        
        # Calculate returns
        returns = recent['close'].pct_change().dropna()
        
        # Calculate metrics
        avg_return = returns.mean()
        volatility = returns.std()
        
        # Price trend
        price_change = (recent['close'].iloc[-1] - recent['close'].iloc[0]) / recent['close'].iloc[0]
        
        # Volume trend
        volume_trend = recent['volume'].tail(24).mean() / recent['volume'].head(24).mean()
        
        # Classify regime
        if volatility > 0.02:  # High volatility (2% hourly)
            return MarketRegime.HIGH_VOLATILITY
        elif price_change > 0.05 and volume_trend > 1.2:  # 5% gain with volume
            return MarketRegime.BULL_TREND
        elif price_change < -0.05:  # 5% loss
            return MarketRegime.BEAR_MARKET
        else:
            return MarketRegime.SIDEWAYS

    def calculate_metrics(
        self,
        trades: List[Trade],
        initial_capital: float,
        final_capital: float,
        price_data: pd.DataFrame,
    ) -> PerformanceMetrics:
        """Calculate performance metrics using real data."""
        
        # Calculate returns series
        equity_curve = [initial_capital]
        current_equity = initial_capital
        
        for trade in trades:
            if trade.pnl:
                current_equity += trade.pnl
            equity_curve.append(current_equity)
            
        # Add final value
        if len(equity_curve) > 0:
            equity_curve[-1] = final_capital
            
        # Convert to series
        equity_series = pd.Series(equity_curve)
        returns = equity_series.pct_change().dropna()
        
        # Calculate metrics
        total_return = (final_capital - initial_capital) / initial_capital
        
        # Annualized return (assuming hourly data)
        hours = len(price_data)
        years = hours / (365 * 24)
        annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        
        # Sharpe ratio (assuming risk-free rate of 2%)
        if len(returns) > 0 and returns.std() > 0:
            excess_returns = returns - 0.02 / (365 * 24)  # Hourly risk-free rate
            sharpe_ratio = np.sqrt(365 * 24) * excess_returns.mean() / returns.std()
        else:
            sharpe_ratio = 0
            
        # Sortino ratio (downside deviation)
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0 and downside_returns.std() > 0:
            sortino_ratio = np.sqrt(365 * 24) * returns.mean() / downside_returns.std()
        else:
            sortino_ratio = sharpe_ratio * 1.5  # Approximation
            
        # Maximum drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Trade statistics
        winning_trades = [t for t in trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl and t.pnl < 0]
        
        win_rate = len(winning_trades) / len(trades) if trades else 0
        
        total_profit = sum(t.pnl for t in winning_trades if t.pnl)
        total_loss = abs(sum(t.pnl for t in losing_trades if t.pnl))
        profit_factor = total_profit / total_loss if total_loss > 0 else float("inf")
        
        # Calmar ratio
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # Average trade duration
        if len(trades) > 1:
            durations = []
            for i in range(1, len(trades)):
                duration = (trades[i].timestamp - trades[i-1].timestamp).total_seconds() / 3600
                durations.append(duration)
            avg_trade_duration = np.mean(durations) if durations else 0
        else:
            avg_trade_duration = 0
            
        # Risk-adjusted return
        risk_adjusted_return = sharpe_ratio * win_rate

        return PerformanceMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            calmar_ratio=calmar_ratio,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=len(trades),
            avg_trade_duration=avg_trade_duration,
            risk_adjusted_return=risk_adjusted_return
        )

    def run(
        self,
        agent_image: str,
        start_date: str = "2024-05-01",
        end_date: str = "2024-05-31",
        strategy_type: str = "arbitrage",
        use_cached_regime: Optional[str] = None
    ) -> BacktestResult:
        """Run backtest with real market data."""
        
        self.console.print(f"[blue]Starting backtest for {agent_image}[/blue]")
        self.console.print(f"Strategy: {strategy_type}")
        
        # Use regime dates if specified
        if use_cached_regime:
            registry = self.data_provider.registry
            if use_cached_regime in registry.registry.get("regime_windows", {}):
                regime_info = registry.registry["regime_windows"][use_cached_regime]
                start_date = regime_info["start"]
                end_date = regime_info["end"]
                self.console.print(
                    f"Using {use_cached_regime}: {regime_info['description']}"
                )
        
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        
        # Initialize strategy engine
        engine = StrategyEngine(strategy_type)
        initial_capital = engine.cash
        
        # Get market data
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("[cyan]Loading market data...", total=None)
            
            # Get data for multiple pairs if needed
            pairs = ["BTC/USDT", "ETH/USDT"] if strategy_type == "arbitrage" else ["BTC/USDT"]
            market_data = self.data_provider.get_multiple_pairs(pairs, start, end)
            
            # Use primary pair for main loop
            primary_pair = "BTC/USDT"
            price_data = market_data[primary_pair]
            
            progress.update(task, description="[cyan]Calculating indicators...")
            
            # Calculate indicators for all pairs
            for pair, data in market_data.items():
                engine.calculate_indicators(data, pair)
            
            progress.update(task, description="[cyan]Running backtest simulation...")
            
            # Track regime performance
            regime_performance = {
                regime.value: {"trades": 0, "pnl": 0, "hours": 0}
                for regime in MarketRegime
            }
            
            # Track data quality
            data_quality = {
                "total_hours": len(price_data),
                "missing_data": price_data['close'].isna().sum(),
                "data_coverage": 1 - (price_data['close'].isna().sum() / len(price_data))
            }
            
            # Run simulation
            for idx, row in price_data.iterrows():
                # Detect market regime
                lookback_data = price_data.loc[:idx]
                regime = self.detect_market_regime(lookback_data)
                regime_performance[regime.value]["hours"] += 1
                
                # Execute strategy (idx is already a timestamp since we set it as index)
                trade = None
                if strategy_type == "arbitrage":
                    trade = engine.execute_arbitrage_strategy(row, primary_pair, regime)
                elif strategy_type == "momentum":
                    trade = engine.execute_momentum_strategy(row, primary_pair, regime)
                elif strategy_type == "market_making":
                    trade = engine.execute_market_making_strategy(row, primary_pair, regime)
                
                if trade:
                    engine.trades.append(trade)
                    regime_performance[regime.value]["trades"] += 1
                    if trade.pnl:
                        regime_performance[regime.value]["pnl"] += trade.pnl
            
            progress.update(task, description="[cyan]Calculating performance metrics...")
        
        # Close all open positions at end price
        final_price = price_data.iloc[-1]['close']
        for pair, position in engine.position.items():
            if position > 0:
                engine.cash += position * final_price * 0.999  # Include fees
                
        # Calculate metrics
        metrics = self.calculate_metrics(
            engine.trades, initial_capital, engine.cash, price_data
        )
        
        # Calculate regime-specific returns
        for regime, stats in regime_performance.items():
            if stats["hours"] > 0:
                # Annualized return for this regime
                regime_return = (stats["pnl"] / initial_capital) * (8760 / stats["hours"])
                stats["annualized_return"] = regime_return
        
        return BacktestResult(
            agent_id=agent_image,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            final_capital=engine.cash,
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
                    "signal": t.strategy_signal,
                }
                for t in engine.trades[:100]  # Limit output
            ],
            strategy_type=strategy_type,
            data_quality=data_quality
        )

    def display_results(self, result: BacktestResult):
        """Display enhanced backtest results."""
        
        # Performance table
        table = Table(title=f"Backtest Results - {result.strategy_type.title()} Strategy")
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
        
        # Regime performance table
        regime_table = Table(title="Performance by Market Regime")
        regime_table.add_column("Regime", style="cyan")
        regime_table.add_column("Hours", style="yellow") 
        regime_table.add_column("Trades", style="yellow")
        regime_table.add_column("Total P&L", style="green")
        regime_table.add_column("Annualized Return", style="green")
        
        for regime, stats in result.regime_performance.items():
            if stats["hours"] > 0:
                regime_table.add_row(
                    regime.replace("_", " ").title(),
                    str(stats["hours"]),
                    str(stats["trades"]),
                    f"${stats['pnl']:.2f}",
                    f"{stats.get('annualized_return', 0):.1%}",
                )
        
        self.console.print(regime_table)
        
        # Data quality info
        self.console.print(f"\n[dim]Data Quality: {result.data_quality['data_coverage']:.1%} coverage "
                          f"({result.data_quality['total_hours']} hours)[/dim]")
        
        # Investment rating
        rating = self._calculate_investment_rating(metrics)
        self.console.print(f"\n[bold]Investment Rating: {rating}[/bold]")
        
    def _calculate_investment_rating(self, metrics: PerformanceMetrics) -> str:
        """Calculate investment grade rating based on metrics."""
        
        score = 0
        
        # Return score (0-40 points)
        if metrics.annualized_return > 0.5:  # 50%+
            score += 40
        elif metrics.annualized_return > 0.3:  # 30%+
            score += 30
        elif metrics.annualized_return > 0.15:  # 15%+
            score += 20
        elif metrics.annualized_return > 0:
            score += 10
            
        # Risk score (0-30 points)
        if metrics.sharpe_ratio > 2:
            score += 30
        elif metrics.sharpe_ratio > 1.5:
            score += 20
        elif metrics.sharpe_ratio > 1:
            score += 10
            
        # Consistency score (0-30 points)
        if metrics.win_rate > 0.6 and metrics.profit_factor > 2:
            score += 30
        elif metrics.win_rate > 0.5 and metrics.profit_factor > 1.5:
            score += 20
        elif metrics.win_rate > 0.4:
            score += 10
            
        # Determine rating
        if score >= 80:
            return "[green]A - Highly Recommended[/green]"
        elif score >= 60:
            return "[green]B - Recommended[/green]"
        elif score >= 40:
            return "[yellow]C - Moderate[/yellow]"
        elif score >= 20:
            return "[yellow]D - Risky[/yellow]"
        else:
            return "[red]F - Not Recommended[/red]"