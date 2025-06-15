# Phase 3B: Simplified Performance Verification Plan

## Executive Summary

Phase 3B completes Arc-Verifier's value proposition by adding **real performance verification** using historical market data. This pragmatic approach focuses on verifying that agents do what they claim, not predicting future profits.

## Core Design Principles

1. **Simplicity First**: Enhance existing architecture, don't replace it
2. **Minimal Dependencies**: Just data fetching, no complex RL frameworks  
3. **Fast to Value**: 3-week implementation, not months
4. **Verification, Not Prediction**: "Does it arbitrage?" not "Will it profit?"

## Week 1: Real Data Integration

### Objective
Replace mock data with real historical crypto prices from public sources.

### Implementation
```python
# arc_verifier/data_providers.py (NEW FILE)
class BinanceDataProvider:
    """Fetches historical data from Binance public CSV files."""
    
    def fetch_regime_data(self, regime: str) -> pd.DataFrame:
        # Download 30-day snapshots for each regime:
        # - Bull: Aug 2021 (BTC: 30k→50k)
        # - Bear: May 2022 (Terra/Luna collapse)
        # - Volatile: March 2020 (COVID crash)
        # - Sideways: Feb 2024 (recent consolidation)

class CoinbaseDataProvider:
    """Backup data source using Coinbase API."""
    
    def fetch_ohlcv(self, pair: str, start: datetime, end: datetime):
        # Simple REST API calls, no websockets needed
```

### Deliverables
- Data fetching module with caching
- Pre-downloaded regime snapshots (parquet files)
- SHA-256 hashes for reproducibility

## Week 2: Strategy Verification Logic

### Objective
Enhance `backtester.py` to verify agents execute their claimed strategies.

### Strategy Detection Algorithms

```python
# arc_verifier/strategy_verifier.py (NEW FILE)
class StrategyVerifier:
    """Detects if agent behavior matches claimed strategy."""
    
    def verify_arbitrage(self, trades: List[Trade]) -> VerificationResult:
        # Arbitrage criteria:
        # - Paired trades within 30 seconds
        # - Cross-exchange or cross-pair
        # - Positive spread capture
        
    def verify_market_making(self, trades: List[Trade]) -> VerificationResult:
        # Market making criteria:
        # - Consistent bid/ask placement
        # - Inventory management
        # - Spread capture metrics
        
    def verify_momentum(self, trades: List[Trade]) -> VerificationResult:
        # Momentum criteria:
        # - Trades align with price trends
        # - Position sizing increases in trends
        # - Proper stop-loss execution
```

### Key Metrics
- **Strategy Adherence Score**: 0-100% match to expected behavior
- **Execution Quality**: Slippage, timing, efficiency
- **Risk Compliance**: Position limits, drawdown control

## Week 3: Fort Score Integration

### Objective
Connect performance verification to the existing 0-180 point scoring system.

### Scoring Adjustments
```python
# Performance contributes -40 to +80 points:
performance_score = 0

# Base performance (0-40 points)
if strategy_verified:
    performance_score += 20
if risk_controlled:
    performance_score += 10
if consistent_across_regimes:
    performance_score += 10

# Comparative adjustments (-40 to +40)
percentile_rank = calculate_percentile(agent, all_agents)
if percentile_rank >= 90:
    performance_score += 40
elif percentile_rank >= 75:
    performance_score += 20
elif percentile_rank <= 25:
    performance_score -= 20
elif percentile_rank <= 10:
    performance_score -= 40
```

### Integration Points
1. Update `_calculate_agent_fort_score()` in `cli.py`
2. Add performance data to verification output
3. Create visual performance report

## How This Completes Our Simulation Story

The complete Arc-Verifier now provides:

1. **Static Analysis**: "This code contains arbitrage logic" (Security scan)
2. **Behavioral Simulation**: "Agent responds to price differences" (Mock testing)
3. **LLM Intelligence**: "Strategy appears sophisticated but risky" (AI analysis)
4. **Performance Verification**: "Agent executed 87% valid arbitrage trades on historical data" (Real backtesting)

This gives NEAR a complete picture: **security + behavior + intelligence + performance = trust decision**.

## Success Criteria

- ✅ Evaluate 100+ agents per day
- ✅ Clear pass/fail on strategy claims
- ✅ Reproducible results with public data
- ✅ < 10 minute evaluation time
- ✅ Seamless integration with existing Fort Score

## Risk Mitigation

1. **Data Quality**: Use multiple sources (Binance + Coinbase) for validation
2. **Overfitting**: Test on out-of-sample data not used in agent training
3. **Gaming**: Rotate test periods to prevent optimization for specific dates
4. **Complexity Creep**: Maintain strict 3-week timeline, defer enhancements

## Next Actions

1. Create `data_providers.py` with Binance CSV fetcher
2. Download and verify 4 regime datasets
3. Implement basic strategy detection for arbitrage
4. Test end-to-end with real agent image

This simplified approach delivers customer value fast while maintaining the option to add complexity later if needed.