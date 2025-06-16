"""Standardized result objects and data models for Arc-Verifier.

This module provides consistent, well-typed result objects that work across
CLI, API, and web interfaces. All results are JSON-serializable and follow
a consistent structure.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict, field
from pydantic import BaseModel, Field


# Enums for standardized values
class VerificationStatus(str, Enum):
    """Overall verification status."""
    PASSED = "PASSED"
    WARNING = "WARNING"
    FAILED = "FAILED"
    ERROR = "ERROR"
    PENDING = "PENDING"


class SecurityTier(str, Enum):
    """Security verification tier."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SeverityLevel(str, Enum):
    """Vulnerability severity levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class TradingStrategy(str, Enum):
    """Detected trading strategies."""
    ARBITRAGE = "arbitrage"
    MARKET_MAKING = "market_making"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    LIQUIDITY_PROVISION = "liquidity_provision"
    UNKNOWN = "unknown"


# Component result models
@dataclass
class SecurityResult:
    """Security scan component result."""
    vulnerabilities_by_severity: Dict[str, int]
    total_vulnerabilities: int
    critical_count: int
    high_count: int
    base_image: Optional[str]
    shade_agent_detected: bool
    security_score: int  # -30 to +30
    
    @property
    def passed(self) -> bool:
        """Whether security scan passed basic requirements."""
        return self.critical_count == 0 and self.high_count <= 5


@dataclass
class PerformanceResult:
    """Performance benchmark component result."""
    throughput_tps: float
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    error_rate_percent: float
    cpu_usage_percent: float
    memory_usage_mb: float
    performance_score: int  # -50 to +90
    
    @property
    def passed(self) -> bool:
        """Whether performance meets minimum requirements."""
        return (self.throughput_tps >= 500 and 
                self.avg_latency_ms <= 100 and 
                self.error_rate_percent <= 5)


@dataclass
class BacktestResult:
    """Historical backtesting component result."""
    total_return_percent: float
    annualized_return_percent: float
    sharpe_ratio: float
    max_drawdown_percent: float
    win_rate_percent: float
    total_trades: int
    profitable_months: int
    total_months: int
    strategy_score: int  # Part of performance score
    
    @property
    def passed(self) -> bool:
        """Whether backtest shows viable strategy."""
        return (self.sharpe_ratio > 0.5 and 
                self.max_drawdown_percent < 30 and
                self.win_rate_percent > 40)


@dataclass
class TEEResult:
    """TEE attestation component result."""
    is_valid: bool
    platform: str
    trust_level: str  # HIGH, MEDIUM, LOW
    measurements: Dict[str, str]
    tee_score: int  # -10 to +5
    
    @property
    def passed(self) -> bool:
        """Whether TEE validation passed."""
        return self.is_valid


@dataclass
class LLMAnalysisResult:
    """LLM behavioral analysis component result."""
    intent_classification: str
    primary_strategy: TradingStrategy
    risk_profile: str  # low, medium, high
    confidence_level: float
    behavioral_flags: List[str]
    code_quality_score: float
    reasoning: str
    llm_score: int  # -30 to +30
    
    @property
    def passed(self) -> bool:
        """Whether LLM analysis found no critical issues."""
        critical_flags = [f for f in self.behavioral_flags 
                         if any(word in f.lower() for word in ["malicious", "dangerous", "critical"])]
        return len(critical_flags) == 0 and self.confidence_level >= 0.7


# Main verification result
@dataclass
class VerificationResult:
    """Complete verification result with all components.
    
    This is the standardized result object used across CLI, API, and web UI.
    """
    # Metadata
    verification_id: str
    agent_id: str  # Docker image name
    timestamp: datetime
    processing_time_seconds: float
    
    # Overall results
    fort_score: int  # 0-180
    status: VerificationStatus
    tier: SecurityTier
    
    # Component results
    security: Optional[SecurityResult] = None
    performance: Optional[PerformanceResult] = None
    backtest: Optional[BacktestResult] = None
    tee: Optional[TEEResult] = None
    llm_analysis: Optional[LLMAnalysisResult] = None
    
    # Recommendations
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Additional metadata
    error_message: Optional[str] = None
    
    @property
    def passed(self) -> bool:
        """Whether verification passed (Fort Score >= 120)."""
        return self.fort_score >= 120
    
    @property
    def deployment_ready(self) -> bool:
        """Whether agent is ready for production deployment (Fort Score >= 150)."""
        return self.fort_score >= 150
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        # Convert datetime to ISO format
        result["timestamp"] = self.timestamp.isoformat()
        # Convert enums to strings
        result["status"] = self.status.value
        result["tier"] = self.tier.value
        if self.llm_analysis:
            result["llm_analysis"]["primary_strategy"] = self.llm_analysis.primary_strategy.value
        return result
    
    def summary(self) -> str:
        """Generate a one-line summary of results."""
        return (f"{self.agent_id}: Fort Score {self.fort_score}/180 - "
                f"{self.status.value} ({self.tier.value} tier)")


# Batch verification result
@dataclass
class BatchVerificationResult:
    """Result for batch verification of multiple agents."""
    # Metadata
    batch_id: str
    timestamp: datetime
    total_processing_time_seconds: float
    
    # Aggregate statistics
    total_agents: int
    successful_verifications: int
    failed_verifications: int
    average_fort_score: float
    
    # Individual results
    results: List[VerificationResult]
    
    # Failures
    failures: List[Dict[str, str]] = field(default_factory=list)  # agent_id -> error
    
    @property
    def success_rate(self) -> float:
        """Percentage of successful verifications."""
        if self.total_agents == 0:
            return 0.0
        return (self.successful_verifications / self.total_agents) * 100
    
    @property
    def passed_agents(self) -> List[str]:
        """List of agents that passed verification."""
        return [r.agent_id for r in self.results if r.passed]
    
    @property
    def failed_agents(self) -> List[str]:
        """List of agents that failed verification."""
        return [r.agent_id for r in self.results if not r.passed]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "batch_id": self.batch_id,
            "timestamp": self.timestamp.isoformat(),
            "total_processing_time_seconds": self.total_processing_time_seconds,
            "total_agents": self.total_agents,
            "successful_verifications": self.successful_verifications,
            "failed_verifications": self.failed_verifications,
            "average_fort_score": self.average_fort_score,
            "success_rate": self.success_rate,
            "passed_agents": self.passed_agents,
            "failed_agents": self.failed_agents,
            "results": [r.to_dict() for r in self.results],
            "failures": self.failures
        }


# Export result for web UI and reports
@dataclass
class ExportableResult:
    """Result formatted for export and web display."""
    # Basic info
    title: str
    subtitle: str
    timestamp: str
    
    # Summary stats
    summary_stats: Dict[str, Union[str, int, float]]
    
    # Detailed results
    verification_results: List[Dict[str, Any]]
    
    # Charts data (for web UI)
    fort_score_distribution: List[int]
    component_scores: Dict[str, List[int]]
    timeline_data: List[Dict[str, Any]]
    
    # Metadata
    export_format: str = "html"  # html, json, pdf
    arc_verifier_version: str = "0.1.2"
    
    def to_html(self) -> str:
        """Generate HTML report."""
        # This will be implemented with the web UI
        pass
    
    def to_json(self) -> str:
        """Export as JSON."""
        import json
        return json.dumps(asdict(self), indent=2)


# Configuration models
class VerificationConfig(BaseModel):
    """Configuration for verification operations."""
    # Resource limits
    max_concurrent_verifications: int = Field(default=8, ge=1, le=100)
    max_concurrent_scans: int = Field(default=12, ge=1, le=100)
    max_concurrent_llm: int = Field(default=6, ge=1, le=20)
    
    # Feature flags
    enable_llm: bool = True
    enable_backtesting: bool = True
    enable_tee: bool = True
    
    # Provider configuration
    llm_provider: str = Field(default="anthropic", pattern="^(anthropic|openai)$")
    
    # Backtesting configuration
    backtest_period: str = Field(default="2024-10-01:2024-10-07", 
                                pattern=r"^\d{4}-\d{2}-\d{2}:\d{4}-\d{2}-\d{2}$")
    backtest_symbols: List[str] = Field(default=["BTC", "ETH"])
    
    # Timeouts
    scan_timeout_seconds: int = Field(default=300, ge=60, le=600)
    benchmark_duration_seconds: int = Field(default=60, ge=30, le=300)
    
    class Config:
        """Pydantic config."""
        use_enum_values = True
        validate_assignment = True
        
    def to_resource_limits(self):
        """Convert to ResourceLimits object."""
        from .core import ResourceLimits
        return ResourceLimits(
            max_concurrent_backtests=min(self.max_concurrent_verifications, 8),
            max_concurrent_scans=self.max_concurrent_scans,
            max_concurrent_llm=self.max_concurrent_llm,
            max_concurrent_tee=min(self.max_concurrent_verifications, 10)
        )


# Helper functions
def create_verification_id(agent_id: str) -> str:
    """Generate unique verification ID."""
    import hashlib
    timestamp = datetime.now().isoformat()
    hash_input = f"{agent_id}:{timestamp}"
    return f"ver_{hashlib.sha256(hash_input.encode()).hexdigest()[:12]}"


def create_batch_id(agents: List[str]) -> str:
    """Generate unique batch verification ID."""
    import hashlib
    timestamp = datetime.now().isoformat()
    agents_str = ",".join(sorted(agents))
    hash_input = f"{agents_str}:{timestamp}"
    return f"batch_{hashlib.sha256(hash_input.encode()).hexdigest()[:12]}"


# Export all models and helpers
__all__ = [
    # Enums
    "VerificationStatus",
    "SecurityTier",
    "SeverityLevel",
    "TradingStrategy",
    
    # Component results
    "SecurityResult",
    "PerformanceResult",
    "BacktestResult",
    "TEEResult",
    "LLMAnalysisResult",
    
    # Main results
    "VerificationResult",
    "BatchVerificationResult",
    "ExportableResult",
    
    # Configuration
    "VerificationConfig",
    
    # Helpers
    "create_verification_id",
    "create_batch_id",
]