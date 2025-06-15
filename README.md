# Arc-Verifier

Open source verification infrastructure for autonomous agents across agentic protocols. Comprehensive security, performance, and behavioral analysis for AI agents that manage real assets and execute transactions.

## Overview

Arc-Verifier provides automated evaluation of autonomous agents deployed on agentic protocols including NEAR Chain Signatures, multichain intent systems, and other agent-based infrastructures. As autonomous agents increasingly manage capital and execute decisions without human intervention, verification becomes critical for protocol safety and user trust.

## Architecture

### Core Components

| Component | Purpose |
|-----------|---------|
| `scanner.py` | Container vulnerability detection using Trivy |
| `validator.py` | TEE attestation validation (Intel SGX, AMD SEV) |
| `benchmarker.py` | Performance testing and resource profiling |
| `strategy_verifier.py` | Trading strategy analysis with real market data |
| `real_backtester.py` | Historical performance simulation |
| `simulator.py` | Agent behavior simulation under various conditions |
| `llm_judge/` | AI-based code analysis and behavioral assessment |
| `tee/` | Trusted Execution Environment validation suite |
| `parallel_verifier.py` | Concurrent verification using Dagger orchestration |
| `verification_pipeline.py` | End-to-end verification workflow coordination |

### LLM Judge Module

Modular AI analysis system for trust-focused evaluation:

```
llm_judge/
├── core.py              # Main orchestrator
├── models.py            # Pydantic data models
├── providers/           # LLM provider abstractions
│   ├── anthropic.py     # Anthropic Claude integration
│   ├── openai.py        # OpenAI GPT integration
│   └── factory.py       # Provider selection logic
├── security/            # Trust-focused analysis
│   ├── analyzers.py     # Security pattern detection
│   ├── prompts.py       # Security evaluation prompts
│   └── scoring.py       # Trust score calculation
└── evaluation/          # General assessment
    ├── ensemble.py      # Multi-provider evaluation
    └── prompts.py       # Behavioral analysis prompts
```

### TEE Validation Suite

Hardware-based verification for trusted execution:

```
tee/
├── attestation_verifier.py    # Attestation validation
├── phala_validator.py         # Phala Network TEE support
├── code_hash_registry.py      # Verified code tracking
└── config.py                  # TEE configuration management
```

## Verification Pipeline

Five-stage automated analysis:

```
Docker Image → Security Scan → TEE Validation → Performance Test → Strategy Analysis → AI Assessment → Score
```

1. **Security Analysis** (`scanner.py`)
   - CVE detection with Trivy
   - Dependency vulnerability assessment
   - Container configuration analysis

2. **TEE Attestation** (`validator.py`, `tee/`)
   - Hardware security validation
   - Enclave measurement verification
   - Code integrity confirmation

3. **Performance Evaluation** (`benchmarker.py`)
   - Load testing and throughput measurement
   - Resource usage profiling
   - Latency analysis under stress

4. **Strategy Verification** (`strategy_verifier.py`, `real_backtester.py`)
   - Historical performance backtesting
   - Market regime analysis
   - Risk-adjusted return calculation

5. **Behavioral Assessment** (`llm_judge/`, `simulator.py`)
   - AI-powered code review
   - Intent classification and validation
   - Deception and malicious pattern detection

## Usage

### Command Line Interface

```bash
# Install
pip install arc-verifier

# Verify single agent
arc-verifier verify myagent:latest --tier high

# Batch verification
arc-verifier verify-batch agent1:latest agent2:latest --max-concurrent 10

# Strategy-specific analysis
arc-verifier verify-strategy trading-agent:latest --regime bull_2024
```

### Programmatic API

```python
from arc_verifier import ParallelVerifier
from arc_verifier.llm_judge import LLMJudge
from arc_verifier.tee import TEEValidator

# Multi-agent verification
verifier = ParallelVerifier(max_concurrent=5)
results = await verifier.verify_batch(["agent1:latest", "agent2:latest"])

# Trust-focused security analysis
judge = LLMJudge()
security_result = judge.evaluate_agent_security(image_data)

# TEE attestation validation
tee_validator = TEEValidator()
attestation_result = tee_validator.validate(agent_image)
```

## Configuration

### Environment Variables

