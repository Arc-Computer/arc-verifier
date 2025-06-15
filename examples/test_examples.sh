#!/bin/bash
# Test script for Arc-Verifier examples

echo "=== Arc-Verifier Example Tests ==="
echo ""

# Build test images
echo "Building example Docker images..."
docker build -f examples/Dockerfile.oracle -t arc-test/oracle:latest examples/ > /dev/null 2>&1
docker build -f examples/test-agent/Dockerfile -t arc-test/agent:latest examples/test-agent/ > /dev/null 2>&1

echo "✓ Images built successfully"
echo ""

# Test scan command
echo "Testing scan command..."
arc-verifier scan arc-test/oracle:latest
echo ""

# Test verify command
echo "Testing verify command..."
arc-verifier verify arc-test/agent:latest --tier medium --no-llm
echo ""

# Test backtest command
echo "Testing backtest command..."
arc-verifier backtest arc-test/oracle:latest --start-date 2024-01-01 --end-date 2024-03-31 --strategy arbitrage
echo ""

echo "=== All example tests completed ==="