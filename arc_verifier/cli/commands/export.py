"""Export commands for Arc-Verifier CLI.

This module provides commands for exporting verification results
in various formats and launching the web UI for viewing results.
"""

import click
import json
import webbrowser
from pathlib import Path
from datetime import datetime
from rich.console import Console

from ...models import ExportableResult, VerificationResult
from ...security import AuditLogger


console = Console()


@click.group()
def export():
    """Export verification results and launch web UI.
    
    Export verification results in various formats (HTML, JSON, PDF)
    and view them in a web interface.
    """
    pass


@export.command()
@click.argument("verification_id", required=False)
@click.option("--format", type=click.Choice(["html", "json", "pdf"]), default="html", help="Export format")
@click.option("--output", type=click.Path(), help="Output file path")
@click.option("--latest", is_flag=True, help="Export latest verification result")
@click.option("--open", "open_browser", is_flag=True, help="Open result in browser (HTML only)")
def results(verification_id, format, output, latest, open_browser):
    """Export verification results to file.
    
    Export a specific verification result or the latest one to various formats
    for reporting, documentation, or further analysis.
    
    Examples:
        arc-verifier export results --latest --format html --open
        arc-verifier export results ver_abc123def456 --format json
        arc-verifier export results --latest --output report.html
    """
    audit_logger = AuditLogger()
    
    # Get verification result
    if latest or not verification_id:
        # Get latest verification
        audits = audit_logger.list_audits()
        if not audits:
            console.print("[red]No verification results found[/red]")
            raise click.ClickException("No verification results to export")
        
        latest_audit = audits[0]  # Already sorted by timestamp desc
        verification_id = latest_audit.get("verification_id", "unknown")
        audit_file = Path(latest_audit["file"])
        
        console.print(f"[blue]Exporting latest verification: {latest_audit['image']}[/blue]")
    else:
        # Find specific verification
        audit_file = None
        for audit in audit_logger.list_audits():
            if audit.get("verification_id") == verification_id:
                audit_file = Path(audit["file"])
                break
        
        if not audit_file:
            console.print(f"[red]Verification ID not found: {verification_id}[/red]")
            raise click.ClickException("Verification ID not found")
    
    # Load full verification data
    with open(audit_file, 'r') as f:
        verification_data = json.load(f)
    
    # Create exportable result
    exportable = create_exportable_result(verification_data)
    
    # Determine output path
    if not output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"arc_verifier_report_{timestamp}.{format}"
        output = Path.cwd() / filename
    else:
        output = Path(output)
    
    # Export based on format
    if format == "json":
        with open(output, 'w') as f:
            f.write(exportable.to_json())
        console.print(f"[green]✓ Exported JSON report to: {output}[/green]")
        
    elif format == "html":
        html_content = generate_html_report(exportable, verification_data)
        with open(output, 'w') as f:
            f.write(html_content)
        console.print(f"[green]✓ Exported HTML report to: {output}[/green]")
        
        if open_browser:
            console.print("[blue]Opening report in browser...[/blue]")
            webbrowser.open(f"file://{output.absolute()}")
            
    elif format == "pdf":
        console.print("[yellow]PDF export not yet implemented[/yellow]")
        console.print("[dim]Tip: Export as HTML and use browser's print-to-PDF feature[/dim]")


