"""Arc-Verifier CLI interface."""

import click
import json
import os
import time
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Load environment variables
try:
    from dotenv import load_dotenv

    # Look for .env file in current directory or project root
    env_paths = [Path.cwd() / ".env", Path(__file__).parent.parent / ".env"]
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            break
except ImportError:
    pass  # dotenv not available, continue without it

from . import __version__
from .scanner import DockerScanner
from .validator import TEEValidator
from .benchmarker import Benchmarker
from .llm_judge import LLMJudge
from .strategy_verifier import StrategyVerifier
from .audit_logger import AuditLogger
from .parallel_verifier import ParallelVerifier

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="arc-verifier")
def cli():
    """Arc-Verifier: Lightweight NEAR Protocol agent verification tool.

    Provides Docker image scanning, TEE attestation validation, and performance
    benchmarking for NEAR Agent Forts evaluation.
    """
    pass


@cli.command()
@click.argument("image")
@click.option(
    "--tier",
    type=click.Choice(["high", "medium", "low"]),
    default="medium",
    help="Security tier for verification",
)
@click.option(
    "--output",
    type=click.Choice(["terminal", "json"]),
    default="terminal",
    help="Output format",
)
@click.option(
    "--enable-llm/--no-llm",
    default=True,
    help="Enable LLM-based behavioral analysis (default: enabled)",
)
@click.option(
    "--llm-provider",
    type=click.Choice(["anthropic", "openai", "local"]),
    default="anthropic",
    help="LLM provider for analysis",
)
def verify(image: str, tier: str, output: str, enable_llm: bool, llm_provider: str):
    """Verify a Docker image for NEAR Agent Fort deployment.

    Performs comprehensive verification including vulnerability scanning,
    TEE attestation validation, and performance benchmarking.

    Examples:
        arc-verifier verify shade/finance-agent:latest
        arc-verifier verify pivortex/shade-agent-template:latest --tier high
        arc-verifier verify myagent:latest --output json
    """
    console.print(f"[bold blue]Verifying image: {image}[/bold blue]")
    console.print(f"Security tier: {tier}")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Now including strategy verification
        total_tasks = 5 if enable_llm else 4
        task = progress.add_task("[cyan]Running verification...", total=total_tasks)

        # Docker scanning
        progress.update(task, description="[cyan]Scanning Docker image...")
        scanner = DockerScanner()
        scan_result = scanner.scan(image)
        progress.advance(task)

        # TEE validation
        progress.update(task, description="[cyan]Validating TEE attestation...")
        validator = TEEValidator()
        tee_result = validator.validate(image)
        progress.advance(task)

        # Performance benchmark
        progress.update(task, description="[cyan]Running performance benchmark...")
        benchmarker = Benchmarker()
        benchmark_type = (
            "trading"
            if any(
                pattern in image.lower() for pattern in ["shade", "agent", "finance"]
            )
            else "standard"
        )
        perf_result = benchmarker.run(image, duration=30, benchmark_type=benchmark_type)
        progress.advance(task)

        # LLM-based behavioral analysis
        llm_result = None
        if enable_llm:
            progress.update(
                task, description="[cyan]Running LLM behavioral analysis..."
            )
            try:
                llm_judge = LLMJudge(primary_provider=llm_provider)
                llm_result = llm_judge.evaluate_agent(
                    image_data=scan_result,
                    market_context={
                        "tier": tier,
                        "timestamp": scan_result.get("timestamp"),
                    },
                )
            except Exception as e:
                import traceback

                console.print(f"[red]LLM analysis failed: {e}[/red]")
                console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")
                llm_result = None
            progress.advance(task)

        # Strategy verification with real market data
        strategy_result = None
        progress.update(task, description="[cyan]Verifying trading strategy...")
        try:
            verifier = StrategyVerifier()
            # Use a short recent period by default
            strategy_result = verifier.verify_strategy(
                image,
                use_regime="bull_2024"  # Use cached regime data if available
            )
        except Exception as e:
            console.print(f"[yellow]Strategy verification skipped: {e}[/yellow]")
            strategy_result = None
        progress.advance(task)

    # Show analysis status
    if enable_llm:
        if llm_result:
            console.print(
                f"[green]🧠 LLM behavioral analysis completed - Strategy: {llm_result.intent_classification.primary_strategy}[/green]"
            )
        else:
            console.print(
                "[yellow]🧠 LLM analysis not available (check API keys in .env)[/yellow]"
            )
    
    if strategy_result:
        console.print(
            f"[green]📈 Strategy verification completed - Type: {strategy_result.detected_strategy} "
            f"(effectiveness: {strategy_result.strategy_effectiveness:.0f}/100)[/green]"
        )

    # Display results
    if output == "json":
        # Combine all results into JSON format
        # Convert datetime to ISO string for JSON serialization
        scan_result_json = scan_result.copy()
        if "timestamp" in scan_result_json:
            if hasattr(scan_result_json["timestamp"], "isoformat"):
                scan_result_json["timestamp"] = scan_result_json[
                    "timestamp"
                ].isoformat()

        verification_result = {
            "verification_id": f"ver_{abs(hash(image + str(scan_result['timestamp']))):x}"[
                :15
            ],
            "image": image,
            "tier": tier,
            "timestamp": scan_result_json["timestamp"],
            "docker_scan": scan_result_json,
            "tee_validation": tee_result,
            "performance_benchmark": perf_result,
            "llm_analysis": llm_result.model_dump(mode="json") if llm_result else None,
            "strategy_verification": strategy_result.model_dump() if strategy_result else None,
            "agent_fort_score": _calculate_agent_fort_score(
                scan_result, tee_result, perf_result, llm_result, strategy_result
            ),
            "overall_status": _determine_overall_status(
                scan_result, tee_result, perf_result, llm_result, strategy_result
            ),
        }
        console.print_json(data=verification_result)
        
        # Log to audit trail
        audit_logger = AuditLogger()
        audit_logger.log_verification(
            image=image,
            verification_result=verification_result,
            llm_reasoning=llm_result.reasoning if llm_result else None
        )
    else:
        _display_terminal_results(scan_result, tee_result, perf_result, llm_result, strategy_result)
        
        # Log to audit trail
        audit_logger = AuditLogger()
        verification_result = {
            "image": image,
            "tier": tier,
            "docker_scan": scan_result,
            "tee_validation": tee_result,
            "performance_benchmark": perf_result,
            "llm_analysis": llm_result.model_dump() if llm_result else None,
            "strategy_verification": strategy_result.model_dump() if strategy_result else None,
            "agent_fort_score": _calculate_agent_fort_score(
                scan_result, tee_result, perf_result, llm_result, strategy_result
            ),
            "overall_status": _determine_overall_status(
                scan_result, tee_result, perf_result, llm_result, strategy_result
            ),
        }
        audit_logger.log_verification(
            image=image,
            verification_result=verification_result,
            llm_reasoning=llm_result.reasoning if llm_result else None
        )