```bash
# LLM Analysis
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
LLM_PRIMARY_PROVIDER=anthropic
LLM_ENABLE_ENSEMBLE=true

# TEE Validation
TEE_INTEL_PCCS_ENDPOINT=https://api.trustedservices.intel.com/sgx/certification/v4
TEE_PHALA_ENDPOINT=https://api.phala.network/v1/verify

# Performance Testing
BENCHMARK_DURATION=60
DOCKER_TIMEOUT=30
```

### TEE Configuration

```bash
# Initialize TEE configuration
python -m arc_verifier.tee.cli init-config

# Add agent to registry
python -m arc_verifier.tee.cli registry add myagent:latest \
  --risk-level medium --capabilities "trading,defi"
```

## Output Formats

### Terminal Output
```
┌──────────────────────────────┐
│     Verification Results     │
├──────────────────────────────┤
│ Security: ✓ 0 critical      │
│ TEE: ✓ Intel SGX verified   │
│ Performance: ✓ 2000 TPS     │
│ Strategy: ✓ 75% effective   │
│ AI Analysis: ✓ No risks     │
└──────────────────────────────┘

Fort Score: 145/180 (Deploy with confidence)
```

### JSON Output
```json
{
  "verification_id": "ver_a1b2c3d4",
  "image": "myagent:latest",
  "timestamp": "2024-01-15T10:30:00Z",
  "fort_score": 145,
  "components": {
    "docker_scan": {
      "vulnerabilities": {"critical": 0, "high": 0},
      "agent_detected": true
    },
    "tee_validation": {
      "valid": true,
      "platform": "Intel SGX",
      "measurements": {"mrenclave": "abc123..."}
    },
    "performance": {
      "throughput": 2000,
      "latency_p99": 45.7,
      "cpu_efficiency": 0.85
    },
    "strategy_analysis": {
      "detected_strategy": "arbitrage",
      "effectiveness": 75.2,
      "max_drawdown": 0.12
    },
    "llm_analysis": {
      "trust_recommendation": "DEPLOY",
      "confidence": 0.92,
      "risk_score": 0.15
    }
  }
}
```

## CI/CD Integration

### GitHub Actions
```yaml
- name: Verify Agent
  run: |
    pip install arc-verifier
    arc-verifier verify ${{ github.repository }}:${{ github.sha }} \
      --tier high --output json > results.json
    
    # Enforce minimum score
    SCORE=$(jq -r '.fort_score' results.json)
    if [ $SCORE -lt 120 ]; then exit 1; fi
```

### Integration with Agentic Protocols

Arc-Verifier integrates with various agentic protocol infrastructures:

- **NEAR Chain Signatures**: Verify multichain agents using NEAR's MPC infrastructure
- **Intent-based Systems**: Validate agents executing cross-chain intents
- **TEE-based Protocols**: Comprehensive attestation for Phala, Oasis, and other TEE networks
- **General Agent Frameworks**: Protocol-agnostic verification for any containerized agent

## Fort Score

Quantitative trustworthiness metric (0-180):

| Component | Range | Evaluation |
|-----------|-------|------------|
| Security | ±30 | Vulnerability assessment, secure coding |
| Intelligence | ±30 | AI analysis of logic and intent |
| Performance | ±30 | Efficiency, reliability, error handling |
| Strategy | ±90 | Backtesting effectiveness, risk management |

**Deployment Guidance:**
- 150-180: Deploy with confidence
- 120-149: Minor improvements recommended
- 90-119: Significant issues require attention
- 0-89: High risk, do not deploy

## Data Sources

Arc-Verifier automatically collects:

| Source | Data | Components |
|--------|------|------------|
| Container Image | Layers, dependencies, configuration | `scanner.py` |
| Runtime Metrics | Resource usage, performance data | `benchmarker.py` |
| Market Data | Historical prices, volatility | `data_fetcher.py`, `data_registry.py` |
| TEE Attestations | Hardware measurements, signatures | `tee/` |
| Code Patterns | Logic analysis, behavioral signatures | `llm_judge/` |

## Installation

```bash
# Requirements: Python 3.11+, Docker
pip install arc-verifier

# Development installation
git clone https://github.com/near/arc-verifier
cd arc-verifier
pip install -e ".[dev]"
```

## Contributing

Open source infrastructure project. See `CONTRIBUTING.md` for development guidelines.

- **Issues**: GitHub Issues for bug reports
- **Development**: Follow conventional commits, maintain test coverage
- **Documentation**: Update relevant component docs with changes

## License

MIT License - Open source infrastructure for the agentic protocol ecosystem.

---

**Verification infrastructure for autonomous agents across all agentic protocols**