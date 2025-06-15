"""Anthropic Claude provider implementation."""

import os

from ..models import LLMProvider
from .base import BaseLLMProvider


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider implementation."""

    def __init__(self):
        super().__init__(LLMProvider.ANTHROPIC)

    def call_llm(self, prompt: str) -> str:
        """Call Anthropic Claude API."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            self.console.print(
                "[yellow]ANTHROPIC_API_KEY not found, using mock response[/yellow]"
            )
            return self.generate_mock_response(prompt)

        try:
            response = self.client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "2048")),
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=float(os.getenv("LLM_TIMEOUT_SECONDS", "30")),
            )
            response.raise_for_status()

            result = response.json()
            return result["content"][0]["text"]

        except Exception as e:
            self.console.print(f"[red]Anthropic API call failed: {e}[/red]")
            self.console.print("[yellow]Falling back to mock response[/yellow]")
            return self.generate_mock_response(prompt)

    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "Anthropic Claude"

    def generate_mock_response(self, prompt: str) -> str:
        """Generate mock Anthropic response for development/testing."""
        return """```json
{
  "intent_classification": {
    "primary_strategy": "arbitrage",
    "risk_profile": "moderate",
    "complexity_score": 0.7,
    "confidence": 0.85
  },
  "code_quality": {
    "architecture_score": 0.8,
    "error_handling_score": 0.7,
    "security_practices_score": 0.9,
    "maintainability_score": 0.75,
    "test_coverage_score": 0.6,
    "overall_score": 0.76,
    "key_findings": ["Well-structured trading logic", "Good security practices", "Could improve test coverage"]
  },
  "risk_assessment": {
    "volatility_sensitivity": 0.6,
    "liquidity_requirements": "medium",
    "systemic_risk_score": 0.3,
    "market_impact_score": 0.4,
    "operational_risk_score": 0.25,
    "regulatory_risk_score": 0.2
  },
  "behavioral_flags": ["High-frequency trading patterns detected"],
  "score_adjustments": {
    "security_critical": 8.0,
    "deception_risk": 5.0,
    "capital_safety": 7.0,
    "transparency": 6.0
  },
  "confidence_level": 0.8,
  "reasoning": "Trust-focused security analysis: Strong key management practices detected, adequate transaction controls with spending limits, no malicious patterns found. Code appears transparent with good audit trails. Recommended for deployment with standard monitoring.",
  "trust_recommendation": "DEPLOY",
  "critical_issues": []
}
```"""
