"""Tests for the TEE validator module."""

import pytest
from arc_verifier.security.tee_validator import TEEValidator


def test_validator_init():
    """Test that TEE validator initializes correctly."""
    validator = TEEValidator()
    assert validator is not None
    assert len(validator.platform_types) > 0


def test_validate_basic():
    """Test basic TEE validation."""
    validator = TEEValidator()
    result = validator.validate("test-image:latest")
    
    assert 'is_valid' in result
    assert 'measurements' in result
    assert 'quote' in result
    assert 'platform' in result
    assert 'trust_level' in result
    assert 'verification_timestamp' in result


def test_validate_shade_agent():
    """Test TEE validation for Shade agents."""
    validator = TEEValidator()
    result = validator.validate("shade/finance-agent:latest")
    
    # Shade agents should typically be valid and have high trust
    assert result['is_valid'] == True
    assert result['platform'] == "Intel SGX"
    assert result['trust_level'] == "HIGH"


def test_validate_malicious_image():
    """Test TEE validation for malicious images."""
    validator = TEEValidator()
    result = validator.validate("malicious/bad-agent:latest")
    
    # Malicious images should be invalid
    assert result['is_valid'] == False
    assert 'errors' in result
    assert result['errors'] is not None
    assert len(result['errors']) > 0


def test_measurements_structure():
    """Test TEE measurements structure."""
    validator = TEEValidator()
    result = validator.validate("test:latest")
    
    measurements = result['measurements']
    assert 'mrenclave' in measurements
    assert 'mrsigner' in measurements
    assert len(measurements['mrenclave']) == 64  # SHA256 hex length
    assert len(measurements['mrsigner']) == 64


def test_quote_structure():
    """Test TEE quote structure."""
    validator = TEEValidator()
    result = validator.validate("test:latest")
    
    quote = result['quote']
    assert 'version' in quote
    assert 'timestamp' in quote
    assert 'signature' in quote
    assert 'nonce' in quote
    assert quote['version'] == 3  # SGX DCAP v3


def test_supported_platforms():
    """Test supported TEE platforms."""
    validator = TEEValidator()
    platforms = validator.get_supported_platforms()
    
    assert "Intel SGX" in platforms
    assert "AMD SEV" in platforms
    assert "ARM TrustZone" in platforms


def test_quote_validation():
    """Test quote-only validation."""
    validator = TEEValidator()
    
    # Valid quote formats
    assert validator.validate_quote_only("0x1234567890abcdef") == True
    assert validator.validate_quote_only("quote_abc123def456") == True
    
    # Invalid quote formats
    assert validator.validate_quote_only("short") == False
    assert validator.validate_quote_only("invalid_format") == False


def test_consistent_results():
    """Test that validation results are consistent for same image."""
    validator = TEEValidator()
    
    result1 = validator.validate("test:latest")
    result2 = validator.validate("test:latest")
    
    # Platform should be consistent for same image
    assert result1['platform'] == result2['platform']
    assert result1['is_valid'] == result2['is_valid']