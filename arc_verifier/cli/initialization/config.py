"""Configuration generation and file writing for Arc-Verifier initialization."""


def generate_env_config(env_type, capabilities):
    """Generate .env configuration based on environment and capabilities."""
    
    config = {
        "# Arc-Verifier Configuration": "",
        "ARC_VERIFIER_ENV": env_type,
        "": "",
        
        "# API Configuration": "",
        "ANTHROPIC_API_KEY": "# Add your Anthropic API key here",
        "OPENAI_API_KEY": "# Add your OpenAI API key here",
        "": "",
        
        "# Resource Limits": "",
        "MAX_CONCURRENT_VERIFICATIONS": str(min(8, capabilities["cpu_cores"])),
        "MAX_CONCURRENT_SCANS": str(min(12, capabilities["cpu_cores"] * 2)),
        "MAX_CONCURRENT_LLM": str(min(6, capabilities["cpu_cores"])),
        "": "",
        
        "# TEE Configuration": "",
        "TEE_ENABLED": "true" if capabilities["tee"]["available"] else "false", 
        "TEE_PLATFORM": capabilities["tee"]["platform"],
        "TEE_SIMULATION_MODE": "false" if capabilities["tee"]["available"] else "true",
        "": "",
        
        "# Data Configuration": "",
        "MARKET_DATA_PATH": "./market_data",
        "CACHE_ENABLED": "true",
        "": "",
    }
    
    if env_type == "production":
        config.update({
            "LOG_LEVEL": "INFO",
            "ENABLE_AUDIT": "true",
            "STRICT_VALIDATION": "true"
        })
    elif env_type == "development":
        config.update({
            "LOG_LEVEL": "DEBUG", 
            "ENABLE_AUDIT": "false",
            "STRICT_VALIDATION": "false",
            "DOWNLOAD_SAMPLE_DATA": "true"
        })
    
    return config


def write_env_file(config, env_file):
    """Write configuration to .env file.""" 
    with open(env_file, 'w') as f:
        for key, value in config.items():
            if key.startswith("#"):
                f.write(f"{key}\n")
            elif key == "":
                f.write("\n")
            else:
                f.write(f"{key}={value}\n")