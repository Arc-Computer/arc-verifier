"""OpenAI GPT provider implementation."""

import os

from ..models import LLMProvider
from .base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider implementation."""

    def __init__(self):
        super().__init__(LLMProvider.OPENAI)

    def call_llm(self, prompt: str) -> str:
        """Call OpenAI API."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            self.console.print(
                "[yellow]OPENAI_API_KEY not found, using mock response[/yellow]"
            )
            return self.generate_mock_response(prompt)

        try:
            response = self.client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                json={
                    "model": "gpt-4.1",
                    "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "2048")),
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                },
                timeout=float(os.getenv("LLM_TIMEOUT_SECONDS", "30")),
            )
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except Exception as e:
            self.console.print(f"[red]OpenAI API call failed: {e}[/red]")
            self.console.print("[yellow]Falling back to mock response[/yellow]")
            return self.generate_mock_response(prompt)

    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "OpenAI GPT"

    def generate_mock_response(self, prompt: str) -> str:
        """Generate mock OpenAI response for development/testing."""
        return """```json
{
  "intent_classification": {
    "primary_strategy": "arbitrage",
    "risk_profile": "moderate",
    "complexity_score": 0.75,
    "confidence": 0.82
  },
  "code_quality": {
    "architecture_score": 0.85,
    "error_handling_score": 0.65,
    "security_practices_score": 0.85,
    "maintainability_score": 0.8,
    "test_coverage_score": 0.55,
    "overall_score": 0.74,
    "key_findings": ["Clean architecture design", "Robust security implementation", "Test coverage needs improvement"]
  },
  "risk_assessment": {
    "volatility_sensitivity": 0.55,
    "liquidity_requirements": "medium",
    "systemic_risk_score": 0.35,
    "market_impact_score": 0.35,
    "operational_risk_score": 0.3,
    "regulatory_risk_score": 0.25
  },
  "behavioral_flags": [],
  "score_adjustments": {
    "security_critical": 7.0,
    "deception_risk": 4.0,
    "capital_safety": 6.0,
    "transparency": 8.0
  },
  "confidence_level": 0.78,
  "reasoning": "Trust-focused security analysis: Good key security implementation, transaction controls present but could be stronger, no deceptive patterns detected. High code transparency with clear audit capabilities. Safe for deployment with moderate risk monitoring.",
  "trust_recommendation": "DEPLOY",
  "critical_issues": []
}
```"""
