"""TEE (Trusted Execution Environment) validation module for Arc-Verifier.

This module provides real attestation verification for secure agent execution,
supporting multiple TEE platforms with a focus on Phala Cloud (Intel TDX/SGX).
"""

from .phala_validator import PhalaCloudValidator
from .attestation_verifier import AttestationVerifier
from .code_hash_registry import CodeHashRegistry, ApprovedAgent

__all__ = [
    "PhalaCloudValidator", 
    "AttestationVerifier", 
    "CodeHashRegistry",
    "ApprovedAgent"
]