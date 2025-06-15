"""Arc-Verifier CLI module.

This module provides a clean, modular CLI interface organized by functionality:
- Verification commands: Core verification workflows  
- Component commands: Individual component testing
- Management commands: System setup and audit management
- Display modules: Rich terminal output formatting
- Scoring modules: Fort Score calculation and status determination
- Initialization modules: System detection and configuration
"""

import click
from rich.console import Console

# Import version from main package
from .. import __version__

# Import all command groups
from .commands import (
    # Verification commands
    verify, core_verify, verify_batch, verify_strategy,
    # Component commands  
    scan, benchmark, backtest, simulate,
    # Management commands
    init, audit_list
)

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="arc-verifier")
def cli():
    """Arc-Verifier: Lightweight NEAR Protocol agent verification tool.

    Provides Docker image scanning, TEE attestation validation, and performance
    benchmarking for NEAR Agent Forts evaluation.
    """
    pass


# Add all commands to the CLI group
# Verification commands
cli.add_command(verify)
cli.add_command(core_verify, name="core-verify")
cli.add_command(verify_batch, name="verify-batch")
cli.add_command(verify_strategy, name="verify-strategy")

# Component commands
cli.add_command(scan)
cli.add_command(benchmark)
cli.add_command(backtest)
cli.add_command(simulate)

# Management commands  
cli.add_command(init)
cli.add_command(audit_list, name="audit-list")


# Entry point for module execution
if __name__ == "__main__":
    cli()