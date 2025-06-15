"""Simulation result display formatting."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def display_simulation_result(result, console: Console):
    """Display simulation result in terminal format."""
    
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