# Getting Started with Arc-Verifier

This guide will help you get up and running with Arc-Verifier in under 5 minutes.

## Prerequisites

- Python 3.11 or higher
- Docker installed and running
- API keys for LLM providers (optional but recommended)

## Installation

```bash
pip install arc-verifier
```

For development or advanced features:

```bash
# Clone the repository
git clone https://github.com/near/arc-verifier
cd arc-verifier

# Install with all dependencies
pip install -e ".[dev,llm,web]"
```

## First Verification

### 1. Initialize Configuration

```bash
arc-verifier init
```

This will:
- Detect your Docker environment
- Check for API keys
- Create default configuration
- Download required tools (Trivy)

### 2. Verify an Agent

```bash
# Verify a public agent image
arc-verifier verify nginx:latest

# Verify with high security tier
arc-verifier verify myagent:latest --tier high

# Save results as JSON
arc-verifier verify myagent:latest --output json > results.json
```

### 3. View Results

Results are displayed in the terminal with a Fort Score summary:

```
┌─────────────────────────────────────┐
│        Verification Results         │
├─────────────────────────────────────┤
│ Security: ✓ 0 critical vulnerabilities │
│ TEE: ⚠ Simulation mode (no hardware)   │
│ Performance: ✓ 2000 TPS achieved      │
│ Strategy: ✓ 75% effectiveness         │
│ AI Analysis: ✓ No malicious patterns  │
└─────────────────────────────────────┘

Fort Score: 145/180 - Deploy with monitoring
```

## Understanding Fort Score

The Fort Score (0-180) indicates agent trustworthiness:

- **150-180**: Production ready, deploy with confidence
- **120-149**: Good, minor improvements recommended
- **90-119**: Significant issues need attention
- **0-89**: High risk, do not deploy

Components:
- Security: ±30 points
- Performance: ±90 points
- Strategy: ±30 points
- Intelligence: ±30 points

## Batch Verification

Verify multiple agents in parallel:

```bash
# From command line
arc-verifier batch agent1:latest agent2:latest agent3:latest

# From configuration file
cat > agents.txt << EOF
trading-bot:v1
arbitrage-agent:latest
market-maker:prod
EOF

arc-verifier batch -f agents.txt --max-concurrent 10
```

## Web Dashboard

Launch the interactive web UI:

```bash
# Install web dependencies
pip install 'arc-verifier[web]'

# Start web server
arc-verifier export web

# Open http://localhost:8080
```

The dashboard provides:
- Verification history
- Fort Score trends
- Component metrics
- Agent comparisons
- Detailed drill-downs

## CI/CD Integration

Add to your GitHub Actions workflow:

```yaml
- name: Verify Agent
  uses: near/arc-verifier-action@v1
  with:
    image: ${{ github.repository }}:${{ github.sha }}
    tier: high
    min-score: 120
```

Or use directly in scripts:

```bash
#!/bin/bash
SCORE=$(arc-verifier verify myagent:latest --output json | jq '.fort_score')
if [ $SCORE -lt 120 ]; then
  echo "Agent failed verification (score: $SCORE)"
  exit 1
fi
```

## Next Steps

- [Configure LLM providers](./configuration.md#llm-configuration) for AI analysis
- [Set up TEE validation](./TEE_SETUP_GUIDE.md) for hardware attestation
- [Explore the API](./API_REFERENCE.md) for programmatic usage
- [View examples](./examples.md) for common use cases