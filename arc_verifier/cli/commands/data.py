"""Data management commands for Arc-Verifier CLI.

This module contains data-related subcommands:
- data download: Download market data for backtesting
- data status: Show cache status and available data
- data clear: Clear cached data
"""

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from ...data import DataRegistry


console = Console()


@click.group()
def data():
    """Market data management for Arc-Verifier.
    
    Download, manage, and monitor historical market data used for 
    agent backtesting and strategy verification.
    """
    pass


@data.command()
@click.option("--symbols", default="BTC,ETH,DOGE", help="Comma-separated symbols to download")
@click.option("--period", default="7d", help="Data period (1d, 7d, 30d, 90d)")
@click.option("--force", is_flag=True, help="Force re-download existing data")
def download(symbols, period, force):
    """Download historical market data for backtesting.
    
    Downloads price and volume data from major exchanges for use in 
    strategy verification and performance backtesting.
    
    Examples:
        arc-verifier data download
        arc-verifier data download --symbols BTC,ETH,SOL --period 30d
        arc-verifier data download --force
    """
    console.print("[bold blue]Downloading Market Data[/bold blue]\n")
    
    # Parse symbols
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    
    console.print(f"Symbols: {', '.join(symbol_list)}")
    console.print(f"Period: {period}")
    console.print(f"Force download: {force}")
    
    # Create data directory
    data_dir = Path.cwd() / "market_data"
    data_dir.mkdir(exist_ok=True)
    console.print(f"Data directory: {data_dir}")
    
    # Initialize registry
    registry = DataRegistry()
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            for symbol in symbol_list:
                if not force and registry.has_data(symbol, period):
                    console.print(f"[yellow]Skipping {symbol} - data already exists (use --force to overwrite)[/yellow]")
                    continue
                
                task = progress.add_task(f"[cyan]Downloading {symbol} data...", total=None)
                
                try:
                    # Download data using registry
                    registry.download_symbol_data(symbol, period, data_dir)
                    console.print(f"[green]✓ Downloaded {symbol} ({period})[/green]")
                    
                except Exception as e:
                    console.print(f"[red]✗ Failed to download {symbol}: {e}[/red]")
                    continue
                finally:
                    progress.remove_task(task)
        
        # Update registry
        registry.save()
        console.print(f"\n[bold green]✅ Data download completed![/bold green]")
        console.print(f"[dim]Run 'arc-verifier data status' to view downloaded data[/dim]")
        
    except Exception as e:
        console.print(f"[red]Data download failed: {e}[/red]")
        raise click.ClickException(str(e))


