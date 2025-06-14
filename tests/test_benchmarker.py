"""Tests for the benchmarker module."""

import pytest
from arc_verifier.benchmarker import Benchmarker


def test_benchmarker_init():
    """Test that benchmarker initializes correctly in mock mode."""
    benchmarker = Benchmarker(force_mock=True)
    assert benchmarker is not None
    assert not benchmarker.docker_available
    assert benchmarker._force_mock


def test_mock_benchmark_result():
    """Test mock benchmark result generation."""
    benchmarker = Benchmarker(force_mock=True)
    
    # Test regular image
    result = benchmarker.run("nginx:latest", duration=10, benchmark_type="standard")
    assert result['image_tag'] == "nginx:latest"
    assert result['duration_seconds'] == 10
    assert result['benchmark_type'] == "standard"
    assert 'performance' in result
    assert 'resources' in result
    
    # Test trading agent image
    result = benchmarker.run("shade/finance-agent:latest", duration=15, benchmark_type="trading")
    assert result['image_tag'] == "shade/finance-agent:latest"
    assert result['benchmark_type'] == "trading"
    assert 'trading_metrics' in result


def test_benchmark_types():
    """Test different benchmark types."""
    benchmarker = Benchmarker(force_mock=True)
    
    types = ["standard", "trading", "stress"]
    for benchmark_type in types:
        result = benchmarker.run("test:latest", duration=5, benchmark_type=benchmark_type)
        assert result['benchmark_type'] == benchmark_type
        assert 'performance' in result
        assert 'resources' in result


def test_performance_metrics_structure():
    """Test performance metrics data structure."""
    benchmarker = Benchmarker(force_mock=True)
    result = benchmarker.run("test:latest", duration=5)
    
    perf = result['performance']
    assert 'throughput_tps' in perf
    assert 'avg_latency_ms' in perf
    assert 'p95_latency_ms' in perf
    assert 'p99_latency_ms' in perf
    assert 'error_rate_percent' in perf
    
    resources = result['resources']
    assert 'cpu_percent' in resources
    assert 'memory_mb' in resources
    assert 'network_rx_mb' in resources
    assert 'network_tx_mb' in resources


def test_trading_specific_metrics():
    """Test trading-specific metrics are included for trading benchmark."""
    benchmarker = Benchmarker(force_mock=True)
    result = benchmarker.run("trading-bot:latest", duration=5, benchmark_type="trading")
    
    trading_metrics = result.get('trading_metrics')
    assert trading_metrics is not None
    assert isinstance(trading_metrics, dict)