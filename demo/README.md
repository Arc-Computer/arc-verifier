# Arc-Verifier Demo Materials

This folder contains all demonstration materials for Arc-Verifier, including sample code, test agents, and presentation scripts.

## Contents

### Demo Scripts
- `demo_api.py` - Basic API demonstration showing single and batch verification
- `clean_api_demo.py` - Clean, comprehensive demo showing all verification components

### Test Agents
- `test-agents/` - Sample Docker agents for testing:
  - `arbitrage-agent/` - Sample arbitrage trading agent
  - `market-maker-agent/` - Sample market maker agent
  - `momentum-agent/` - Sample momentum trading agent
  - `market_data/` - Historical market data for backtesting

### Configuration
- `agents.txt` - List of agent images for batch verification demos

## Quick Start

1. Ensure Arc-Verifier is installed:
   ```bash
   pip install arc-verifier
   ```

2. Set up API keys (for LLM analysis):
   ```bash
   export ANTHROPIC_API_KEY="your-key"
   export OPENAI_API_KEY="your-key"
   ```

3. Run the clean demo:
   ```bash
   python demo/clean_api_demo.py
   ```

## Demo Highlights

- **End-to-End Verification**: Shows all 5 verification stages
- **Real LLM Analysis**: Uses actual API calls to Claude/GPT-4
- **Fort Score™ Calculation**: Demonstrates the trust metric
- **Batch Processing**: Shows concurrent agent verification
- **Production Ready**: Examples of CI/CD integration

For more information, see the main [Arc-Verifier README](../README.md).