@cli.command()
@click.argument("image")
@click.option(
    "--output",
    type=click.Choice(["terminal", "json"]),
    default="terminal",
    help="Output format",
)
def scan(image: str, output: str):
    """Quick vulnerability scan of a Docker image.

    Performs rapid security scanning without full verification workflow.

    Examples:
        arc-verifier scan nginx:latest
        arc-verifier scan myagent:latest --output json
    """
    console.print(f"[bold blue]Scanning image: {image}[/bold blue]")

    # Run Docker scan
    scanner = DockerScanner()
    scan_result = scanner.scan(image)

    if output == "json":
        console.print_json(data=scan_result)
    else:
        table = Table(title=f"Scan Results for {image}")
        table.add_column("Check", style="cyan")
        table.add_column("Result", style="green")

        # Count vulnerabilities by severity
        vulns = scan_result.get("vulnerabilities", [])
        critical = len([v for v in vulns if v.get("severity") == "CRITICAL"])
        high = len([v for v in vulns if v.get("severity") == "HIGH"])
        medium = len([v for v in vulns if v.get("severity") == "MEDIUM"])
        low = len([v for v in vulns if v.get("severity") == "LOW"])

        vuln_summary = f"{critical} critical, {high} high, {medium} medium, {low} low"
        if critical > 0:
            vuln_color = "red"
            vuln_status = f"✗ {vuln_summary}"
        elif high > 0:
            vuln_color = "yellow"
            vuln_status = f"⚠ {vuln_summary}"
        else:
            vuln_color = "green"
            vuln_status = f"✓ {vuln_summary}"

        table.add_row("Image ID", scan_result.get("image_id", "N/A")[:12] + "...")
        table.add_row("Size", f"{scan_result.get('size', 0) / 1024 / 1024:.1f} MB")
        table.add_row("Vulnerabilities", f"[{vuln_color}]{vuln_status}[/{vuln_color}]")
        table.add_row(
            "Shade Agent",
            (
                "✓ Detected"
                if scan_result.get("shade_agent_detected")
                else "✗ Not detected"
            ),
        )

        console.print(table)