@export.command()
@click.option("--port", default=8080, help="Port to run web server on")
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--debug", is_flag=True, help="Run in debug mode")
def web(port, host, debug):
    """Launch web UI for viewing verification results.
    
    Starts a lightweight web server to browse verification history,
    view detailed reports, and analyze trends in an interactive dashboard.
    
    Examples:
        arc-verifier export web
        arc-verifier export web --port 3000
        arc-verifier export web --debug
    """
    console.print(f"[bold blue]Starting Arc-Verifier Web UI[/bold blue]")
    console.print(f"Server: http://{host}:{port}")
    
    try:
        # Import web server (will be implemented)
        from ...web import create_app
        
        app = create_app()
        
        console.print("\n[green]Web UI is running![/green]")
        console.print("Press Ctrl+C to stop the server\n")
        
        # Open browser automatically
        import threading
        import time
        
        def open_browser_delayed():
            time.sleep(1)  # Give server time to start
            webbrowser.open(f"http://{host}:{port}")
        
        threading.Thread(target=open_browser_delayed, daemon=True).start()
        
        # Run server
        app.run(host=host, port=port, debug=debug)
        
    except ImportError:
        console.print("[red]Web UI dependencies not installed[/red]")
        console.print("\n[yellow]To enable the web UI, install the required dependencies:[/yellow]")
        console.print("\n  pip install flask flask-cors")
        console.print("\nFor production deployment, also install:")
        console.print("  pip install gunicorn flask-compress flask-caching")
        console.print("\n[dim]The web UI provides a comprehensive dashboard for viewing:[/dim]")
        console.print("[dim]  • Verification history and trends[/dim]")
        console.print("[dim]  • Detailed metrics across all components[/dim]")
        console.print("[dim]  • Agent performance comparisons[/dim]")
        console.print("[dim]  • Interactive charts and visualizations[/dim]")
        
    except Exception as e:
        console.print(f"[red]Failed to start web server: {e}[/red]")
        raise click.ClickException(str(e))


def create_exportable_result(verification_data: dict) -> ExportableResult:
    """Convert verification data to exportable format."""
    # Extract key information - handle nested structure
    if "results" in verification_data:
        result = verification_data["results"]
    elif "verification_result" in verification_data:
        result = verification_data["verification_result"]
    else:
        result = verification_data
    
    # Calculate summary statistics
    fort_score = result.get("fort_score", result.get("agent_fort_score", 0))
    status = result.get("overall_status", result.get("status", "UNKNOWN"))
    
    # Component scores
    security_score = result.get("docker_scan", {}).get("security_score", 0)
    perf_score = result.get("performance_benchmark", {}).get("performance_score", 0)
    strategy_score = result.get("strategy_verification", {}).get("strategy_effectiveness", 0)
    
    # Count total vulnerabilities
    vuln_count = 0
    if "docker_scan" in result:
        vulns = result["docker_scan"].get("vulnerabilities", [])
        if isinstance(vulns, list):
            vuln_count = len(vulns)
        elif isinstance(vulns, dict):
            vuln_count = sum(vulns.values())
    
    return ExportableResult(
        title=f"Arc-Verifier Report - {result.get('image', 'Unknown')}",
        subtitle=f"Fort Score: {fort_score}/180 - {status}",
        timestamp=result.get("timestamp", datetime.now().isoformat()),
        summary_stats={
            "fort_score": fort_score,
            "status": status,
            "security_score": security_score,
            "performance_score": perf_score,
            "strategy_score": strategy_score,
            "vulnerabilities": vuln_count
        },
        verification_results=[result],
        fort_score_distribution=[fort_score],
        component_scores={
            "security": [security_score],
            "performance": [perf_score],
            "strategy": [strategy_score]
        },
        timeline_data=[{
            "timestamp": result.get("timestamp"),
            "fort_score": fort_score,
            "status": status
        }]
    )


