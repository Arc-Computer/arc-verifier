"""Arc-Verifier CLI interface."""

import click
import json
import os
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
@click.argument('image')
@click.option('--tier', type=click.Choice(['high', 'medium', 'low']), 
              default='medium', help='Security tier for verification')
@click.option('--output', type=click.Choice(['terminal', 'json']), 
              default='terminal', help='Output format')
@click.option('--enable-llm/--no-llm', default=True,
              help='Enable LLM-based behavioral analysis (default: enabled)')
@click.option('--llm-provider', type=click.Choice(['anthropic', 'openai', 'local']),
              default='anthropic', help='LLM provider for analysis')
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
        total_tasks = 4 if enable_llm else 3
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
        benchmark_type = "trading" if any(pattern in image.lower() for pattern in ['shade', 'agent', 'finance']) else "standard"
        perf_result = benchmarker.run(image, duration=30, benchmark_type=benchmark_type)
        progress.advance(task)
        
        # LLM-based behavioral analysis
        llm_result = None
        if enable_llm:
            progress.update(task, description="[cyan]Running LLM behavioral analysis...")
            try:
                llm_judge = LLMJudge(primary_provider=llm_provider)
                llm_result = llm_judge.evaluate_agent(
                    image_data=scan_result,
                    market_context={"tier": tier, "timestamp": scan_result.get('timestamp')}
                )
            except Exception as e:
                import traceback
                console.print(f"[red]LLM analysis failed: {e}[/red]")
                console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")
                llm_result = None
            progress.advance(task)
    
    # Show LLM analysis status
    if enable_llm:
        if llm_result:
            console.print(f"[green]🧠 LLM behavioral analysis completed - Strategy: {llm_result.intent_classification.primary_strategy}[/green]")
        else:
            console.print("[yellow]🧠 LLM analysis not available (check API keys in .env)[/yellow]")
    
    # Display results
    if output == 'json':
        # Combine all results into JSON format
        # Convert datetime to ISO string for JSON serialization
        scan_result_json = scan_result.copy()
        if 'timestamp' in scan_result_json:
            if hasattr(scan_result_json['timestamp'], 'isoformat'):
                scan_result_json['timestamp'] = scan_result_json['timestamp'].isoformat()
        
        verification_result = {
            "verification_id": f"ver_{abs(hash(image + str(scan_result['timestamp']))):x}"[:15],
            "image": image,
            "tier": tier,
            "timestamp": scan_result_json['timestamp'],
            "docker_scan": scan_result_json,
            "tee_validation": tee_result,
            "performance_benchmark": perf_result,
            "llm_analysis": llm_result.model_dump(mode='json') if llm_result else None,
            "agent_fort_score": _calculate_agent_fort_score(scan_result, tee_result, perf_result, llm_result),
            "overall_status": _determine_overall_status(scan_result, tee_result, perf_result, llm_result)
        }
        console.print_json(data=verification_result)
    else:
        _display_terminal_results(scan_result, tee_result, perf_result, llm_result)


@cli.command()
@click.argument('image')
@click.option('--output', type=click.Choice(['terminal', 'json']), 
              default='terminal', help='Output format')
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
    
    if output == 'json':
        console.print_json(data=scan_result)
    else:
        table = Table(title=f"Scan Results for {image}")
        table.add_column("Check", style="cyan")
        table.add_column("Result", style="green")
        
        # Count vulnerabilities by severity
        vulns = scan_result.get('vulnerabilities', [])
        critical = len([v for v in vulns if v.get('severity') == 'CRITICAL'])
        high = len([v for v in vulns if v.get('severity') == 'HIGH'])
        medium = len([v for v in vulns if v.get('severity') == 'MEDIUM'])
        low = len([v for v in vulns if v.get('severity') == 'LOW'])
        
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
        
        table.add_row("Image ID", scan_result.get('image_id', 'N/A')[:12] + "...")
        table.add_row("Size", f"{scan_result.get('size', 0) / 1024 / 1024:.1f} MB")
        table.add_row("Vulnerabilities", f"[{vuln_color}]{vuln_status}[/{vuln_color}]")
        table.add_row("Shade Agent", "✓ Detected" if scan_result.get('shade_agent_detected') else "✗ Not detected")
        
        console.print(table)


