"""Core LLM judge orchestrator for trust-focused agent evaluation."""

import os
from typing import Any

from rich.console import Console

from .evaluation.ensemble import EnsembleEvaluator
from .models import LLMJudgeResult, LLMProvider, TrustFocusedResult
from .providers.factory import create_fallback_provider, create_provider
from .security.analyzers import (
    CapitalRiskAnalyzer,
    DeceptionDetector,
    KeySecurityAnalyzer,
    TransactionControlAnalyzer,
)
from .security.scoring import TrustScoreCalculator
from .utils import load_evaluation_templates, prepare_evaluation_context


class LLMJudge:
    """LLM-as-Judge integration for advanced agent evaluation."""

    def __init__(
        self,
        primary_provider: LLMProvider = LLMProvider.ANTHROPIC,
        fallback_provider: LLMProvider | None = LLMProvider.OPENAI,
        enable_ensemble: bool = True,
    ):
        self.console = Console()

        # Load from environment variables if available
        env_provider = os.getenv("LLM_PRIMARY_PROVIDER")
        self.primary_provider = (
            LLMProvider(env_provider) if env_provider else primary_provider
        )
        fallback_env = os.getenv("LLM_FALLBACK_PROVIDER")
        self.fallback_provider = (
            LLMProvider(fallback_env) if fallback_env else fallback_provider
        )
        ensemble_env = os.getenv("LLM_ENABLE_ENSEMBLE")
        self.enable_ensemble = (
            ensemble_env.lower() == "true" if ensemble_env else enable_ensemble
        )

        # Initialize providers
        self.primary_llm_provider = create_provider(self.primary_provider)
        self.fallback_llm_provider = create_fallback_provider()

        # Initialize analyzers
        self.key_security_analyzer = KeySecurityAnalyzer()
        self.transaction_control_analyzer = TransactionControlAnalyzer()
        self.deception_detector = DeceptionDetector()
        self.capital_risk_analyzer = CapitalRiskAnalyzer()
        self.trust_score_calculator = TrustScoreCalculator()
        self.ensemble_evaluator = EnsembleEvaluator()

        # Load prompts and templates
        self.templates = load_evaluation_templates()

    def evaluate_agent_security(
        self,
        image_data: dict[str, Any],
        code_analysis: dict[str, Any] | None = None,
        market_context: dict[str, Any] | None = None,
    ) -> TrustFocusedResult:
        """
        Perform trust-focused security evaluation for transaction agents.

        Args:
            image_data: Docker image analysis results
            code_analysis: Static code analysis results (if available)
            market_context: Current market conditions and context

        Returns:
            Trust-focused security evaluation result
        """
        self.console.print("[blue]🔐 Starting trust-focused security evaluation...[/blue]")

        try:
            # Prepare evaluation context
            evaluation_context = prepare_evaluation_context(
                image_data, code_analysis, market_context
            )

            # Stage 1: Critical Security Analysis
            key_security = self.key_security_analyzer.analyze(
                evaluation_context, self.primary_llm_provider
            )
            transaction_controls = self.transaction_control_analyzer.analyze(
                evaluation_context, self.primary_llm_provider
            )

            # Stage 2: Behavioral Integrity Analysis
            deception_analysis = self.deception_detector.analyze(
                evaluation_context, self.primary_llm_provider
            )

            # Stage 3: Capital Risk Assessment
            capital_risk = self.capital_risk_analyzer.analyze(
                evaluation_context, self.primary_llm_provider
            )

            # Stage 4: Overall Trust Assessment
            trust_result = self.trust_score_calculator.calculate_trust_assessment(
                key_security, transaction_controls, deception_analysis, capital_risk
            )

            return trust_result

        except Exception as e:
            self.console.print(f"[red]Trust-focused evaluation failed: {e}[/red]")
            # Return conservative fallback assessment
            return self.trust_score_calculator.generate_fallback_trust_assessment(image_data)

    def evaluate_agent(
        self,
        image_data: dict[str, Any],
        code_analysis: dict[str, Any] | None = None,
        market_context: dict[str, Any] | None = None,
    ) -> LLMJudgeResult:
        """
        Perform comprehensive LLM-based agent evaluation.

        Args:
            image_data: Docker image analysis results
            code_analysis: Static code analysis results (if available)
            market_context: Current market conditions and context

        Returns:
            Complete LLM evaluation result
        """
        self.console.print("[blue]🧠 Starting LLM-based agent evaluation...[/blue]")

        try:
            # Prepare evaluation context
            evaluation_context = prepare_evaluation_context(
                image_data, code_analysis, market_context
            )

            # Run primary evaluation
            primary_result = self.ensemble_evaluator.run_evaluation(
                evaluation_context, self.primary_llm_provider
            )

            # Run ensemble evaluation if enabled
            if self.enable_ensemble and self.fallback_llm_provider:
                ensemble_result = self.ensemble_evaluator.run_ensemble_evaluation(
                    evaluation_context, primary_result, self.fallback_llm_provider
                )
                return ensemble_result

            return primary_result

        except Exception as e:
            self.console.print(f"[red]LLM evaluation failed: {e}[/red]")
            # Return conservative fallback assessment
            return self.ensemble_evaluator._generate_fallback_assessment(image_data)
