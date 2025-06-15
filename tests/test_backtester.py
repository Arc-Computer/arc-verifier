"""Tests for the backtester module."""

import pytest
from datetime import datetime
from arc_verifier.backtester import (
    Backtester, MarketRegime, Trade, PerformanceMetrics,
    BacktestResult, MarketDataProvider, AgentSimulator
)


def test_market_data_provider():
    """Test market data generation."""
    provider = MarketDataProvider()
    start = datetime(2024, 1, 1)
    end = datetime(2024, 1, 7)  # One week
    
    prices = provider.get_historical_prices("BTC/USDT", start, end)
    
    # Should have hourly data (at least 144 hours for 6 days)
    assert len(prices) >= 144  # At least 6 days of hourly data
    
    # Check price structure
    for timestamp, price in prices:
        assert isinstance(timestamp, datetime)
        assert isinstance(price, float)
        assert price > 0


def test_agent_simulator_arbitrage():
    """Test arbitrage strategy simulator."""
    simulator = AgentSimulator(strategy_type="arbitrage")
    
    # Initial state
    assert simulator.cash == 100000
    assert simulator.position == 0
    assert len(simulator.trades) == 0
    
    # Execute strategy multiple times
    trades_executed = 0
    for i in range(100):
        trade = simulator.execute_strategy(
            datetime.now(), 50000, MarketRegime.HIGH_VOLATILITY
        )
        if trade:
            trades_executed += 1
            assert trade.pnl > 0  # Arbitrage should always be profitable
    
    # Should have executed some trades
    assert trades_executed > 0
    assert simulator.cash > 100000  # Should have made profit


def test_agent_simulator_momentum():
    """Test momentum strategy simulator."""
    simulator = AgentSimulator(strategy_type="momentum")
    
    # Buy in bull market
    trade = simulator.execute_strategy(
        datetime.now(), 50000, MarketRegime.BULL_TREND
    )
    # Might or might not trade depending on position
    
    # If we have position, should sell in bear market
    if simulator.position > 0:
        trade = simulator.execute_strategy(
            datetime.now(), 50000, MarketRegime.BEAR_MARKET
        )
        assert trade is not None
        assert trade.side == "sell"


def test_market_regime_detection():
    """Test market regime detection."""
    backtester = Backtester()
    
    # Bull market scenario (rising prices)
    prices = [100, 101, 102, 103, 104, 105, 106, 107]
    regime = backtester.detect_market_regime(prices, window=len(prices))
    assert regime == MarketRegime.BULL_TREND
    
    # Bear market scenario (falling prices)
    prices = [100, 99, 98, 97, 96, 95, 94, 93]
    regime = backtester.detect_market_regime(prices, window=len(prices))
    assert regime == MarketRegime.BEAR_MARKET
    
    # High volatility scenario
    prices = [100, 110, 90, 115, 85, 120, 80, 125]
    regime = backtester.detect_market_regime(prices, window=len(prices))
    assert regime == MarketRegime.HIGH_VOLATILITY


def test_performance_metrics_calculation():
    """Test performance metrics calculation."""
    backtester = Backtester()
    
    trades = [
        Trade(datetime.now(), "BTC/USDT", "buy", 50000, 0.1, pnl=50),
        Trade(datetime.now(), "BTC/USDT", "sell", 51000, 0.1, pnl=100),
        Trade(datetime.now(), "BTC/USDT", "buy", 49000, 0.1, pnl=-50),
    ]
    
    metrics = backtester.calculate_metrics(trades, 100000, 100100, 30)
    
    assert metrics.total_return == pytest.approx(0.001, rel=1e-3)  # 0.1%
    assert metrics.win_rate == pytest.approx(0.667, rel=1e-2)  # 2/3
    assert metrics.profit_factor == pytest.approx(3.0, rel=1e-2)  # 150/50
    assert metrics.total_trades == 3


def test_backtester_run():
    """Test full backtest run."""
    backtester = Backtester()
    
    result = backtester.run(
        "test/agent:latest",
        start_date="2024-01-01",
        end_date="2024-01-07",  # One week
        strategy_type="arbitrage"
    )
    
    assert isinstance(result, BacktestResult)
    assert result.agent_id == "test/agent:latest"
    assert result.initial_capital == 100000
    assert result.final_capital >= 100000  # Should not lose money with arbitrage
    assert isinstance(result.metrics, PerformanceMetrics)
    
    # Check regime performance tracking
    assert len(result.regime_performance) == 4  # All regimes
    for regime, stats in result.regime_performance.items():
        assert "trades" in stats
        assert "pnl" in stats
        assert "hours" in stats


def test_backtest_result_serialization():
    """Test that backtest results can be serialized to JSON."""
    backtester = Backtester()
    
    result = backtester.run(
        "test/agent:latest",
        start_date="2024-01-01",
        end_date="2024-01-02",
        strategy_type="momentum"
    )
    
    # Should be able to dump to dict for JSON
    data = result.model_dump()
    
    assert "agent_id" in data
    assert "metrics" in data
    assert "regime_performance" in data
    assert isinstance(data["metrics"]["sharpe_ratio"], float)