@cli.command()
@click.argument("image")
@click.option(
    "--scenario",
    type=click.Choice(["price_oracle", "arbitrage", "all"]),
    default="all",
    help="Simulation scenario type",
)
@click.option(
    "--output",
    type=click.Choice(["terminal", "json"]),
    default="terminal",
    help="Output format",
)
def simulate(image: str, scenario: str, output: str):
    """Run behavioral simulation on a Docker image.

    Tests agent behavior in controlled scenarios to verify claimed functionality.

    Examples:
        arc-verifier simulate shade/oracle-agent:latest --scenario price_oracle
        arc-verifier simulate myagent:latest --scenario arbitrage --output json
    """
    from .simulator import AgentSimulator, ScenarioLibrary
    import asyncio
    from ..tests.fixtures.mock_server import MockServerManager

    console.print(f"[bold blue]Starting agent simulation for: {image}[/bold blue]")
    console.print(f"Scenario type: {scenario}")

    # Start mock server
    mock_manager = MockServerManager()
    import threading

    server_thread = threading.Thread(target=mock_manager.run_in_background, daemon=True)
    server_thread.start()
    time.sleep(2)  # Give server time to start

    # Initialize simulator
    simulator = AgentSimulator()

    # Get scenarios
    scenarios = []
    if scenario == "price_oracle" or scenario == "all":
        scenarios.extend(ScenarioLibrary.get_price_oracle_scenarios())
    if scenario == "arbitrage" or scenario == "all":
        scenarios.extend(ScenarioLibrary.get_arbitrage_scenarios())

    # Run simulations
    results = []
    for sim_scenario in scenarios:
        # Update mock server with scenario data
        asyncio.run(mock_manager.update_scenario(sim_scenario.steps[0].market_data))

        # Run simulation
        result = simulator.run_simulation(image, sim_scenario)
        results.append(result)

        # Display result
        if output == "terminal":
            _display_simulation_result(result)

    if output == "json":
        # Convert results to JSON format
        json_results = [r.model_dump(mode="json") for r in results]
        console.print_json(
            data={
                "image": image,
                "simulations": json_results,
                "summary": {
                    "total": len(results),
                    "passed": len([r for r in results if r.passed]),
                    "failed": len([r for r in results if not r.passed]),
                },
            }
        )


@cli.command()
@click.argument("image")
@click.option(
    "--start-date", default="2024-01-01", help="Backtest start date (YYYY-MM-DD)"
)
@click.option("--end-date", default="2024-12-31", help="Backtest end date (YYYY-MM-DD)")
@click.option(
    "--strategy",
    type=click.Choice(["arbitrage", "momentum", "market_making"]),
    default="arbitrage",
    help="Strategy type to simulate",
)
@click.option(
    "--regime",
    type=click.Choice(["bull_2024", "bear_2024", "volatile_2024", "sideways_2024"]),
    default=None,
    help="Use pre-defined market regime (overrides start/end dates)",
)
@click.option(
    "--use-real-data/--use-mock-data",
    default=True,
    help="Use real market data (if available) or mock data",
)
@click.option(
    "--output",
    type=click.Choice(["terminal", "json"]),
    default="terminal",
    help="Output format",
)
def backtest(
    image: str, 
    start_date: str, 
    end_date: str, 
    strategy: str, 
    regime: str,
    use_real_data: bool,
    output: str
):
    """Run historical backtest on a trading agent.

    Simulates agent performance using historical market data to predict profitability.

    Examples:
        arc-verifier backtest shade/arbitrage-agent:latest
        arc-verifier backtest myagent:latest --regime bull_2024
        arc-verifier backtest agent:v1 --strategy momentum --use-mock-data
        arc-verifier backtest agent:v1 --output json
    """
    # Use real backtester - the only production-ready implementation
    from .real_backtester import RealBacktester
    from .data_registry import DataRegistry
    
    console.print(f"[bold blue]Backtesting image: {image}[/bold blue]")
    console.print(f"Period: {start_date} to {end_date} | Strategy: {strategy}")
    
    try:
        # Check if we have real data available
        registry = DataRegistry()
        has_data = len(registry.registry.get("cached_files", {})) > 0
        
        if has_data and use_real_data:
            console.print("[green]Using real market data for backtest[/green]")
        elif use_real_data:
            console.print("[yellow]No real market data cached, downloading may be needed[/yellow]")
            console.print("[dim]Tip: Run 'python scripts/download_market_data.py --regimes' to download data[/dim]")
        else:
            console.print("[blue]Using real backtester with available data[/blue]")

        # Run backtest with real implementation
        backtester = RealBacktester()
        result = backtester.run(
            image, 
            start_date, 
            end_date, 
            strategy,
            use_cached_regime=regime
        )
        
        if output == "json":
            console.print_json(data=result.model_dump())
        else:
            backtester.display_results(result)
            
    except Exception as e:
        console.print(f"[red]Backtest failed: {e}[/red]")
        console.print("[dim]Ensure market data is available or check your configuration[/dim]")
        raise click.ClickException(f"Backtest failed: {e}")


