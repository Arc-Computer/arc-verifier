"""Verification commands for Arc-Verifier CLI.

This module contains the core verification workflows that produce Fort Scores:
- verify: Complete verification workflow
- core-verify: Lightweight Phase 1 verification
- verify-batch: Parallel batch verification
- verify-strategy: Trading strategy-specific verification
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
    help="Enable LLM-based behavioral analysis",
)
@click.option(
    "--llm-provider",
    type=click.Choice(["anthropic", "openai"]),
    default="anthropic",
    help="LLM provider for behavioral analysis",
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
            progress.update(task, description="[cyan]Analyzing with LLM...")
            llm_judge = LLMJudge(provider=llm_provider)
            
            # Prepare context for LLM analysis
            agent_context = {
                "image_tag": image,
                "vulnerabilities": scan_result.get("vulnerabilities", []),
                "shade_agent_detected": scan_result.get("shade_agent_detected", False),
                "base_image": scan_result.get("base_image"),
                "performance_metrics": perf_result.get("performance", {}),
                "tee_attestation": tee_result,
            }

            verification_context = {
                "verification_tier": tier,
                "timestamp": datetime.now(),
                "performance_score": perf_result.get("performance", {}),
                "vulnerability_summary": {
                    "critical": len([v for v in scan_result.get("vulnerabilities", []) if v.get("severity") == "CRITICAL"]),
                    "high": len([v for v in scan_result.get("vulnerabilities", []) if v.get("severity") == "HIGH"]),
                    "medium": len([v for v in scan_result.get("vulnerabilities", []) if v.get("severity") == "MEDIUM"]),
                    "low": len([v for v in scan_result.get("vulnerabilities", []) if v.get("severity") == "LOW"])
                }
            }

            try:
                llm_result = llm_judge.evaluate_agent(agent_context, verification_context)
            except Exception as e:
                console.print(f"[yellow]LLM analysis failed: {e}[/yellow]")
                
            progress.advance(task)

        # Basic strategy verification for completeness
        progress.update(task, description="[cyan]Verifying strategy...")
        strategy_verifier = StrategyVerifier()
        
        # Use a default date range for quick strategy check
        start_date = "2024-10-01"
        end_date = "2024-10-07"
        
        try:
            strategy_result = strategy_verifier.verify_strategy(image, start_date, end_date)
        except Exception as e:
            console.print(f"[yellow]Strategy verification failed: {e}[/yellow]")
            strategy_result = None
            
        progress.advance(task)

    # Display results
    if output == "json":
        # Build structured JSON output
        verification_result = {
            "image": image,
            "timestamp": datetime.now().isoformat(),
            "tier": tier,
            "scan_result": scan_result,
            "tee_result": tee_result,
            "performance_result": perf_result,
            "fort_score": calculate_agent_fort_score(
                scan_result, tee_result, perf_result, llm_result, strategy_result
            ),
            "overall_status": determine_overall_status(
                scan_result, tee_result, perf_result, llm_result, strategy_result
            ),
        }
        
        if llm_result:
            verification_result["llm_analysis"] = {
                "intent_classification": llm_result.intent_classification._asdict() if hasattr(llm_result.intent_classification, '_asdict') else str(llm_result.intent_classification),
                "confidence_level": llm_result.confidence_level,
                "behavioral_flags": llm_result.behavioral_flags,
                "reasoning": llm_result.reasoning,
                "score_adjustments": llm_result.score_adjustments
            }
            
        if strategy_result:
            verification_result["strategy_verification"] = {
                "detected_strategy": strategy_result.detected_strategy,
                "verification_status": strategy_result.verification_status,
                "strategy_effectiveness": strategy_result.strategy_effectiveness,
                "risk_score": strategy_result.risk_score
            }

        console.print_json(data=verification_result)
    else:
        # Terminal output with enhanced display
        display_terminal_results(
            scan_result, 
            tee_result, 
            perf_result, 
            llm_result, 
            strategy_result,
            console=console,
            calculate_fort_score_func=calculate_agent_fort_score,
            determine_status_func=determine_overall_status
        )

    # Log the verification
    audit_logger = AuditLogger()
    audit_logger.log_verification(
        image=image,
        verification_result={
            "fort_score": calculate_agent_fort_score(scan_result, tee_result, perf_result, llm_result, strategy_result),
            "status": determine_overall_status(scan_result, tee_result, perf_result, llm_result, strategy_result),
            "tier": tier
        },
        llm_reasoning=llm_result.reasoning if llm_result else None
    )


@click.command()
@click.argument("images", nargs=-1, required=True)
@click.option("--enable-llm/--no-llm", default=True, help="Enable LLM analysis")
@click.option("--enable-backtesting/--no-backtesting", default=True, help="Enable backtesting")
@click.option("--backtest-period", default="2024-10-01:2024-10-07", help="Backtest date range (start:end)")
@click.option("--max-concurrent", default=8, help="Maximum concurrent verifications")
@click.option("--output", type=click.Choice(["terminal", "json"]), default="terminal", help="Output format")
def core_verify(images, enable_llm, enable_backtesting, backtest_period, max_concurrent, output):
    """Core lightweight verification focused on immediate value.
    
    Phase 1 verification that emphasizes:
    - Real market data backtesting (core value)
    - Security scanning (baseline protection)  
    - TEE attestation (production security)
    - Resource-efficient concurrent processing
    
    Examples:
        arc-verifier core-verify agent1:latest agent2:latest
        arc-verifier core-verify agent:latest --no-backtesting --max-concurrent 4
    """
    console.print(f"[bold blue]🚀 Core Verification - Phase 1 Pipeline[/bold blue]")
    console.print(f"Verifying {len(images)} agent(s) with resource-efficient processing\n")
    
    # Initialize core verifier with resource limits
    resource_limits = ResourceLimits(
        max_concurrent_backtests=min(max_concurrent, 8),
        max_concurrent_scans=min(max_concurrent * 2, 16),
        max_concurrent_llm=min(max_concurrent, 6),
        max_concurrent_tee=min(max_concurrent, 10)
    )
    
    core_verifier = CoreArcVerifier(
        resource_limits=resource_limits,
        console=console
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
            console.print_json(data=json_result)
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
        arc-verifier verify-batch myagent:latest agent2:latest --max-concurrent 5
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


@click.command()
@click.argument("image")
@click.option("--start-date", default="2024-10-01", help="Start date for backtesting (YYYY-MM-DD)")
@click.option("--end-date", default="2024-10-07", help="End date for backtesting (YYYY-MM-DD)")
@click.option("--regime", help="Market regime filter for testing")
@click.option("--output", type=click.Choice(["terminal", "json"]), default="terminal", help="Output format")
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