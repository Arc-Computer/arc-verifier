# TEE Validation Setup Guide

This guide shows developers how to configure and use the TEE validation system for verifying agent containers in their own environments.

## Quick Start

### 1. Initialize Configuration

Create a TEE configuration file:

```bash
# Create example configuration
python -m arc_verifier.tee.cli init-config

# Or specify custom location
python -m arc_verifier.tee.cli init-config --output ./my-tee-config.json
```

This creates a configuration file at `~/.arc-verifier/tee_config.json` with example settings.

### 2. Configure for Your Environment

Edit the configuration file:

```json
{
  "registry_path": "~/.arc-verifier/my_agent_registry.json",
  "auto_register_local_images": true,
  "default_trust_level": "LOW",
  "allow_simulation_mode": true,
  "allow_arm64_development": true,
  "strict_architecture_check": false,
  "intel_pccs_endpoint": "https://api.trustedservices.intel.com/sgx/certification/v4",
  "phala_verification_endpoint": "https://api.phala.network/v1/verify",
  "nvidia_nras_endpoint": "https://nras.attestation.nvidia.com/v3/attest/gpu",
  "intel_root_ca_path": "~/.arc-verifier/certs/intel_root_ca.pem",
  "custom_ca_paths": [
    "~/.arc-verifier/certs/my_custom_ca.pem"
  ]
}
```

### 3. Initialize Agent Registry

```bash
# Auto-discover local Docker images
python -m arc_verifier.tee.cli registry init --auto-discover

# Or start with example agents
python -m arc_verifier.tee.cli registry init
```

### 4. Add Your Agents

```bash
# Add a custom agent
python -m arc_verifier.tee.cli registry add my-trading-agent:v1.0.0 \\
    --name "My Trading Agent" \\
    --description "Custom DeFi trading agent" \\
    --risk-level medium \\
    --capabilities "trading,defi"

# Approve the agent
python -m arc_verifier.tee.cli registry approve my-trading-agent:v1.0.0 --status approved
```

## Configuration Options

### TEE Settings

- **`registry_path`**: Path to agent registry JSON file
- **`auto_register_local_images`**: Automatically discover Docker images matching agent patterns
- **`allow_simulation_mode`**: Allow TEE simulation when no hardware available
- **`allow_arm64_development`**: Allow development on ARM64 Macs
- **`strict_architecture_check`**: Enforce AMD64 architecture requirement

### Endpoints

Configure external service endpoints:

- **`intel_pccs_endpoint`**: Intel Platform Configuration and Certification Service
- **`phala_verification_endpoint`**: Phala Network verification service
- **`nvidia_nras_endpoint`**: NVIDIA Remote Attestation Service

### Certificates

Configure trusted CA certificates:

- **`intel_root_ca_path`**: Path to Intel SGX Root CA certificate
- **`custom_ca_paths`**: List of paths to custom CA certificates

## Agent Registry Management

### Agent Patterns

The system automatically recognizes common agent types:

```json
{
  "shade": {
    "name_pattern": "*shade*",
    "default_capabilities": ["trading"],
    "default_risk_level": "medium"
  },
  "near": {
    "name_pattern": "*near*",
    "default_capabilities": ["blockchain"], 
    "default_risk_level": "low"
  },
  "generic": {
    "name_pattern": "*agent*",
    "default_capabilities": ["generic"],
    "default_risk_level": "high"
  }
}
```

### Agent Status Levels

- **`APPROVED`**: Fully trusted agents ready for production
- **`EXPERIMENTAL`**: Agents approved for testing/development
- **`PENDING`**: Agents awaiting approval
- **`REVOKED`**: Agents that have been disabled

### Command Reference

```bash
# List all registered agents
python -m arc_verifier.tee.cli registry list

# Verify an agent
python -m arc_verifier.tee.cli registry verify my-agent:latest

# Remove an agent
python -m arc_verifier.tee.cli registry remove my-agent:latest

# Show current configuration
python -m arc_verifier.tee.cli show-config
```

