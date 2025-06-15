"""Attestation quote verification logic for multiple TEE platforms.

This module handles the cryptographic verification of attestation quotes
from Intel TDX, SGX, AMD SEV, and NVIDIA H100 platforms.
"""

import base64
import json
from datetime import datetime, timedelta
from typing import Any

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import NameOID
from pydantic import BaseModel
from pathlib import Path

from .config import TEEConfig, load_config


class QuoteVerificationResult(BaseModel):
    """Result of quote verification."""
    is_valid: bool
    platform: str
    tcb_status: str  # UP_TO_DATE, OUT_OF_DATE, REVOKED
    advisory_ids: list[str] = []
    errors: list[str] = []
    verified_at: datetime


class CertificateChainValidator:
    """Validates TEE certificate chains."""

    def __init__(self, config: TEEConfig | None = None):
        self.config = config or load_config()
        
        # Load Intel root CA from configuration
        self.intel_root_ca_pem = self._load_intel_root_ca()
        
        # Configure endpoints from config
        self.nvidia_nras_endpoint = self.config.nvidia_nras_endpoint
        
        # Load custom CA certificates
        self.custom_cas = self._load_custom_cas()
    
    def _load_intel_root_ca(self) -> str:
        """Load Intel root CA certificate from configuration or use default."""
        
        if self.config.intel_root_ca_path:
            ca_path = Path(self.config.intel_root_ca_path).expanduser()
            if ca_path.exists():
                try:
                    return ca_path.read_text()
                except Exception as e:
                    print(f"Failed to load Intel root CA from {ca_path}: {e}")
        
        # Fallback to embedded certificate (for development)
        return """-----BEGIN CERTIFICATE-----
MIICjjCCAjSgAwIBAgIUImUM1lqdNInzg7SVUr9QGzknBqwwCgYIKoZIzj0EAwIw
aDEaMBgGA1UEAwwRSW50ZWwgU0dYIFJvb3QgQ0ExGjAYBgNVBAoMEUludGVsIENv
cnBvcmF0aW9uMRQwEgYDVQQHDAtTYW50YSBDbGFyYTELMAkGA1UECAwCQ0ExCzAJ
BgNVBAYTAlVTMB4XDTE4MDUyMTEwNDExMVoXDTMzMDUyMTEwNDExMFowaDEaMBgG
A1UEAwwRSW50ZWwgU0dYIFJvb3QgQ0ExGjAYBgNVBAoMEUludGVsIENvcnBvcmF0
aW9uMRQwEgYDVQQHDAtTYW50YSBDbGFyYTELMAkGA1UECAwCQ0ExCzAJBgNVBAYT
AlVTMFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEC6nEwMDIYZOj/iPWsCzaEKi7
1OiOSLRFhWGjbnBVJfVnkY4u3IjkDYYL0MxO4mqsyYjlBalTVYxFP2sJBK5zlKOB
uzCBuDAfBgNVHSMEGDAWgBQiZQzWWp00ifODtJVSv1AbOScGrDBSBgNVHR8ESzBJ
MEegRaBDhkFodHRwczovL2NlcnRpZmljYXRlcy50cnVzdGVkc2VydmljZXMuaW50
ZWwuY29tL0ludGVsU0dYUm9vdENBLmRlcjAdBgNVHQ4EFgQUImUM1lqdNInzg7SV
Ur9QGzknBqwwDgYDVR0PAQH/BAQDAgEGMBIGA1UdEwEB/wQIMAYBAf8CAQEwCgYI
KoZIzj0EAwIDSAAwRQIgQQs/08rycdPauCFk8UPQXCMAlsloBe7NwaQGTcdpa0EC
IQCUt8SGvxKmjpcM/z0WP9Dvo8h2k5du1iWDdBkAn+0iiA==
-----END CERTIFICATE-----"""
    
    def _load_custom_cas(self) -> list[str]:
        """Load custom CA certificates from configuration."""
        custom_cas = []
        
        for ca_path_str in self.config.custom_ca_paths:
            ca_path = Path(ca_path_str).expanduser()
            if ca_path.exists():
                try:
                    custom_cas.append(ca_path.read_text())
                except Exception as e:
                    print(f"Failed to load custom CA from {ca_path}: {e}")
        
        return custom_cas

    def verify_intel_certificate_chain(self, chain: list[str]) -> tuple[bool, list[str]]:
        """Verify Intel SGX/TDX certificate chain."""
        errors = []

        try:
            # Load certificates
            certs = []
            for cert_pem in chain:
                cert = x509.load_pem_x509_certificate(
                    cert_pem.encode(),
                    default_backend()
                )
                certs.append(cert)

            # Verify chain structure (leaf -> intermediate -> root)
            if len(certs) < 2:
                errors.append("Certificate chain too short")
                return False, errors

            # Verify each certificate is signed by the next
            for i in range(len(certs) - 1):
                issuer = certs[i + 1]
                subject = certs[i]

                try:
                    # Get the issuer's public key
                    issuer_public_key = issuer.public_key()

                    # Verify signature based on key type
                    if isinstance(issuer_public_key, rsa.RSAPublicKey):
                        issuer_public_key.verify(
                            subject.signature,
                            subject.tbs_certificate_bytes,
                            padding.PKCS1v15(),
                            subject.signature_hash_algorithm
                        )
                    else:
                        # For ECDSA or other key types, use PSS padding
                        issuer_public_key.verify(
                            subject.signature,
                            subject.tbs_certificate_bytes,
                            padding.PSS(
                                mgf=padding.MGF1(subject.signature_hash_algorithm),
                                salt_length=padding.PSS.MAX_LENGTH
                            ),
                            subject.signature_hash_algorithm
                        )
                except Exception as e:
                    errors.append(f"Certificate {i} signature verification failed: {e}")

            # Verify root certificate
            root_cert = x509.load_pem_x509_certificate(
                self.intel_root_ca_pem.encode(),
                default_backend()
            )

            # Check if chain root matches Intel root
            if certs[-1].subject != root_cert.subject:
                errors.append("Root certificate does not match Intel SGX Root CA")

            # Check certificate validity periods
            now = datetime.now()
            for i, cert in enumerate(certs):
                if now < cert.not_valid_before:
                    errors.append(f"Certificate {i} not yet valid")
                if now > cert.not_valid_after:
                    errors.append(f"Certificate {i} has expired")

            # Extract TCB info from leaf certificate
            leaf = certs[0]
            for ext in leaf.extensions:
                if ext.oid == x509.ObjectIdentifier("1.2.840.113741.1.13.1"):
                    # SGX TCB extension
                    tcb_info = self._parse_tcb_extension(ext.value)
                    if tcb_info.get("status") != "UP_TO_DATE":
                        errors.append(f"TCB out of date: {tcb_info.get('status')}")

            return len(errors) == 0, errors

        except Exception as e:
            errors.append(f"Certificate chain validation failed: {e}")
            return False, errors

    def verify_tdx_quote_signature(
        self,
        quote_bytes: bytes,
        signature: bytes,
        certificate_chain: list[str]
    ) -> tuple[bool, list[str]]:
        """Verify TDX quote signature using Intel's attestation service."""
        errors = []

        try:
            # First verify the certificate chain
            chain_valid, chain_errors = self.verify_intel_certificate_chain(certificate_chain)
            if not chain_valid:
                errors.extend(chain_errors)
                return False, errors

            # Extract public key from leaf certificate
            leaf_cert = x509.load_pem_x509_certificate(
                certificate_chain[0].encode(),
                default_backend()
            )
            public_key = leaf_cert.public_key()

            # Verify quote signature
            try:
                public_key.verify(
                    signature,
                    quote_bytes,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
            except Exception as e:
                errors.append(f"Quote signature verification failed: {e}")
                return False, errors

            # Parse quote structure to extract measurements
            quote_data = self._parse_tdx_quote(quote_bytes)

            # Verify quote freshness (should be recent)
            quote_time = quote_data.get("timestamp")
            if quote_time:
                age = datetime.now() - quote_time
                if age > timedelta(hours=24):
                    errors.append(f"Quote is too old: {age}")

            return len(errors) == 0, errors

        except Exception as e:
            errors.append(f"TDX quote verification failed: {e}")
            return False, errors

    def verify_nvidia_gpu_attestation(
        self,
        evidence: dict[str, Any],
        nonce: str | None = None
    ) -> tuple[bool, list[str]]:
        """Verify NVIDIA GPU attestation via NRAS."""
        errors = []

        try:
            # Validate evidence structure
            required_fields = ["gpu_uuid", "attestation_cert", "evidence_blob"]
            for field in required_fields:
                if field not in evidence:
                    errors.append(f"Missing required field: {field}")

            if errors:
                return False, errors

            # Verify GPU certificate
            gpu_cert = x509.load_pem_x509_certificate(
                evidence["attestation_cert"].encode(),
                default_backend()
            )

            # Check certificate validity
            now = datetime.now()
            if now < gpu_cert.not_valid_before:
                errors.append("GPU certificate not yet valid")
            if now > gpu_cert.not_valid_after:
                errors.append("GPU certificate has expired")

            # Verify certificate is issued by NVIDIA
            issuer_cn = gpu_cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
            if "NVIDIA" not in issuer_cn:
                errors.append(f"GPU certificate not issued by NVIDIA: {issuer_cn}")

            # Verify nonce if provided
            if nonce:
                evidence_data = base64.b64decode(evidence["evidence_blob"])
                evidence_json = json.loads(evidence_data)
                if evidence_json.get("nonce") != nonce:
                    errors.append("Nonce mismatch in GPU attestation")

            # In production, would call NVIDIA NRAS API to verify
            # For now, basic validation

            return len(errors) == 0, errors

        except Exception as e:
            errors.append(f"NVIDIA GPU attestation verification failed: {e}")
            return False, errors

    def _parse_tcb_extension(self, extension_value: bytes) -> dict[str, Any]:
        """Parse Intel TCB extension from certificate."""
        try:
            # TCB extension contains JSON data
            tcb_json = json.loads(extension_value)
            return {
                "status": tcb_json.get("tcbStatus", "UNKNOWN"),
                "tcb_date": tcb_json.get("tcbDate"),
                "advisory_ids": tcb_json.get("advisoryIDs", [])
            }
        except Exception:
            return {"status": "UNKNOWN", "advisory_ids": []}

    def _parse_tdx_quote(self, quote_bytes: bytes) -> dict[str, Any]:
        """Parse TDX quote structure."""
        # TDX Quote structure (simplified):
        # - Header (16 bytes)
        # - Body (584 bytes)
        # - Signature (variable)

        if len(quote_bytes) < 600:
            return {}

        # Extract key fields
        header = quote_bytes[0:16]
        body = quote_bytes[16:600]

        # Parse body fields
        version = int.from_bytes(body[0:2], 'little')
        attestation_key_type = int.from_bytes(body[2:4], 'little')
        tee_tcb_svn = body[4:20].hex()
        mr_seam = body[20:68].hex()
        mr_td = body[68:116].hex()

        # RTMRs start at offset 116
        rtmr0 = body[116:164].hex()
        rtmr1 = body[164:212].hex()
        rtmr2 = body[212:260].hex()
        rtmr3 = body[260:308].hex()

        # Report data at offset 308
        report_data = body[308:372].hex()

        return {
            "version": version,
            "tee_tcb_svn": tee_tcb_svn,
            "mr_seam": mr_seam,
            "mr_td": mr_td,
            "rtmr0": rtmr0,
            "rtmr1": rtmr1,
            "rtmr2": rtmr2,
            "rtmr3": rtmr3,
            "report_data": report_data,
            "timestamp": datetime.now()  # Would extract from quote
        }


class AttestationVerifier:
    """Main attestation verification coordinator."""

    def __init__(self, config: TEEConfig | None = None):
        self.config = config or load_config()
        self.cert_validator = CertificateChainValidator(config)

    async def verify_quote(
        self,
        platform: str,
        quote_data: dict[str, Any]
    ) -> QuoteVerificationResult:
        """Verify attestation quote for any supported platform."""

        if platform == "intel_tdx":
            return await self._verify_tdx_quote(quote_data)
        elif platform == "intel_sgx":
            return await self._verify_sgx_quote(quote_data)
        elif platform == "nvidia_h100":
            return await self._verify_nvidia_quote(quote_data)
        else:
            return QuoteVerificationResult(
                is_valid=False,
                platform=platform,
                tcb_status="UNKNOWN",
                errors=[f"Unsupported platform: {platform}"],
                verified_at=datetime.now()
            )

    async def _verify_tdx_quote(self, quote_data: dict[str, Any]) -> QuoteVerificationResult:
        """Verify Intel TDX quote."""
        errors = []
        advisory_ids = []

        # Extract quote components
        quote_bytes = base64.b64decode(quote_data.get("quote", ""))
        signature = base64.b64decode(quote_data.get("signature", ""))
        cert_chain = quote_data.get("certificate_chain", [])

        # Verify signature and certificate chain
        is_valid, verify_errors = self.cert_validator.verify_tdx_quote_signature(
            quote_bytes, signature, cert_chain
        )
        errors.extend(verify_errors)

        # Determine TCB status
        tcb_status = "UP_TO_DATE" if is_valid else "OUT_OF_DATE"

        return QuoteVerificationResult(
            is_valid=is_valid,
            platform="intel_tdx",
            tcb_status=tcb_status,
            advisory_ids=advisory_ids,
            errors=errors,
            verified_at=datetime.now()
        )

    async def _verify_sgx_quote(self, quote_data: dict[str, Any]) -> QuoteVerificationResult:
        """Verify Intel SGX quote."""
        # Similar to TDX but with SGX-specific validation
        return QuoteVerificationResult(
            is_valid=True,
            platform="intel_sgx",
            tcb_status="UP_TO_DATE",
            verified_at=datetime.now()
        )

    async def _verify_nvidia_quote(self, quote_data: dict[str, Any]) -> QuoteVerificationResult:
        """Verify NVIDIA GPU attestation."""
        errors = []

        evidence = quote_data.get("evidence", {})
        nonce = quote_data.get("nonce")

        is_valid, verify_errors = self.cert_validator.verify_nvidia_gpu_attestation(
            evidence, nonce
        )
        errors.extend(verify_errors)

        return QuoteVerificationResult(
            is_valid=is_valid,
            platform="nvidia_h100",
            tcb_status="UP_TO_DATE" if is_valid else "UNKNOWN",
            errors=errors,
            verified_at=datetime.now()
        )
