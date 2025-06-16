"""Arc-Verifier Public API - Clean programmatic interface for developers.

This module provides a high-level, developer-friendly API for agent verification
without requiring CLI interaction. Perfect for CI/CD integration and programmatic usage.

Example usage:
    from arc_verifier import api
    
    # Simple verification
    result = await api.verify_agent("myagent:latest")
    print(f"Fort Score: {result.fort_score}")
    
    # Batch verification
    results = await api.verify_batch(["agent1:latest", "agent2:latest"])
    
    # Custom configuration
    result = await api.verify_agent(
        "myagent:latest",
        enable_llm=True,
        enable_backtesting=True,
        backtest_period="2024-01-01:2024-12-31"
    )
"""

import asyncio
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
from datetime import datetime

from .core import CoreArcVerifier, ResourceLimits, CoreVerificationResult, BatchVerificationResult
from .security import DockerScanner, TEEValidator
from .analysis import Benchmarker, LLMJudge, StrategyVerifier
from .data import RealBacktester
from .utils import AgentSimulator
from .orchestration import ParallelVerifier


# Import standardized models
from .models import (
    VerificationResult as StandardVerificationResult,
    BatchVerificationResult as StandardBatchResult,
    VerificationConfig,
    create_verification_id,
    create_batch_id,
    VerificationStatus,
    SecurityTier,
    SecurityResult,
    PerformanceResult,
    BacktestResult,
    LLMAnalysisResult,
    TEEResult
)


def _convert_core_to_standard(
    core_result: CoreVerificationResult, 
    image: str,
    tier: str
) -> StandardVerificationResult:
    """Convert CoreVerificationResult to StandardVerificationResult."""
    # Determine status based on fort score
    if core_result.fort_score >= 150:
        status = VerificationStatus.PASSED
    elif core_result.fort_score >= 120:
        status = VerificationStatus.WARNING
    else:
        status = VerificationStatus.FAILED
    
    # Convert security result
    security = None
    if core_result.scan_result:
        vulns = core_result.scan_result.get("vulnerabilities", [])
        vuln_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        if isinstance(vulns, list):
            for v in vulns:
                sev = v.get("severity", "LOW")
                if sev in vuln_counts:
                    vuln_counts[sev] += 1
        
        security = SecurityResult(
            vulnerabilities_by_severity=vuln_counts,
            total_vulnerabilities=sum(vuln_counts.values()),
            critical_count=vuln_counts["CRITICAL"],
            high_count=vuln_counts["HIGH"],
            base_image=core_result.scan_result.get("base_image"),
            shade_agent_detected=core_result.scan_result.get("shade_agent_detected", False),
            security_score=int(core_result.security_score)
        )
    
    # Convert performance result (from backtest)
    performance = None
    if core_result.backtest_result:
        perf = core_result.backtest_result
        performance = PerformanceResult(
            throughput_tps=perf.get("throughput", 0),
            avg_latency_ms=perf.get("avg_latency_ms", 0),
            p95_latency_ms=perf.get("p95_latency_ms", 0),
            p99_latency_ms=perf.get("p99_latency_ms", 0),
            error_rate_percent=perf.get("error_rate", 0),
            cpu_usage_percent=perf.get("cpu_usage_percent", 0),
            memory_usage_mb=perf.get("memory_usage_mb", 0),
            performance_score=perf.get("performance_score", 0)
        )
    
    # Extract other components similarly...
    
    return StandardVerificationResult(
        verification_id=create_verification_id(image),
        agent_id=image,
        timestamp=datetime.now(),
        processing_time_seconds=core_result.processing_time,
        fort_score=int(core_result.fort_score),
        status=status,
        tier=SecurityTier(tier),
        security=security,
        performance=performance,
        backtest=None,  # TODO: Add backtest conversion
        tee=None,  # TODO: Add TEE conversion
        llm_analysis=None,  # TODO: Add LLM conversion
        warnings=core_result.warnings or [],
        recommendations=core_result.recommendations or []
    )


