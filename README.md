# Arc-Verifier

Comprehensive verification infrastructure for autonomous trading agents on blockchain protocols. Arc-Verifier provides security scanning, performance benchmarking, and behavioral analysis to establish trust in agentic systems managing real capital.

## The Challenge

Autonomous agents managing $40k+ annually require robust verification before deployment. Arc-Verifier addresses the primary concern in agentic protocols: **"How do we know we can trust this agent?"**

## Architecture

Arc-Verifier runs five comprehensive verification stages:

1. **Security Scanning** - Vulnerability detection in agent containers
2. **TEE Attestation** - Verification of secure execution environments  
3. **Performance Testing** - Load testing and resource profiling
4. **Strategy Verification** - Behavioral analysis with real market data
5. **AI Risk Assessment** - LLM-based code review and anomaly detection

### Key Features

- **Parallel Verification**: Test 100+ agents concurrently using Dagger orchestration
- **Real Market Data**: Backtesting with historical data from major exchanges
- **Fort Score™**: Comprehensive 0-180 point rating system
- **Strategy Detection**: Automatic classification of trading strategies
- **Extensible Architecture**: Plugin system for custom verifiers

## Quick Start

```bash
# Install
pip install arc-verifier

# Verify a single agent
arc-verifier verify shade/finance-agent:latest

# Batch verification with parallel execution
arc-verifier verify-batch agent1:latest agent2:latest agent3:latest --max-concurrent 5

# Verify trading strategy
arc-verifier verify-strategy shade/arbitrage-agent:latest --regime bull_2024
```

### Example Output

```
┌─────────────────────────────────┐
│    Verification Results         │
├─────────────────────────────────┤
│ Vulnerabilities: ✓ 0 critical  │
│ TEE Attestation: ✓ Intel TDX   │
│ Performance: ✓ 2000 TPS        │
│ Strategy: ✓ Arbitrage (75%)    │
│ Overall Status: ✓ PASSED       │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│    Agent Fort Score: 145/180    │
└─────────────────────────────────┘
```

## Fort Score™ Explained

The Fort Score provides a single metric for agent trustworthiness:

| Score Range | Rating | Interpretation |
|-------------|--------|----------------|
| 150-180 | Excellent | Deploy with confidence |
| 120-149 | Good | Minor improvements recommended |
| 90-119 | Fair | Significant issues to address |
| 0-89 | Poor | High risk - do not deploy |

### Scoring Components

- **Security (±30 points)**: Vulnerabilities, TEE validation, secure coding
- **Intelligence (±30 points)**: LLM assessment of code quality and intent
- **Behavior (±30 points)**: Performance under load, error handling
- **Strategy (-50 to +90 points)**: Effectiveness, risk management, consistency

## Installation

### Requirements

- Python 3.11+
- Docker
- Dagger (for parallel execution)

### Install from PyPI

```bash
pip install arc-verifier
```

### Install from Source

```bash
git clone https://github.com/near/arc-verifier
cd arc-verifier
pip install -e ".[dev]"
```

## Core Commands

### `verify` - Complete Agent Verification

```bash
arc-verifier verify <image> [OPTIONS]

Options:
  --tier [high|medium|low]      Security tier (default: medium)
  --output [terminal|json]      Output format
  --enable-llm/--no-llm        Enable AI analysis (default: enabled)
  --llm-provider [anthropic|openai|local]  LLM provider
```

### `verify-batch` - Parallel Multi-Agent Verification

```bash
arc-verifier verify-batch <image1> <image2> ... [OPTIONS]

Options:
  --max-concurrent INTEGER      Max parallel verifications (default: 3)
  --tier [high|medium|low]     Security tier for all agents
  --output [terminal|json]     Output format
```

### `verify-strategy` - Trading Strategy Analysis

```bash
arc-verifier verify-strategy <image> [OPTIONS]

Options:
  --start-date TEXT            Analysis start date (YYYY-MM-DD)
  --end-date TEXT             Analysis end date
  --regime [bull_2024|bear_2024|volatile_2024|sideways_2024]
  --output [terminal|json]    Output format
```

## Technical Architecture

### Verification Pipeline

```
Docker Image → Scanner → Validator → Benchmarker → Strategy Verifier → LLM Judge → Fort Score
     │            │          │            │               │               │           │
     ▼            ▼          ▼            ▼               ▼               ▼           ▼
  Agent Code   Security    TEE      Performance    Real Market    Behavioral    Final
             Assessment  Attestation   Metrics        Analysis      Analysis    Rating
```

### Dagger Integration

Arc-Verifier leverages Dagger for container orchestration:

```python
# Parallel verification of multiple agents
async with dagger.connect() as client:
    # Run Trivy scanner in container
    scan_result = await (
        client.container()
        .from_("aquasec/trivy:latest")
        .with_exec(["image", "--format", "json", agent_image])
        .stdout()
    )
    
    # Run agent as service for load testing
    agent_service = (
        client.container()
        .from_(agent_image)
        .with_exposed_port(8080)
        .as_service()
    )
```