@cli.command()
@click.argument("image")
@click.option(
    "--start-date", 
    default=None, 
    help="Verification start date (YYYY-MM-DD)"
)
@click.option(
    "--end-date", 
    default=None, 
    help="Verification end date (YYYY-MM-DD)"
)
@click.option(
    "--regime",
    type=click.Choice(["bull_2024", "bear_2024", "volatile_2024", "sideways_2024"]),
    default=None,
    help="Use pre-defined market regime (overrides start/end dates)",
)
@click.option(
    "--output",
    type=click.Choice(["terminal", "json"]),
    default="terminal",
    help="Output format",
)
def verify_strategy(image: str, start_date: str, end_date: str, regime: str, output: str):
    """Verify trading strategy implementation and effectiveness.

    Analyzes agent behavior to detect strategy type, verify claimed functionality,
    and assess performance potential.

    Examples:
        arc-verifier verify-strategy shade/arbitrage-agent:latest
        arc-verifier verify-strategy myagent:latest --regime bull_2024
        arc-verifier verify-strategy agent:v1 --start-date 2024-10-01 --end-date 2024-10-07
    """
    console.print(f"[bold blue]Verifying strategy for: {image}[/bold blue]")
    
    # Initialize verifier
    verifier = StrategyVerifier()
    
    try:
        # Run verification
        result = verifier.verify_strategy(
            image,
            start_date=start_date,
            end_date=end_date,
            use_regime=regime
        )
        
        if output == "json":
            console.print_json(data=result.model_dump())
        else:
            verifier.display_verification_report(result)
            
    except Exception as e:
        console.print(f"[red]Strategy verification failed: {e}[/red]")
        if output == "json":
            console.print_json(data={"error": str(e), "status": "failed"})
        raise click.ClickException(str(e))


@cli.command()
@click.argument("image")
@click.option("--duration", default=60, help="Benchmark duration in seconds")
@click.option(
    "--type",
    "benchmark_type",
    type=click.Choice(["standard", "trading", "stress"]),
    default="standard",
    help="Benchmark type",
)
@click.option(
    "--output",
    type=click.Choice(["terminal", "json"]),
    default="terminal",
    help="Output format",
)
def benchmark(image: str, duration: int, benchmark_type: str, output: str):
    """Run performance benchmark on a Docker image.

    Tests container performance under load for the specified duration.

    Examples:
        arc-verifier benchmark myagent:latest
        arc-verifier benchmark shade/finance-agent:latest --duration 120 --type trading
        arc-verifier benchmark myagent:latest --type stress --output json
    """
    console.print(f"[bold blue]Benchmarking image: {image}[/bold blue]")
    console.print(f"Duration: {duration} seconds | Type: {benchmark_type}")

    # Run benchmark
    benchmarker = Benchmarker()
    result = benchmarker.run(image, duration, benchmark_type)

    if output == "json":
        console.print_json(data=result)
    else:
        _display_benchmark_results(result)


def _display_simulation_result(result):
    """Display simulation result in terminal format."""
    from rich.panel import Panel
    from rich.table import Table

    # Status panel
    status_color = "green" if result.passed else "red"
    status_text = "✓ PASSED" if result.passed else "✗ FAILED"

    console.print(
        Panel(
            f"[bold {status_color}]{status_text}[/bold {status_color}]\n"
            f"Scenario: {result.scenario_name}\n"
            f"Execution Time: {result.execution_time_seconds:.1f}s",
            title="Simulation Result",
            border_style=status_color,
        )
    )

    # Behavior scores table
    scores_table = Table(title="Behavioral Scores")
    scores_table.add_column("Metric", style="cyan")
    scores_table.add_column("Score", style="green")
    scores_table.add_column("Rating", style="yellow")

    for metric, score in result.behavior_scores.items():
        rating = (
            "Excellent"
            if score >= 0.9
            else "Good" if score >= 0.7 else "Fair" if score >= 0.5 else "Poor"
        )
        scores_table.add_row(metric.title(), f"{score:.2f}", rating)

    console.print(scores_table)

    # Anomalies if any
    if result.anomalies:
        console.print("\n[red]Anomalies Detected:[/red]")
        for anomaly in result.anomalies:
            console.print(f"  • {anomaly}")

    # Action summary
    if result.observed_actions:
        console.print(
            f"\n[blue]Observed Actions:[/blue] {len(result.observed_actions)}"
        )
        action_types = {}
        for action in result.observed_actions:
            action_type = action.get("type", "unknown")
            action_types[action_type] = action_types.get(action_type, 0) + 1

        for action_type, count in action_types.items():
            console.print(f"  • {action_type}: {count}")


