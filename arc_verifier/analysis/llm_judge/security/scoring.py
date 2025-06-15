"""Trust score calculation and reasoning generation."""


from ..models import (
    CapitalRiskResult,
    DeceptionDetectionResult,
    KeySecurityResult,
    TransactionControlResult,
    TrustFocusedResult,
)


class TrustScoreCalculator:
    """Calculator for trust scores and recommendations."""

    def calculate_trust_assessment(
        self,
        key_security: KeySecurityResult,
        transaction_controls: TransactionControlResult,
        deception_analysis: DeceptionDetectionResult,
        capital_risk: CapitalRiskResult
    ) -> TrustFocusedResult:
        """Calculate overall trust score and compile results."""

        # Critical failures that immediately disqualify
        critical_vulnerabilities = []
        if key_security.has_plaintext_keys:
            critical_vulnerabilities.append("Private keys stored in plaintext")
        if not transaction_controls.has_spending_limits:
            critical_vulnerabilities.append("No transaction spending limits")
        if deception_analysis.backdoor_detected:
            critical_vulnerabilities.append("Backdoor access detected")
        if deception_analysis.risk_level == "critical":
            critical_vulnerabilities.append("Critical deception patterns detected")

        # Calculate weighted trust score
        trust_score = 0.0

        # Key security (30% weight)
        key_score = 0.0
        if not key_security.has_plaintext_keys:
            key_score += 0.4
        if key_security.key_generation_secure:
            key_score += 0.3
        if key_security.key_storage_encrypted:
            key_score += 0.2
        if key_security.key_rotation_implemented:
            key_score += 0.1
        trust_score += key_score * 0.3

        # Transaction controls (25% weight)
        tx_score = 0.0
        if transaction_controls.has_spending_limits:
            tx_score += 0.4
        if transaction_controls.has_approval_mechanisms:
            tx_score += 0.3
        if transaction_controls.emergency_stop_present:
            tx_score += 0.2
        if transaction_controls.transaction_monitoring:
            tx_score += 0.1
        trust_score += tx_score * 0.25

        # Deception analysis (20% weight)
        deception_score = 1.0  # Start with full score
        if deception_analysis.backdoor_detected:
            deception_score -= 0.5
        if deception_analysis.time_bomb_detected:
            deception_score -= 0.3
        if deception_analysis.obfuscated_code_found:
            deception_score -= 0.2
        deception_score = max(0.0, deception_score)
        trust_score += deception_score * 0.2

        # Capital risk (25% weight)
        capital_score = 0.0
        if capital_risk.max_loss_bounded:
            capital_score += 0.3
        if capital_risk.position_size_controls:
            capital_score += 0.3
        if capital_risk.stop_loss_implemented:
            capital_score += 0.2
        if capital_risk.risk_controls_adequate:
            capital_score += 0.2
        trust_score += capital_score * 0.25

        # Determine if agent can be trusted with capital
        can_trust = (
            len(critical_vulnerabilities) == 0 and
            trust_score > 0.8 and
            key_security.key_exposure_risk in ["low", "medium"] and
            transaction_controls.control_strength != "weak"
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            key_security, transaction_controls, capital_risk
        )

        return TrustFocusedResult(
            can_trust_with_capital=can_trust,
            trust_score=trust_score,
            key_security=key_security,
            transaction_controls=transaction_controls,
            deception_analysis=deception_analysis,
            capital_risk=capital_risk,
            critical_vulnerabilities=critical_vulnerabilities,
            security_recommendations=recommendations,
            confidence_level=0.85,  # High confidence in security-focused analysis
            reasoning=self._generate_trust_reasoning(
                key_security, transaction_controls, deception_analysis, capital_risk, trust_score
            )
        )

    def _generate_recommendations(
        self,
        key_security: KeySecurityResult,
        transaction_controls: TransactionControlResult,
        capital_risk: CapitalRiskResult
    ) -> list[str]:
        """Generate security recommendations based on analysis."""
        recommendations = []

        if key_security.has_plaintext_keys:
            recommendations.append("CRITICAL: Implement secure key storage (TEE/encryption)")
        if not transaction_controls.has_spending_limits:
            recommendations.append("CRITICAL: Add transaction spending limits")
        if not capital_risk.max_loss_bounded:
            recommendations.append("HIGH: Implement maximum loss limits")
        if not transaction_controls.emergency_stop_present:
            recommendations.append("MEDIUM: Add emergency stop mechanisms")

        return recommendations

    def _generate_trust_reasoning(
        self,
        key_security: KeySecurityResult,
        transaction_controls: TransactionControlResult,
        deception_analysis: DeceptionDetectionResult,
        capital_risk: CapitalRiskResult,
        trust_score: float
    ) -> str:
        """Generate detailed reasoning for trust assessment."""

        reasoning_parts = []

        # Key security assessment
        if key_security.has_plaintext_keys:
            reasoning_parts.append("🚨 CRITICAL: Private keys stored in plaintext - immediate security failure.")
        elif key_security.key_exposure_risk == "high":
            reasoning_parts.append("⚠️ HIGH RISK: Significant private key exposure risks detected.")
        elif key_security.key_generation_secure and key_security.key_storage_encrypted:
            reasoning_parts.append("✅ Key security appears adequate with secure generation and encrypted storage.")

        # Transaction controls
        if not transaction_controls.has_spending_limits:
            reasoning_parts.append("🚨 CRITICAL: No transaction spending limits - agent can drain wallet.")
        elif transaction_controls.control_strength == "strong":
            reasoning_parts.append("✅ Strong transaction controls with comprehensive safeguards.")
        elif transaction_controls.control_strength == "weak":
            reasoning_parts.append("⚠️ Weak transaction controls - insufficient protection.")

        # Deception analysis
        if deception_analysis.backdoor_detected:
            reasoning_parts.append("🚨 CRITICAL: Backdoor access mechanisms detected.")
        elif deception_analysis.risk_level == "high":
            reasoning_parts.append("⚠️ HIGH RISK: Suspicious behavioral patterns detected.")
        elif deception_analysis.risk_level == "low":
            reasoning_parts.append("✅ No significant deceptive patterns detected.")

        # Capital risk
        if capital_risk.estimated_max_loss == "unlimited":
            reasoning_parts.append("🚨 CRITICAL: Unlimited loss potential - inadequate risk controls.")
        elif not capital_risk.risk_controls_adequate:
            reasoning_parts.append("⚠️ Risk management controls are insufficient for capital protection.")
        elif capital_risk.max_loss_bounded and capital_risk.stop_loss_implemented:
            reasoning_parts.append("✅ Adequate risk controls with bounded loss potential.")

        # Overall assessment
        if trust_score > 0.9:
            reasoning_parts.append(f"🟢 TRUST SCORE: {trust_score:.2f} - High confidence for deployment.")
        elif trust_score > 0.7:
            reasoning_parts.append(f"🟡 TRUST SCORE: {trust_score:.2f} - Acceptable with monitoring.")
        else:
            reasoning_parts.append(f"🔴 TRUST SCORE: {trust_score:.2f} - Not recommended for deployment.")

        return "\n\n".join(reasoning_parts)

    def generate_fallback_trust_assessment(self, context: dict) -> TrustFocusedResult:
        """Generate conservative fallback trust assessment."""
        key_security = KeySecurityResult(
            has_plaintext_keys=True,
            key_generation_secure=False,
            key_storage_encrypted=False,
            key_rotation_implemented=False,
            key_exposure_risk="critical",
            security_concerns=["Analysis failed - manual security review required"],
            code_references=[]
        )

        transaction_controls = TransactionControlResult(
            has_spending_limits=False,
            has_approval_mechanisms=False,
            emergency_stop_present=False,
            cross_chain_controls=False,
            transaction_monitoring=False,
            control_strength="weak",
            control_gaps=["Analysis failed - manual review required"]
        )

        deception_analysis = DeceptionDetectionResult(
            backdoor_detected=False,
            time_bomb_detected=False,
            obfuscated_code_found=True,
            data_exfiltration_risk=True,
            environment_specific_behavior=True,
            deception_indicators=["Analysis failed - comprehensive manual review required"],
            risk_level="high"
        )

        capital_risk = CapitalRiskResult(
            max_loss_bounded=False,
            position_size_controls=False,
            stop_loss_implemented=False,
            leverage_controls=False,
            flash_loan_usage=True,
            risk_controls_adequate=False,
            estimated_max_loss="unlimited"
        )

        return TrustFocusedResult(
            can_trust_with_capital=False,  # Never trust when analysis fails
            trust_score=0.0,
            key_security=key_security,
            transaction_controls=transaction_controls,
            deception_analysis=deception_analysis,
            capital_risk=capital_risk,
            critical_vulnerabilities=["Security analysis failed - comprehensive manual review required"],
            security_recommendations=[
                "CRITICAL: Perform manual security audit before deployment",
                "CRITICAL: Verify private key security manually",
                "CRITICAL: Test transaction controls manually",
                "HIGH: Review code for deceptive patterns"
            ],
            confidence_level=0.0,
            reasoning="Trust-focused security analysis failed. Conservative assessment applied. Manual security review strongly recommended before any deployment."
        )
