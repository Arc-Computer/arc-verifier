"""Tests for the Docker scanner module."""

import pytest
from arc_verifier.security.scanner import DockerScanner


def test_scanner_init():
    """Test that scanner initializes correctly."""
    scanner = DockerScanner(force_mock=True)
    # Scanner should initialize even without Docker
    assert scanner is not None
    assert not scanner.docker_available


def test_mock_scan_result():
    """Test mock scan result generation."""
    scanner = DockerScanner(force_mock=True)
    
    # Test regular image
    result = scanner._get_mock_scan_result("nginx:latest")
    assert result['image_tag'] == "nginx:latest"
    assert not result['shade_agent_detected']  # nginx shouldn't be detected as shade agent
    
    # Test Shade agent image
    result = scanner._get_mock_scan_result("pivortex/shade-agent-template:latest")
    assert result['image_tag'] == "pivortex/shade-agent-template:latest"
    assert result['shade_agent_detected']  # This should be detected as shade agent


def test_shade_agent_detection():
    """Test enhanced agentic protocol detection patterns."""
    scanner = DockerScanner(force_mock=True)
    
    # Test various image names for broader agentic protocol support
    test_cases = [
        # Should NOT be detected as agentic
        ("nginx:latest", False),
        ("ubuntu:20.04", False),
        ("redis:alpine", False),
        ("postgres:13", False),
        
        # NEAR/Shade specific - should be detected
        ("shade/finance-agent:latest", True),
        ("pivortex/shade-agent-template:latest", True),
        ("mycompany/near-trading-agent:v1", True),
        
        # General agentic patterns - should be detected
        ("test/finance-bot:latest", True),
        ("company/trading-bot:v2", True),
        ("myorg/defi-agent:stable", True),
        ("acme/arbitrage-bot:prod", True),
        
        # AI/ML agents - should be detected
        ("openai/gpt-agent:latest", True),
        ("anthropic/claude-bot:v1", True),
        ("company/llm-trading:latest", True),
        
        # Multi-protocol agents - should be detected
        ("ethereum/swap-agent:v1", True),
        ("solana/liquidity-bot:latest", True),
        ("polygon/market-maker:stable", True),
        
        # Framework-based agents - should be detected
        ("langchain/agent-runner:latest", True),
        ("autogen/multi-agent:v2", True),
        ("crewai/finance-crew:prod", True),
    ]
    
    for image_tag, expected in test_cases:
        result = scanner._get_mock_scan_result(image_tag)
        assert result['shade_agent_detected'] == expected, f"Failed for {image_tag}"


def test_vulnerability_parsing():
    """Test vulnerability data structure."""
    scanner = DockerScanner(force_mock=True)
    vulns = scanner._get_mock_vulnerabilities()
    
    assert len(vulns) > 0
    for vuln in vulns:
        assert hasattr(vuln, 'severity')
        assert hasattr(vuln, 'cve_id')
        assert hasattr(vuln, 'package')
        assert hasattr(vuln, 'version')
        assert vuln.severity in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']


def test_scan_with_mock_data():
    """Test complete scan workflow with mock data."""
    scanner = DockerScanner(force_mock=True)
    
    result = scanner.scan("test/agent:latest")
    
    # Verify result structure
    assert 'image_tag' in result
    assert 'image_id' in result
    assert 'vulnerabilities' in result
    assert 'layers' in result
    assert 'shade_agent_detected' in result
    assert 'checksum' in result
    assert 'size' in result
    assert 'timestamp' in result
    
    assert result['image_tag'] == "test/agent:latest"
    assert isinstance(result['vulnerabilities'], list)
    assert isinstance(result['layers'], list)