def _display_benchmark_results(result: dict):
    """Display benchmark results in terminal format."""
    perf = result.get("performance", {})
    resources = result.get("resources", {})
    trading = result.get("trading_metrics", {})

    # Main metrics table
    table = Table(
        title=f"Benchmark Results - {result.get('benchmark_type', 'standard').title()}"
    )
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    # Performance metrics
    table.add_row("Throughput", f"{perf.get('throughput_tps', 0):.0f} TPS")
    table.add_row("Avg Latency", f"{perf.get('avg_latency_ms', 0):.1f} ms")
    table.add_row("P95 Latency", f"{perf.get('p95_latency_ms', 0):.1f} ms")
    table.add_row("P99 Latency", f"{perf.get('p99_latency_ms', 0):.1f} ms")
    table.add_row("Error Rate", f"{perf.get('error_rate_percent', 0):.1f}%")

    # Resource metrics
    table.add_row("CPU Usage", f"{resources.get('cpu_percent', 0):.1f}%")
    table.add_row("Memory Peak", f"{resources.get('memory_mb', 0):.0f} MB")
    table.add_row("Network RX", f"{resources.get('network_rx_mb', 0):.1f} MB")
    table.add_row("Network TX", f"{resources.get('network_tx_mb', 0):.1f} MB")

    console.print(table)

    # Trading-specific metrics if available
    if trading:
        trading_table = Table(title="Trading Metrics")
        trading_table.add_column("Operation", style="cyan")
        trading_table.add_column("Avg Latency", style="green")
        trading_table.add_column("Throughput", style="yellow")

        for key, value in trading.items():
            if "avg_latency_ms" in key:
                op_name = key.replace("_avg_latency_ms", "").replace("_", " ").title()
                throughput_key = key.replace("avg_latency_ms", "throughput_ops")
                throughput = trading.get(throughput_key, 0)
                trading_table.add_row(op_name, f"{value:.1f} ms", f"{throughput} ops")

        if trading_table.rows:
            console.print(trading_table)


def _display_terminal_results(
    scan_result: dict, tee_result: dict, perf_result: dict, llm_result=None, strategy_result=None
):
    """Display verification results in terminal format."""
    table = Table(title="Verification Results")
    table.add_column("Check", style="cyan")
    table.add_column("Result", style="green")

    # Vulnerability analysis
    vulns = scan_result.get("vulnerabilities", [])
    critical = len([v for v in vulns if v.get("severity") == "CRITICAL"])
    high = len([v for v in vulns if v.get("severity") == "HIGH"])
    medium = len([v for v in vulns if v.get("severity") == "MEDIUM"])
    low = len([v for v in vulns if v.get("severity") == "LOW"])

    if critical > 0:
        vuln_status = f"[red]✗ {critical} critical, {high} high[/red]"
    elif high > 0:
        vuln_status = f"[yellow]⚠ {high} high, {medium} medium[/yellow]"
    else:
        vuln_status = f"[green]✓ {medium} medium, {low} low[/green]"

    table.add_row("Vulnerabilities", vuln_status)

    # TEE status
    tee_valid = tee_result.get("is_valid", True)
    tee_platform = tee_result.get("platform", "Unknown")
    tee_status = f"✓ {tee_platform}" if tee_valid else f"✗ {tee_platform}"
    tee_color = "green" if tee_valid else "red"
    table.add_row("TEE Attestation", f"[{tee_color}]{tee_status}[/{tee_color}]")

    table.add_row(
        "Shade Agent",
        "✓ Detected" if scan_result.get("shade_agent_detected") else "✗ Not detected",
    )

    # Performance metrics
    perf_metrics = perf_result.get("performance", {})
    throughput = perf_metrics.get("throughput_tps", 0)
    avg_latency = perf_metrics.get("avg_latency_ms", 0)
    table.add_row("Performance", f"✓ {throughput:.0f} TPS, {avg_latency:.1f}ms avg")

    # LLM Analysis (if available)
    if llm_result:
        intent = llm_result.intent_classification
        risk_profile = intent.risk_profile
        strategy = intent.primary_strategy
        confidence = llm_result.confidence_level

        llm_status = f"✓ {strategy.title()} | {risk_profile.title()} Risk | {confidence:.0%} Confidence"
        if llm_result.behavioral_flags:
            flag_count = len(llm_result.behavioral_flags)
            llm_status += f" | {flag_count} Flag{'s' if flag_count != 1 else ''}"

        table.add_row("LLM Analysis", llm_status)
    
    # Strategy verification
    if strategy_result:
        strategy_status = f"✓ {strategy_result.detected_strategy.title()} | "
        strategy_status += f"Effectiveness: {strategy_result.strategy_effectiveness:.0f}/100 | "
        strategy_status += f"Risk: {strategy_result.risk_score:.0f}/100"
        
        status_icon = "✓" if strategy_result.verification_status == "verified" else "⚠"
        table.add_row("Strategy Verification", f"{status_icon} {strategy_status}")

    # Overall status
    overall_status = _determine_overall_status(
        scan_result, tee_result, perf_result, llm_result, strategy_result
    )
    status_color = "green" if overall_status == "PASSED" else "red"
    table.add_row(
        "Overall Status", f"[{status_color}]✓ {overall_status}[/{status_color}]"
    )

    console.print(table)

    # Calculate Agent Fort Score
    score = _calculate_agent_fort_score(
        scan_result, tee_result, perf_result, llm_result, strategy_result
    )
    score_color = "green" if score >= 80 else "yellow" if score >= 60 else "red"

    # Enhanced score display with LLM insights
    score_text = f"[bold {score_color}]{score}/180[/bold {score_color}]"
    if llm_result and llm_result.score_adjustments:
        total_llm_adjustment = sum(llm_result.score_adjustments.values())
        if total_llm_adjustment != 0:
            adjustment_color = "green" if total_llm_adjustment > 0 else "red"
            score_text += f"\n[{adjustment_color}]LLM Adjustment: {total_llm_adjustment:+.1f}[/{adjustment_color}]"

    score_panel = Panel(score_text, title="Agent Fort Score", border_style=score_color)
    console.print(score_panel)

    # Display LLM insights if available
    if llm_result and llm_result.reasoning:
        insights_panel = Panel(
            llm_result.reasoning[:300]
            + ("..." if len(llm_result.reasoning) > 300 else ""),
            title="🧠 LLM Insights",
            border_style="blue",
        )
        console.print(insights_panel)


