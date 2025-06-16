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
    verify, batch,
    # Component commands  
    scan, benchmark, backtest, simulate,
    # Management commands
    init, audit_list,
    # Command groups
    config, data, export
)

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="arc-verifier")
def cli():
    """Arc-Verifier: Verification and evaluation framework for agentic protocols.

    Simulates, backtests, and evaluates autonomous agents using historical 
    transaction data and latest security standards. Built for developers to 
    stress test and measure performance and reliability of agent systems.
    """
    pass


# Add all commands to the CLI group
# Primary verification commands
cli.add_command(verify)
cli.add_command(batch)

# Component testing commands
cli.add_command(scan)
cli.add_command(benchmark)
cli.add_command(backtest)
cli.add_command(simulate)

# Setup and management
cli.add_command(init)
cli.add_command(audit_list, name="history")

# Command groups
cli.add_command(config)
cli.add_command(data)
cli.add_command(export)


# Entry point for module execution
if __name__ == "__main__":
    cli()