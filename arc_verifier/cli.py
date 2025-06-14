"""Arc-Verifier CLI interface."""

import click
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from . import __version__
from .scanner import DockerScanner
from .validator import TEEValidator
from .benchmarker import Benchmarker

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
def verify(image: str, tier: str, output: str):
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
        task = progress.add_task("[cyan]Running verification...", total=3)
        
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
            "agent_fort_score": _calculate_agent_fort_score(scan_result, tee_result, perf_result),
            "overall_status": _determine_overall_status(scan_result, tee_result, perf_result)
        }
        console.print_json(data=verification_result)
    else:
        _display_terminal_results(scan_result, tee_result, perf_result)


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


def _display_terminal_results(scan_result: dict, tee_result: dict, perf_result: dict):
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
    
    # Overall status
    overall_status = _determine_overall_status(scan_result, tee_result, perf_result)
    status_color = "green" if overall_status == "PASSED" else "red"
    table.add_row("Overall Status", f"[{status_color}]✓ {overall_status}[/{status_color}]")
    
    console.print(table)
    
    # Calculate Agent Fort Score
    score = _calculate_agent_fort_score(scan_result, tee_result, perf_result)
    score_color = "green" if score >= 80 else "yellow" if score >= 60 else "red"
    
    score_panel = Panel(
        f"[bold {score_color}]{score}/100[/bold {score_color}]",
        title="Agent Fort Score",
        border_style=score_color
    )
    console.print(score_panel)


def _calculate_agent_fort_score(scan_result: dict, tee_result: dict, perf_result: dict) -> int:
    """Calculate Agent Fort score based on verification results."""
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
    
    return max(0, min(100, score))


def _determine_overall_status(scan_result: dict, tee_result: dict, perf_result: dict) -> str:
    """Determine overall verification status."""
    vulns = scan_result.get('vulnerabilities', [])
    critical = len([v for v in vulns if v.get('severity') == 'CRITICAL'])
    high = len([v for v in vulns if v.get('severity') == 'HIGH'])
    
    tee_valid = tee_result.get('is_valid', True)
    
    perf_metrics = perf_result.get('performance', {})
    error_rate = perf_metrics.get('error_rate_percent', 0)
    
    # Fail conditions
    if critical > 0:
        return "FAILED"
    if not tee_valid:
        return "FAILED"
    if error_rate > 10:
        return "FAILED"
    
    # Warning conditions
    if high > 5:
        return "WARNING"
    if error_rate > 5:
        return "WARNING"
    
    return "PASSED"


if __name__ == "__main__":
    cli()