def _calculate_agent_fort_score(
    scan_result: dict, tee_result: dict, perf_result: dict, llm_result=None, strategy_result=None
) -> int:
    """Calculate Agent Fort score based on verification results with balanced scoring.
    
    New balanced scoring (based on executive feedback):
    - Base score: 100
    - Security: ±30 points max (was ±50)
    - LLM: ±30 points max (was ±50)
    - Behavior: ±30 points (unchanged)
    - Performance: -50 to +90 points (was -40 to +80)
    
    Total range: 0-180 points
    """
    score = 100

    # SECURITY SCORING (±30 points max)
    security_adjustment = 0
    
    # Vulnerability penalties (capped at -20)
    vulns = scan_result.get("vulnerabilities", [])
    critical = len([v for v in vulns if v.get("severity") == "CRITICAL"])
    high = len([v for v in vulns if v.get("severity") == "HIGH"])
    medium = len([v for v in vulns if v.get("severity") == "MEDIUM"])
    
    vuln_penalty = min(20, critical * 10 + high * 5 + medium * 2)
    security_adjustment -= vuln_penalty

    # TEE validation bonus/penalty
    if not tee_result.get("is_valid", True):
        security_adjustment -= 10
    else:
        # Bonus for high trust level
        trust_level = tee_result.get("trust_level", "LOW")
        if trust_level == "HIGH":
            security_adjustment += 5
        elif trust_level == "MEDIUM":
            security_adjustment += 3

    # Shade agent detection bonus
    if scan_result.get("shade_agent_detected", False):
        security_adjustment += 5

    # Cap security adjustments at ±30
    security_adjustment = max(-30, min(30, security_adjustment))
    score += security_adjustment

    # LLM INTELLIGENCE SCORING (±30 points max)
    llm_adjustment = 0
    
    if llm_result:
        # Base LLM score adjustments
        if llm_result.score_adjustments:
            for category, adjustment in llm_result.score_adjustments.items():
                llm_adjustment += adjustment

        # Code quality assessment
        if hasattr(llm_result, "code_quality") and llm_result.code_quality:
            code_quality_bonus = (llm_result.code_quality.overall_score - 0.5) * 10
            llm_adjustment += code_quality_bonus

        # Risk assessment
        if hasattr(llm_result, "risk_assessment") and llm_result.risk_assessment:
            # Critical risk flag = auto-reject (separate from scoring)
            if llm_result.risk_assessment.systemic_risk_score > 0.9:
                # This would trigger auto-reject in the status determination
                llm_adjustment -= 30
            else:
                systemic_risk_penalty = llm_result.risk_assessment.systemic_risk_score * 10
                llm_adjustment -= systemic_risk_penalty

        # Behavioral flags
        if llm_result.behavioral_flags:
            llm_adjustment -= min(10, len(llm_result.behavioral_flags) * 3)
    
    # Cap LLM adjustments at ±30
    llm_adjustment = max(-30, min(30, llm_adjustment))
    score += llm_adjustment

    # BEHAVIORAL TESTING SCORING (±30 points, from Phase 3A simulation)
    # Note: This is currently embedded in basic performance metrics
    # Will be properly separated when Phase 3A simulation results are available
    behavior_adjustment = 0
    
    # Basic performance checks (temporary placeholder for behavior scoring)
    perf_metrics = perf_result.get("performance", {})
    throughput = perf_metrics.get("throughput_tps", 0)
    avg_latency = perf_metrics.get("avg_latency_ms", 0)
    error_rate = perf_metrics.get("error_rate_percent", 0)

    # Throughput check
    if throughput < 500:
        behavior_adjustment -= 10
    elif throughput > 2000:
        behavior_adjustment += 5

    # Latency check
    if avg_latency > 100:
        behavior_adjustment -= 5
    elif avg_latency < 20:
        behavior_adjustment += 5

    # Error rate check
    if error_rate > 5:
        behavior_adjustment -= 10
    elif error_rate < 1:
        behavior_adjustment += 5

    # Cap behavior adjustments at ±30
    behavior_adjustment = max(-30, min(30, behavior_adjustment))
    score += behavior_adjustment

    # PERFORMANCE VERIFICATION SCORING (-50 to +90 points, Phase 3B)
    performance_adjustment = 0
    
    if strategy_result:
        # Strategy verification: Does it actually work as advertised? (up to +40)
        if strategy_result.verification_status == "verified":
            performance_adjustment += 30
        elif strategy_result.verification_status == "partial":
            performance_adjustment += 15
        else:
            performance_adjustment -= 20
            
        # Effectiveness score contribution (up to +30)
        effectiveness_bonus = (strategy_result.strategy_effectiveness / 100) * 30
        performance_adjustment += effectiveness_bonus
        
        # Risk management (-20 to +10)
        risk_penalty = 0
        if strategy_result.risk_score > 80:
            risk_penalty = -20  # Very high risk
        elif strategy_result.risk_score > 60:
            risk_penalty = -10  # High risk
        elif strategy_result.risk_score < 30:
            risk_penalty = 10   # Low risk, well managed
        performance_adjustment += risk_penalty
        
        # Consistency across regimes (up to +20)
        if hasattr(strategy_result, 'performance_by_regime'):
            positive_regimes = sum(1 for r in strategy_result.performance_by_regime.values() 
                                 if r.get('annualized_return', 0) > 0)
            regime_bonus = (positive_regimes / len(strategy_result.performance_by_regime)) * 20
            performance_adjustment += regime_bonus
    else:
        # No strategy verification available, use basic performance metrics
        if error_rate == 0 and throughput > 1000:
            performance_adjustment += 10  # Basic competence bonus
    
    # Final score calculation
    final_score = score + performance_adjustment
    
    # Ensure score stays within 0-180 range
    return max(0, min(180, int(final_score)))


