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

            # Helper function to parse boolean-like values from LLM
            def parse_bool(value, conservative_default: bool) -> bool:
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    if value.lower() in ["true", "yes", "1"]:
                        return True
                    elif value.lower() in ["false", "no", "0"]:
                        return False
                    else:  # "unknown", "unclear", etc.
                        return conservative_default
                return conservative_default

            return KeySecurityResult(
                has_plaintext_keys=parse_bool(data.get("has_plaintext_keys"), True),  # Conservative: assume yes
                key_generation_secure=parse_bool(data.get("key_generation_secure"), False),  # Conservative: assume no
                key_storage_encrypted=parse_bool(data.get("key_storage_encrypted"), False),  # Conservative: assume no
                key_rotation_implemented=parse_bool(data.get("key_rotation_implemented"), False),  # Conservative: assume no
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

            # Helper function to parse boolean-like values from LLM
            def parse_bool(value, conservative_default: bool) -> bool:
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    if value.lower() in ["true", "yes", "1"]:
                        return True
                    elif value.lower() in ["false", "no", "0"]:
                        return False
                    else:  # "unknown", "unclear", etc.
                        return conservative_default
                return conservative_default

            return TransactionControlResult(
                has_spending_limits=parse_bool(data.get("has_spending_limits"), False),  # Conservative: assume no
                has_approval_mechanisms=parse_bool(data.get("has_approval_mechanisms"), False),  # Conservative: assume no
                emergency_stop_present=parse_bool(data.get("emergency_stop_present"), False),  # Conservative: assume no
                cross_chain_controls=parse_bool(data.get("cross_chain_controls"), False),  # Conservative: assume no
                transaction_monitoring=parse_bool(data.get("transaction_monitoring"), False),  # Conservative: assume no
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

            # Helper function to parse boolean-like values from LLM
            def parse_bool(value, conservative_default: bool) -> bool:
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    if value.lower() in ["true", "yes", "1"]:
                        return True
                    elif value.lower() in ["false", "no", "0"]:
                        return False
                    else:  # "unknown", "unclear", etc.
                        return conservative_default
                return conservative_default

            return DeceptionDetectionResult(
                backdoor_detected=parse_bool(data.get("backdoor_detected"), False),  # Conservative: can't detect if unknown
                time_bomb_detected=parse_bool(data.get("time_bomb_detected"), False),  # Conservative: can't detect if unknown
                obfuscated_code_found=parse_bool(data.get("obfuscated_code_found"), True),  # Conservative: assume yes if unknown
                data_exfiltration_risk=parse_bool(data.get("data_exfiltration_risk"), True),  # Conservative: assume risk if unknown
                environment_specific_behavior=parse_bool(data.get("environment_specific_behavior"), True),  # Conservative: assume risk if unknown
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

            # Helper function to parse boolean-like values from LLM
            def parse_bool(value, conservative_default: bool) -> bool:
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    if value.lower() in ["true", "yes", "1"]:
                        return True
                    elif value.lower() in ["false", "no", "0"]:
                        return False
                    else:  # "unknown", "unclear", etc.
                        return conservative_default
                return conservative_default

            return CapitalRiskResult(
                max_loss_bounded=parse_bool(data.get("max_loss_bounded"), False),  # Conservative: assume no
                position_size_controls=parse_bool(data.get("position_size_controls"), False),  # Conservative: assume no
                stop_loss_implemented=parse_bool(data.get("stop_loss_implemented"), False),  # Conservative: assume no
                leverage_controls=parse_bool(data.get("leverage_controls"), False),  # Conservative: assume no
                flash_loan_usage=parse_bool(data.get("flash_loan_usage"), True),  # Conservative: assume yes if unknown
                risk_controls_adequate=parse_bool(data.get("risk_controls_adequate"), False),  # Conservative: assume no
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