def generate_html_report(exportable: ExportableResult, verification_data: dict) -> str:
    """Generate HTML report from exportable result."""
    # HTML template with inline CSS and JS for standalone report
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
        }}
        .header .subtitle {{
            color: #666;
            font-size: 18px;
        }}
        .fort-score {{
            font-size: 48px;
            font-weight: bold;
            color: {score_color};
            margin: 20px 0;
        }}
        .status {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
            background: {status_bg};
            color: white;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric-card h3 {{
            margin: 0 0 10px 0;
            color: #34495e;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            color: #2c3e50;
        }}
        .section {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .section h2 {{
            margin-top: 0;
            color: #2c3e50;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #ecf0f1;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        .warning {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 15px;
            border-radius: 4px;
            margin: 10px 0;
        }}
        .recommendation {{
            background: #d4edda;
            border: 1px solid #c3e6cb;
            padding: 15px;
            border-radius: 4px;
            margin: 10px 0;
        }}
        .footer {{
            text-align: center;
            color: #666;
            margin-top: 50px;
            padding: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <div class="subtitle">{subtitle}</div>
        <div class="fort-score">Fort Score: {fort_score}/180</div>
        <span class="status">{status}</span>
        <div style="margin-top: 20px; color: #666;">
            Generated: {timestamp}
        </div>
    </div>
    
    <div class="metrics-grid">
        <div class="metric-card">
            <h3>Security Score</h3>
            <div class="metric-value">{security_score}</div>
            <div>Vulnerabilities: {vulnerabilities}</div>
        </div>
        <div class="metric-card">
            <h3>Performance Score</h3>
            <div class="metric-value">{performance_score}</div>
        </div>
        <div class="metric-card">
            <h3>Strategy Score</h3>
            <div class="metric-value">{strategy_score}</div>
        </div>
    </div>
    
    {details_sections}
    
    <div class="footer">
        <p>Generated by Arc-Verifier v{version}</p>
        <p>Verification and evaluation framework for agentic protocols</p>
    </div>
</body>
</html>"""
    
    # Determine colors based on score
    fort_score = exportable.summary_stats["fort_score"]
    if fort_score >= 150:
        score_color = "#27ae60"
        status_bg = "#27ae60"
    elif fort_score >= 120:
        score_color = "#f39c12"
        status_bg = "#f39c12"
    else:
        score_color = "#e74c3c"
        status_bg = "#e74c3c"
    
    # Generate detailed sections
    details_sections = generate_details_sections(verification_data)
    
    # Fill template
    return html_template.format(
        title=exportable.title,
        subtitle=exportable.subtitle,
        fort_score=fort_score,
        status=exportable.summary_stats["status"],
        score_color=score_color,
        status_bg=status_bg,
        timestamp=exportable.timestamp,
        security_score=exportable.summary_stats.get("security_score", 0),
        performance_score=exportable.summary_stats.get("performance_score", 0),
        strategy_score=exportable.summary_stats.get("strategy_score", 0),
        vulnerabilities=exportable.summary_stats.get("vulnerabilities", 0),
        details_sections=details_sections,
        version=exportable.arc_verifier_version
    )


def generate_details_sections(verification_data: dict) -> str:
    """Generate detailed sections for HTML report."""
    sections = []
    result = verification_data.get("results", verification_data)
    
    # Warnings section
    warnings = result.get("warnings", [])
    if warnings:
        warnings_html = '<div class="section"><h2>Warnings</h2>'
        for warning in warnings:
            warnings_html += f'<div class="warning">{warning}</div>'
        warnings_html += '</div>'
        sections.append(warnings_html)
    
    # Recommendations section
    recommendations = result.get("recommendations", [])
    if recommendations:
        rec_html = '<div class="section"><h2>Recommendations</h2>'
        for rec in recommendations:
            rec_html += f'<div class="recommendation">{rec}</div>'
        rec_html += '</div>'
        sections.append(rec_html)
    
    # Security details
    if "docker_scan" in result:
        security_html = '<div class="section"><h2>Security Analysis</h2>'
        scan = result["docker_scan"]
        vulns = scan.get("vulnerabilities", [])
        
        # Count vulnerabilities by severity
        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        if isinstance(vulns, list):
            for vuln in vulns:
                severity = vuln.get("severity", "UNKNOWN")
                if severity in severity_counts:
                    severity_counts[severity] += 1
        elif isinstance(vulns, dict):
            # Handle old format where vulns might be a dict
            severity_counts = vulns
        
        security_html += '<table>'
        security_html += '<tr><th>Severity</th><th>Count</th></tr>'
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            count = severity_counts.get(severity, 0)
            security_html += f'<tr><td>{severity}</td><td>{count}</td></tr>'
        security_html += '</table></div>'
        sections.append(security_html)
    
    return '\n'.join(sections)