"""Overall status determination logic."""


def determine_overall_status(
    scan_result: dict, tee_result: dict, perf_result: dict, llm_result=None, strategy_result=None
) -> str:
    """Determine overall verification status with LLM and strategy insights."""
    vulns = scan_result.get("vulnerabilities", [])
    critical = len([v for v in vulns if v.get("severity") == "CRITICAL"])
    high = len([v for v in vulns if v.get("severity") == "HIGH"])

    tee_valid = tee_result.get("is_valid", True)

    perf_metrics = perf_result.get("performance", {})
    error_rate = perf_metrics.get("error_rate_percent", 0)

    # LLM-based risk factors
    llm_risk_flags = 0
    if llm_result:
        # Count serious behavioral flags
        serious_flags = [
            flag
            for flag in llm_result.behavioral_flags
            if any(
                keyword in flag.lower()
                for keyword in ["malicious", "suspicious", "high risk", "dangerous"]
            )
        ]
        llm_risk_flags = len(serious_flags)

        # Check for high systemic risk
        if (
            hasattr(llm_result, "risk_assessment")
            and llm_result.risk_assessment
            and llm_result.risk_assessment.systemic_risk_score > 0.8
        ):
            llm_risk_flags += 1

    # Fail conditions (enhanced with LLM)
    if critical > 0:
        return "FAILED"
    if not tee_valid:
        return "FAILED"
    if error_rate > 10:
        return "FAILED"
    if llm_risk_flags >= 2:  # Multiple serious LLM flags
        return "FAILED"

    # Warning conditions (enhanced with LLM)
    if high > 5:
        return "WARNING"
    if error_rate > 5:
        return "WARNING"
    if llm_risk_flags >= 1:  # Single serious LLM flag
        return "WARNING"
    if llm_result and llm_result.confidence_level < 0.5:  # Low LLM confidence
        return "WARNING"
    
    # Strategy verification checks
    if strategy_result:
        if strategy_result.verification_status == "failed":
            return "FAILED"
        if strategy_result.risk_score > 80:  # Very high risk strategy
            return "WARNING"
        if strategy_result.strategy_effectiveness < 40:  # Low effectiveness
            return "WARNING"

    return "PASSED"