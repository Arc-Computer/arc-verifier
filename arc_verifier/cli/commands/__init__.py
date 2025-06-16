"""CLI command modules for Arc-Verifier.

This package contains the command groups organized by functionality:
- verification: Core verification workflows (verify, batch)
- components: Individual component testing (scan, benchmark, backtest, simulate)  
- config: Configuration management (validate, show)
- data: Market data management (download, status, clear)
- management: System setup and audit management (init, history)
"""

# Import all commands for easy access
from .verification import verify, batch
from .components import scan, benchmark, backtest, simulate
from .management import init, audit_list
from .config import config
from .data import data
from .export import export

__all__ = [
    # Verification commands
    "verify",
    "batch",
    
    # Component commands
    "scan",
    "benchmark", 
    "backtest",
    "simulate",
    
    # Management commands
    "init",
    "audit_list",
    
    # Command groups
    "config",
    "data",
    "export"
]