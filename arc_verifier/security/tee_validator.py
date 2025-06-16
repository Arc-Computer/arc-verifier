"""TEE attestation validator for secure agent verification.

This module now serves as a compatibility layer that delegates to the
real TEE validation implementation in the tee/ module.
"""

import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

from rich.console import Console

from ..tee import PhalaCloudValidator, CodeHashRegistry, AttestationVerifier


class TEEValidator:
    """TEE attestation validator that uses real Phala Cloud implementation.
    
    This class maintains backward compatibility while delegating to the
    production-ready TEE validation system.
    """
    
    def __init__(self, console=None):
        self.console = console or Console()
        self.phala_validator = PhalaCloudValidator(console=self.console)
        self.code_registry = CodeHashRegistry()
        self.attestation_verifier = AttestationVerifier()
        
    def validate(self, image_tag: str) -> Dict[str, Any]:
        """Validate TEE attestation for an image.
        
        Args:
            image_tag: Docker image tag to validate
            
        Returns:
            Dictionary containing attestation validation results
        """
        # Run async validation in sync context for backward compatibility
        result = asyncio.run(self._async_validate(image_tag))
        return result
    
    async def _async_validate(self, image_tag: str) -> Dict[str, Any]:
        """Async validation implementation."""
        # Check for docker-compose.yaml in current directory
        compose_path = Path.cwd() / "docker-compose.yaml"
        if not compose_path.exists():
            compose_path = None
            
        # Perform real TEE validation
        attestation_result = await self.phala_validator.validate(
            image_tag,
            docker_compose_path=compose_path
        )
        
        # Check code hash against registry
        code_hash = attestation_result.code_hash
        is_approved, agent_info, warnings = self.code_registry.verify_code_hash(code_hash)
        
        # Add registry information to result
        result_dict = attestation_result.model_dump(mode="json")
        result_dict['registry_status'] = {
            'is_approved': is_approved,
            'agent_name': agent_info.agent_name if agent_info else None,
            'strategy': agent_info.metadata.get('strategy') if agent_info else None,
            'risk_level': agent_info.metadata.get('risk_level') if agent_info else None,
            'warnings': warnings
        }
        
        # Map to legacy format for compatibility
        legacy_result = {
            'is_valid': attestation_result.is_valid and is_approved,
            'measurements': result_dict.get('measurements', {}),
            'quote': result_dict.get('quote'),
            'platform': result_dict.get('platform'),
            'trust_level': result_dict.get('trust_level'),
            'verification_timestamp': result_dict.get('verification_timestamp'),
            'errors': result_dict.get('errors', []),
            # Additional fields from new implementation
            'code_hash': code_hash,
            'registry_status': result_dict['registry_status']
        }
        
        return legacy_result
    
    def get_supported_platforms(self) -> list:
        """Get list of supported TEE platforms."""
        return [
            "Intel TDX",  # Primary platform for Phala Cloud
            "Intel SGX",  # Legacy support
            "AMD SEV",    # Future support
            "NVIDIA H100" # GPU attestation
        ]
    
    def validate_quote_only(self, quote_data: str) -> bool:
        """Validate just a quote without full attestation (for testing)."""
        try:
            # Delegate to attestation verifier
            quote_dict = {
                "quote": quote_data.replace('0x', ''),
                "signature": "",
                "certificate_chain": []
            }
            result = asyncio.run(
                self.attestation_verifier.verify_quote("intel_tdx", quote_dict)
            )
            return result.is_valid
        except Exception:
            return False
    
    async def close(self):
        """Clean up resources."""
        await self.phala_validator.close()