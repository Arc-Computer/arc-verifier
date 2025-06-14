"""TEE attestation validator for secure agent verification."""

import hashlib
import time
import json
import random
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from pydantic import BaseModel


class TEEMeasurement(BaseModel):
    """TEE measurement data."""
    mrenclave: str
    mrsigner: str
    report_data: Optional[str] = None
    enclave_held_data: Optional[str] = None


class TEEQuote(BaseModel):
    """TEE attestation quote."""
    version: int
    timestamp: datetime
    signature: str
    nonce: Optional[str] = None
    platform_info: Optional[str] = None


class AttestationResult(BaseModel):
    """TEE attestation verification result."""
    is_valid: bool
    measurements: TEEMeasurement
    quote: TEEQuote
    platform: str
    trust_level: str
    verification_timestamp: datetime
    errors: Optional[list] = None


class TEEValidator:
    """Mock TEE attestation validator for PoC with realistic simulation."""
    
    def __init__(self):
        self.console = Console()
        self.platform_types = ["Intel SGX", "AMD SEV", "ARM TrustZone", "Mock TEE"]
        
    def validate(self, image_tag: str) -> Dict[str, Any]:
        """Validate TEE attestation for an image.
        
        Args:
            image_tag: Docker image tag to validate
            
        Returns:
            Dictionary containing attestation validation results
        """
        self.console.print(f"[blue]Validating TEE attestation for {image_tag}[/blue]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("[cyan]Verifying attestation...", total=4)
            
            # Simulate TEE verification steps
            progress.update(task, description="[cyan]Connecting to TEE platform...")
            time.sleep(0.5)
            progress.advance(task)
            
            progress.update(task, description="[cyan]Validating measurements...")
            time.sleep(0.8)
            progress.advance(task)
            
            progress.update(task, description="[cyan]Verifying quote signature...")
            time.sleep(0.6)
            progress.advance(task)
            
            progress.update(task, description="[cyan]Checking trust chain...")
            time.sleep(0.4)
            progress.advance(task)
        
        # Generate attestation result
        result = self._generate_attestation_result(image_tag)
        
        status = "✓ Valid" if result.is_valid else "✗ Invalid"
        color = "green" if result.is_valid else "red"
        self.console.print(f"[{color}]TEE Attestation: {status}[/{color}]")
        
        return result.model_dump(mode='json')
    
    def _generate_attestation_result(self, image_tag: str) -> AttestationResult:
        """Generate realistic mock attestation result."""
        # Determine validity based on image characteristics
        is_valid = self._assess_image_trustworthiness(image_tag)
        
        # Select platform type
        platform = self._select_platform_type(image_tag)
        
        # Generate measurements
        measurements = self._generate_measurements(image_tag)
        
        # Generate quote
        quote = self._generate_quote(image_tag)
        
        # Determine trust level
        trust_level = self._calculate_trust_level(is_valid, image_tag)
        
        errors = None
        if not is_valid:
            errors = self._generate_validation_errors(image_tag)
        
        return AttestationResult(
            is_valid=is_valid,
            measurements=measurements,
            quote=quote,
            platform=platform,
            trust_level=trust_level,
            verification_timestamp=datetime.now(),
            errors=errors
        )
    
    def _assess_image_trustworthiness(self, image_tag: str) -> bool:
        """Assess if image should be considered trustworthy."""
        # Known problematic patterns
        untrusted_patterns = [
            'malicious', 'test-malware', 'compromised', 'unsigned',
            'debug-backdoor', 'insecure'
        ]
        
        # Check for untrusted patterns
        if any(pattern in image_tag.lower() for pattern in untrusted_patterns):
            return False
        
        # Shade agents and known good images are trusted
        trusted_patterns = [
            'shade', 'agent', 'near', 'pivortex', 'finance',
            'nginx', 'ubuntu', 'alpine', 'node', 'python'
        ]
        
        if any(pattern in image_tag.lower() for pattern in trusted_patterns):
            return True
        
        # Default to valid for demo purposes (90% success rate)
        return random.random() > 0.1
    
    def _select_platform_type(self, image_tag: str) -> str:
        """Select appropriate TEE platform type."""
        # Shade agents typically run on Intel SGX
        if any(pattern in image_tag.lower() for pattern in ['shade', 'agent', 'near']):
            return "Intel SGX"
        
        # Use hash to consistently assign platform
        hash_val = abs(hash(image_tag)) % len(self.platform_types)
        return self.platform_types[hash_val]
    
    def _generate_measurements(self, image_tag: str) -> TEEMeasurement:
        """Generate realistic TEE measurements."""
        base_hash = hashlib.sha256(image_tag.encode()).hexdigest()
        
        # Generate MRENCLAVE (measurement of enclave code)
        mrenclave = hashlib.sha256(f"mrenclave-{base_hash}".encode()).hexdigest()[:64]
        
        # Generate MRSIGNER (measurement of enclave signer)
        mrsigner = hashlib.sha256(f"mrsigner-{base_hash}".encode()).hexdigest()[:64]
        
        # Optional: report data for agent-specific data
        report_data = None
        if 'agent' in image_tag.lower():
            report_data = hashlib.sha256(f"agent-data-{base_hash}".encode()).hexdigest()[:32]
        
        return TEEMeasurement(
            mrenclave=mrenclave,
            mrsigner=mrsigner,
            report_data=report_data,
            enclave_held_data=f"ehd_{abs(hash(image_tag)):x}"[:16]
        )
    
    def _generate_quote(self, image_tag: str) -> TEEQuote:
        """Generate TEE attestation quote."""
        base_hash = hashlib.sha256(image_tag.encode()).hexdigest()
        
        # Generate quote signature
        signature = hashlib.sha256(f"quote-sig-{base_hash}-{datetime.now().isoformat()}".encode()).hexdigest()
        
        # Generate nonce for freshness
        nonce = hashlib.sha256(f"nonce-{base_hash}-{time.time()}".encode()).hexdigest()[:16]
        
        return TEEQuote(
            version=3,  # SGX DCAP v3
            timestamp=datetime.now(),
            signature=signature,
            nonce=nonce,
            platform_info=f"platform_{abs(hash(image_tag)):x}"[:8]
        )
    
    def _calculate_trust_level(self, is_valid: bool, image_tag: str) -> str:
        """Calculate trust level based on validation results."""
        if not is_valid:
            return "UNTRUSTED"
        
        # High trust for known Shade agents
        if any(pattern in image_tag.lower() for pattern in ['shade', 'pivortex', 'near']):
            return "HIGH"
        
        # Medium trust for standard images
        if any(pattern in image_tag.lower() for pattern in ['nginx', 'ubuntu', 'alpine']):
            return "MEDIUM"
        
        # Lower trust for unknown images
        return "LOW"
    
    def _generate_validation_errors(self, image_tag: str) -> list:
        """Generate realistic validation errors for failed attestations."""
        errors = []
        
        if 'malicious' in image_tag.lower():
            errors.append("MRENCLAVE measurement mismatch")
            errors.append("Untrusted signer certificate")
        
        if 'unsigned' in image_tag.lower():
            errors.append("Missing enclave signature")
        
        if 'compromised' in image_tag.lower():
            errors.append("Quote signature verification failed")
            errors.append("Platform security version too old")
        
        if not errors:
            # Default error for unknown failures
            errors.append("General attestation verification failure")
        
        return errors
    
    def get_supported_platforms(self) -> list:
        """Get list of supported TEE platforms."""
        return self.platform_types.copy()
    
    def validate_quote_only(self, quote_data: str) -> bool:
        """Validate just a quote without full attestation (for testing)."""
        try:
            # Simple validation - check if it looks like a valid quote
            if len(quote_data) < 16:  # Minimum reasonable length
                return False
            
            # Check for basic structure
            if not quote_data.startswith(('0x', 'quote_')):
                return False
            
            return True
        except Exception:
            return False