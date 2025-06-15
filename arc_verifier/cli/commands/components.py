"""Component commands for Arc-Verifier CLI.

This module contains individual component testing and analysis commands:
- scan: Docker vulnerability scanning
- benchmark: Performance benchmarking  
- backtest: Historical market data backtesting
- simulate: Agent behavioral simulation
"""

import click
from rich.console import Console

from ...security import DockerScanner
from ...analysis import Benchmarker, StrategyVerifier
from ...utils import AgentSimulator
from ...data import RealBacktester
from ..display import display_benchmark_results, display_simulation_result


console = Console()


@click.command()
@click.argument("image")
@click.option(
    "--output",
    type=click.Choice(["terminal", "json"]),
    default="terminal",
    help="Output format",
)
def scan(image: str, output: str):
    """Quick vulnerability scan of a Docker image.

    Performs Trivy-based vulnerability scanning and detects Shade agent presence.

    Examples:
        arc-verifier scan nginx:latest
        arc-verifier scan shade/agent:latest --output json
    """
    console.print(f"[bold blue]Scanning image: {image}[/bold blue]")

    scanner = DockerScanner()
    result = scanner.scan(image)

    if output == "json":
        console.print_json(data=result)
    else:
        # Terminal display
        vulns = result.get("vulnerabilities", [])
        critical = len([v for v in vulns if v.get("severity") == "CRITICAL"])
        high = len([v for v in vulns if v.get("severity") == "HIGH"])
        medium = len([v for v in vulns if v.get("severity") == "MEDIUM"])
        low = len([v for v in vulns if v.get("severity") == "LOW"])

        console.print(f"\n[bold]Scan Results:[/bold]")
        console.print(f"Critical: {critical}")
        console.print(f"High: {high}")
        console.print(f"Medium: {medium}")
        console.print(f"Low: {low}")

        if result.get("shade_agent_detected"):
            console.print("\n[green]✓ Shade agent detected[/green]")
        else:
            console.print("\n[yellow]⚠ No Shade agent detected[/yellow]")

        if critical > 0:
            console.print(f"\n[red]❌ {critical} critical vulnerabilities found[/red]")
        elif high > 5:
            console.print(f"\n[yellow]⚠️ {high} high-severity vulnerabilities[/yellow]")
        else:
            console.print("\n[green]✅ Security scan passed[/green]")


@click.command()
@click.argument("image")
@click.option("--duration", default=60, help="Benchmark duration in seconds")
@click.option("--benchmark-type", type=click.Choice(["standard", "trading", "stress"]), default="standard", help="Type of benchmark to run")
@click.option("--output", type=click.Choice(["terminal", "json"]), default="terminal", help="Output format")
def benchmark(image: str, duration: int, benchmark_type: str, output: str):
    """Run performance benchmark on a Docker image.

    Measures throughput, latency, and resource utilization under load.

    Examples:
        arc-verifier benchmark nginx:latest
        arc-verifier benchmark shade/agent:latest --benchmark-type trading
        arc-verifier benchmark myagent:latest --duration 120 --output json
    """
    console.print(f"[bold blue]Benchmarking image: {image}[/bold blue]")
    console.print(f"Duration: {duration}s")
    console.print(f"Benchmark type: {benchmark_type}")

    benchmarker = Benchmarker()
    result = benchmarker.run(image, duration=duration, benchmark_type=benchmark_type)

    if output == "json":
        console.print_json(data=result)
    else:
        display_benchmark_results(result, console)


