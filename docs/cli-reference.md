# CLI Reference

Complete reference for all Arc-Verifier command-line interface commands.

## Global Options

```bash
arc-verifier [OPTIONS] COMMAND [ARGS]...
```

Options:
- `--version`: Show version and exit
- `--help`: Show help message and exit

## Primary Commands

### verify

Verify a single agent with comprehensive analysis.

```bash
arc-verifier verify IMAGE [OPTIONS]
```

Arguments:
- `IMAGE`: Docker image to verify (required)

Options:
- `--tier [high|medium|low]`: Security tier (default: medium)
- `--enable-llm/--no-llm`: Enable AI analysis (default: enabled)
- `--enable-backtesting/--no-backtesting`: Enable historical testing (default: enabled)
- `--backtest-period TEXT`: Date range for backtesting (default: "2024-10-01:2024-10-07")
- `--output [terminal|json]`: Output format (default: terminal)
- `--output-file PATH`: Save results to file
- `--verbose`: Show detailed progress

Examples:
```bash
# Basic verification
arc-verifier verify myagent:latest

# High-tier verification with JSON output
arc-verifier verify myagent:latest --tier high --output json

# Skip AI analysis for faster results
arc-verifier verify myagent:latest --no-llm

# Custom backtest period
arc-verifier verify trader:v1 --backtest-period "2024-01-01:2024-12-31"
```

### batch

Verify multiple agents in parallel.

```bash
arc-verifier batch IMAGES... [OPTIONS]
```

Arguments:
- `IMAGES`: Space-separated list of Docker images

Options:
- `--file PATH`: Read images from file (one per line)
- `--max-concurrent INT`: Maximum parallel verifications (default: 8)
- `--tier [high|medium|low]`: Security tier for all agents
- `--continue-on-error`: Continue if an agent fails
- `--output [terminal|json|csv]`: Output format
- `--summary`: Show only summary statistics

Examples:
```bash
# Verify multiple agents
arc-verifier batch agent1:latest agent2:latest agent3:latest

# From file with high concurrency
arc-verifier batch --file agents.txt --max-concurrent 20

# Continue on errors with summary
arc-verifier batch --file production.txt --continue-on-error --summary
```

## Component Commands

### scan

Run security scan only.

```bash
arc-verifier scan IMAGE [OPTIONS]
```

Options:
- `--severity [critical|high|medium|low]`: Minimum severity to report
- `--ignore-unfixed`: Ignore vulnerabilities without fixes
- `--output [terminal|json|sarif]`: Output format

### benchmark

Run performance benchmark only.

```bash
arc-verifier benchmark IMAGE [OPTIONS]
```

Options:
- `--duration INT`: Test duration in seconds (default: 60)
- `--type [standard|trading|stress]`: Benchmark type
- `--concurrent INT`: Concurrent load threads
- `--output [terminal|json]`: Output format

### backtest

Run historical backtest only.

```bash
arc-verifier backtest IMAGE [OPTIONS]
```

Options:
- `--start-date DATE`: Start date (YYYY-MM-DD)
- `--end-date DATE`: End date (YYYY-MM-DD)
- `--symbols TEXT`: Comma-separated symbols (default: "BTC,ETH")
- `--initial-capital FLOAT`: Starting capital (default: 100000)

### simulate

Run behavioral simulation only.

```bash
arc-verifier simulate IMAGE [OPTIONS]
```

Options:
- `--scenario [standard|adversarial|stress]`: Simulation scenario
- `--duration INT`: Simulation duration in seconds
- `--seed INT`: Random seed for reproducibility

## Management Commands

### init

Initialize Arc-Verifier environment.

```bash
arc-verifier init [OPTIONS]
```

Options:
- `--force`: Overwrite existing configuration
- `--docker-check/--no-docker-check`: Check Docker availability
- `--install-tools`: Install required tools (Trivy, etc.)

### history

View verification history.

```bash
arc-verifier history [OPTIONS]
```

Options:
- `--limit INT`: Number of results to show (default: 20)
- `--image TEXT`: Filter by image name
- `--since DATE`: Show results since date
- `--status [passed|failed|all]`: Filter by status

## Configuration Commands

### config validate

Validate configuration file.

```bash
arc-verifier config validate [CONFIG_FILE]
```

### config show

Show current configuration.

```bash
arc-verifier config show [OPTIONS]
```

Options:
- `--format [yaml|json]`: Output format
- `--secrets/--no-secrets`: Include secret values

## Data Commands

### data download

Download market data for backtesting.

```bash
arc-verifier data download [OPTIONS]
```

Options:
- `--symbols TEXT`: Comma-separated symbols
- `--start-date DATE`: Start date
- `--end-date DATE`: End date
- `--exchange TEXT`: Exchange name (default: binance)

### data status

Check market data availability.

```bash
arc-verifier data status [OPTIONS]
```

Options:
- `--symbols TEXT`: Check specific symbols
- `--detailed`: Show detailed coverage

### data clear-cache

Clear cached market data.

```bash
arc-verifier data clear-cache [OPTIONS]
```

Options:
- `--older-than DAYS`: Only clear data older than N days
- `--confirm`: Skip confirmation prompt

## Export Commands

### export results

Export verification results.

```bash
arc-verifier export results [VERIFICATION_ID] [OPTIONS]
```

Options:
- `--format [html|json|pdf]`: Export format (default: html)
- `--output PATH`: Output file path
- `--latest`: Export latest verification
- `--open`: Open in browser (HTML only)

### export web

Launch web UI dashboard.

```bash
arc-verifier export web [OPTIONS]
```

Options:
- `--port INT`: Port number (default: 8080)
- `--host TEXT`: Host address (default: 127.0.0.1)
- `--debug`: Enable debug mode

## Environment Variables

Arc-Verifier respects the following environment variables:

```bash
# API Keys
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key

# Configuration
ARC_VERIFIER_CONFIG=/path/to/config.yaml
DOCKER_TIMEOUT=30

# Logging
ARC_VERIFIER_LOG_LEVEL=INFO
```

## Exit Codes

- `0`: Success
- `1`: General error
- `2`: Configuration error
- `3`: Docker not available
- `4`: Verification failed (Fort Score below threshold)
- `5`: Network error

## Examples

Common usage patterns:

```bash
# Production deployment check
arc-verifier verify prod-agent:latest --tier high --output json | \
  jq -e '.fort_score >= 120' || exit 1

# Batch verification with progress
arc-verifier batch -f agents.txt --max-concurrent 10 --verbose

# Generate HTML report
arc-verifier verify myagent:latest --output-file report.json
arc-verifier export results --latest --format html --open

# CI/CD integration
arc-verifier verify $IMAGE --tier $TIER --output json > results.json
if [ $(jq '.fort_score' results.json) -lt 120 ]; then
  echo "Verification failed"
  exit 1
fi
```