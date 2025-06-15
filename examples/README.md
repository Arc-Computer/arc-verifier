# Arc-Verifier Examples

This directory contains example Docker images and agents for testing Arc-Verifier functionality.

## Example Images

### 1. Price Oracle Agent (`arc-test/oracle`)

A simple price oracle agent that demonstrates the structure of a NEAR Protocol finance agent.

Build:
```bash
docker build -f Dockerfile.oracle -t arc-test/oracle:latest .
```

Features:
- Shade agent labels for detection
- Simulated price fetching and oracle updates
- JSON structured logging for simulation monitoring

### 2. Test Trading Agent (`arc-test/agent`)

A minimal trading agent for testing Arc-Verifier's scanning and verification capabilities.

Build:
```bash
docker build -f test-agent/Dockerfile -t arc-test/agent:latest test-agent/
```

Features:
- Multiple agent detection patterns (labels, environment variables)
- Web3 dependencies installed
- Configuration file demonstrating agent metadata

## Testing Commands

### 1. Vulnerability Scanning
```bash
arc-verifier scan arc-test/oracle:latest
```

### 2. Full Verification
```bash
arc-verifier verify arc-test/agent:latest --tier high
```

### 3. Performance Benchmarking
```bash
arc-verifier benchmark arc-test/agent:latest --duration 60 --type trading
```

### 4. Historical Backtesting
```bash
arc-verifier backtest arc-test/oracle:latest --start-date 2024-01-01 --strategy arbitrage
```

### 5. Behavioral Simulation
```bash
arc-verifier simulate arc-test/oracle:latest --scenario price_oracle
```

## Running All Examples

Use the provided test script:
```bash
./test_examples.sh
```

## Creating Your Own Test Agent

To create a test agent for Arc-Verifier:

1. Add Shade agent indicators:
   - Labels: `shade.agent=true`, `agent.type=your-type`
   - Environment variables: `SHADE_*`, `AGENT_*`
   - Dependencies: Web3 libraries, trading frameworks

2. Implement structured logging:
   ```python
   logging.info(json.dumps({
       "action": "your_action",
       "details": {...}
   }))
   ```

3. Handle mock API endpoints when `MOCK_MODE=true`

4. Keep the container running for benchmarking tests

## Notes

- These examples use mock data and simulated behavior
- Real agents would connect to actual blockchain networks and APIs
- The test script builds images locally - no registry access required
- Benchmark results may show failures as these are minimal test containers