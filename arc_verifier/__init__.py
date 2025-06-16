"""Arc-Verifier: Verification and evaluation framework for agentic protocols.

Simulates, backtests, and evaluates autonomous agents using historical 
transaction data and latest security standards.
"""

from .__version__ import __version__, __version_info__

__author__ = "Arc-Verifier Contributors"
__description__ = "Verification and evaluation framework for agentic protocols"

# High-level verification interfaces
from .core import CoreArcVerifier, ResourceLimits, CoreVerificationResult, BatchVerificationResult
from .core import VerificationPipeline, AgentStrategy

# Component modules
from . import security, analysis, data, orchestration, utils

# Public API module
from . import api

# Backward compatibility - commonly used classes
from .security import DockerScanner, TEEValidator, AuditLogger
from .analysis import Benchmarker, LLMJudge, StrategyVerifier
from .data import RealBacktester, BinanceDataFetcher, MarketDataManager, DataRegistry
from .orchestration import ParallelVerifier

__all__ = [
    # Version info
    "__version__",
    
    # Public API
    "api",
    
    # Core verification
    "CoreArcVerifier", 
    "ResourceLimits",
    "CoreVerificationResult",
    "BatchVerificationResult",
    "VerificationPipeline",
    "AgentStrategy",
    
    # Component modules
    "security",
    "analysis", 
    "data",
    "orchestration",
    "utils",
    
    # Backward compatibility
    "DockerScanner",
    "TEEValidator", 
    "Benchmarker",
    "AuditLogger",
    "LLMJudge",
    "StrategyVerifier",
    "RealBacktester",
    "BinanceDataFetcher",
    "MarketDataManager",
    "DataRegistry",
    "ParallelVerifier"
]
