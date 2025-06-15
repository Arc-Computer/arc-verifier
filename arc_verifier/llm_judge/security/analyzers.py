"""Trust-focused security analyzers."""

import json
import re
from typing import Any

from rich.console import Console

from ..models import (
    CapitalRiskResult,
    DeceptionDetectionResult,
    KeySecurityResult,
    TransactionControlResult,
)
from ..providers.base import BaseLLMProvider
from .prompts import (
    build_capital_risk_prompt,
    build_deception_detection_prompt,
    build_key_security_prompt,
    build_transaction_control_prompt,
)


class SecurityAnalyzer:
    """Base class for security analyzers."""

    def __init__(self):
        self.console = Console()


class KeySecurityAnalyzer(SecurityAnalyzer):
    """Analyzer for private key security patterns."""

    def analyze(self, context: dict[str, Any], provider: BaseLLMProvider) -> KeySecurityResult:
        """Analyze private key security patterns using LLM."""

        prompt = build_key_security_prompt(context)

        try:
            response = provider.call_llm(prompt)
            return self._parse_response(response)
        except Exception as e:
            self.console.print(f"[yellow]Key security analysis failed: {e}[/yellow]")
            return self._generate_fallback_result()

    def _parse_response(self, response: str) -> KeySecurityResult:
        """Parse LLM response for key security analysis."""
        try:
            json_match = re.search(r"```json\s*(\{.*?\})\s*```", response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
            else:
                data = json.loads(response)

            return KeySecurityResult(
                has_plaintext_keys=data.get("has_plaintext_keys", True),  # Conservative default
                key_generation_secure=data.get("key_generation_secure", False),
                key_storage_encrypted=data.get("key_storage_encrypted", False),
                key_rotation_implemented=data.get("key_rotation_implemented", False),
                key_exposure_risk=data.get("key_exposure_risk", "high"),
                security_concerns=data.get("security_concerns", ["Unable to analyze"]),
                code_references=data.get("code_references", [])
            )
        except Exception as e:
            self.console.print(f"[yellow]Failed to parse key security response: {e}[/yellow]")
            return self._generate_fallback_result()

    def _generate_fallback_result(self) -> KeySecurityResult:
        """Generate conservative fallback for key security analysis."""
        return KeySecurityResult(
            has_plaintext_keys=True,  # Conservative: assume worst case
            key_generation_secure=False,
            key_storage_encrypted=False,
            key_rotation_implemented=False,
            key_exposure_risk="critical",
            security_concerns=["Analysis failed - manual security review required"],
            code_references=[]
        )


class TransactionControlAnalyzer(SecurityAnalyzer):
    """Analyzer for transaction authorization controls."""

    def analyze(self, context: dict[str, Any], provider: BaseLLMProvider) -> TransactionControlResult:
        """Analyze transaction authorization controls using LLM."""

        prompt = build_transaction_control_prompt(context)

        try:
            response = provider.call_llm(prompt)
            return self._parse_response(response)
        except Exception as e:
            self.console.print(f"[yellow]Transaction control analysis failed: {e}[/yellow]")
            return self._generate_fallback_result()

    def _parse_response(self, response: str) -> TransactionControlResult:
        """Parse LLM response for transaction control analysis."""
        try:
            json_match = re.search(r"```json\s*(\{.*?\})\s*```", response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
            else:
                data = json.loads(response)

            return TransactionControlResult(
                has_spending_limits=data.get("has_spending_limits", False),
                has_approval_mechanisms=data.get("has_approval_mechanisms", False),
                emergency_stop_present=data.get("emergency_stop_present", False),
                cross_chain_controls=data.get("cross_chain_controls", False),
                transaction_monitoring=data.get("transaction_monitoring", False),
                control_strength=data.get("control_strength", "weak"),
                control_gaps=data.get("control_gaps", ["Unable to analyze"])
            )
        except Exception as e:
            self.console.print(f"[yellow]Failed to parse transaction control response: {e}[/yellow]")
            return self._generate_fallback_result()

    def _generate_fallback_result(self) -> TransactionControlResult:
        """Generate conservative fallback for transaction controls."""
        return TransactionControlResult(
            has_spending_limits=False,
            has_approval_mechanisms=False,
            emergency_stop_present=False,
            cross_chain_controls=False,
            transaction_monitoring=False,
            control_strength="weak",
            control_gaps=["Analysis failed - manual review required"]
        )


class DeceptionDetector(SecurityAnalyzer):
    """Detector for malicious patterns and deception."""

    def analyze(self, context: dict[str, Any], provider: BaseLLMProvider) -> DeceptionDetectionResult:
        """Detect malicious patterns and deception using LLM."""

        prompt = build_deception_detection_prompt(context)

        try:
            response = provider.call_llm(prompt)
            return self._parse_response(response)
        except Exception as e:
            self.console.print(f"[yellow]Deception detection failed: {e}[/yellow]")
            return self._generate_fallback_result()

    def _parse_response(self, response: str) -> DeceptionDetectionResult:
        """Parse LLM response for deception detection analysis."""
        try:
            json_match = re.search(r"```json\s*(\{.*?\})\s*```", response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
            else:
                data = json.loads(response)

            return DeceptionDetectionResult(
                backdoor_detected=data.get("backdoor_detected", False),
                time_bomb_detected=data.get("time_bomb_detected", False),
                obfuscated_code_found=data.get("obfuscated_code_found", False),
                data_exfiltration_risk=data.get("data_exfiltration_risk", False),
                environment_specific_behavior=data.get("environment_specific_behavior", False),
                deception_indicators=data.get("deception_indicators", []),
                risk_level=data.get("risk_level", "medium")
            )
        except Exception as e:
            self.console.print(f"[yellow]Failed to parse deception response: {e}[/yellow]")
            return self._generate_fallback_result()

    def _generate_fallback_result(self) -> DeceptionDetectionResult:
        """Generate conservative fallback for deception detection."""
        return DeceptionDetectionResult(
            backdoor_detected=False,  # Can't detect if analysis fails
            time_bomb_detected=False,
            obfuscated_code_found=True,  # Conservative: assume obfuscation
            data_exfiltration_risk=True,  # Conservative: assume risk
            environment_specific_behavior=True,  # Conservative: assume risk
            deception_indicators=["Analysis failed - comprehensive manual review required"],
            risk_level="high"  # Conservative: high risk when uncertain
        )


class CapitalRiskAnalyzer(SecurityAnalyzer):
    """Analyzer for capital and financial risk assessment."""

    def analyze(self, context: dict[str, Any], provider: BaseLLMProvider) -> CapitalRiskResult:
        """Assess capital and financial risk using LLM."""

        prompt = build_capital_risk_prompt(context)

        try:
            response = provider.call_llm(prompt)
            return self._parse_response(response)
        except Exception as e:
            self.console.print(f"[yellow]Capital risk assessment failed: {e}[/yellow]")
            return self._generate_fallback_result()

    def _parse_response(self, response: str) -> CapitalRiskResult:
        """Parse LLM response for capital risk analysis."""
        try:
            json_match = re.search(r"```json\s*(\{.*?\})\s*```", response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
            else:
                data = json.loads(response)

            return CapitalRiskResult(
                max_loss_bounded=data.get("max_loss_bounded", False),
                position_size_controls=data.get("position_size_controls", False),
                stop_loss_implemented=data.get("stop_loss_implemented", False),
                leverage_controls=data.get("leverage_controls", False),
                flash_loan_usage=data.get("flash_loan_usage", True),  # Conservative: assume yes
                risk_controls_adequate=data.get("risk_controls_adequate", False),
                estimated_max_loss=data.get("estimated_max_loss", "unlimited")
            )
        except Exception as e:
            self.console.print(f"[yellow]Failed to parse capital risk response: {e}[/yellow]")
            return self._generate_fallback_result()

    def _generate_fallback_result(self) -> CapitalRiskResult:
        """Generate conservative fallback for capital risk."""
        return CapitalRiskResult(
            max_loss_bounded=False,
            position_size_controls=False,
            stop_loss_implemented=False,
            leverage_controls=False,
            flash_loan_usage=True,  # Conservative: assume high risk
            risk_controls_adequate=False,
            estimated_max_loss="unlimited"
        )
