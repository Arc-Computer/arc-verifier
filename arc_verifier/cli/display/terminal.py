"""Terminal display formatting for verification results."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel


def display_terminal_results(
    scan_result: dict, 
    tee_result: dict, 
    perf_result: dict, 
    llm_result=None, 
    strategy_result=None,
    console: Console = None,
    calculate_fort_score_func=None,
    determine_status_func=None
):
    """Display verification results in terminal format."""
    if console is None:
        console = Console()
    
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
    if determine_status_func:
        overall_status = determine_status_func(
            scan_result, tee_result, perf_result, llm_result, strategy_result
        )
        status_color = "green" if overall_status == "PASSED" else "red"
        table.add_row(
            "Overall Status", f"[{status_color}]✓ {overall_status}[/{status_color}]"
        )

    console.print(table)

    # Calculate Agent Fort Score
    if calculate_fort_score_func:
        score = calculate_fort_score_func(
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