@cli.command()
@click.argument('image')
@click.option('--duration', default=60, help='Benchmark duration in seconds')
@click.option('--type', 'benchmark_type', type=click.Choice(['standard', 'trading', 'stress']), 
              default='standard', help='Benchmark type')
@click.option('--output', type=click.Choice(['terminal', 'json']), 
              default='terminal', help='Output format')
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
    
    if output == 'json':
        console.print_json(data=result)
    else:
        _display_benchmark_results(result)


def _display_benchmark_results(result: dict):
    """Display benchmark results in terminal format."""
    perf = result.get('performance', {})
    resources = result.get('resources', {})
    trading = result.get('trading_metrics', {})
    
    # Main metrics table
    table = Table(title=f"Benchmark Results - {result.get('benchmark_type', 'standard').title()}")
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
            if 'avg_latency_ms' in key:
                op_name = key.replace('_avg_latency_ms', '').replace('_', ' ').title()
                throughput_key = key.replace('avg_latency_ms', 'throughput_ops')
                throughput = trading.get(throughput_key, 0)
                trading_table.add_row(op_name, f"{value:.1f} ms", f"{throughput} ops")
        
        if trading_table.rows:
            console.print(trading_table)


def _display_terminal_results(scan_result: dict, tee_result: dict, perf_result: dict, llm_result=None):
    """Display verification results in terminal format."""
    table = Table(title="Verification Results")
    table.add_column("Check", style="cyan")
    table.add_column("Result", style="green")
    
    # Vulnerability analysis
    vulns = scan_result.get('vulnerabilities', [])
    critical = len([v for v in vulns if v.get('severity') == 'CRITICAL'])
    high = len([v for v in vulns if v.get('severity') == 'HIGH'])
    medium = len([v for v in vulns if v.get('severity') == 'MEDIUM'])
    low = len([v for v in vulns if v.get('severity') == 'LOW'])
    
    if critical > 0:
        vuln_status = f"[red]✗ {critical} critical, {high} high[/red]"
    elif high > 0:
        vuln_status = f"[yellow]⚠ {high} high, {medium} medium[/yellow]"
    else:
        vuln_status = f"[green]✓ {medium} medium, {low} low[/green]"
    
    table.add_row("Vulnerabilities", vuln_status)
    
    # TEE status
    tee_valid = tee_result.get('is_valid', True)
    tee_platform = tee_result.get('platform', 'Unknown')
    tee_status = f"✓ {tee_platform}" if tee_valid else f"✗ {tee_platform}"
    tee_color = "green" if tee_valid else "red"
    table.add_row("TEE Attestation", f"[{tee_color}]{tee_status}[/{tee_color}]")
    
    table.add_row("Shade Agent", "✓ Detected" if scan_result.get('shade_agent_detected') else "✗ Not detected")
    
    # Performance metrics
    perf_metrics = perf_result.get('performance', {})
    throughput = perf_metrics.get('throughput_tps', 0)
    avg_latency = perf_metrics.get('avg_latency_ms', 0)
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
    
    # Overall status
    overall_status = _determine_overall_status(scan_result, tee_result, perf_result, llm_result)
    status_color = "green" if overall_status == "PASSED" else "red"
    table.add_row("Overall Status", f"[{status_color}]✓ {overall_status}[/{status_color}]")
    
    console.print(table)
    
    # Calculate Agent Fort Score
    score = _calculate_agent_fort_score(scan_result, tee_result, perf_result, llm_result)
    score_color = "green" if score >= 80 else "yellow" if score >= 60 else "red"
    
    # Enhanced score display with LLM insights
    score_text = f"[bold {score_color}]{score}/180[/bold {score_color}]"
    if llm_result and llm_result.score_adjustments:
        total_llm_adjustment = sum(llm_result.score_adjustments.values())
        if total_llm_adjustment != 0:
            adjustment_color = "green" if total_llm_adjustment > 0 else "red"
            score_text += f"\n[{adjustment_color}]LLM Adjustment: {total_llm_adjustment:+.1f}[/{adjustment_color}]"
    
    score_panel = Panel(
        score_text,
        title="Agent Fort Score",
        border_style=score_color
    )
    console.print(score_panel)
    
    # Display LLM insights if available
    if llm_result and llm_result.reasoning:
        insights_panel = Panel(
            llm_result.reasoning[:300] + ("..." if len(llm_result.reasoning) > 300 else ""),
            title="🧠 LLM Insights",
            border_style="blue"
        )
        console.print(insights_panel)


