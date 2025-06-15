"""Pydantic models for LLM judge evaluation results."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class LLMProvider(str, Enum):
    """Supported LLM providers for agent evaluation."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    LOCAL = "local"


class AgentIntentClassification(BaseModel):
    """Agent intent classification result."""

    primary_strategy: str  # e.g., "arbitrage", "market_making", "yield_farming"
    risk_profile: str  # "conservative", "moderate", "aggressive"
    complexity_score: float  # 0.0 - 1.0
    confidence: float  # 0.0 - 1.0


class CodeQualityAnalysis(BaseModel):
    """Code quality evaluation result."""

    architecture_score: float  # 0.0 - 1.0
    error_handling_score: float  # 0.0 - 1.0
    security_practices_score: float  # 0.0 - 1.0
    maintainability_score: float  # 0.0 - 1.0
    test_coverage_score: float  # 0.0 - 1.0
    overall_score: float  # 0.0 - 1.0
    key_findings: list[str]


class RiskAssessment(BaseModel):
    """Contextual risk assessment result."""

    volatility_sensitivity: float  # 0.0 - 1.0 (higher = more sensitive)
    liquidity_requirements: str  # "low", "medium", "high"
    systemic_risk_score: float  # 0.0 - 1.0 (higher = more systemic risk)
    market_impact_score: float  # 0.0 - 1.0 (higher = more market impact)
    operational_risk_score: float  # 0.0 - 1.0
    regulatory_risk_score: float  # 0.0 - 1.0


class KeySecurityResult(BaseModel):
    """Private key security analysis result."""

    has_plaintext_keys: bool  # Critical security failure
    key_generation_secure: bool  # Generated in TEE/secure environment
    key_storage_encrypted: bool  # Keys encrypted at rest
    key_rotation_implemented: bool  # Rotation capability exists
    key_exposure_risk: str  # "low", "medium", "high", "critical"
    security_concerns: list[str]  # Specific issues found
    code_references: list[str]  # Lines/files with issues


class TransactionControlResult(BaseModel):
    """Transaction authorization control analysis."""

    has_spending_limits: bool  # Transaction amount limits
    has_approval_mechanisms: bool  # Multi-sig, time-locks, etc.
    emergency_stop_present: bool  # Circuit breaker mechanisms
    cross_chain_controls: bool  # Bridge/cross-chain security
    transaction_monitoring: bool  # Audit trail implementation
    control_strength: str  # "weak", "moderate", "strong"
    control_gaps: list[str]  # Missing or weak controls


class DeceptionDetectionResult(BaseModel):
    """Malicious pattern and deception detection."""

    backdoor_detected: bool  # Hidden admin access
    time_bomb_detected: bool  # Delayed activation logic
    obfuscated_code_found: bool  # Deliberately hidden logic
    data_exfiltration_risk: bool  # Unauthorized data transmission
    environment_specific_behavior: bool  # Different behavior in test vs prod
    deception_indicators: list[str]  # Specific suspicious patterns
    risk_level: str  # "low", "medium", "high", "critical"


class CapitalRiskResult(BaseModel):
    """Capital and financial risk assessment."""

    max_loss_bounded: bool  # Maximum possible loss is limited
    position_size_controls: bool  # Position sizing safeguards
    stop_loss_implemented: bool  # Automatic loss limits
    leverage_controls: bool  # Leverage/margin restrictions
    flash_loan_usage: bool  # Uses flash loans (higher risk)
    risk_controls_adequate: bool  # Overall risk management quality
    estimated_max_loss: str  # "bounded", "portfolio_percentage", "unlimited"


class TrustFocusedResult(BaseModel):
    """Trust-focused evaluation result for transaction agents."""

    can_trust_with_capital: bool  # Primary trust decision
    trust_score: float  # 0.0 - 1.0 overall trust score
    key_security: KeySecurityResult
    transaction_controls: TransactionControlResult
    deception_analysis: DeceptionDetectionResult
    capital_risk: CapitalRiskResult
    critical_vulnerabilities: list[str]  # Show-stopper issues
    security_recommendations: list[str]  # Required fixes
    confidence_level: float  # Confidence in analysis
    reasoning: str  # Detailed security assessment


class LLMJudgeResult(BaseModel):
    """Complete LLM judge evaluation result."""

    intent_classification: AgentIntentClassification
    code_quality: CodeQualityAnalysis
    risk_assessment: RiskAssessment
    behavioral_flags: list[str]
    score_adjustments: dict[str, float]  # category -> adjustment (-50 to +50)
    confidence_level: float  # Overall confidence in assessment
    reasoning: str  # Detailed explanation
    trust_recommendation: str | None = None  # DEPLOY/CAUTION/DO_NOT_DEPLOY
    critical_issues: list[str] = []  # Critical security issues found
    timestamp: datetime
