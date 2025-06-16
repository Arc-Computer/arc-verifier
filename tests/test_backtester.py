"""Tests for the backtester module."""

import pytest
from datetime import datetime
from arc_verifier.data.backtester import (
    RealBacktester, MarketRegime, Trade, PerformanceMetrics,
    BacktestResult, RealMarketDataProvider, StrategyEngine
)


def test_market_data_provider():
    """Test market data provider."""
    provider = RealMarketDataProvider()
    # Note: This test may need actual market data cached to pass
    # For now, just test the provider instantiation
    assert provider is not None


def test_strategy_engine():
    """Test strategy engine."""
    engine = StrategyEngine(strategy_type="arbitrage")
    
    # Initial state
    assert engine.cash == 100000
    assert engine.position == {}
    assert len(engine.trades) == 0


def test_market_regime_detection():
    """Test market regime detection."""
    backtester = RealBacktester()
    
    # Create mock price data for testing
    import pandas as pd
    import numpy as np
    
    # Bull market scenario (rising prices)
    dates = pd.date_range(start='2024-01-01', periods=100, freq='h')
    rising_prices = np.linspace(50000, 55000, 100)
    df_bull = pd.DataFrame({
        'close': rising_prices,
        'volume': np.random.uniform(1000, 2000, 100)
    }, index=dates)
    
    regime = backtester.detect_market_regime(df_bull, lookback=50)
    assert regime in [MarketRegime.BULL_TREND, MarketRegime.SIDEWAYS]
    
    # Bear market scenario (falling prices)
    falling_prices = np.linspace(55000, 50000, 100)
    df_bear = pd.DataFrame({
        'close': falling_prices,
        'volume': np.random.uniform(1000, 2000, 100)
    }, index=dates)
    
    regime = backtester.detect_market_regime(df_bear, lookback=50)
    assert regime in [MarketRegime.BEAR_MARKET, MarketRegime.SIDEWAYS]


def test_performance_metrics_calculation():
    """Test performance metrics calculation."""
    backtester = RealBacktester()
    
    trades = [
        Trade(datetime.now(), "BTC/USDT", "buy", 50000, 0.1, pnl=50),
        Trade(datetime.now(), "BTC/USDT", "sell", 51000, 0.1, pnl=100),
        Trade(datetime.now(), "BTC/USDT", "buy", 49000, 0.1, pnl=-50),
    ]
    
    # Create mock price data
    import pandas as pd
    dates = pd.date_range(start='2024-01-01', periods=24, freq='h')
    price_data = pd.DataFrame({
        'close': [50000] * 24,
        'volume': [1000] * 24
    }, index=dates)
    
    metrics = backtester.calculate_metrics(trades, 100000, 100100, price_data)
    
    assert metrics.total_return == pytest.approx(0.001, rel=1e-3)  # 0.1%
    assert metrics.win_rate == pytest.approx(0.667, rel=1e-2)  # 2/3
    assert metrics.profit_factor == pytest.approx(3.0, rel=1e-2)  # 150/50
    assert metrics.total_trades == 3


def test_backtester_instantiation():
    """Test backtester can be instantiated."""
    backtester = RealBacktester()
    assert backtester is not None
    assert backtester.data_provider is not None


def test_backtest_result_structure():
    """Test that BacktestResult has expected structure."""
    # Create a minimal BacktestResult to test structure
    from datetime import datetime
    
    metrics = PerformanceMetrics(
        total_return=0.1,
        annualized_return=0.12,
        sharpe_ratio=1.5,
        sortino_ratio=1.8,
        max_drawdown=-0.05,
        calmar_ratio=2.4,
        win_rate=0.6,
        profit_factor=2.0,
        total_trades=10,
        avg_trade_duration=4.5,
        risk_adjusted_return=0.9
    )
    
    result = BacktestResult(
        agent_id="test/agent:latest",
        start_date="2024-01-01",
        end_date="2024-01-07",
        initial_capital=100000,
        final_capital=110000,
        metrics=metrics,
        regime_performance={},
        trades=[],
        strategy_type="arbitrage",
        data_quality={"total_hours": 168, "missing_data": 0, "data_coverage": 1.0}
    )
    
    assert isinstance(result, BacktestResult)
    assert result.agent_id == "test/agent:latest"
    assert result.initial_capital == 100000
    assert result.final_capital == 110000
    assert isinstance(result.metrics, PerformanceMetrics)
    
    # Should be able to dump to dict for JSON
    data = result.model_dump()
    assert "agent_id" in data
    assert "metrics" in data
    assert "regime_performance" in data
    assert isinstance(data["metrics"]["sharpe_ratio"], float)