def _determine_overall_status(
    scan_result: dict, tee_result: dict, perf_result: dict, llm_result=None, strategy_result=None
) -> str:
    """Determine overall verification status with LLM and strategy insights."""
    vulns = scan_result.get("vulnerabilities", [])
    critical = len([v for v in vulns if v.get("severity") == "CRITICAL"])
    high = len([v for v in vulns if v.get("severity") == "HIGH"])

    tee_valid = tee_result.get("is_valid", True)

    perf_metrics = perf_result.get("performance", {})
    error_rate = perf_metrics.get("error_rate_percent", 0)

    # LLM-based risk factors
    llm_risk_flags = 0
    if llm_result:
        # Count serious behavioral flags
        serious_flags = [
            flag
            for flag in llm_result.behavioral_flags
            if any(
                keyword in flag.lower()
                for keyword in ["malicious", "suspicious", "high risk", "dangerous"]
            )
        ]
        llm_risk_flags = len(serious_flags)

        # Check for high systemic risk
        if (
            hasattr(llm_result, "risk_assessment")
            and llm_result.risk_assessment
            and llm_result.risk_assessment.systemic_risk_score > 0.8
        ):
            llm_risk_flags += 1

    # Fail conditions (enhanced with LLM)
    if critical > 0:
        return "FAILED"
    if not tee_valid:
        return "FAILED"
    if error_rate > 10:
        return "FAILED"
    if llm_risk_flags >= 2:  # Multiple serious LLM flags
        return "FAILED"

    # Warning conditions (enhanced with LLM)
    if high > 5:
        return "WARNING"
    if error_rate > 5:
        return "WARNING"
    if llm_risk_flags >= 1:  # Single serious LLM flag
        return "WARNING"
    if llm_result and llm_result.confidence_level < 0.5:  # Low LLM confidence
        return "WARNING"
    
    # Strategy verification checks
    if strategy_result:
        if strategy_result.verification_status == "failed":
            return "FAILED"
        if strategy_result.risk_score > 80:  # Very high risk strategy
            return "WARNING"
        if strategy_result.strategy_effectiveness < 40:  # Low effectiveness
            return "WARNING"

    return "PASSED"


