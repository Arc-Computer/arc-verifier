"""Configuration management for TEE validation.

This module provides configurable settings for TEE validation,
allowing developers to customize agent registries, endpoints, and certificates.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pydantic import BaseModel


@dataclass
class TEEConfig:
    """Configuration for TEE validation."""
    
    # Registry settings
    registry_path: Optional[str] = None
    auto_register_local_images: bool = False
    default_trust_level: str = "UNTRUSTED"
    
    # Platform endpoints
    intel_pccs_endpoint: str = "https://api.trustedservices.intel.com/sgx/certification/v4"
    phala_verification_endpoint: str = "https://api.phala.network/v1/verify"
    nvidia_nras_endpoint: str = "https://nras.attestation.nvidia.com/v3/attest/gpu"
    
    # Development settings
    allow_simulation_mode: bool = True
    allow_arm64_development: bool = True
    strict_architecture_check: bool = False
    
    # Trusted measurements (can be overridden)
    trusted_measurements: Optional[Dict[str, Any]] = None
    
    # Certificate paths (external files)
    intel_root_ca_path: Optional[str] = None
    custom_ca_paths: List[str] = None
    
    def __post_init__(self):
        if self.custom_ca_paths is None:
            self.custom_ca_paths = []


class AgentRegistryConfig(BaseModel):
    """Configuration for agent registry initialization."""
    
    # Built-in agent patterns (for common frameworks)
    agent_patterns: Dict[str, Dict[str, Any]] = {
        "shade": {
            "name_pattern": "*shade*",
            "default_capabilities": ["trading"],
            "default_risk_level": "medium",
            "tee_platform": "intel_tdx"
        },
        "near": {
            "name_pattern": "*near*",
            "default_capabilities": ["blockchain"],
            "default_risk_level": "low", 
            "tee_platform": "intel_tdx"
        },
        "generic": {
            "name_pattern": "*agent*",
            "default_capabilities": ["generic"],
            "default_risk_level": "high",
            "tee_platform": "intel_tdx"
        }
    }
    
    # Example configurations for developers
    example_agents: List[Dict[str, Any]] = [
        {
            "image_tag": "my-trading-agent:v1.0.0",
            "agent_name": "My Trading Agent",
            "description": "Custom trading agent for DeFi protocols",
            "capabilities": ["trading", "defi"],
            "risk_level": "medium",
            "metadata": {
                "max_position_size": "1000",
                "supported_protocols": "Uniswap,Aave",
                "tee_platform": "intel_tdx"
            }
        }
    ]


def load_config(config_path: Optional[Path] = None) -> TEEConfig:
    """Load TEE configuration from file or create default."""
    
    if config_path is None:
        config_path = Path.home() / ".arc-verifier" / "tee_config.json"
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
                return TEEConfig(**data)
        except Exception as e:
            print(f"Failed to load config from {config_path}: {e}")
            print("Using default configuration")
    
    # Return default configuration
    return TEEConfig()


def save_config(config: TEEConfig, config_path: Optional[Path | str] = None) -> bool:
    """Save TEE configuration to file."""
    
    if config_path is None:
        config_path = Path.home() / ".arc-verifier" / "tee_config.json"
    else:
        config_path = Path(config_path)
    
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(asdict(config), f, indent=2)
        
        return True
    except Exception as e:
        print(f"Failed to save config to {config_path}: {e}")
        return False


def create_example_config() -> str:
    """Create an example configuration file content."""
    
    example_config = TEEConfig(
        registry_path="~/.arc-verifier/my_agent_registry.json",
        auto_register_local_images=True,
        default_trust_level="LOW",
        allow_simulation_mode=True,
        allow_arm64_development=True,
        strict_architecture_check=False,
        intel_root_ca_path="~/.arc-verifier/certs/intel_root_ca.pem",
        custom_ca_paths=[
            "~/.arc-verifier/certs/my_custom_ca.pem"
        ]
    )
    
    return json.dumps(asdict(example_config), indent=2)


def get_default_trusted_measurements() -> Dict[str, Any]:
    """Get default trusted measurements database."""
    return {
        "intel_tdx": {
            "mr_seam": [
                # Add known good TDX module firmware hashes
                "example_tdx_module_hash_1",
                "example_tdx_module_hash_2"
            ],
            "kernel_hashes": [
                # Add known good kernel measurements
                "example_kernel_hash_1", 
                "example_kernel_hash_2"
            ]
        },
        "intel_sgx": {
            "trusted_signers": [
                # Add trusted SGX enclave signers
                "0xexample_signer_1",
                "0xexample_signer_2"
            ]
        },
        "amd_sev": {
            "firmware_versions": [
                # Add trusted SEV firmware versions
                "sev_fw_version_1",
                "sev_fw_version_2"
            ]
        },
        "nvidia_h100": {
            "driver_versions": [
                # Add trusted NVIDIA driver versions
                "nvidia_driver_1",
                "nvidia_driver_2"
            ]
        }
    }