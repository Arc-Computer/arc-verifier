"""Configuration management commands for Arc-Verifier CLI.

This module contains configuration-related subcommands:
- config validate: Environment validation
- config show: Display current configuration
"""

import click
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table

from ..initialization import detect_system_capabilities


console = Console()


@click.group()
def config():
    """Configuration management for Arc-Verifier.
    
    Manage environment setup, validation, and display current settings.
    """
    pass


@config.command()
@click.option("--fix", is_flag=True, help="Attempt to fix configuration issues automatically")
def validate(fix):
    """Validate Arc-Verifier configuration and environment.
    
    Checks configuration files, API keys, system dependencies, and 
    verifies the environment is ready for agent verification.
    
    Examples:
        arc-verifier config validate
        arc-verifier config validate --fix
    """
    console.print("[bold blue]Validating Arc-Verifier Configuration[/bold blue]\n")
    
    issues = []
    warnings = []
    
    # Check .env file exists
    env_file = Path.cwd() / ".env"
    if not env_file.exists():
        issues.append("No .env file found. Run 'arc-verifier init' to create one.")
    else:
        console.print("[green]✓ .env file found[/green]")
        
        # Load and validate .env contents
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            console.print("[green]✓ .env file loaded successfully[/green]")
        except Exception as e:
            issues.append(f".env file cannot be loaded: {e}")
    
    # Check API keys
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not anthropic_key or anthropic_key.startswith("#"):
        warnings.append("ANTHROPIC_API_KEY not configured (LLM analysis will be limited)")
    else:
        console.print("[green]✓ Anthropic API key configured[/green]")
        
    if not openai_key or openai_key.startswith("#"):
        warnings.append("OPENAI_API_KEY not configured (GPT-4.1 analysis not available)")
    else:
        console.print("[green]✓ OpenAI API key configured[/green]")
    
    # Check Docker availability
    try:
        import docker
        client = docker.from_env()
        client.ping()
        console.print("[green]✓ Docker is available and running[/green]")
    except Exception as e:
        issues.append(f"Docker not available: {e}")
    
    # Check system capabilities
    capabilities = detect_system_capabilities()
    
    if capabilities["cpu_cores"] < 4:
        warnings.append(f"Low CPU cores ({capabilities['cpu_cores']}). Recommended: 4+")
    else:
        console.print(f"[green]✓ CPU cores: {capabilities['cpu_cores']}[/green]")
        
    if capabilities["memory_gb"] < 8:
        warnings.append(f"Low memory ({capabilities['memory_gb']}GB). Recommended: 8GB+")
    else:
        console.print(f"[green]✓ Memory: {capabilities['memory_gb']}GB[/green]")
    
    # Check TEE status
    if not capabilities["tee"]["available"]:
        warnings.append("TEE not available - using simulation mode (development only)")
    else:
        console.print(f"[green]✓ TEE available: {capabilities['tee']['platform']}[/green]")
    
    # Check data directory
    data_dir = Path.cwd() / "market_data"
    if not data_dir.exists():
        warnings.append("No market_data directory found. Run 'arc-verifier data download' for sample data.")
    else:
        console.print("[green]✓ Market data directory exists[/green]")
    
    # Display results
    if issues:
        console.print("\n[red]Configuration Issues Found:[/red]")
        for issue in issues:
            console.print(f"  ❌ {issue}")
            
        if fix:
            console.print("\n[yellow]Attempting to fix issues...[/yellow]")
            if "No .env file found" in str(issues):
                console.print("Run 'arc-verifier init' to create configuration")
        
        raise click.ClickException("Configuration validation failed")
    
    if warnings:
        console.print("\n[yellow]Configuration Warnings:[/yellow]")
        for warning in warnings:
            console.print(f"  ⚠️  {warning}")
    
    console.print("\n[bold green]✅ Configuration validation passed![/bold green]")
    console.print("[dim]Your Arc-Verifier environment is ready for agent verification.[/dim]")