## Using TEE Validation in Code

### Basic Usage

```python
import asyncio
from arc_verifier.tee import PhalaCloudValidator, CodeHashRegistry

async def validate_agent():
    # Initialize with custom config
    validator = PhalaCloudValidator()
    
    # Validate an agent
    result = await validator.validate("my-trading-agent:v1.0.0")
    
    print(f"Valid: {result.is_valid}")
    print(f"Trust Level: {result.trust_level}")
    print(f"Platform: {result.platform}")
    
    await validator.close()

# Run validation
asyncio.run(validate_agent())
```

### Custom Configuration

```python
from arc_verifier.tee import TEEConfig, PhalaCloudValidator

# Create custom configuration
config = TEEConfig(
    allow_simulation_mode=True,
    strict_architecture_check=False,
    auto_register_local_images=True
)

# Use with validator
validator = PhalaCloudValidator(config=config)
```

### Registry Operations

```python
from arc_verifier.tee import CodeHashRegistry, ApprovedAgent, AgentStatus
from datetime import datetime

# Initialize registry
registry = CodeHashRegistry()

# Add new agent
agent = ApprovedAgent(
    code_hash="abc123...",
    image_tag="my-agent:v1.0.0",
    agent_name="My Custom Agent",
    description="Description of the agent",
    status=AgentStatus.APPROVED,
    approved_date=datetime.now(),
    risk_level="medium",
    capabilities=["trading", "analytics"],
    metadata={"version": "1.0.0"}
)

registry.add_agent(agent)

# Verify agent
is_approved, agent_info, warnings = registry.verify_code_hash("abc123...")
```

## Production Deployment

### Hardware Requirements

For production TEE validation, you need:

- **Intel TDX**: CPU with Trust Domain Extensions
- **Intel SGX**: CPU with Software Guard Extensions  
- **AMD SEV**: CPU with Secure Encrypted Virtualization
- **NVIDIA H100**: GPU with attestation support

### Certificate Management

1. **Download Intel Root CA**:
   ```bash
   wget https://certificates.trustedservices.intel.com/IntelSGXRootCA.der
   openssl x509 -inform DER -in IntelSGXRootCA.der -out intel_root_ca.pem
   ```

2. **Configure certificate paths**:
   ```json
   {
     "intel_root_ca_path": "/etc/arc-verifier/certs/intel_root_ca.pem",
     "custom_ca_paths": [
       "/etc/arc-verifier/certs/my_org_ca.pem"
     ]
   }
   ```

### Environment Variables

Override configuration with environment variables:

```bash
export ARC_TEE_REGISTRY_PATH="/etc/arc-verifier/agents.json"
export ARC_TEE_STRICT_ARCH_CHECK="true"
export ARC_TEE_INTEL_ROOT_CA="/etc/ssl/certs/intel_root_ca.pem"
```

## Troubleshooting

### Common Issues

1. **"Docker image not found"**: Image must be pulled locally first
2. **"Architecture not compatible"**: Disable strict checking for development
3. **"Certificate validation failed"**: Check CA certificate paths
4. **"TEE device not found"**: Enable simulation mode for development

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# TEE validation will show detailed debug information
```

### Development vs Production

| Feature | Development | Production |
|---------|-------------|------------|
| Architecture Check | Relaxed | Strict |
| Simulation Mode | Enabled | Disabled |
| Certificate Validation | Relaxed | Strict |
| Agent Auto-Discovery | Enabled | Manual |

## Examples

See the `/examples` directory for complete working examples:

- `examples/basic_validation.py` - Simple agent validation
- `examples/custom_registry.py` - Custom agent registry setup  
- `examples/production_config.py` - Production configuration
- `examples/ci_cd_integration.py` - CI/CD pipeline integration

## Support

For issues and questions:

1. Check the [troubleshooting guide](TROUBLESHOOTING.md)
2. Review [example configurations](examples/)
3. Open an issue on GitHub with debug logs