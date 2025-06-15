# Arc-Verifier

A lightweight, standalone CLI tool for verifying NEAR Protocol finance agents. No heavy dependencies, no complex infrastructure - just simple, effective verification.

## Features

- 🔍 **Docker Image Scanning**: Vulnerability detection using Trivy
- 🛡️ **TEE Attestation**: Validate trusted execution environments
- ⚡ **Performance Benchmarking**: Quick performance profiling
- 📈 **Historical Backtesting**: Simulate trading performance with real market data
- 🧠 **AI-Powered Analysis**: LLM-based behavioral assessment and risk profiling
- 🎯 **Strategy Classification**: Identify trading strategies (arbitrage, momentum, etc.)
- 💰 **Profitability Prediction**: Forecast returns based on historical performance
- 📊 **Multiple Output Formats**: Terminal tables or JSON export
- 🚀 **Minimal Dependencies**: Install and run in seconds

## Quick Start

```bash
# Install
pip install arc-verifier

# Verify an agent (full analysis with LLM)
arc-verifier verify shade/finance-agent:latest

# Quick vulnerability scan
arc-verifier scan myagent:latest

# Run performance benchmark
arc-verifier benchmark myagent:latest --duration 60

# Historical backtest for profitability
arc-verifier backtest shade/arbitrage-agent:latest --start-date 2024-01-01

# Simulate agent behavior
arc-verifier simulate shade/oracle-agent:latest --scenario price_oracle
```

## Installation

### Requirements

- Python 3.11+
- Docker
- Trivy (auto-installed on first run)

### Install from PyPI

```bash
pip install arc-verifier
```

### Install from Source

```bash
git clone https://github.com/near/arc-verifier
cd arc-verifier
pip install -e .
```

## Usage

### Verify Command

Complete verification including vulnerabilities, TEE attestation, and performance:

```bash
arc-verifier verify <image> [OPTIONS]

Options:
  --tier [high|medium|low]  Security tier (default: medium)
  --output [terminal|json]  Output format (default: terminal)
```

Example:
```bash
$ arc-verifier verify shade/finance-agent:latest

[blue]Verifying image: shade/finance-agent:latest[/blue]
[cyan]Running verification...[/cyan] ━━━━━━━━━━━━━━━━━━━━ 100% 0:00:30

Verification Results
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Check               ┃ Result                 ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Vulnerabilities     │ ✓ 0 critical, 2 low   │
│ TEE Attestation     │ ✓ Valid (Mock)        │
│ Shade Agent         │ ✓ Detected            │
│ Performance         │ ✓ 1,247 tx/s          │
│ Overall Status      │ ✓ PASSED              │
└─────────────────────┴────────────────────────┘
```

### Scan Command

Quick vulnerability scan only:

```bash
arc-verifier scan <image> [OPTIONS]

Options:
  --output [terminal|json]  Output format (default: terminal)
```

### Benchmark Command

Performance benchmarking:

```bash
arc-verifier benchmark <image> [OPTIONS]

Options:
  --duration INTEGER  Benchmark duration in seconds (default: 60)
  --type [standard|trading|stress]  Benchmark type (default: standard)
```

### Backtest Command

Historical performance simulation for trading agents:

```bash
arc-verifier backtest <image> [OPTIONS]

Options:
  --start-date TEXT  Backtest start date YYYY-MM-DD (default: 2024-01-01)
  --end-date TEXT    Backtest end date YYYY-MM-DD (default: 2024-12-31)
  --strategy [arbitrage|momentum|market_making]  Strategy type (default: arbitrage)
  --output [terminal|json]  Output format (default: terminal)
```

Example:
```bash
$ arc-verifier backtest shade/arbitrage-agent:latest --start-date 2024-01-01

[blue]Starting backtest for shade/arbitrage-agent:latest[/blue]
Period: 2024-01-01 to 2024-12-31 | Strategy: arbitrage

Backtest Results
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Metric              ┃ Value      ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ Total Return        │ 18.5%      │
│ Annualized Return   │ 18.5%      │
│ Sharpe Ratio        │ 1.85       │
│ Max Drawdown        │ -12.0%     │
│ Win Rate            │ 62.0%      │
│ Profit Factor       │ 1.80       │
│ Total Trades        │ 1,247      │
└─────────────────────┴────────────┘

Performance by Market Regime
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Regime              ┃ Hours ┃ Trades ┃ Annualized Return┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ Bull Trend          │ 2,190 │ 312    │ 22.0%           │
│ Bear Market         │ 2,190 │ 298    │ 8.0%            │
│ High Volatility     │ 1,460 │ 425    │ 35.0%           │
│ Sideways            │ 2,920 │ 212    │ 5.0%            │
└─────────────────────┴───────┴────────┴─────────────────┘

[bold]Investment Rating: [green]A - Highly Recommended[/green][/bold]
Recommended Capital: $188,000
```

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

### GitHub Actions

```yaml
name: Verify Agent
on: [push]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build Docker Image
        run: docker build -t myagent:${{ github.sha }} .
      
      - name: Install Arc-Verifier
        run: pip install arc-verifier
      
      - name: Verify Agent
        run: |
          arc-verifier verify myagent:${{ github.sha }} --output json > results.json
          
          # Fail if critical vulnerabilities
          jq -e '.docker_scan.vulnerabilities.critical == 0' results.json
```

### GitLab CI

```yaml
verify:
  stage: test
  script:
    - pip install arc-verifier
    - arc-verifier verify $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  only:
    - main
    - merge_requests
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/near/arc-verifier
cd arc-verifier

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black arc_verifier/
mypy arc_verifier/
```

### Project Structure

```
arc-verifier/
├── arc_verifier/
│   ├── __init__.py
│   ├── cli.py           # Click CLI implementation
│   ├── scanner.py       # Docker vulnerability scanning
│   ├── validator.py     # TEE attestation validation
│   ├── benchmarker.py   # Performance benchmarking
│   └── reporter.py      # Output formatting
├── tests/
│   └── test_*.py       # Test suite
├── pyproject.toml      # Project configuration
└── README.md           # This file
```

## Roadmap

### v0.1.0 (Current)
- [x] Basic Docker vulnerability scanning
- [x] Mock TEE attestation
- [x] Simple performance benchmarking
- [x] Terminal and JSON output

### v0.2.0 (Planned)
- [ ] Real TEE integration (Intel SGX, AWS Nitro)
- [ ] Advanced vulnerability analysis
- [ ] Performance regression detection
- [ ] SARIF output format

### v0.3.0 (Future)
- [ ] NEAR blockchain integration
- [ ] Multi-agent comparison
- [ ] Custom verification plugins
- [ ] Web dashboard (optional)

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

## Why Arc-Verifier?

Unlike heavy, complex verification platforms, Arc-Verifier focuses on:

- **Simplicity**: One command to install, one command to verify
- **Speed**: Results in under 60 seconds
- **Portability**: Works anywhere Python and Docker run
- **Integration**: Easy to add to any CI/CD pipeline
- **Extensibility**: Plugin architecture for custom checks

Perfect for teams that need reliable verification without infrastructure overhead.

---

Built with ❤️ for the NEAR Protocol ecosystem