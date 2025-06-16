# Arc-Verifier Documentation

Welcome to the Arc-Verifier documentation. This guide covers installation, usage, architecture, and development.

## Table of Contents

1. [Getting Started](./getting-started.md)
2. [Installation Guide](./installation.md)
3. [CLI Reference](./cli-reference.md)
4. [API Reference](./API_REFERENCE.md)
5. [Architecture Overview](./architecture.md)
6. [TEE Setup Guide](./TEE_SETUP_GUIDE.md)
7. [Web UI Guide](./web-ui.md)
8. [Configuration](./configuration.md)
9. [Fort Score Methodology](./fort-score.md)
10. [Development Guide](./development.md)
11. [Examples](./examples.md)

## Quick Start

```bash
# Install Arc-Verifier
pip install arc-verifier

# Verify your first agent
arc-verifier verify myagent:latest

# View results in web UI
arc-verifier export web
```

## Key Features

- **Security Scanning**: Container vulnerability detection with Trivy
- **TEE Validation**: Hardware attestation for Intel SGX and AMD SEV
- **Performance Testing**: Load testing and resource profiling
- **Strategy Verification**: Historical backtesting with real market data
- **LLM Analysis**: AI-powered behavioral assessment
- **Fort Score™**: Comprehensive trustworthiness metric (0-180)
- **Parallel Processing**: Verify 100+ agents concurrently
- **Web Dashboard**: Interactive visualization of results

## Architecture Overview

Arc-Verifier uses a modular pipeline architecture:

```
Agent Image → Security Scan → TEE Validation → Performance Test → Strategy Analysis → AI Assessment → Fort Score
```

Each component can be used independently or as part of the full pipeline.

## Support

- **Issues**: [GitHub Issues](https://github.com/near/arc-verifier/issues)
- **Discussions**: [GitHub Discussions](https://github.com/near/arc-verifier/discussions)
- **Security**: Report vulnerabilities to security@near.org