"""Agent Fort Score calculation logic."""


def calculate_agent_fort_score(
    scan_result: dict, tee_result: dict, perf_result: dict, llm_result=None, strategy_result=None
) -> int:
    """Calculate Agent Fort score based on verification results with balanced scoring.
    
    New balanced scoring (based on executive feedback):
    - Base score: 100
    - Security: ±30 points max (was ±50)
    - LLM: ±30 points max (was ±50)
    - Behavior: ±30 points (unchanged)
    - Performance: -50 to +90 points (was -40 to +80)
    
    Total range: 0-180 points
    """
    score = 100

    # SECURITY SCORING (±30 points max)
    security_adjustment = 0
    
    # Vulnerability penalties (capped at -20)
    vulns = scan_result.get("vulnerabilities", [])
    critical = len([v for v in vulns if v.get("severity") == "CRITICAL"])
    high = len([v for v in vulns if v.get("severity") == "HIGH"])
    medium = len([v for v in vulns if v.get("severity") == "MEDIUM"])
    
    vuln_penalty = min(20, critical * 10 + high * 5 + medium * 2)
    security_adjustment -= vuln_penalty

    # TEE validation bonus/penalty
    if not tee_result.get("is_valid", True):
        security_adjustment -= 10
    else:
        # Bonus for high trust level
        trust_level = tee_result.get("trust_level", "LOW")
        if trust_level == "HIGH":
            security_adjustment += 5
        elif trust_level == "MEDIUM":
            security_adjustment += 3

    # Shade agent detection bonus
    if scan_result.get("shade_agent_detected", False):
        security_adjustment += 5

    # Cap security adjustments at ±30
    security_adjustment = max(-30, min(30, security_adjustment))
    score += security_adjustment

    # LLM INTELLIGENCE SCORING (±30 points max)
    llm_adjustment = 0
    
    if llm_result:
        # Base LLM score adjustments
        if llm_result.score_adjustments:
            for category, adjustment in llm_result.score_adjustments.items():
                llm_adjustment += adjustment

        # Code quality assessment
        if hasattr(llm_result, "code_quality") and llm_result.code_quality:
            code_quality_bonus = (llm_result.code_quality.overall_score - 0.5) * 10
            llm_adjustment += code_quality_bonus

        # Risk assessment
        if hasattr(llm_result, "risk_assessment") and llm_result.risk_assessment:
            # Critical risk flag = auto-reject (separate from scoring)
            if llm_result.risk_assessment.systemic_risk_score > 0.9:
                # This would trigger auto-reject in the status determination
                llm_adjustment -= 30
            else:
                systemic_risk_penalty = llm_result.risk_assessment.systemic_risk_score * 10
                llm_adjustment -= systemic_risk_penalty

        # Behavioral flags
        if llm_result.behavioral_flags:
            llm_adjustment -= min(10, len(llm_result.behavioral_flags) * 3)
    
    # Cap LLM adjustments at ±30
    llm_adjustment = max(-30, min(30, llm_adjustment))
    score += llm_adjustment

    # BEHAVIORAL TESTING SCORING (±30 points, from Phase 3A simulation)
    # Note: This is currently embedded in basic performance metrics
    # Will be properly separated when Phase 3A simulation results are available
    behavior_adjustment = 0
    
    # Basic performance checks (temporary placeholder for behavior scoring)
    perf_metrics = perf_result.get("performance", {})
    throughput = perf_metrics.get("throughput_tps", 0)
    avg_latency = perf_metrics.get("avg_latency_ms", 0)
    error_rate = perf_metrics.get("error_rate_percent", 0)

    # Throughput check
    if throughput < 500:
        behavior_adjustment -= 10
    elif throughput > 2000:
        behavior_adjustment += 5

    # Latency check
    if avg_latency > 100:
        behavior_adjustment -= 5
    elif avg_latency < 20:
        behavior_adjustment += 5

    # Error rate check
    if error_rate > 5:
        behavior_adjustment -= 10
    elif error_rate < 1:
        behavior_adjustment += 5

    # Cap behavior adjustments at ±30
    behavior_adjustment = max(-30, min(30, behavior_adjustment))
    score += behavior_adjustment

    # PERFORMANCE VERIFICATION SCORING (-50 to +90 points, Phase 3B)
    performance_adjustment = 0
    
    if strategy_result:
        # Strategy verification: Does it actually work as advertised? (up to +40)
        if strategy_result.verification_status == "verified":
            performance_adjustment += 30
        elif strategy_result.verification_status == "partial":
            performance_adjustment += 15
        else:
            performance_adjustment -= 20
            
        # Effectiveness score contribution (up to +30)
        effectiveness_bonus = (strategy_result.strategy_effectiveness / 100) * 30
        performance_adjustment += effectiveness_bonus
        
        # Risk management (-20 to +10)
        risk_penalty = 0
        if strategy_result.risk_score > 80:
            risk_penalty = -20  # Very high risk
        elif strategy_result.risk_score > 60:
            risk_penalty = -10  # High risk
        elif strategy_result.risk_score < 30:
            risk_penalty = 10   # Low risk, well managed
        performance_adjustment += risk_penalty
        
        # Consistency across regimes (up to +20)
        if hasattr(strategy_result, 'performance_by_regime'):
            positive_regimes = sum(1 for r in strategy_result.performance_by_regime.values() 
                                 if r.get('annualized_return', 0) > 0)
            regime_bonus = (positive_regimes / len(strategy_result.performance_by_regime)) * 20
            performance_adjustment += regime_bonus
    else:
        # No strategy verification available, use basic performance metrics
        if error_rate == 0 and throughput > 1000:
            performance_adjustment += 10  # Basic competence bonus
    
    # Final score calculation
    final_score = score + performance_adjustment
    
    # Ensure score stays within 0-180 range
    return max(0, min(180, int(final_score)))