@data.command()
@click.option("--details", is_flag=True, help="Show detailed information about each dataset")
def status(details):
    """Show market data cache status and available datasets.
    
    Displays information about downloaded market data, cache usage,
    and available data for backtesting operations.
    
    Examples:
        arc-verifier data status
        arc-verifier data status --details
    """
    console.print("[bold blue]Market Data Status[/bold blue]\n")
    
    # Check data directory
    data_dir = Path.cwd() / "market_data"
    if not data_dir.exists():
        console.print("[yellow]No market_data directory found[/yellow]")
        console.print("Run 'arc-verifier data download' to get started")
        return
    
    # Initialize registry
    registry = DataRegistry()
    
    # Calculate directory size
    total_size = sum(f.stat().st_size for f in data_dir.rglob('*') if f.is_file())
    size_mb = total_size / (1024 * 1024)
    
    # Count files
    file_count = len(list(data_dir.rglob('*.json')))
    
    # Summary table
    summary_table = Table(title="Data Cache Summary")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")
    
    summary_table.add_row("Cache Directory", str(data_dir))
    summary_table.add_row("Total Size", f"{size_mb:.1f} MB")
    summary_table.add_row("Data Files", str(file_count))
    summary_table.add_row("Registry Status", "✓ Active" if registry.registry else "⚠️ Empty")
    
    console.print(summary_table)
    
    # Available datasets
    if registry.registry and "cached_files" in registry.registry:
        cached_files = registry.registry["cached_files"]
        
        if cached_files:
            console.print("\n[bold]Available Datasets:[/bold]")
            
            if details:
                # Detailed view
                dataset_table = Table()
                dataset_table.add_column("Symbol", style="cyan")
                dataset_table.add_column("Period", style="green")
                dataset_table.add_column("Size", style="yellow")
                dataset_table.add_column("Last Updated", style="blue")
                
                for filename, info in cached_files.items():
                    size_kb = info.get("size", 0) / 1024
                    dataset_table.add_row(
                        info.get("symbol", "Unknown"),
                        info.get("period", "Unknown"), 
                        f"{size_kb:.1f} KB",
                        info.get("timestamp", "Unknown")[:10]  # Date only
                    )
                
                console.print(dataset_table)
            else:
                # Simple view
                symbols = set()
                for info in cached_files.values():
                    if "symbol" in info:
                        symbols.add(info["symbol"])
                
                console.print(f"Symbols: {', '.join(sorted(symbols))}")
        else:
            console.print("\n[yellow]No datasets found[/yellow]")
            console.print("Run 'arc-verifier data download' to download market data")
    else:
        console.print("\n[yellow]No cached data registry found[/yellow]")


@data.command()
@click.option("--symbol", help="Clear data for specific symbol only")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
def clear(symbol, confirm):
    """Clear cached market data.
    
    Removes downloaded market data to free up space or force fresh downloads.
    Use with caution as this will require re-downloading data for backtesting.
    
    Examples:
        arc-verifier data clear --confirm
        arc-verifier data clear --symbol BTC
        arc-verifier data clear  # Will prompt for confirmation
    """
    data_dir = Path.cwd() / "market_data"
    
    if not data_dir.exists():
        console.print("[yellow]No market_data directory found - nothing to clear[/yellow]")
        return
    
    # Calculate current size
    total_size = sum(f.stat().st_size for f in data_dir.rglob('*') if f.is_file())
    size_mb = total_size / (1024 * 1024)
    
    if symbol:
        console.print(f"[bold blue]Clearing data for symbol: {symbol}[/bold blue]")
        target_files = list(data_dir.glob(f"*{symbol}*"))
    else:
        console.print(f"[bold blue]Clearing all market data ({size_mb:.1f} MB)[/bold blue]")
        target_files = list(data_dir.rglob('*'))
    
    if not target_files:
        console.print(f"[yellow]No files found to clear[/yellow]")
        return
    
    # Confirmation
    if not confirm:
        if symbol:
            message = f"Clear data for {symbol}?"
        else:
            message = f"Clear all market data ({len(target_files)} files, {size_mb:.1f} MB)?"
        
        if not click.confirm(message):
            console.print("Cancelled")
            return
    
    # Clear data
    try:
        cleared_count = 0
        for file_path in target_files:
            if file_path.is_file():
                file_path.unlink()
                cleared_count += 1
            elif file_path.is_dir() and not any(file_path.iterdir()):
                file_path.rmdir()
        
        # Update registry
        registry = DataRegistry()
        if symbol:
            # Remove specific symbol from registry
            if "cached_files" in registry.registry:
                registry.registry["cached_files"] = {
                    k: v for k, v in registry.registry["cached_files"].items()
                    if not k.startswith(symbol.lower())
                }
        else:
            # Clear entire registry
            registry.registry = {"cached_files": {}}
        
        registry.save()
        
        if symbol:
            console.print(f"[green]✓ Cleared {cleared_count} files for {symbol}[/green]")
        else:
            console.print(f"[green]✓ Cleared {cleared_count} files[/green]")
            
    except Exception as e:
        console.print(f"[red]Failed to clear data: {e}[/red]")
        raise click.ClickException(str(e))