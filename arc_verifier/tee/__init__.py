"""TEE (Trusted Execution Environment) validation module for Arc-Verifier.

This module provides real attestation verification for secure agent execution,
supporting multiple TEE platforms with a focus on Phala Cloud (Intel TDX/SGX).
"""

from .attestation_verifier import AttestationVerifier
from .code_hash_registry import ApprovedAgent, CodeHashRegistry, AgentStatus
from .phala_validator import PhalaCloudValidator, TEEPlatform
from .config import TEEConfig, load_config, save_config

__all__ = [
    "PhalaCloudValidator",
    "AttestationVerifier", 
    "CodeHashRegistry",
    "ApprovedAgent",
    "AgentStatus",
    "TEEPlatform",
    "TEEConfig",
    "load_config",
    "save_config"
]
