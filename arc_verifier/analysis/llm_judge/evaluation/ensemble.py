"""Ensemble evaluation combining multiple LLM assessments."""

import json
import re
from datetime import datetime
from typing import Any

from rich.console import Console

from ..models import (
    AgentIntentClassification,
    CodeQualityAnalysis,
    LLMJudgeResult,
    RiskAssessment,
)
from ..providers.base import BaseLLMProvider
from .prompts import build_evaluation_prompt


class EnsembleEvaluator:
    """Evaluator that combines multiple LLM assessments."""

    def __init__(self):
        self.console = Console()

    def run_evaluation(
        self,
        context: dict[str, Any],
        provider: BaseLLMProvider
    ) -> LLMJudgeResult:
        """Run evaluation using specified LLM provider."""

        # Construct evaluation prompt
        prompt = build_evaluation_prompt(context)

        # Get LLM response
        response = provider.call_llm(prompt)

        # Parse and validate response
        return self._parse_llm_response(response, context)

    def run_ensemble_evaluation(
        self,
        context: dict[str, Any],
        primary_result: LLMJudgeResult,
        fallback_provider: BaseLLMProvider | None = None
    ) -> LLMJudgeResult:
        """Run ensemble evaluation with multiple models."""
        if not fallback_provider:
            return primary_result

        try:
            # Get secondary evaluation
            secondary_result = self.run_evaluation(context, fallback_provider)

            # Combine results using weighted averaging
            ensemble_result = self._combine_evaluations(
                primary_result,
                secondary_result,
                primary_weight=0.7,
                secondary_weight=0.3,
            )

            self.console.print("[green]✓ Ensemble evaluation completed[/green]")
            return ensemble_result

        except Exception as e:
            self.console.print(
                f"[yellow]Ensemble evaluation failed: {e}, using primary result[/yellow]"
            )
            return primary_result

    def _parse_llm_response(
        self, response: str, context: dict[str, Any]
    ) -> LLMJudgeResult:
        """Parse and validate LLM response."""
        try:
            # Extract JSON from response
            json_match = re.search(r"```json\s*(\{.*?\})\s*```", response, re.DOTALL)
            if json_match:
                response_data = json.loads(json_match.group(1))
            else:
                # Try to parse entire response as JSON
                response_data = json.loads(response)

            # Validate and construct result
            return LLMJudgeResult(
                intent_classification=AgentIntentClassification(
                    **response_data["intent_classification"]
                ),
                code_quality=CodeQualityAnalysis(**response_data["code_quality"]),
                risk_assessment=RiskAssessment(**response_data["risk_assessment"]),
                behavioral_flags=response_data.get("behavioral_flags", []),
                score_adjustments=response_data.get("score_adjustments", {}),
                confidence_level=response_data.get("confidence_level", 0.5),
                reasoning=response_data.get("reasoning", ""),
                trust_recommendation=response_data.get("trust_recommendation", "CAUTION"),
                critical_issues=response_data.get("critical_issues", []),
                timestamp=datetime.now(),
            )

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            self.console.print(f"[red]Failed to parse LLM response: {e}[/red]")
            return self._generate_fallback_assessment(context)

    def _combine_evaluations(
        self,
        primary: LLMJudgeResult,
        secondary: LLMJudgeResult,
        primary_weight: float = 0.7,
        secondary_weight: float = 0.3,
    ) -> LLMJudgeResult:
        """Combine multiple LLM evaluations using weighted averaging."""

        # Weighted average for numerical scores
        def weighted_avg(p_val: float, s_val: float) -> float:
            return primary_weight * p_val + secondary_weight * s_val

        # Combine code quality scores
        combined_code_quality = CodeQualityAnalysis(
            architecture_score=weighted_avg(
                primary.code_quality.architecture_score,
                secondary.code_quality.architecture_score,
            ),
            error_handling_score=weighted_avg(
                primary.code_quality.error_handling_score,
                secondary.code_quality.error_handling_score,
            ),
            security_practices_score=weighted_avg(
                primary.code_quality.security_practices_score,
                secondary.code_quality.security_practices_score,
            ),
            maintainability_score=weighted_avg(
                primary.code_quality.maintainability_score,
                secondary.code_quality.maintainability_score,
            ),
            test_coverage_score=weighted_avg(
                primary.code_quality.test_coverage_score,
                secondary.code_quality.test_coverage_score,
            ),
            overall_score=weighted_avg(
                primary.code_quality.overall_score, secondary.code_quality.overall_score
            ),
            key_findings=list(
                set(
                    primary.code_quality.key_findings
                    + secondary.code_quality.key_findings
                )
            ),
        )

        # Combine risk assessment
        combined_risk = RiskAssessment(
            volatility_sensitivity=weighted_avg(
                primary.risk_assessment.volatility_sensitivity,
                secondary.risk_assessment.volatility_sensitivity,
            ),
            liquidity_requirements=primary.risk_assessment.liquidity_requirements,  # Use primary
            systemic_risk_score=weighted_avg(
                primary.risk_assessment.systemic_risk_score,
                secondary.risk_assessment.systemic_risk_score,
            ),
            market_impact_score=weighted_avg(
                primary.risk_assessment.market_impact_score,
                secondary.risk_assessment.market_impact_score,
            ),
            operational_risk_score=weighted_avg(
                primary.risk_assessment.operational_risk_score,
                secondary.risk_assessment.operational_risk_score,
            ),
            regulatory_risk_score=weighted_avg(
                primary.risk_assessment.regulatory_risk_score,
                secondary.risk_assessment.regulatory_risk_score,
            ),
        )

        # Combine score adjustments
        combined_adjustments = {}
        for key in set(primary.score_adjustments.keys()).union(
            secondary.score_adjustments.keys()
        ):
            p_val = primary.score_adjustments.get(key, 0)
            s_val = secondary.score_adjustments.get(key, 0)
            combined_adjustments[key] = weighted_avg(p_val, s_val)

        # Combine trust recommendations (conservative approach)
        trust_recommendations = [primary.trust_recommendation, secondary.trust_recommendation]
        if "DO_NOT_DEPLOY" in trust_recommendations:
            combined_trust = "DO_NOT_DEPLOY"
        elif "CAUTION" in trust_recommendations:
            combined_trust = "CAUTION"
        else:
            combined_trust = "DEPLOY"

        # Combine critical issues
        combined_critical_issues = list(set(primary.critical_issues + secondary.critical_issues))

        return LLMJudgeResult(
            intent_classification=primary.intent_classification,  # Use primary
            code_quality=combined_code_quality,
            risk_assessment=combined_risk,
            behavioral_flags=list(
                set(primary.behavioral_flags + secondary.behavioral_flags)
            ),
            score_adjustments=combined_adjustments,
            confidence_level=weighted_avg(
                primary.confidence_level, secondary.confidence_level
            ),
            reasoning=f"Ensemble evaluation:\n\nPrimary: {primary.reasoning}\n\nSecondary: {secondary.reasoning}",
            trust_recommendation=combined_trust,
            critical_issues=combined_critical_issues,
            timestamp=datetime.now(),
        )

    def _generate_fallback_assessment(self, context: dict[str, Any]) -> LLMJudgeResult:
        """Generate conservative fallback assessment when LLM evaluation fails."""
        return LLMJudgeResult(
            intent_classification=AgentIntentClassification(
                primary_strategy="unknown",
                risk_profile="conservative",
                complexity_score=0.5,
                confidence=0.3,
            ),
            code_quality=CodeQualityAnalysis(
                architecture_score=0.5,
                error_handling_score=0.5,
                security_practices_score=0.5,
                maintainability_score=0.5,
                test_coverage_score=0.5,
                overall_score=0.5,
                key_findings=["LLM evaluation unavailable - manual review recommended"],
            ),
            risk_assessment=RiskAssessment(
                volatility_sensitivity=0.7,  # Conservative assumption
                liquidity_requirements="high",
                systemic_risk_score=0.8,  # Conservative assumption
                market_impact_score=0.6,
                operational_risk_score=0.7,
                regulatory_risk_score=0.8,
            ),
            behavioral_flags=["LLM evaluation failed - requires manual review"],
            score_adjustments={},  # No adjustments when evaluation fails
            confidence_level=0.1,  # Very low confidence
            reasoning="LLM evaluation failed. Conservative assessment applied. Manual review strongly recommended.",
            trust_recommendation="DO_NOT_DEPLOY",  # Conservative fallback
            critical_issues=["LLM security evaluation failed - manual security audit required"],
            timestamp=datetime.now(),
        )
