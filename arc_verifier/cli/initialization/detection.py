"""System capability detection for Arc-Verifier initialization."""

from pathlib import Path


def detect_system_capabilities():
    """Detect system capabilities for Arc-Verifier."""
    capabilities = {
        "docker": False,
        "tee": {"available": False, "platform": "none"},
        "gpu": False,
        "memory_gb": 0,
        "cpu_cores": 0
    }
    
    # Check Docker
    try:
        import docker
        client = docker.from_env()
        client.ping()
        capabilities["docker"] = True
    except:
        pass
    
    # Check TEE capabilities
    tee_paths = {
        "/dev/tdx-guest": "intel_tdx",
        "/dev/sgx_enclave": "intel_sgx", 
        "/dev/sev-guest": "amd_sev"
    }
    
    for path, platform in tee_paths.items():
        if Path(path).exists():
            capabilities["tee"]["available"] = True
            capabilities["tee"]["platform"] = platform
            break
    
    # Check system resources
    try:
        import psutil
        capabilities["memory_gb"] = round(psutil.virtual_memory().total / (1024**3))
        capabilities["cpu_cores"] = psutil.cpu_count()
    except ImportError:
        # Fallback to basic detection
        try:
            import os
            capabilities["cpu_cores"] = os.cpu_count() or 4
        except:
            capabilities["cpu_cores"] = 4
        capabilities["memory_gb"] = 8  # Default assumption
    
    return capabilities