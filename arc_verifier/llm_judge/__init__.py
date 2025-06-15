"""LLM-as-Judge integration for advanced Fort scoring.

This module provides trust-focused security evaluation for autonomous trading agents.
The core question answered is: "Can this agent be trusted with user capital?"

Backward compatibility: All existing imports from arc_verifier.llm_judge continue to work.
"""

# Import everything from the modular structure
from .core import LLMJudge
from .evaluation.ensemble import EnsembleEvaluator
from .models import (
    AgentIntentClassification,
    CapitalRiskResult,
    CodeQualityAnalysis,
    DeceptionDetectionResult,
    KeySecurityResult,
    LLMJudgeResult,
    LLMProvider,
    RiskAssessment,
    TransactionControlResult,
    TrustFocusedResult,
)
from .providers.factory import create_fallback_provider, create_provider

# Import specialized analyzers for advanced usage
from .security.analyzers import (
    CapitalRiskAnalyzer,
    DeceptionDetector,
    KeySecurityAnalyzer,
    TransactionControlAnalyzer,
)
from .security.scoring import TrustScoreCalculator

__all__ = [
    # Core functionality (backward compatible)
    "LLMJudge",
    "LLMProvider",

    # Result models (backward compatible)
    "AgentIntentClassification",
    "CodeQualityAnalysis",
    "RiskAssessment",
    "KeySecurityResult",
    "TransactionControlResult",
    "DeceptionDetectionResult",
    "CapitalRiskResult",
    "TrustFocusedResult",
    "LLMJudgeResult",

    # Advanced modular components (new exports)
    "KeySecurityAnalyzer",
    "TransactionControlAnalyzer",
    "DeceptionDetector",
    "CapitalRiskAnalyzer",
    "TrustScoreCalculator",
    "EnsembleEvaluator",
    "create_provider",
    "create_fallback_provider",
]