def _convert_batch_to_standard(
    batch_result: BatchVerificationResult,
    images: List[str]
) -> StandardBatchResult:
    """Convert BatchVerificationResult to StandardBatchResult."""
    # Convert individual results
    converted_results = []
    for i, result in enumerate(batch_result.results):
        if isinstance(result, CoreVerificationResult):
            # Get the corresponding image name
            image = images[i] if i < len(images) else "unknown"
            converted_results.append(_convert_core_to_standard(result, image, "medium"))
    
    # Calculate averages
    total_fort_score = sum(r.fort_score for r in converted_results)
    avg_fort_score = total_fort_score / len(converted_results) if converted_results else 0
    
    return StandardBatchResult(
        batch_id=create_batch_id(),
        timestamp=datetime.now(),
        total_processing_time_seconds=batch_result.total_processing_time,
        total_agents=batch_result.total_agents,
        successful_verifications=batch_result.successful_agents,
        failed_verifications=batch_result.failed_agents,
        average_fort_score=avg_fort_score,
        results=converted_results,
        failures=batch_result.failures
    )


# Main API functions
async def verify_agent(
    image: str,
    *,
    enable_llm: bool = True,
    enable_backtesting: bool = True,
    llm_provider: str = "anthropic",
    backtest_period: str = "2024-10-01:2024-10-07",
    tier: str = "medium",
    config: Optional[VerificationConfig] = None
) -> StandardVerificationResult:
    """Verify a single agent with comprehensive analysis.
    
    Args:
        image: Docker image to verify (e.g., "myagent:latest")
        enable_llm: Enable AI-powered behavioral analysis
        enable_backtesting: Enable historical market data testing
        llm_provider: LLM provider ("anthropic" or "openai")
        backtest_period: Date range for backtesting (start:end format)
        resource_limits: Optional resource constraints
        
    Returns:
        VerificationResult object with fort_score, status, and details
        
    Example:
        result = await verify_agent("shade/agent:latest")
        if result.passed:
            print(f"Agent verified! Score: {result.fort_score}")
    """
    # Use configuration or default resource limits
    if config:
        resource_limits = config.to_resource_limits()
    else:
        resource_limits = ResourceLimits()
        
    # Initialize verifier
    verifier = CoreArcVerifier(resource_limits=resource_limits)
    
    # Run verification
    raw_result = await verifier.verify_agent(
        agent_image=image,
        enable_llm=enable_llm,
        enable_backtesting=enable_backtesting,
        backtest_period=backtest_period
    )
    
    # Convert raw result to standardized format
    return _convert_core_to_standard(raw_result, image, tier)


async def verify_batch(
    images: List[str],
    *,
    enable_llm: bool = True,
    enable_backtesting: bool = True,
    llm_provider: str = "anthropic",
    backtest_period: str = "2024-10-01:2024-10-07",
    max_concurrent: int = 8,
    resource_limits: Optional[ResourceLimits] = None
) -> StandardBatchResult:
    """Verify multiple agents in parallel.
    
    Args:
        images: List of Docker images to verify
        enable_llm: Enable AI-powered behavioral analysis
        enable_backtesting: Enable historical market data testing
        llm_provider: LLM provider ("anthropic" or "openai")
        backtest_period: Date range for backtesting (start:end format)
        max_concurrent: Maximum concurrent verifications
        resource_limits: Optional resource constraints
        
    Returns:
        BatchResult object with aggregate statistics and individual results
        
    Example:
        results = await verify_batch(["agent1:v1", "agent2:v2", "agent3:v3"])
        print(f"Passed: {results.passed_count}/{results.total_agents}")
    """
    # Use default resource limits if not provided
    if resource_limits is None:
        resource_limits = ResourceLimits(
            max_concurrent_backtests=min(max_concurrent, 8),
            max_concurrent_scans=min(max_concurrent * 2, 16),
            max_concurrent_llm=min(max_concurrent, 6)
        )
        
    # Initialize verifier
    verifier = CoreArcVerifier(resource_limits=resource_limits)
    
    # Run batch verification
    raw_result = await verifier.verify_batch(
        agent_images=images,
        enable_llm=enable_llm,
        enable_backtesting=enable_backtesting,
        backtest_period=backtest_period
    )
    
    # Convert raw result to standardized format
    return _convert_batch_to_standard(raw_result, images)


