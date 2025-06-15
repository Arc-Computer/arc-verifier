"""Arc-Verifier: Lightweight NEAR Protocol agent verification tool."""

__version__ = "0.1.0"
__author__ = "NEAR Protocol"
__description__ = "Lightweight NEAR Protocol agent verification tool for Agent Forts"

from .scanner import DockerScanner
from .validator import TEEValidator
from .benchmarker import Benchmarker
from .audit_logger import AuditLogger
from .verification_pipeline import VerificationPipeline, AgentStrategy
from .data_fetcher import BinanceDataFetcher, MarketDataManager
from .data_registry import DataRegistry

__all__ = [
    "DockerScanner", 
    "TEEValidator", 
    "Benchmarker",
    "AuditLogger",
    "VerificationPipeline",
    "AgentStrategy",
    "BinanceDataFetcher",
    "MarketDataManager",
    "DataRegistry"
]