@config.command()
@click.option("--format", type=click.Choice(["table", "json", "env"]), default="table", help="Output format")
def show(format):
    """Display current Arc-Verifier configuration.
    
    Shows environment variables, system capabilities, and current settings
    used by Arc-Verifier for verification operations.
    
    Examples:
        arc-verifier config show
        arc-verifier config show --format json
        arc-verifier config show --format env
    """
    console.print("[bold blue]Arc-Verifier Configuration[/bold blue]\n")
    
    # Load configuration
    from dotenv import load_dotenv
    
    env_file = Path.cwd() / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        console.print(f"[green]Configuration loaded from: {env_file}[/green]\n")
    else:
        console.print("[yellow]No .env file found - using defaults[/yellow]\n")
    
    # Get system capabilities
    capabilities = detect_system_capabilities()
    
    # Collect configuration data
    config_data = {
        "environment": {
            "ARC_VERIFIER_ENV": os.getenv("ARC_VERIFIER_ENV", "development"),
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
            "ENABLE_AUDIT": os.getenv("ENABLE_AUDIT", "false"),
            "STRICT_VALIDATION": os.getenv("STRICT_VALIDATION", "false")
        },
        "api_keys": {
            "ANTHROPIC_API_KEY": "configured" if os.getenv("ANTHROPIC_API_KEY") and not os.getenv("ANTHROPIC_API_KEY").startswith("#") else "not configured",
            "OPENAI_API_KEY": "configured" if os.getenv("OPENAI_API_KEY") and not os.getenv("OPENAI_API_KEY").startswith("#") else "not configured"
        },
        "resource_limits": {
            "MAX_CONCURRENT_VERIFICATIONS": os.getenv("MAX_CONCURRENT_VERIFICATIONS", "8"),
            "MAX_CONCURRENT_SCANS": os.getenv("MAX_CONCURRENT_SCANS", "12"),
            "MAX_CONCURRENT_LLM": os.getenv("MAX_CONCURRENT_LLM", "6")
        },
        "tee_configuration": {
            "TEE_ENABLED": os.getenv("TEE_ENABLED", "false"),
            "TEE_PLATFORM": os.getenv("TEE_PLATFORM", "none"),
            "TEE_SIMULATION_MODE": os.getenv("TEE_SIMULATION_MODE", "true")
        },
        "data_configuration": {
            "MARKET_DATA_PATH": os.getenv("MARKET_DATA_PATH", "./market_data"),
            "CACHE_ENABLED": os.getenv("CACHE_ENABLED", "true")
        },
        "system_capabilities": {
            "docker_available": capabilities["docker"],
            "cpu_cores": capabilities["cpu_cores"],
            "memory_gb": capabilities["memory_gb"],
            "tee_available": capabilities["tee"]["available"],
            "tee_platform": capabilities["tee"]["platform"]
        }
    }
    
    # Display based on format
    if format == "json":
        console.print_json(data=config_data)
    elif format == "env":
        # Show as environment variable format
        for section, settings in config_data.items():
            if section != "system_capabilities":  # Skip read-only capabilities
                console.print(f"# {section.replace('_', ' ').title()}")
                for key, value in settings.items():
                    if key.endswith("_KEY") and value == "configured":
                        console.print(f"{key}=***")  # Hide actual key values
                    else:
                        console.print(f"{key}={value}")
                console.print()
    else:
        # Table format (default)
        
        # Environment settings
        env_table = Table(title="Environment Settings")
        env_table.add_column("Setting", style="cyan")
        env_table.add_column("Value", style="green")
        
        for key, value in config_data["environment"].items():
            env_table.add_row(key, str(value))
        
        console.print(env_table)
        
        # API configuration
        api_table = Table(title="API Configuration")
        api_table.add_column("Provider", style="cyan")
        api_table.add_column("Status", style="green")
        
        for key, value in config_data["api_keys"].items():
            provider = key.replace("_API_KEY", "").title()
            status_color = "green" if value == "configured" else "yellow"
            api_table.add_row(provider, f"[{status_color}]{value}[/{status_color}]")
        
        console.print(api_table)
        
        # System capabilities
        sys_table = Table(title="System Capabilities")
        sys_table.add_column("Capability", style="cyan")
        sys_table.add_column("Status", style="green")
        
        caps = config_data["system_capabilities"]
        sys_table.add_row("Docker", "✓ Available" if caps["docker_available"] else "❌ Not Available")
        sys_table.add_row("CPU Cores", str(caps["cpu_cores"]))
        sys_table.add_row("Memory", f"{caps['memory_gb']}GB")
        sys_table.add_row("TEE", f"✓ {caps['tee_platform']}" if caps["tee_available"] else "⚠️ Simulation Mode")
        
        console.print(sys_table)