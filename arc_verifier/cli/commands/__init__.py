"""CLI command modules for Arc-Verifier.

This package contains the command groups organized by functionality:
- verification: Core verification workflows (verify, core-verify, verify-batch, verify-strategy)
- components: Individual component testing (scan, benchmark, backtest, simulate)  
- management: System setup and audit management (init, audit-list)
"""

# Import all commands for easy access
from .verification import verify, core_verify, verify_batch, verify_strategy
from .components import scan, benchmark, backtest, simulate
from .management import init, audit_list

__all__ = [
    # Verification commands
    "verify",
    "core_verify", 
    "verify_batch",
    "verify_strategy",
    
    # Component commands
    "scan",
    "benchmark", 
    "backtest",
    "simulate",
    
    # Management commands
    "init",
    "audit_list"
]