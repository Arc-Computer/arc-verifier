"""Verification commands for Arc-Verifier CLI.

This module contains the core verification workflows:
- verify: Main comprehensive agent verification
- batch: Parallel multi-agent verification
"""

import click
import json
import time
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ...security import DockerScanner, TEEValidator, AuditLogger
from ...analysis import Benchmarker, LLMJudge, StrategyVerifier
from ...orchestration import ParallelVerifier
from ...core import CoreArcVerifier, ResourceLimits
from ..display import display_terminal_results
from ..scoring import calculate_agent_fort_score, determine_overall_status


console = Console()




@click.command()
@click.argument("images", nargs=-1, required=True)
@click.option("--enable-llm/--no-llm", default=True, help="Enable LLM analysis")
@click.option("--enable-backtesting/--no-backtesting", default=True, help="Enable backtesting")
@click.option("--backtest-period", default="2024-10-01:2024-10-07", help="Backtest date range (start:end)")
@click.option("--max-concurrent", default=8, help="Maximum concurrent verifications")
@click.option("--output", type=click.Choice(["terminal", "json"]), default="terminal", help="Output format")
def verify(images, enable_llm, enable_backtesting, backtest_period, max_concurrent, output):
    """Comprehensive agent verification with simulation, backtesting, and evaluation.
    
    Main verification command providing security scanning, performance testing,
    historical backtesting, and AI-powered behavioral analysis for autonomous agents.
    
    Examples:
        arc-verifier verify agent:latest
        arc-verifier verify agent1:latest agent2:latest --no-backtesting
        arc-verifier verify agent:latest --backtest-period 2024-11-01:2024-11-07
    """
    # Only show terminal output if not JSON mode
    if output == "terminal":
        console.print(f"[bold blue]🚀 Core Verification - Phase 1 Pipeline[/bold blue]")
        console.print(f"Verifying {len(images)} agent(s) with resource-efficient processing\n")
    
    # Initialize core verifier with resource limits
    resource_limits = ResourceLimits(
        max_concurrent_backtests=min(max_concurrent, 8),
        max_concurrent_scans=min(max_concurrent * 2, 16),
        max_concurrent_llm=min(max_concurrent, 6),
        max_concurrent_tee=min(max_concurrent, 10)
    )
    
    # Use a quiet console for JSON output mode
    quiet_console = Console(quiet=(output == "json"))
    core_verifier = CoreArcVerifier(
        resource_limits=resource_limits,
        console=quiet_console
    )
    
    start_time = time.time()
    
    try:
        # Run batch verification
        batch_result = asyncio.run(core_verifier.verify_batch(
            agent_images=list(images),
            enable_llm=enable_llm,
            enable_backtesting=enable_backtesting,
            backtest_period=backtest_period
        ))
        
        processing_time = time.time() - start_time
        
        if output == "json":
            # Convert to JSON-serializable format
            json_result = {
                "core_verification_batch": {
                    "total_agents": batch_result.total_agents,
                    "successful_verifications": batch_result.successful_verifications,
                    "failed_verifications": batch_result.failed_verifications,
                    "average_fort_score": batch_result.average_fort_score,
                    "processing_time": batch_result.processing_time,
                    "timestamp": batch_result.timestamp.isoformat(),
                    "results": [
                        {
                            "agent_id": result.agent_id,
                            "fort_score": result.fort_score,
                            "security_score": result.security_score,
                            "strategy_score": result.strategy_score,
                            "trust_score": result.trust_score,
                            "tee_score": result.tee_score,
                            "processing_time": result.processing_time,
                            "timestamp": result.timestamp.isoformat(),
                            "warnings": result.warnings,
                            "recommendations": result.recommendations
                        }
                        for result in batch_result.results
                    ],
                    "failures": batch_result.failures
                }
            }
            click.echo(json.dumps(json_result, indent=2))
        else:
            # Display batch results with rich formatting
            core_verifier.display_batch_results(batch_result)
            console.print(f"\n[bold]Core Verification Complete[/bold]")
            console.print(f"Total processing time: {processing_time:.1f}s")
        
    except Exception as e:
        console.print(f"[red]Core verification failed: {e}[/red]")
        raise click.ClickException(str(e))


# Import asyncio here to avoid import at module level
import asyncio


@click.command()
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
    help="Enable LLM-based behavioral analysis",
)
@click.option(
    "--llm-provider",
    type=click.Choice(["anthropic", "openai"]),
    default="anthropic",
    help="LLM provider for behavioral analysis",
)
@click.option(
    "--max-concurrent",
    default=3,
    help="Maximum concurrent verifications"
)
def batch(
    images: tuple,
    tier: str,
    output: str,
    enable_llm: bool,
    llm_provider: str,
    max_concurrent: int,
):
    """Verify multiple Docker images in parallel.

    Performs comprehensive verification of multiple agents concurrently,
    including vulnerability scanning, TEE attestation, and performance benchmarking.

    Examples:
        arc-verifier batch shade/agent1:latest shade/agent2:latest
        arc-verifier batch myagent:v1 myagent:v2 myagent:v3 --tier high
        arc-verifier batch myagent:latest agent2:latest --max-concurrent 5
        arc-verifier batch --output json agent1:latest agent2:latest
    """
    if not images:
        console.print("[red]Error: No images provided[/red]")
        raise click.ClickException("At least one image must be specified")
    
    # Only show terminal output if not JSON mode
    if output == "terminal":
        console.print(f"[bold blue]Starting batch verification of {len(images)} images[/bold blue]")
        console.print(f"Security tier: {tier}")
        console.print(f"Max concurrent: {max_concurrent}")
    
    # Initialize parallel verifier
    verifier = ParallelVerifier(max_concurrent=max_concurrent)
    
    # Run async verification
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
            click.echo(json.dumps(json_result, indent=2))
            
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


