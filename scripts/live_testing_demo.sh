#!/bin/bash
# Live Testing Demo Script for NEAR Agent Forts
# Demonstrates arc-verifier testing against real Shade Agent images

set -e

echo "🚀 Arc-Verifier Production Demo for NEAR Agent Forts"
echo "===================================================="
echo ""

# Check if arc-verifier is installed
if ! command -v arc-verifier &> /dev/null; then
    echo "❌ arc-verifier not found. Please install first:"
    echo "   pip install -e ."
    exit 1
fi

echo "✅ arc-verifier CLI detected"

# Check if Docker is running
echo "🐳 Checking Docker daemon..."
if docker info >/dev/null 2>&1; then
    echo "✅ Docker daemon is running"
else
    echo "❌ Docker daemon is not running"
    echo ""
    echo "Please start Docker and run setup script:"
    echo "   ./scripts/setup_docker.sh"
    echo ""
    echo "Exiting demo..."
    exit 1
fi

# Check if Trivy is installed
echo "🔍 Checking Trivy scanner..."
if command -v trivy &> /dev/null; then
    echo "✅ Trivy scanner detected: $(trivy --version | head -1)"
else
    echo "❌ Trivy scanner not found"
    echo ""
    echo "Please install Trivy:"
    echo "   ./scripts/install_trivy.sh"
    echo ""
    echo "Exiting demo..."
    exit 1
fi

echo ""

# Test 1: Regular image (should not detect Shade Agent)
echo "Test 1: Regular Docker Image Scan"
echo "----------------------------------"
echo "Testing: nginx:latest (should NOT be detected as Shade Agent)"
echo ""
arc-verifier scan nginx:latest
echo ""

# Test 2: Shade Agent template (should detect Shade Agent)
echo "Test 2: Shade Agent Detection"
echo "------------------------------"
echo "Testing: pivortex/shade-agent-template:latest (should be detected as Shade Agent)"
echo ""
arc-verifier scan pivortex/shade-agent-template:latest
echo ""

# Test 3: Full verification workflow with JSON output
echo "Test 3: Full Agent Fort Verification"
echo "-------------------------------------"
echo "Testing: pivortex/shade-agent-template:latest with high security tier"
echo ""
arc-verifier verify pivortex/shade-agent-template:latest --tier high
echo ""

# Test 4: JSON output for NEAR pipeline integration
echo "Test 4: JSON Output for NEAR Pipeline"
echo "--------------------------------------"
echo "Testing: JSON output for pipeline integration"
echo ""
echo "Command: arc-verifier verify pivortex/shade-agent-template:latest --output json"
echo ""
arc-verifier verify pivortex/shade-agent-template:latest --output json > /tmp/verification_result.json
echo ""
echo "✅ JSON result saved to /tmp/verification_result.json"
echo ""
echo "Sample Agent Fort Score extraction:"
echo "Command: cat /tmp/verification_result.json | jq '.docker_scan.shade_agent_detected'"
if command -v jq &> /dev/null; then
    cat /tmp/verification_result.json | jq '.docker_scan.shade_agent_detected'
else
    echo "(jq not available - install jq to parse JSON results)"
fi
echo ""

# Test 5: Performance benchmark
echo "Test 5: Performance Benchmarking"
echo "---------------------------------"
echo "Testing: Performance benchmark for trading agent"
echo ""
arc-verifier benchmark pivortex/shade-agent-template:latest --duration 30
echo ""

# Test 6: Multiple agent comparison
echo "Test 6: Multiple Agent Comparison"
echo "----------------------------------"
echo "Comparing different agent types for Agent Fort evaluation"
echo ""

agents=(
    "nginx:latest"
    "pivortex/shade-agent-template:latest"
    "shade/finance-agent:latest"
)

for agent in "${agents[@]}"; do
    echo "Scanning: $agent"
    echo "------------------------"
    arc-verifier scan "$agent" --output json | jq -c '{
        image: .image_tag,
        shade_detected: .shade_agent_detected,
        vulnerabilities: {
            critical: [.vulnerabilities[] | select(.severity=="CRITICAL")] | length,
            high: [.vulnerabilities[] | select(.severity=="HIGH")] | length,
            medium: [.vulnerabilities[] | select(.severity=="MEDIUM")] | length,
            low: [.vulnerabilities[] | select(.severity=="LOW")] | length
        }
    }' 2>/dev/null || echo "  (JSON parsing requires jq)"
    echo ""
done

echo "🎉 Live Testing Demo Complete!"
echo ""
echo "Summary:"
echo "--------"
echo "✅ Docker image scanning with vulnerability detection"
echo "✅ Shade Agent pattern recognition" 
echo "✅ Agent Fort scoring system"
echo "✅ JSON output for NEAR pipeline integration"
echo "✅ Performance benchmarking for trading agents"
echo "✅ Multiple agent comparison capabilities"
echo ""
echo "Next Steps:"
echo "----------"
echo "1. Deploy to NEAR infrastructure"
echo "2. Integrate with Agent Fort evaluation pipeline"
echo "3. Add real TEE attestation validation"
echo "4. Scale to 100+ Agent Fort verifications"
echo ""
echo "For production use:"
echo "  pip install arc-verifier"
echo "  arc-verifier verify <agent-image> --tier high --output json"