@cli.command()
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
    
    Shows historical verification results with audit trail.
    
    Examples:
        arc-verifier audit-list
        arc-verifier audit-list --image shade/finance-agent
        arc-verifier audit-list --latest
    """
    audit_logger = AuditLogger()
    audits = audit_logger.list_audits(image_filter=image)
    
    if not audits:
        console.print("[yellow]No audit records found[/yellow]")
        return
        
    table = Table(title="Verification Audit Trail")
    table.add_column("Timestamp", style="cyan")
    table.add_column("Image", style="yellow")
    table.add_column("Fort Score", style="green")
    table.add_column("Status", style="bold")
    
    # Filter to latest if requested
    if latest:
        seen_images = set()
        filtered_audits = []
        for audit in audits:
            if audit["image"] not in seen_images:
                filtered_audits.append(audit)
                seen_images.add(audit["image"])
        audits = filtered_audits
    
    for audit in audits:
        status_color = "green" if audit["status"] == "PASSED" else "red"
        table.add_row(
            audit["timestamp"],
            audit["image"],
            str(audit["fort_score"]),
            f"[{status_color}]{audit['status']}[/{status_color}]"
        )
        
    console.print(table)
    console.print(f"\n[dim]Total records: {len(audits)}[/dim]")


@cli.command()
@click.argument("images", nargs=-1, required=True)
@click.option(
    "--tier",
    type=click.Choice(["high", "medium", "low"]),
    default="medium",
    help="Security tier for verification",
)
@click.option(
    "--output",
    type=click.Choice(["terminal", "json"]),
    default="terminal",
    help="Output format",
)
@click.option(
    "--enable-llm/--no-llm",
    default=True,
    help="Enable LLM-based behavioral analysis (default: enabled)",
)
@click.option(
    "--llm-provider",
    type=click.Choice(["anthropic", "openai", "local"]),
    default="anthropic",
    help="LLM provider for analysis",
)
@click.option(
    "--max-concurrent",
    type=int,
    default=3,
    help="Maximum concurrent verifications (default: 3)",
)
def verify_batch(
    images: tuple,
    tier: str,
    output: str,
    enable_llm: bool,
    llm_provider: str,
    max_concurrent: int,
):
    """Verify multiple Docker images in parallel using Dagger.

    Performs comprehensive verification of multiple agents concurrently,
    including vulnerability scanning, TEE attestation, and performance benchmarking.

    Examples:
        arc-verifier verify-batch shade/agent1:latest shade/agent2:latest
        arc-verifier verify-batch myagent:v1 myagent:v2 myagent:v3 --tier high
        arc-verifier verify-batch agent1:latest agent2:latest --max-concurrent 5
        arc-verifier verify-batch --output json agent1:latest agent2:latest agent3:latest
    """
    if not images:
        console.print("[red]Error: No images provided[/red]")
        raise click.ClickException("At least one image must be specified")
    
    console.print(f"[bold blue]Starting batch verification of {len(images)} images[/bold blue]")
    console.print(f"Security tier: {tier}")
    console.print(f"Max concurrent: {max_concurrent}")
    
    # Initialize parallel verifier
    verifier = ParallelVerifier(max_concurrent=max_concurrent)
    
    # Run async verification
    import asyncio
    try:
        result = asyncio.run(
            verifier.verify_batch(
                list(images),
                tier=tier,
                enable_llm=enable_llm,
                llm_provider=llm_provider
            )
        )
        
        if output == "json":
            # Convert to JSON-serializable format
            json_result = {
                "batch_verification": {
                    "total_images": result.total_images,
                    "successful": result.successful,
                    "failed": result.failed,
                    "duration_seconds": result.duration_seconds,
                    "timestamp": result.timestamp.isoformat(),
                    "images": list(images),
                    "results": result.results
                }
            }
            console.print_json(data=json_result)
            
            # Log batch results
            audit_logger = AuditLogger()
            for res in result.results:
                audit_logger.log_verification(
                    image=res["image"],
                    verification_result=res,
                    llm_reasoning=res.get("llm_analysis", {}).get("reasoning") if res.get("llm_analysis") else None
                )
        else:
            # Terminal output is handled by ParallelVerifier
            # Log batch results
            audit_logger = AuditLogger()
            for res in result.results:
                audit_logger.log_verification(
                    image=res["image"],
                    verification_result=res,
                    llm_reasoning=res.get("llm_analysis", {}).get("reasoning") if res.get("llm_analysis") else None
                )
            
            # Display final summary
            console.print(f"\n[bold]Batch Verification Complete[/bold]")
            console.print(f"Total time: {result.duration_seconds:.1f}s")
            console.print(f"Success rate: {(result.successful / result.total_images * 100):.1f}%")
            
    except Exception as e:
        console.print(f"[red]Batch verification failed: {e}[/red]")
        raise click.ClickException(str(e))


if __name__ == "__main__":
    cli()