# Synchronous wrappers for ease of use
def verify_agent_sync(image: str, **kwargs) -> StandardVerificationResult:
    """Synchronous wrapper for verify_agent.
    
    Example:
        from arc_verifier import api
        result = api.verify_agent_sync("myagent:latest")
    """
    return asyncio.run(verify_agent(image, **kwargs))


def verify_batch_sync(images: List[str], **kwargs) -> StandardBatchResult:
    """Synchronous wrapper for verify_batch.
    
    Example:
        from arc_verifier import api
        results = api.verify_batch_sync(["agent1:v1", "agent2:v2"])
    """
    return asyncio.run(verify_batch(images, **kwargs))


# Individual component APIs for granular control
async def scan_security(image: str) -> Dict[str, Any]:
    """Run security scan only.
    
    Returns vulnerability counts and security status.
    """
    scanner = DockerScanner()
    return scanner.scan(image)


async def test_performance(
    image: str, 
    duration: int = 60,
    benchmark_type: str = "standard"
) -> Dict[str, Any]:
    """Run performance benchmark only.
    
    Returns throughput, latency, and resource usage metrics.
    """
    benchmarker = Benchmarker()
    return benchmarker.run(image, duration, benchmark_type)


async def backtest_strategy(
    image: str,
    start_date: str = "2024-10-01",
    end_date: str = "2024-10-07",
    symbols: List[str] = ["BTC", "ETH"]
) -> Dict[str, Any]:
    """Run historical backtest only.
    
    Returns trading performance metrics and strategy analysis.
    """
    backtester = RealBacktester()
    return backtester.run(image, start_date, end_date, symbols)


async def simulate_behavior(
    image: str,
    scenario: str = "market_stress"
) -> Dict[str, Any]:
    """Run behavioral simulation only.
    
    Returns behavioral compliance and anomaly detection results.
    """
    simulator = AgentSimulator()
    return simulator.simulate(image, scenario)


# Configuration helpers
def create_resource_limits(
    max_concurrent_total: int = 8,
    max_memory_gb: int = 16,
    max_cpu_cores: int = 8
) -> ResourceLimits:
    """Create custom resource limits for verification.
    
    Args:
        max_concurrent_total: Maximum total concurrent operations
        max_memory_gb: Maximum memory usage in GB
        max_cpu_cores: Maximum CPU cores to use
        
    Returns:
        ResourceLimits object for use with verification functions
    """
    return ResourceLimits(
        max_concurrent_backtests=min(max_concurrent_total, 8),
        max_concurrent_scans=min(max_concurrent_total * 2, 16),
        max_concurrent_llm=min(max_concurrent_total, 6),
        max_concurrent_tee=min(max_concurrent_total, 10)
    )


def configure_environment(
    anthropic_api_key: Optional[str] = None,
    openai_api_key: Optional[str] = None,
    market_data_path: Optional[str] = None,
    enable_cache: bool = True
) -> None:
    """Configure Arc-Verifier environment programmatically.
    
    Args:
        anthropic_api_key: Anthropic API key for Claude
        openai_api_key: OpenAI API key for GPT-4.1
        market_data_path: Path to market data directory
        enable_cache: Enable caching for performance
    """
    import os
    
    if anthropic_api_key:
        os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key
    if openai_api_key:
        os.environ["OPENAI_API_KEY"] = openai_api_key
    if market_data_path:
        os.environ["MARKET_DATA_PATH"] = market_data_path
    os.environ["CACHE_ENABLED"] = str(enable_cache).lower()


# Export main functions
__all__ = [
    # Main verification APIs
    "verify_agent",
    "verify_batch",
    "verify_agent_sync",
    "verify_batch_sync",
    
    # Component APIs
    "scan_security",
    "test_performance",
    "backtest_strategy",
    "simulate_behavior",
    
    
    # Configuration
    "create_resource_limits",
    "configure_environment",
]