def _calculate_agent_fort_score(scan_result: dict, tee_result: dict, perf_result: dict, llm_result=None) -> int:
    """Calculate Agent Fort score based on verification results with LLM augmentation."""
    score = 100
    
    # Vulnerability penalties
    vulns = scan_result.get('vulnerabilities', [])
    critical = len([v for v in vulns if v.get('severity') == 'CRITICAL'])
    high = len([v for v in vulns if v.get('severity') == 'HIGH'])
    medium = len([v for v in vulns if v.get('severity') == 'MEDIUM'])
    
    score -= critical * 30  # -30 per critical
    score -= high * 15      # -15 per high
    score -= medium * 5     # -5 per medium
    
    # TEE validation bonus/penalty
    if not tee_result.get('is_valid', True):
        score -= 20
    else:
        # Bonus for high trust level
        trust_level = tee_result.get('trust_level', 'LOW')
        if trust_level == 'HIGH':
            score += 10
        elif trust_level == 'MEDIUM':
            score += 5
    
    # Shade agent detection bonus
    if scan_result.get('shade_agent_detected', False):
        score += 5
    
    # Performance considerations
    perf_metrics = perf_result.get('performance', {})
    throughput = perf_metrics.get('throughput_tps', 0)
    avg_latency = perf_metrics.get('avg_latency_ms', 0)
    error_rate = perf_metrics.get('error_rate_percent', 0)
    
    # Throughput scoring
    if throughput < 500:
        score -= 10
    elif throughput > 2000:
        score += 5
    
    # Latency scoring
    if avg_latency > 100:
        score -= 5
    elif avg_latency < 20:
        score += 3
    
    # Error rate penalty
    if error_rate > 5:
        score -= 15
    elif error_rate > 1:
        score -= 5
    
    # LLM-based adjustments (Phase 2 innovation)
    if llm_result and llm_result.score_adjustments:
        for category, adjustment in llm_result.score_adjustments.items():
            score += adjustment
            
        # Additional LLM-based factors
        if hasattr(llm_result, 'code_quality') and llm_result.code_quality:
            # Bonus/penalty based on code quality assessment
            code_quality_bonus = (llm_result.code_quality.overall_score - 0.5) * 20
            score += code_quality_bonus
            
        # Risk assessment adjustments
        if hasattr(llm_result, 'risk_assessment') and llm_result.risk_assessment:
            # Penalty for high systemic risk
            systemic_risk_penalty = llm_result.risk_assessment.systemic_risk_score * 15
            score -= systemic_risk_penalty
            
        # Behavioral flags penalty
        if llm_result.behavioral_flags:
            score -= len(llm_result.behavioral_flags) * 5
    
    # New scoring range: 0-180 points (base 100 + up to 80 from LLM adjustments)
    return max(0, min(180, int(score)))


def _determine_overall_status(scan_result: dict, tee_result: dict, perf_result: dict, llm_result=None) -> str:
    """Determine overall verification status with LLM insights."""
    vulns = scan_result.get('vulnerabilities', [])
    critical = len([v for v in vulns if v.get('severity') == 'CRITICAL'])
    high = len([v for v in vulns if v.get('severity') == 'HIGH'])
    
    tee_valid = tee_result.get('is_valid', True)
    
    perf_metrics = perf_result.get('performance', {})
    error_rate = perf_metrics.get('error_rate_percent', 0)
    
    # LLM-based risk factors
    llm_risk_flags = 0
    if llm_result:
        # Count serious behavioral flags
        serious_flags = [flag for flag in llm_result.behavioral_flags 
                        if any(keyword in flag.lower() for keyword in 
                              ['malicious', 'suspicious', 'high risk', 'dangerous'])]
        llm_risk_flags = len(serious_flags)
        
        # Check for high systemic risk
        if (hasattr(llm_result, 'risk_assessment') and llm_result.risk_assessment and
            llm_result.risk_assessment.systemic_risk_score > 0.8):
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
    if (llm_result and llm_result.confidence_level < 0.5):  # Low LLM confidence
        return "WARNING"
    
    return "PASSED"


if __name__ == "__main__":
    cli()