"""Helper utilities for LLM judge functionality."""

from datetime import datetime
from typing import Any


def summarize_vulnerabilities(vulnerabilities: list[dict]) -> dict[str, int]:
    """Summarize vulnerability counts by severity."""
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for vuln in vulnerabilities:
        severity = vuln.get("severity", "UNKNOWN")
        if severity in counts:
            counts[severity] += 1
    return counts


def extract_agent_patterns(layers: list[dict]) -> dict[str, list[str]]:
    """Extract agent-related patterns from Docker layers."""
    patterns = {"dependencies": [], "configurations": [], "commands": []}

    for layer in layers:
        command = layer.get("command", "").lower()

        # Look for agent-related dependencies
        if any(
            dep in command for dep in ["npm install", "pip install", "yarn add"]
        ):
            patterns["dependencies"].append(command[:100])

        # Look for configuration patterns
        if any(cfg in command for cfg in ["config", "env", "secret"]):
            patterns["configurations"].append(command[:100])

        # Look for execution commands
        if any(cmd in command for cmd in ["run", "start", "exec"]):
            patterns["commands"].append(command[:100])

    return patterns


def format_agent_patterns(patterns: dict[str, list[str]]) -> str:
    """Format agent patterns for prompt inclusion."""
    formatted = []
    for category, items in patterns.items():
        if items:
            formatted.append(f"**{category.title()}:**")
            for item in items[:3]:  # Limit to 3 items per category
                formatted.append(f"  - {item}")
    return "\n".join(formatted) if formatted else "No specific patterns detected"


def prepare_evaluation_context(
    image_data: dict[str, Any],
    code_analysis: dict[str, Any] | None,
    market_context: dict[str, Any] | None,
) -> dict[str, Any]:
    """Prepare comprehensive context for LLM evaluation."""

    context = {
        "image_info": {
            "tag": image_data.get("image_tag", "unknown"),
            "size": image_data.get("size", 0),
            "layers": len(image_data.get("layers", [])),
            "shade_agent_detected": image_data.get("shade_agent_detected", False),
            "vulnerabilities": summarize_vulnerabilities(
                image_data.get("vulnerabilities", [])
            ),
        },
        "deployment_context": {
            "timestamp": datetime.now().isoformat(),
            "evaluation_version": "2.0",
            "market_conditions": market_context or {"status": "unknown"},
        },
    }

    # Add code analysis if available
    if code_analysis:
        context["code_analysis"] = code_analysis

    # Extract agent patterns from image layers
    context["agent_patterns"] = extract_agent_patterns(
        image_data.get("layers", [])
    )

    return context


def load_evaluation_templates() -> dict[str, str]:
    """Load evaluation templates and prompts."""
    # In production, these would be loaded from files or configuration
    return {
        "agent_classification": "Classify agent strategy and risk profile",
        "code_quality": "Assess code architecture and maintainability",
        "risk_assessment": "Evaluate market and operational risks",
    }
