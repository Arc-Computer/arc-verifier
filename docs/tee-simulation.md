# TEE Simulation Mode

Arc-Verifier includes TEE (Trusted Execution Environment) validation capabilities that operate in two modes: simulation and production.

## Current Status: Simulation Mode

Arc-Verifier currently operates in **simulation mode** for TEE validation. This allows developers to:

- Test verification workflows without TEE hardware
- Understand TEE validation requirements
- Prepare for production TEE deployment
- Develop and test agent code locally

### What Simulation Mode Provides

```python
# Example output in simulation mode
🔐 Validating TEE attestation for myagent:latest
  Validating runtime measurements...
TEE Attestation: ✗ Invalid
Platform: intel_tdx
Trust Level: UNTRUSTED
Warnings:
  • Not running in TEE environment - using simulation mode
```

### Simulation Mode Behavior

1. **Attestation Validation**: Always returns "Invalid" with simulation warning
2. **Platform Detection**: Simulates Intel TDX or AMD SEV platforms
3. **Trust Level**: Always "UNTRUSTED" in simulation
4. **Fort Score Impact**: TEE component contributes 0 points in simulation

## Production Mode (Future)

When TEE hardware is available, Arc-Verifier will:

1. **Validate Real Attestations**
   - Intel SGX/TDX attestation quotes
   - AMD SEV-SNP reports
   - Phala Network TEE verification

2. **Verify Code Integrity**
   - Match code hashes against registry
   - Validate enclave measurements
   - Check attestation freshness

3. **Provide Trust Guarantees**
   - Hardware-backed security verification
   - Tamper-proof execution confirmation
   - Key isolation validation

## Configuration

### Enable/Disable TEE Validation

```bash
# Skip TEE validation entirely
arc-verifier verify myagent:latest --no-tee

# Run with TEE validation (simulation mode)
arc-verifier verify myagent:latest --enable-tee
```

### Environment Variables

```bash
# Configure TEE endpoints (for future production use)
export TEE_INTEL_PCCS_ENDPOINT="https://api.trustedservices.intel.com/sgx/certification/v4"
export TEE_PHALA_ENDPOINT="https://api.phala.network/v1/verify"

# Set TEE mode (currently only simulation supported)
export TEE_MODE="simulation"  # Default
```

## API Usage

```python
from arc_verifier.security import TEEValidator

# Create validator (automatically uses simulation mode)
validator = TEEValidator()

# Validate agent
result = validator.validate("myagent:latest")

# Check simulation mode
if result["simulation_mode"]:
    print("Running in simulation mode - no real TEE hardware")
```

## Fort Score Impact

In simulation mode:
- TEE validation always contributes 0 points
- Maximum possible Fort Score is reduced
- Production deployment requires real TEE validation

In production mode (future):
- Valid TEE attestation: +10 to +30 points
- Invalid attestation: -30 points
- Missing TEE when required: -30 points

## Development Recommendations

1. **Develop with Simulation**: Use simulation mode for local development
2. **Test Workflows**: Ensure your verification pipeline handles TEE results
3. **Plan for Production**: Design agents to run in TEE environments
4. **Monitor TEE Status**: Check warnings about simulation mode

## Roadmap

TEE production support is planned for future releases:

1. **Phase 1**: Intel SGX integration
2. **Phase 2**: AMD SEV-SNP support  
3. **Phase 3**: Phala Network validation
4. **Phase 4**: Multi-TEE platform support

## FAQ

**Q: Why does TEE validation always fail?**
A: Arc-Verifier is running in simulation mode. Real TEE hardware is required for valid attestations.

**Q: Can I deploy agents without TEE validation?**
A: Yes, but Fort Score will be limited and production deployment is not recommended without TEE validation.

**Q: When will production TEE support be available?**
A: Check the project roadmap and releases for TEE integration updates.