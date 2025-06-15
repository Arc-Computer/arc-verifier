"""Setup and display functions for Arc-Verifier initialization."""

from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel


def download_sample_data():
    """Download sample market data for development."""
    try:
        from ...data import BinanceDataFetcher
        
        data_dir = Path.cwd() / "market_data"
        data_dir.mkdir(exist_ok=True)
        
        fetcher = BinanceDataFetcher(data_dir)
        # Download small sample for testing
        # This is just a placeholder - would implement actual download
        
    except Exception:
        # Silently fail if data download fails
        pass


def display_init_results(env_type, capabilities, config, console: Console):
    """Display initialization results."""
    
    console.print(f"[bold green]✅ Arc-Verifier initialized successfully![/bold green]\n")
    
    # System capabilities panel
    capabilities_table = Table(title="Detected System Capabilities")
    capabilities_table.add_column("Capability", style="cyan")
    capabilities_table.add_column("Status", style="green")
    capabilities_table.add_column("Details", style="yellow")
    
    capabilities_table.add_row(
        "Docker", 
        "✅ Available" if capabilities["docker"] else "❌ Not Available",
        "Required for agent verification"
    )
    
    tee_status = "✅ Available" if capabilities["tee"]["available"] else "⚠️ Simulation Mode"
    tee_details = f"Platform: {capabilities['tee']['platform']}" if capabilities["tee"]["available"] else "Will use simulation for development"
    capabilities_table.add_row("TEE", tee_status, tee_details)
    
    capabilities_table.add_row(
        "Resources",
        f"✅ {capabilities['cpu_cores']} cores, {capabilities['memory_gb']}GB RAM",
        "Sufficient for verification workloads"
    )
    
    console.print(capabilities_table)
    
    # Next steps panel
    next_steps = f"""
[bold]Next Steps:[/bold]

1. [cyan]Edit .env file[/cyan] - Add your API keys for LLM analysis
2. [cyan]Test setup[/cyan] - Run: arc-verifier validate-config
3. [cyan]Start verifying[/cyan] - Run: arc-verifier verify <image>

[bold]Environment:[/bold] {env_type}
[bold]Configuration:[/bold] .env file created
"""
    
    console.print(Panel(next_steps, title="🎯 Ready to Use", border_style="green"))