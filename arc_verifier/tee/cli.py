"""CLI tools for TEE configuration and agent management.

This module provides command-line tools for developers to configure
TEE validation settings and manage agent registries.
"""

import json
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .config import TEEConfig, load_config, save_config, create_example_config
from .code_hash_registry import CodeHashRegistry, ApprovedAgent, AgentStatus


console = Console()


@click.group()
def tee():
    """TEE validation configuration and management tools."""
    pass


@tee.command()
@click.option('--output', '-o', help='Output file path')
def init_config(output):
    """Create an example TEE configuration file."""
    
    if output:
        config_path = Path(output)
    else:
        config_path = Path.home() / ".arc-verifier" / "tee_config.json"
    
    if config_path.exists():
        if not click.confirm(f"Configuration file {config_path} already exists. Overwrite?"):
            return
    
    # Create example configuration
    example_content = create_example_config()
    
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(example_content)
        
        console.print(f"[green]✓[/green] Example configuration created at: {config_path}")
        console.print("\n[yellow]Next steps:[/yellow]")
        console.print("1. Edit the configuration file to match your environment")
        console.print("2. Set up certificate paths if using custom CAs")
        console.print("3. Configure agent registry settings")
        console.print("4. Run 'arc-verifier tee registry init' to initialize agent registry")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to create configuration: {e}")


@tee.command()
def show_config():
    """Display current TEE configuration."""
    
    config = load_config()
    
    console.print("[bold]Current TEE Configuration[/bold]")
    
    # Create configuration table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Registry Path", str(config.registry_path) if config.registry_path else "Default")
    table.add_row("Auto Register Local Images", str(config.auto_register_local_images))
    table.add_row("Allow Simulation Mode", str(config.allow_simulation_mode))
    table.add_row("Allow ARM64 Development", str(config.allow_arm64_development))
    table.add_row("Strict Architecture Check", str(config.strict_architecture_check))
    table.add_row("Intel PCCS Endpoint", config.intel_pccs_endpoint)
    table.add_row("Phala Verification Endpoint", config.phala_verification_endpoint)
    table.add_row("NVIDIA NRAS Endpoint", config.nvidia_nras_endpoint)
    
    console.print(table)


@tee.group()
def registry():
    """Agent registry management commands."""
    pass


@registry.command()
@click.option('--auto-discover', is_flag=True, help='Auto-discover local Docker images')
def init(auto_discover):
    """Initialize agent registry."""
    
    config = load_config()
    if auto_discover:
        config.auto_register_local_images = True
    
    # Create new registry
    registry = CodeHashRegistry(config=config)
    
    agents = registry.list_agents()
    
    console.print(f"[green]✓[/green] Agent registry initialized with {len(agents)} agents")
    
    if agents:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Agent Name", style="cyan")
        table.add_column("Image Tag", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Risk Level", style="red")
        
        for agent in agents:
            table.add_row(
                agent.agent_name,
                agent.image_tag,
                agent.status.value,
                agent.risk_level
            )
        
        console.print(table)


@registry.command()
def list():
    """List all registered agents."""
    
    registry = CodeHashRegistry()
    agents = registry.list_agents()
    
    if not agents:
        console.print("[yellow]No agents registered. Run 'arc-verifier tee registry init' first.[/yellow]")
        return
    
    console.print(f"[bold]Registered Agents ({len(agents)})[/bold]")
    
    for agent in agents:
        status_color = {
            AgentStatus.APPROVED: "green",
            AgentStatus.EXPERIMENTAL: "yellow", 
            AgentStatus.PENDING: "blue",
            AgentStatus.REVOKED: "red"
        }.get(agent.status, "white")
        
        panel = Panel(
            f"[bold]Image:[/bold] {agent.image_tag}\\n"
            f"[bold]Hash:[/bold] {agent.code_hash[:16]}...\\n"
            f"[bold]Risk Level:[/bold] {agent.risk_level}\\n"
            f"[bold]Capabilities:[/bold] {', '.join(agent.capabilities)}\\n"
            f"[bold]Approved:[/bold] {agent.approved_date.strftime('%Y-%m-%d')}",
            title=agent.agent_name,
            border_style=status_color
        )
        console.print(panel)


@registry.command()
@click.argument('image_tag')
@click.option('--name', help='Agent name')
@click.option('--description', help='Agent description')
@click.option('--risk-level', type=click.Choice(['low', 'medium', 'high']), default='medium')
@click.option('--capabilities', help='Comma-separated list of capabilities')
def add(image_tag, name, description, risk_level, capabilities):
    """Add a new agent to the registry."""
    
    registry = CodeHashRegistry()
    
    # Calculate code hash
    code_hash = registry.calculate_code_hash(image_tag)
    
    # Create agent
    agent = ApprovedAgent(
        code_hash=code_hash,
        image_tag=image_tag,
        agent_name=name or f"Agent ({image_tag})",
        description=description or f"Manually added agent for {image_tag}",
        status=AgentStatus.PENDING,
        approved_date=datetime.now(),
        risk_level=risk_level,
        capabilities=capabilities.split(',') if capabilities else ['generic'],
        metadata={
            "manually_added": "true"
        }
    )
    
    # Add to registry
    if registry.add_agent(agent):
        console.print(f"[green]✓[/green] Agent added successfully")
        console.print(f"[blue]Hash:[/blue] {code_hash[:16]}...")
    else:
        console.print(f"[red]✗[/red] Failed to add agent")


@registry.command()
@click.argument('image_tag')
@click.option('--status', type=click.Choice(['approved', 'experimental', 'pending', 'revoked']))
def approve(image_tag, status):
    """Approve or change status of an agent."""
    
    registry = CodeHashRegistry()
    code_hash = registry.calculate_code_hash(image_tag)
    
    agent = registry.get_agent(code_hash)
    if not agent:
        console.print(f"[red]✗[/red] Agent not found for image: {image_tag}")
        return
    
    # Update status
    agent.status = AgentStatus(status)
    
    if registry.add_agent(agent):  # This updates existing
        console.print(f"[green]✓[/green] Agent status updated to: {status}")
    else:
        console.print(f"[red]✗[/red] Failed to update agent status")


@registry.command()
@click.argument('image_tag')
def remove(image_tag):
    """Remove an agent from the registry."""
    
    registry = CodeHashRegistry()
    code_hash = registry.calculate_code_hash(image_tag)
    
    if registry.remove_agent(code_hash):
        console.print(f"[green]✓[/green] Agent removed successfully")
    else:
        console.print(f"[red]✗[/red] Agent not found or failed to remove")


@registry.command()
@click.argument('image_tag')
def verify(image_tag):
    """Verify if an agent is approved."""
    
    registry = CodeHashRegistry()
    code_hash = registry.calculate_code_hash(image_tag)
    
    is_approved, agent, warnings = registry.verify_code_hash(code_hash)
    
    console.print(f"[bold]Verification Result for {image_tag}[/bold]")
    console.print(f"[bold]Hash:[/bold] {code_hash[:16]}...")
    
    if is_approved:
        console.print(f"[green]✓ APPROVED[/green]")
        console.print(f"[bold]Agent:[/bold] {agent.agent_name}")
        console.print(f"[bold]Risk Level:[/bold] {agent.risk_level}")
    else:
        console.print(f"[red]✗ NOT APPROVED[/red]")
    
    if warnings:
        console.print(f"[yellow]Warnings:[/yellow]")
        for warning in warnings:
            console.print(f"  • {warning}")


if __name__ == '__main__':
    from datetime import datetime
    tee()