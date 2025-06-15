# Phase 3B V1 Implementation Plan
## Focused Delivery in 3 Weeks

### Week 1: Real Data Integration (Days 1-5)

#### Day 1-2: Binance Historical Data
```python
# arc_verifier/data_fetcher.py
class DataFetcher:
    """Simple data fetcher for V1 - no complex frameworks."""
    
    SUPPORTED_PAIRS = [
        "ETHUSDT", "BTCUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT",
        "MATICUSDT", "LINKUSDT", "UNIUSDT", "AAVEUSDT", "SUSHIUSDT"
    ]
    
    MARKET_REGIMES = {
        "bull_trend": {"start": "2024-01-01", "end": "2024-01-30"},
        "bear_market": {"start": "2022-05-01", "end": "2022-05-30"},
        "sideways": {"start": "2023-08-01", "end": "2023-08-30"},
        "high_volatility": {"start": "2020-03-01", "end": "2020-03-30"}
    }
    
    def fetch_binance_klines(self, symbol: str, interval: str = "1h", 
                           start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch historical klines from Binance."""
        pass
    
    def download_regime_data(self, regime: str) -> Dict[str, pd.DataFrame]:
        """Download all pairs for a specific market regime."""
        pass
```

#### Day 3: Coinbase API Integration
```python
def fetch_coinbase_prices(self, symbol: str, start: str, end: str) -> pd.DataFrame:
    """Simple Coinbase API client for validation."""
    # Using requests, no complex SDK
    pass
```

#### Day 4-5: Data Caching and Validation
```python
class DataCache:
    """File-based caching for historical data."""
    
    def __init__(self, cache_dir: str = "./cache/market_data"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_or_fetch(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        """Check cache first, fetch if missing."""
        pass
```

### Week 2: Strategy Verification (Days 6-10)

#### Day 6-7: Core Strategy Detectors
```python
# arc_verifier/strategy_detector.py
class StrategyDetector:
    """V1 strategy detection - hardcoded for speed."""
    
    def detect_arbitrage(self, trades: pd.DataFrame) -> Dict:
        """Detect cross-exchange arbitrage patterns."""
        indicators = {
            "cross_exchange_trades": 0,
            "profit_per_trade": [],
            "execution_speed": [],
            "strategy_confirmed": False
        }
        # Simple pattern matching
        return indicators
    
    def detect_market_making(self, trades: pd.DataFrame) -> Dict:
        """Detect bid/ask spread capture."""
        indicators = {
            "bid_ask_positions": 0,
            "spread_capture_rate": 0.0,
            "inventory_management": False,
            "strategy_confirmed": False
        }
        return indicators
    
    def detect_momentum(self, trades: pd.DataFrame) -> Dict:
        """Detect trend following behavior."""
        pass
    
    def detect_yield_farming(self, trades: pd.DataFrame) -> Dict:
        """Detect DeFi yield strategies."""
        pass
    
    def detect_grid_trading(self, trades: pd.DataFrame) -> Dict:
        """Detect range-bound grid strategies."""
        pass
```

#### Day 8-9: Enhance Backtester
```python
# Enhance existing arc_verifier/backtester.py
class Backtester:
    def run_with_real_data(self, agent_image: str, start_date: str, 
                          end_date: str, strategy_type: str) -> BacktestResult:
        """Run backtest with real historical data."""
        
        # 1. Fetch real data
        data = self.data_fetcher.get_or_fetch("ETHUSDT", start_date, end_date)
        
        # 2. Simulate agent execution
        trades = self.simulate_agent_trading(agent_image, data)
        
        # 3. Detect actual strategy
        detected_strategy = self.strategy_detector.detect_all(trades)
        
        # 4. Verify claims vs actual
        verification_result = self.verify_strategy_claims(
            claimed=strategy_type,
            detected=detected_strategy
        )
        
        # 5. Calculate metrics
        metrics = self.calculate_performance_metrics(trades, data)
        
        return BacktestResult(
            claimed_strategy=strategy_type,
            detected_strategy=detected_strategy,
            verification_passed=verification_result.passed,
            metrics=metrics
        )
```

#### Day 10: Integration Testing
- Test with example agents
- Verify strategy detection accuracy
- Performance benchmarking

### Week 3: Scoring Integration (Days 11-15)

#### Day 11-12: Percentile Ranking System
```python
# arc_verifier/ranking.py
class AgentRanker:
    """Rank agents based on relative performance."""
    
    def calculate_percentile_rank(self, agent_metrics: Dict, 
                                all_agents_metrics: List[Dict]) -> float:
        """Calculate percentile rank for an agent."""
        # Simple percentile calculation
        # No complex statistical libraries
        pass
    
    def generate_rankings(self, verification_results: List[VerificationResult]) -> List[Dict]:
        """Generate comparative rankings."""
        rankings = []
        for result in verification_results:
            rank = {
                "agent": result.image_tag,
                "strategy_accuracy": result.strategy_match_score,
                "risk_compliance": result.risk_score,
                "consistency": result.consistency_score,
                "overall_percentile": 0.0
            }
            rankings.append(rank)
        return sorted(rankings, key=lambda x: x["overall_percentile"], reverse=True)
```

#### Day 13-14: Fort Score Integration
```python
# Update arc_verifier/cli.py
def calculate_performance_score(backtest_result: BacktestResult, 
                              percentile_rank: float) -> float:
    """Calculate performance component of Fort Score (-50 to +90)."""
    
    base_score = 0
    
    # Strategy verification (up to 40 points)
    if backtest_result.verification_passed:
        base_score += 40 * backtest_result.strategy_match_score
    
    # Risk compliance (up to 20 points)
    if backtest_result.metrics.max_drawdown > -0.30:  # Within 30% drawdown
        base_score += 20
    
    # Consistency (up to 30 points)
    consistency_score = backtest_result.regime_performance.consistency_score
    base_score += 30 * consistency_score
    
    # Percentile adjustment (-50 to +90 total)
    if percentile_rank >= 0.9:  # Top 10%
        return 90
    elif percentile_rank <= 0.1:  # Bottom 10%
        return -50
    else:
        # Linear interpolation
        return base_score * percentile_rank
```

#### Day 15: Polish and Documentation
- Update CLI output formats
- Write user documentation
- Create example usage guides

### Implementation Priorities

1. **Keep It Simple**:
   - No async/await in V1
   - Single-threaded execution
   - File-based storage

2. **Focus on Accuracy**:
   - Conservative strategy detection
   - Multiple validation sources
   - Clear pass/fail criteria

3. **Performance Targets**:
   - 30 days of data: < 2 minutes processing
   - Full verification: < 10 minutes
   - Memory usage: < 2GB

### Testing Strategy

1. **Unit Tests**: Each strategy detector
2. **Integration Tests**: Full verification flow
3. **Example Agents**: 
   - Working arbitrage bot
   - Fake momentum trader
   - Broken market maker

### Success Criteria

V1 ships successfully when:
1. Can verify 5 core strategies with 90%+ accuracy
2. Processes standard 30-day backtest in < 10 minutes
3. Produces clear, actionable rankings
4. Integrates seamlessly with existing Fort Score

### What We're NOT Doing in V1

- Complex ML models
- Real-time data feeds
- Multi-chain support
- Database storage
- Web UI
- API endpoints
- Custom strategy plugins

All of these are documented as extension points for V1.1+.

### Next Immediate Action

Start implementing `data_fetcher.py` with Binance historical data download functionality. Target: Working data fetcher by end of Day 2.