## Strategy Verification

Arc-Verifier automatically detects and verifies trading strategies:

### Supported Strategies

- **Arbitrage**: Cross-exchange price differentials
- **Market Making**: Bid-ask spread capture
- **Momentum**: Trend following
- **Mean Reversion**: Counter-trend trading

### Verification Process

1. **Behavioral Analysis**: Observe agent trading patterns
2. **Strategy Classification**: Identify strategy type with confidence score
3. **Effectiveness Rating**: Measure strategy performance (0-100)
4. **Risk Assessment**: Evaluate drawdown and volatility
5. **Regime Testing**: Performance across different market conditions

## Output Formats

### Terminal Output (Default)

Beautiful, colored terminal output using Rich library:
- Clear tables with results
- Color-coded status indicators
- Progress bars during execution

### JSON Output

Machine-readable JSON for integration with other tools:

```bash
arc-verifier verify myagent:latest --output json > results.json
```

```json
{
  "verification_id": "ver_abc123",
  "timestamp": "2024-01-15T10:30:00Z",
  "image": "myagent:latest",
  "docker_scan": {
    "vulnerabilities": {
      "critical": 0,
      "high": 0,
      "medium": 1,
      "low": 2
    },
    "size": 268435456,
    "layers": 12,
    "shade_agent_detected": true
  },
  "tee_validation": {
    "valid": true,
    "platform": "Intel SGX (Mock)",
    "measurements": {
      "mrenclave": "abc123...",
      "mrsigner": "def456..."
    }
  },
  "performance": {
    "throughput": 1247,
    "avg_latency": 12.3,
    "p99_latency": 45.7,
    "cpu_avg": 34.2,
    "memory_peak": 536870912
  },
  "overall_status": "PASSED"
}
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Agent Verification
on: [push, pull_request]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Agent Image
        run: docker build -t myagent:${{ github.sha }} .
      
      - name: Install Arc-Verifier
        run: pip install arc-verifier
      
      - name: Run Verification
        run: |
          arc-verifier verify myagent:${{ github.sha }} \
            --output json \
            --tier high > results.json
          
      - name: Check Fort Score
        run: |
          SCORE=$(jq -r '.agent_fort_score' results.json)
          if [ $SCORE -lt 120 ]; then
            echo "Fort Score too low: $SCORE/180"
            exit 1
          fi
      
      - name: Upload Results
        uses: actions/upload-artifact@v3
        with:
          name: verification-results
          path: results.json
```

## API Usage

```python
from arc_verifier import ParallelVerifier

# Initialize verifier
verifier = ParallelVerifier(max_concurrent=5)

# Verify multiple agents
results = await verifier.verify_batch(
    ["agent1:latest", "agent2:latest", "agent3:latest"],
    tier="high",
    enable_llm=True
)

# Check results
for result in results.results:
    print(f"{result['image']}: Score {result['agent_fort_score']}/180")
```

## Extensibility

### Custom Verifiers

```python
from arc_verifier.base import BaseVerifier

class CustomVerifier(BaseVerifier):
    async def verify(self, image: str) -> dict:
        # Your custom verification logic
        return {
            "status": "passed",
            "score_adjustment": 10
        }

# Register verifier
registry.register(CustomVerifier())
```

## Performance

### Benchmarks

| Agents | Sequential Time | Parallel Time | Speedup |
|--------|----------------|---------------|----------|
| 10 | 100 minutes | 10 minutes | 10x |
| 50 | 500 minutes | 25 minutes | 20x |
| 100 | 1000 minutes | 40 minutes | 25x |

### Resource Requirements

- **CPU**: 4+ cores recommended for parallel execution
- **Memory**: 2GB + 512MB per concurrent verification
- **Disk**: 10GB for Docker images and cache
- **Network**: Stable connection for pulling images

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Guidelines

1. Keep dependencies minimal
2. Maintain backward compatibility
3. Write tests for new features
4. Follow Python PEP 8 style guide
5. Update documentation

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/near/arc-verifier/issues)
- **Discussions**: [GitHub Discussions](https://github.com/near/arc-verifier/discussions)
- **Documentation**: [docs/](docs/)

## Use Cases

### For Protocol Developers
- Verify agents before allowing them in your ecosystem
- Set minimum Fort Score requirements for participation
- Monitor agent behavior post-deployment

### For Agent Developers  
- Pre-deployment verification to catch issues early
- CI/CD integration for continuous verification
- Performance optimization insights

### For Investors/Users
- Verify agents before allocating capital
- Compare multiple agents objectively
- Understand risk profiles

## Security Considerations

Arc-Verifier runs untrusted agent containers in isolated environments:
- Containers are resource-limited
- Network access is restricted
- No persistent storage access
- Automatic cleanup after verification

---

Built with ❤️ for the NEAR Protocol ecosystem