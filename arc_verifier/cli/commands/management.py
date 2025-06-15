"""Management commands for Arc-Verifier CLI.

This module contains system setup and audit management commands:
- init: Environment initialization and configuration
- audit-list: Verification audit record management
"""

import click
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ...security import AuditLogger
from ..initialization import (
    detect_system_capabilities,
    generate_env_config, 
    write_env_file,
    download_sample_data,
    display_init_results
)


console = Console()


@click.command()
@click.option("--env", type=click.Choice(["production", "staging", "development"]), default="development", help="Environment type")
@click.option("--force", is_flag=True, help="Overwrite existing configuration")
def init(env, force):
    """Initialize Arc-Verifier environment and configuration."""
    
    console.print("[bold blue]🚀 Initializing Arc-Verifier Environment[/bold blue]\n")
    
    # Check if already initialized
    env_file = Path.cwd() / ".env"
    if env_file.exists() and not force:
        console.print("[yellow]⚠️  Arc-Verifier already initialized (.env file exists)[/yellow]")
        console.print("Use --force to overwrite existing configuration")
        return
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        # Step 1: Detect capabilities
        task = progress.add_task("[cyan]Detecting system capabilities...", total=None)
        capabilities = detect_system_capabilities()
        progress.remove_task(task)
        
        # Step 2: Generate configuration
        task = progress.add_task("[cyan]Generating configuration...", total=None)
        config = generate_env_config(env, capabilities)
        progress.remove_task(task)
        
        # Step 3: Write .env file
        task = progress.add_task("[cyan]Writing configuration file...", total=None)
        write_env_file(config, env_file)
        progress.remove_task(task)
        
        # Step 4: Download sample data (if requested)
        if env == "development":
            task = progress.add_task("[cyan]Downloading sample market data...", total=None)
            download_sample_data()
            progress.remove_task(task)
    
    # Display results
    display_init_results(env, capabilities, config, console)


@click.command()
@click.option(
    "--image",
    help="Filter audits by image name",
)
@click.option(
    "--latest",
    is_flag=True,
    help="Show only the latest audit for each image",
)
def audit_list(image: str, latest: bool):
    """List verification audit records.

    Shows verification history and audit trail for transparency and compliance.

    Examples:
        arc-verifier audit-list
        arc-verifier audit-list --image shade/agent:latest
        arc-verifier audit-list --latest
    """
    console.print("[bold blue]Verification Audit Records[/bold blue]\n")

    audit_logger = AuditLogger()
    
    try:
        # Get audit records
        records = audit_logger.get_audit_records(image_filter=image, latest_only=latest)
        
        if not records:
            console.print("[yellow]No audit records found[/yellow]")
            if image:
                console.print(f"No records found for image: {image}")
            return
        
        # Display records in table format
        from rich.table import Table
        
        table = Table(title=f"Audit Records{f' for {image}' if image else ''}")
        table.add_column("Timestamp", style="cyan")
        table.add_column("Image", style="green")
        table.add_column("Fort Score", style="yellow")
        table.add_column("Status", style="magenta")
        table.add_column("Tier", style="blue")
        
        for record in records:
            timestamp = record.get("timestamp", "Unknown")
            if isinstance(timestamp, str):
                # Format timestamp if it's a string
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamp = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            
            image_name = record.get("image", "Unknown")
            fort_score = record.get("verification_result", {}).get("fort_score", "N/A")
            status = record.get("verification_result", {}).get("status", "Unknown")
            tier = record.get("verification_result", {}).get("tier", "Unknown")
            
            # Color code status
            if status == "PASSED":
                status = f"[green]{status}[/green]"
            elif status == "FAILED":
                status = f"[red]{status}[/red]"
            else:
                status = f"[yellow]{status}[/yellow]"
            
            table.add_row(
                str(timestamp),
                image_name[:40] + "..." if len(image_name) > 40 else image_name,
                str(fort_score),
                status,
                tier
            )
        
        console.print(table)
        console.print(f"\nTotal records: {len(records)}")
        
    except Exception as e:
        console.print(f"[red]Failed to retrieve audit records: {e}[/red]")
        raise click.ClickException(str(e))