@click.command()
@click.argument("image")
@click.option("--start-date", default="2024-10-01", help="Start date for backtesting (YYYY-MM-DD)")
@click.option("--end-date", default="2024-10-07", help="End date for backtesting (YYYY-MM-DD)")
@click.option("--symbols", default="BTC,ETH", help="Comma-separated list of symbols to test")
@click.option("--output", type=click.Choice(["terminal", "json"]), default="terminal", help="Output format")
def backtest(image: str, start_date: str, end_date: str, symbols: str, output: str):
    """Run historical backtest on a trading agent.

    Tests agent performance against real market data from specified time period.

    Examples:
        arc-verifier backtest shade/arbitrage-agent:latest
        arc-verifier backtest myagent:latest --start-date 2024-09-01 --end-date 2024-09-30
        arc-verifier backtest agent:v1 --symbols BTC,ETH,DOGE --output json
    """
    console.print(f"[bold blue]Running backtest: {image}[/bold blue]")
    console.print(f"Period: {start_date} to {end_date}")
    console.print(f"Symbols: {symbols}")

    # Parse symbols
    symbol_list = [s.strip() for s in symbols.split(",")]
    
    # Initialize backtester
    backtester = RealBacktester()
    
    try:
        # Run backtest
        result = backtester.run(
            image, 
            start_date=start_date, 
            end_date=end_date,
            symbols=symbol_list
        )
        
        if output == "json":
            # Convert to dict if it's a Pydantic model
            if hasattr(result, 'model_dump'):
                console.print_json(data=result.model_dump())
            else:
                console.print_json(data=result)
        else:
            # Terminal display
            console.print(f"\n[bold]Backtest Results:[/bold]")
            if hasattr(result, 'metrics'):
                metrics = result.metrics
                console.print(f"Total Return: {metrics.get('total_return', 0):.2%}")
                console.print(f"Annualized Return: {metrics.get('annualized_return', 0):.2%}")
                console.print(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
                console.print(f"Max Drawdown: {metrics.get('max_drawdown', 0):.2%}")
                console.print(f"Win Rate: {metrics.get('win_rate', 0):.2%}")
                console.print(f"Total Trades: {metrics.get('total_trades', 0)}")
            else:
                console.print("Backtest completed - see raw results above")
                
    except Exception as e:
        console.print(f"[red]Backtest failed: {e}[/red]")
        if output == "json":
            console.print_json(data={"error": str(e), "status": "failed"})
        raise click.ClickException(str(e))


@click.command()
@click.argument("image")
@click.option("--scenario", default="market_stress", help="Simulation scenario to run")
@click.option("--output", type=click.Choice(["terminal", "json"]), default="terminal", help="Output format")
def simulate(image: str, scenario: str, output: str):
    """Run behavioral simulation on a Docker image.

    Tests agent behavior under various market conditions and stress scenarios.

    Examples:
        arc-verifier simulate shade/agent:latest
        arc-verifier simulate myagent:latest --scenario flash_crash
        arc-verifier simulate agent:v1 --scenario high_volatility --output json
    """
    console.print(f"[bold blue]Simulating agent: {image}[/bold blue]")
    console.print(f"Scenario: {scenario}")

    # Initialize simulator
    simulator = AgentSimulator()

    try:
        # Run simulation
        result = simulator.simulate(image, scenario)

        if output == "json":
            # Convert to dict for JSON output
            if hasattr(result, 'model_dump'):
                console.print_json(data=result.model_dump())
            elif hasattr(result, '_asdict'):
                console.print_json(data=result._asdict())
            else:
                # Fallback for basic dict/object
                json_data = {
                    "scenario_name": getattr(result, 'scenario_name', scenario),
                    "passed": getattr(result, 'passed', False),
                    "execution_time_seconds": getattr(result, 'execution_time_seconds', 0),
                    "behavior_scores": getattr(result, 'behavior_scores', {}),
                    "anomalies": getattr(result, 'anomalies', []),
                    "observed_actions": getattr(result, 'observed_actions', [])
                }
                console.print_json(data=json_data)
        else:
            # Terminal display
            display_simulation_result(result, console)

    except Exception as e:
        console.print(f"[red]Simulation failed: {e}[/red]")
        if output == "json":
            console.print_json(data={"error": str(e), "status": "failed"})
        raise click.ClickException(str(e))