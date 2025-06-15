"""Performance and benchmark result display formatting."""

from rich.console import Console
from rich.table import Table


def display_benchmark_results(result: dict, console: Console):
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