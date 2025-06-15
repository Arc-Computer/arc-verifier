# Arc-Verifier V1 Delivery Strategy
## Speed, Focus, and Extensibility

### Executive Summary

This document clarifies our V1 delivery strategy based on key learnings and feedback. We maintain our core Phase 3B objectives while adding strategic clarity on scalability and extensibility.

**Core Principle**: Ship a focused V1 that solves 80% of use cases, with clear extension points for community contributions.

### V1 Scope Definition (80/20 Rule)

#### What V1 WILL Include:

1. **Top 5 Trading Strategies** (covers ~80% of current agents):
   - **Arbitrage**: Cross-exchange and DEX/CEX arbitrage
   - **Market Making**: Bid/ask spread capture on major pairs
   - **Momentum Trading**: Trend following on ETH/BTC/major tokens
   - **DeFi Yield**: Simple yield farming and liquidity provision
   - **Grid Trading**: Range-bound trading strategies

2. **Core Asset Coverage**:
   - Major pairs: ETH/USDT, BTC/USDT, BNB/USDT
   - Top 10 DeFi tokens by volume
   - Stablecoin pairs (USDC/USDT, DAI/USDT)

3. **Primary Data Sources**:
   - Binance historical data (CSV export)
   - Coinbase API (real-time validation)
   - Uniswap V3 subgraph (DeFi strategies)

#### What V1 Will NOT Include (but will support via extensions):
- NFT trading strategies
- Options/derivatives strategies
- Cross-chain bridge arbitrage
- MEV strategies
- Exotic DeFi protocols

### Technical Architecture for Extensibility

#### 1. Strategy Plugin System (Post-V1 Ready)

```python
# V1: Hardcoded strategies in backtester.py
class Backtester:
    def verify_arbitrage(self, trades):
        # Direct implementation
        pass
    
    def verify_market_making(self, trades):
        # Direct implementation
        pass

# V1.5+: Plugin system (prepared but not required for V1)
class StrategyPlugin(ABC):
    @abstractmethod
    def detect_pattern(self, trades: List[Trade]) -> bool:
        pass
    
    @abstractmethod
    def calculate_metrics(self, trades: List[Trade]) -> Dict:
        pass
```

#### 2. Data Adapter Interface (Minimal V1)

```python
# V1: Simple data fetching
class DataFetcher:
    def get_binance_data(self, pair, start, end):
        # Direct CSV parsing
        pass
    
    def get_coinbase_data(self, pair, start, end):
        # Simple API calls
        pass

# Future: Extensible adapters
# class DataAdapter(ABC): ...
```

### V1 Delivery Timeline (3 Weeks)

#### Week 1: Real Data Integration
- [ ] Binance CSV downloader for top 10 pairs
- [ ] Basic Coinbase API client
- [ ] 30-day snapshots for 4 market regimes:
  - Bull trend (Jan 2024)
  - Bear market (May 2022)
  - Sideways (Aug 2023)
  - High volatility (Mar 2020)
- [ ] Simple file-based caching

#### Week 2: Strategy Verification
- [ ] Enhance backtester.py with real data
- [ ] Implement 5 core strategy detectors
- [ ] Add basic trade analysis:
  - Entry/exit pattern matching
  - Profit/loss calculation
  - Risk metrics (position sizing, stop losses)
- [ ] Integration tests with example agents

#### Week 3: Scoring Integration
- [ ] Percentile ranking system across agents
- [ ] Performance score calculation (-50 to +90 points)
- [ ] Integration with existing Fort Score
- [ ] Final CLI polish and documentation

### Key Success Metrics

1. **Functionality**:
   - Can verify 5 core strategies accurately
   - Processes 30 days of data in < 10 minutes
   - Clear pass/fail on strategy claims

2. **Usability**:
   - Single command verification: `arc-verifier verify <image>`
   - Human-readable reports
   - JSON output for CI/CD integration

3. **Extensibility**:
   - Clear code structure for adding strategies
   - Documented data format requirements
   - Example custom strategy implementation

### What This Enables

For NEAR and similar organizations:
1. **Immediate Value**: Can verify and rank current agent submissions
2. **Trust Building**: "Arc-Verified" becomes meaningful certification
3. **Scalability Path**: Community can add strategies without core changes

### Post-V1 Roadmap

**V1.1** (Month 2):
- Plugin system activation
- 3 additional strategies (community contributed)
- Performance optimizations

**V1.2** (Month 3):
- Protocol adapters (Aave, Compound, Curve)
- Advanced risk metrics
- Real-time monitoring hooks

**V2.0** (Month 4+):
- Multi-chain support
- ML-based strategy detection
- Automated strategy documentation

### Design Decisions for Speed

1. **No Complex Frameworks**: Just `requests` and `pandas`
2. **File-Based Data**: CSV storage, no database required
3. **Single Process**: No distributed computing for V1
4. **Fixed Strategies**: Hardcode the top 5, extensibility later
5. **English Only**: Documentation and reports in English

### Extension Points (Prepared but Not Implemented)

1. **Strategy Registry**: Folder structure ready for plugins
2. **Data Adapters**: Interface defined but not enforced
3. **Custom Metrics**: Scoring system accepts additional inputs
4. **Multi-Language**: i18n structure in place

### Risk Mitigation

1. **Scope Creep**: Anything not in "V1 WILL Include" is deferred
2. **Performance**: 10-minute limit enforced via timeout
3. **Data Quality**: Validate against 2 sources minimum
4. **False Positives**: Conservative detection thresholds

### Conclusion

V1 delivers a focused, working solution that:
- Solves NEAR's immediate need (verify and rank agents)
- Covers 80% of current use cases
- Ships in 3 weeks
- Provides clear extension points for community growth

The key is discipline: Build the essential features well, document the extension points, and let the community drive expanded coverage.

**Next Step**: Begin Week 1 implementation of Binance CSV data fetcher.