"""LLM-as-Judge Integration for Advanced Fort Scoring."""

import json
import os
import re
from datetime import datetime
from enum import Enum
from typing import Any

import httpx
from pydantic import BaseModel
from rich.console import Console


class LLMProvider(str, Enum):
    """Supported LLM providers for agent evaluation."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    LOCAL = "local"


class AgentIntentClassification(BaseModel):
    """Agent intent classification result."""

    primary_strategy: str  # e.g., "arbitrage", "market_making", "yield_farming"
    risk_profile: str  # "conservative", "moderate", "aggressive"
    complexity_score: float  # 0.0 - 1.0
    confidence: float  # 0.0 - 1.0


class CodeQualityAnalysis(BaseModel):
    """Code quality evaluation result."""

    architecture_score: float  # 0.0 - 1.0
    error_handling_score: float  # 0.0 - 1.0
    security_practices_score: float  # 0.0 - 1.0
    maintainability_score: float  # 0.0 - 1.0
    test_coverage_score: float  # 0.0 - 1.0
    overall_score: float  # 0.0 - 1.0
    key_findings: list[str]


class RiskAssessment(BaseModel):
    """Contextual risk assessment result."""

    volatility_sensitivity: float  # 0.0 - 1.0 (higher = more sensitive)
    liquidity_requirements: str  # "low", "medium", "high"
    systemic_risk_score: float  # 0.0 - 1.0 (higher = more systemic risk)
    market_impact_score: float  # 0.0 - 1.0 (higher = more market impact)
    operational_risk_score: float  # 0.0 - 1.0
    regulatory_risk_score: float  # 0.0 - 1.0


class KeySecurityResult(BaseModel):
    """Private key security analysis result."""

    has_plaintext_keys: bool  # Critical security failure
    key_generation_secure: bool  # Generated in TEE/secure environment
    key_storage_encrypted: bool  # Keys encrypted at rest
    key_rotation_implemented: bool  # Rotation capability exists
    key_exposure_risk: str  # "low", "medium", "high", "critical"
    security_concerns: list[str]  # Specific issues found
    code_references: list[str]  # Lines/files with issues


class TransactionControlResult(BaseModel):
    """Transaction authorization control analysis."""

    has_spending_limits: bool  # Transaction amount limits
    has_approval_mechanisms: bool  # Multi-sig, time-locks, etc.
    emergency_stop_present: bool  # Circuit breaker mechanisms
    cross_chain_controls: bool  # Bridge/cross-chain security
    transaction_monitoring: bool  # Audit trail implementation
    control_strength: str  # "weak", "moderate", "strong"
    control_gaps: list[str]  # Missing or weak controls


class DeceptionDetectionResult(BaseModel):
    """Malicious pattern and deception detection."""

    backdoor_detected: bool  # Hidden admin access
    time_bomb_detected: bool  # Delayed activation logic
    obfuscated_code_found: bool  # Deliberately hidden logic
    data_exfiltration_risk: bool  # Unauthorized data transmission
    environment_specific_behavior: bool  # Different behavior in test vs prod
    deception_indicators: list[str]  # Specific suspicious patterns
    risk_level: str  # "low", "medium", "high", "critical"


class CapitalRiskResult(BaseModel):
    """Capital and financial risk assessment."""

    max_loss_bounded: bool  # Maximum possible loss is limited
    position_size_controls: bool  # Position sizing safeguards
    stop_loss_implemented: bool  # Automatic loss limits
    leverage_controls: bool  # Leverage/margin restrictions
    flash_loan_usage: bool  # Uses flash loans (higher risk)
    risk_controls_adequate: bool  # Overall risk management quality
    estimated_max_loss: str  # "bounded", "portfolio_percentage", "unlimited"


class TrustFocusedResult(BaseModel):
    """Trust-focused evaluation result for transaction agents."""

    can_trust_with_capital: bool  # Primary trust decision
    trust_score: float  # 0.0 - 1.0 overall trust score
    key_security: KeySecurityResult
    transaction_controls: TransactionControlResult
    deception_analysis: DeceptionDetectionResult
    capital_risk: CapitalRiskResult
    critical_vulnerabilities: list[str]  # Show-stopper issues
    security_recommendations: list[str]  # Required fixes
    confidence_level: float  # Confidence in analysis
    reasoning: str  # Detailed security assessment


class LLMJudgeResult(BaseModel):
    """Complete LLM judge evaluation result."""

    intent_classification: AgentIntentClassification
    code_quality: CodeQualityAnalysis
    risk_assessment: RiskAssessment
    behavioral_flags: list[str]
    score_adjustments: dict[str, float]  # category -> adjustment (-50 to +50)
    confidence_level: float  # Overall confidence in assessment
    reasoning: str  # Detailed explanation
    trust_recommendation: str | None = None  # DEPLOY/CAUTION/DO_NOT_DEPLOY
    critical_issues: list[str] = []  # Critical security issues found
    timestamp: datetime


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

        # Initialize HTTP client for API calls
        timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
        self.client = httpx.Client(timeout=timeout)

        # Load prompts and templates
        self._load_evaluation_templates()

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
            evaluation_context = self._prepare_evaluation_context(
                image_data, code_analysis, market_context
            )

            # Stage 1: Critical Security Analysis
            key_security = self._analyze_key_security(evaluation_context)
            transaction_controls = self._analyze_transaction_controls(evaluation_context)

            # Stage 2: Behavioral Integrity Analysis
            deception_analysis = self._detect_malicious_patterns(evaluation_context)

            # Stage 3: Capital Risk Assessment
            capital_risk = self._assess_capital_risk(evaluation_context)

            # Stage 4: Overall Trust Assessment
            trust_result = self._calculate_trust_score(
                key_security, transaction_controls, deception_analysis, capital_risk
            )

            return trust_result

        except Exception as e:
            self.console.print(f"[red]Trust-focused evaluation failed: {e}[/red]")
            # Return conservative fallback assessment
            return self._generate_fallback_trust_assessment(image_data)

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
            evaluation_context = self._prepare_evaluation_context(
                image_data, code_analysis, market_context
            )

            # Run primary evaluation
            primary_result = self._run_evaluation(
                evaluation_context, self.primary_provider
            )

            # Run ensemble evaluation if enabled
            if self.enable_ensemble and self.fallback_provider:
                ensemble_result = self._run_ensemble_evaluation(
                    evaluation_context, primary_result
                )
                return ensemble_result

            return primary_result

        except Exception as e:
            self.console.print(f"[red]LLM evaluation failed: {e}[/red]")
            # Return conservative fallback assessment
            return self._generate_fallback_assessment(image_data)

    def _prepare_evaluation_context(
        self,
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
                "vulnerabilities": self._summarize_vulnerabilities(
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
        context["agent_patterns"] = self._extract_agent_patterns(
            image_data.get("layers", [])
        )

        return context

    def _run_evaluation(
        self, context: dict[str, Any], provider: LLMProvider
    ) -> LLMJudgeResult:
        """Run evaluation using specified LLM provider."""

        # Construct evaluation prompt
        prompt = self._build_evaluation_prompt(context)

        # Get LLM response
        if provider == LLMProvider.ANTHROPIC:
            response = self._call_anthropic(prompt)
        elif provider == LLMProvider.OPENAI:
            response = self._call_openai(prompt)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        # Parse and validate response
        return self._parse_llm_response(response, context)

    def _run_ensemble_evaluation(
        self, context: dict[str, Any], primary_result: LLMJudgeResult
    ) -> LLMJudgeResult:
        """Run ensemble evaluation with multiple models."""
        try:
            # Get secondary evaluation
            if self.fallback_provider is None:
                return primary_result
            secondary_result = self._run_evaluation(context, self.fallback_provider)

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

    def _build_evaluation_prompt(self, context: dict[str, Any]) -> str:
        """Build trust-focused evaluation prompt for LLM."""

        prompt = f"""
# Trust-Critical Agent Evaluation Task

You are a security auditor evaluating if this autonomous agent can be trusted with user capital. Users will potentially trust this agent with $40k+ annually.

**CORE QUESTION: Can this agent be trusted with real money?**

## Agent Context
- **Image**: {context['image_info']['tag']}
- **Size**: {context['image_info']['size'] / 1024 / 1024:.1f} MB
- **Layers**: {context['image_info']['layers']}
- **Shade Agent Detected**: {context['image_info']['shade_agent_detected']}
- **Vulnerabilities**: {context['image_info']['vulnerabilities']}

## Agent Patterns Detected
{self._format_agent_patterns(context.get('agent_patterns', {}))}

## TRUST-FOCUSED EVALUATION REQUIREMENTS

Be paranoid. Focus on trust-critical security concerns:

### 1. Intent Classification (Basic Strategy Understanding)
- Primary strategy (arbitrage, market_making, yield_farming, etc.)
- Risk profile (conservative, moderate, aggressive)
- Complexity assessment (0.0-1.0)

### 2. CRITICAL SECURITY ANALYSIS

#### A. Private Key Security (CRITICAL)
- How are private keys generated? (entropy source, randomness)
- Where are keys stored? (plaintext files, environment variables, encrypted)
- Can keys be exposed through logs, errors, or API responses?
- Is there proper key rotation capability?
- Are keys isolated in TEE/secure enclave?

**RED FLAGS**: Plaintext keys, hardcoded keys, keys in logs, predictable generation

#### B. Transaction Authorization Controls (CRITICAL)
- What authorizes a transaction? (approval mechanisms)
- Are there transaction amount limits?
- Can the agent drain all funds?
- Are there emergency stop mechanisms?
- Multi-signature or time-lock requirements?
- Cross-chain bridge security

**RED FLAGS**: No spending limits, unlimited fund access, no emergency stops

#### C. Malicious Pattern Detection (CRITICAL)
- Hidden functionality that activates later (time bombs)
- Obfuscated or encrypted code sections
- Different behavior in testnet vs mainnet
- Unauthorized network connections
- Data exfiltration attempts
- Backdoor mechanisms or admin overrides

**RED FLAGS**: Base64 strings, dynamic code execution, environment-specific behavior

### 3. Code Quality Analysis (Secondary)
- Architecture design quality (0.0-1.0)
- Error handling completeness (0.0-1.0)
- Security best practices (0.0-1.0)
- Maintainability score (0.0-1.0)
- Key findings and recommendations

### 4. Risk Assessment (Secondary)
- Volatility sensitivity (0.0-1.0)
- Liquidity requirements (low/medium/high)
- Systemic risk potential (0.0-1.0)
- Market impact assessment (0.0-1.0)

### 5. Trust Score Adjustments
Provide score adjustments (-50 to +50 points) for:
- **security_critical**: Private key security, transaction controls
- **deception_risk**: Malicious patterns, hidden functionality
- **capital_safety**: Fund protection, emergency mechanisms
- **transparency**: Code clarity, audit-friendly implementation

## TRUST EVALUATION STANDARDS

**CRITICAL FAILURES** (Immediate disqualification):
- Private keys in plaintext (-50 points)
- No transaction limits (-40 points)
- Malicious patterns detected (-50 points)
- Hidden backdoors (-50 points)

**HIGH RISK** (Major concerns):
- Weak key storage (-30 points)
- Poor transaction controls (-25 points)
- Obfuscated code (-20 points)
- No emergency stops (-20 points)

Return your analysis in JSON format matching this structure:
```json
{{
  "intent_classification": {{
    "primary_strategy": "strategy_name",
    "risk_profile": "conservative|moderate|aggressive",
    "complexity_score": 0.0,
    "confidence": 0.0
  }},
  "code_quality": {{
    "architecture_score": 0.0,
    "error_handling_score": 0.0,
    "security_practices_score": 0.0,
    "maintainability_score": 0.0,
    "test_coverage_score": 0.0,
    "overall_score": 0.0,
    "key_findings": ["finding1", "finding2"]
  }},
  "risk_assessment": {{
    "volatility_sensitivity": 0.0,
    "liquidity_requirements": "low|medium|high",
    "systemic_risk_score": 0.0,
    "market_impact_score": 0.0,
    "operational_risk_score": 0.0,
    "regulatory_risk_score": 0.0
  }},
  "behavioral_flags": ["flag1", "flag2"],
  "score_adjustments": {{
    "security_critical": 0.0,
    "deception_risk": 0.0,
    "capital_safety": 0.0,
    "transparency": 0.0
  }},
  "confidence_level": 0.0,
  "reasoning": "Focus on trust-critical security concerns and specific vulnerabilities found...",
  "trust_recommendation": "DEPLOY|CAUTION|DO_NOT_DEPLOY",
  "critical_issues": ["List any critical security issues that must be fixed"]
}}
```

**REMEMBER**: Users are trusting this agent with real money. Be thorough and paranoid about security.
"""
        return prompt.strip()

    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude API."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            self.console.print(
                "[yellow]ANTHROPIC_API_KEY not found, using mock response[/yellow]"
            )
            return self._generate_mock_anthropic_response(prompt)

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
            return self._generate_mock_anthropic_response(prompt)

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            self.console.print(
                "[yellow]OPENAI_API_KEY not found, using mock response[/yellow]"
            )
            return self._generate_mock_openai_response(prompt)

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
            return self._generate_mock_openai_response(prompt)

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

    # Trust-focused security analysis methods

    def _analyze_key_security(self, context: dict[str, Any]) -> KeySecurityResult:
        """Analyze private key security patterns using LLM."""

        prompt = self._build_key_security_prompt(context)

        try:
            if self.primary_provider == LLMProvider.ANTHROPIC:
                response = self._call_anthropic(prompt)
            elif self.primary_provider == LLMProvider.OPENAI:
                response = self._call_openai(prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.primary_provider}")

            return self._parse_key_security_response(response)
        except Exception as e:
            self.console.print(f"[yellow]Key security analysis failed: {e}[/yellow]")
            return self._generate_fallback_key_security()

    def _analyze_transaction_controls(self, context: dict[str, Any]) -> TransactionControlResult:
        """Analyze transaction authorization controls using LLM."""

        prompt = self._build_transaction_control_prompt(context)

        try:
            if self.primary_provider == LLMProvider.ANTHROPIC:
                response = self._call_anthropic(prompt)
            elif self.primary_provider == LLMProvider.OPENAI:
                response = self._call_openai(prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.primary_provider}")

            return self._parse_transaction_control_response(response)
        except Exception as e:
            self.console.print(f"[yellow]Transaction control analysis failed: {e}[/yellow]")
            return self._generate_fallback_transaction_controls()

    def _detect_malicious_patterns(self, context: dict[str, Any]) -> DeceptionDetectionResult:
        """Detect malicious patterns and deception using LLM."""

        prompt = self._build_deception_detection_prompt(context)

        try:
            if self.primary_provider == LLMProvider.ANTHROPIC:
                response = self._call_anthropic(prompt)
            elif self.primary_provider == LLMProvider.OPENAI:
                response = self._call_openai(prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.primary_provider}")

            return self._parse_deception_response(response)
        except Exception as e:
            self.console.print(f"[yellow]Deception detection failed: {e}[/yellow]")
            return self._generate_fallback_deception_detection()

    def _assess_capital_risk(self, context: dict[str, Any]) -> CapitalRiskResult:
        """Assess capital and financial risk using LLM."""

        prompt = self._build_capital_risk_prompt(context)

        try:
            if self.primary_provider == LLMProvider.ANTHROPIC:
                response = self._call_anthropic(prompt)
            elif self.primary_provider == LLMProvider.OPENAI:
                response = self._call_openai(prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.primary_provider}")

            return self._parse_capital_risk_response(response)
        except Exception as e:
            self.console.print(f"[yellow]Capital risk assessment failed: {e}[/yellow]")
            return self._generate_fallback_capital_risk()

    def _calculate_trust_score(
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
        recommendations = []
        if key_security.has_plaintext_keys:
            recommendations.append("CRITICAL: Implement secure key storage (TEE/encryption)")
        if not transaction_controls.has_spending_limits:
            recommendations.append("CRITICAL: Add transaction spending limits")
        if not capital_risk.max_loss_bounded:
            recommendations.append("HIGH: Implement maximum loss limits")
        if not transaction_controls.emergency_stop_present:
            recommendations.append("MEDIUM: Add emergency stop mechanisms")

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

    # Helper methods for processing and mock responses

    def _summarize_vulnerabilities(self, vulnerabilities: list[dict]) -> dict[str, int]:
        """Summarize vulnerability counts by severity."""
        counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "UNKNOWN")
            if severity in counts:
                counts[severity] += 1
        return counts

    def _extract_agent_patterns(self, layers: list[dict]) -> dict[str, list[str]]:
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

    def _format_agent_patterns(self, patterns: dict[str, list[str]]) -> str:
        """Format agent patterns for prompt inclusion."""
        formatted = []
        for category, items in patterns.items():
            if items:
                formatted.append(f"**{category.title()}:**")
                for item in items[:3]:  # Limit to 3 items per category
                    formatted.append(f"  - {item}")
        return "\n".join(formatted) if formatted else "No specific patterns detected"

    def _load_evaluation_templates(self):
        """Load evaluation templates and prompts."""
        # In production, these would be loaded from files or configuration
        self.templates = {
            "agent_classification": "Classify agent strategy and risk profile",
            "code_quality": "Assess code architecture and maintainability",
            "risk_assessment": "Evaluate market and operational risks",
        }

    # Trust-focused prompt building methods

    def _build_key_security_prompt(self, context: dict[str, Any]) -> str:
        """Build prompt for private key security analysis."""
        return f"""
# Private Key Security Analysis

You are a security auditor evaluating if this autonomous agent can be trusted with private key management.

## Context
- **Image**: {context.get('image_info', {}).get('tag', 'unknown')}
- **Agent Patterns**: {self._format_agent_patterns(context.get('agent_patterns', {}))}

## Critical Security Analysis

Analyze for private key security vulnerabilities based on Coinbase CDP and Stripe security patterns:

### Key Generation Security
- Are private keys generated securely with proper entropy?
- Is key generation performed in TEE/secure enclave?
- Are keys generated deterministically or non-deterministically?
- Is there proper randomness validation?

### Key Storage Security
- How are private keys stored? (plaintext/encrypted/TEE-only)
- Are keys exposed in environment variables or config files?
- Is there memory protection for key material?
- Are keys automatically destroyed after use?

### Key Exposure Risks
- Can keys be exposed through logs, errors, or API responses?
- Are keys transmitted over insecure channels?
- Is there key serialization/deserialization that could leak keys?
- Are there debugging features that might expose keys?

### Key Management Best Practices
- Is there key rotation capability?
- Are keys isolated per user/session?
- Is there backup/recovery for keys?
- Are wallet.json files or mnemonic phrases handled securely?

## Red Flags (Immediate Disqualification)
- Private keys in plaintext anywhere
- Keys hardcoded in source code
- Keys in environment variables without encryption
- Keys logged to files or console

Return your analysis in JSON format:
```json
{{
  "has_plaintext_keys": false,
  "key_generation_secure": true,
  "key_storage_encrypted": true,
  "key_rotation_implemented": true,
  "key_exposure_risk": "low|medium|high|critical",
  "security_concerns": ["concern1", "concern2"],
  "code_references": ["file:line", "pattern"]
}}
```

Be paranoid. Users will trust this agent with $40k+ annually.
"""

    def _build_transaction_control_prompt(self, context: dict[str, Any]) -> str:
        """Build prompt for transaction control analysis."""
        return f"""
# Transaction Authorization Control Analysis

You are a security auditor evaluating transaction controls for an autonomous trading agent.

## Context
- **Image**: {context.get('image_info', {}).get('tag', 'unknown')}
- **Agent Patterns**: {self._format_agent_patterns(context.get('agent_patterns', {}))}

## Transaction Security Analysis

Based on Stripe's granular permission model and Coinbase CDP security patterns:

### Spending Limits & Controls
- Are there per-transaction amount limits?
- Are there daily/hourly spending limits?
- Are there percentage-of-portfolio limits?
- Can the agent drain the entire wallet?

### Authorization Mechanisms
- What authorizes a transaction? (multi-sig, time-locks, approvals)
- Are there human-in-the-loop requirements for large transactions?
- Is there transaction preview/confirmation?
- Are there emergency stop mechanisms?

### Cross-Chain Security
- How are bridge transactions validated?
- Is there slippage protection?
- Are gas estimation safeguards in place?
- Is there MEV protection?

### Transaction Monitoring
- Are all transactions logged immutably?
- Is there real-time transaction monitoring?
- Are suspicious patterns detected?
- Is there audit trail completeness?

## Stripe Security Model Evaluation
- Granular permissions per action type (create/read/update)
- Explicit action allowlists
- Context-based restrictions (account-specific operations)
- Request validation and sanitization

Look for functions like: sign_tx(), approve(), transfer(), send(), swap()

Return your analysis in JSON format:
```json
{{
  "has_spending_limits": true,
  "has_approval_mechanisms": true,
  "emergency_stop_present": true,
  "cross_chain_controls": true,
  "transaction_monitoring": true,
  "control_strength": "weak|moderate|strong",
  "control_gaps": ["gap1", "gap2"]
}}
```

Focus on: Can this agent drain funds or execute unauthorized transactions?
"""

    def _build_deception_detection_prompt(self, context: dict[str, Any]) -> str:
        """Build prompt for deception and malicious pattern detection."""
        return f"""
# Malicious Pattern & Deception Detection

You are a security auditor looking for deceptive or malicious patterns in an autonomous agent.

## Context
- **Image**: {context.get('image_info', {}).get('tag', 'unknown')}
- **Agent Patterns**: {self._format_agent_patterns(context.get('agent_patterns', {}))}

## Deception Analysis

### Hidden Functionality
- Time-delayed activation logic
- Environment-specific behavior (testnet vs mainnet)
- Hidden admin commands or backdoors
- Debug modes that shouldn't be in production

### Obfuscation Patterns
- Base64 encoded strings (suspicious)
- Dynamic code execution
- Encrypted or obfuscated code sections
- Unusual imports or dependencies

### Market Manipulation Risks
- Front-running capabilities
- Pump-and-dump patterns
- Wash trading logic
- Order book manipulation

### Data Exfiltration Risks
- Unauthorized network connections
- Data encryption before transmission
- Keylogging or screen capture
- Memory dumping capabilities

### Behavioral Inconsistencies
- Logic that behaves differently in test vs production
- Random delays or timing patterns
- Unusual error handling that might hide malicious activity
- Code that activates based on specific dates/times

## Red Flags
- Any backdoor access mechanisms
- Code that phones home to unexpected servers
- Logic that can change fundamental behavior
- Patterns that suggest the agent is doing more than claimed

Return your analysis in JSON format:
```json
{{
  "backdoor_detected": false,
  "time_bomb_detected": false,
  "obfuscated_code_found": false,
  "data_exfiltration_risk": false,
  "environment_specific_behavior": false,
  "deception_indicators": ["indicator1", "indicator2"],
  "risk_level": "low|medium|high|critical"
}}
```

Be extremely suspicious. Look for anything that suggests the agent might not do what it claims.
"""

    def _build_capital_risk_prompt(self, context: dict[str, Any]) -> str:
        """Build prompt for capital risk assessment."""
        return f"""
# Capital & Financial Risk Assessment

You are a risk management auditor evaluating capital protection for an autonomous trading agent.

## Context
- **Image**: {context.get('image_info', {}).get('tag', 'unknown')}
- **Agent Patterns**: {self._format_agent_patterns(context.get('agent_patterns', {}))}

## Capital Risk Analysis

### Maximum Loss Assessment
- What's the maximum possible loss in a single transaction?
- What's the maximum possible loss in a single day?
- Can the agent lose 100% of allocated capital?
- Are there circuit breakers for large losses?

### Position Size Controls
- Are there position size limits relative to portfolio?
- Can the agent over-leverage positions?
- Are there correlation limits across positions?
- Is there proper portfolio allocation logic?

### Risk Management Controls
- Are stop-loss mechanisms implemented and tested?
- Is there proper risk/reward calculation?
- Are there drawdown limits?
- Is there volatility-based position sizing?

### Advanced Risk Factors
- Does the agent use leverage or margin trading?
- Are flash loans utilized (higher risk)?
- Is there exposure to liquidation cascades?
- Are there counterparty risks?

### Market Risk Controls
- How does the agent handle extreme market conditions?
- Are there safeguards against flash crashes?
- Is there protection against market manipulation?
- How are outlier events handled?

## Risk Control Evaluation
Look for functions like: calculate_position_size(), set_stop_loss(), check_risk_limits()

Return your analysis in JSON format:
```json
{{
  "max_loss_bounded": true,
  "position_size_controls": true,
  "stop_loss_implemented": true,
  "leverage_controls": true,
  "flash_loan_usage": false,
  "risk_controls_adequate": true,
  "estimated_max_loss": "bounded|portfolio_percentage|unlimited"
}}
```

Critical question: Could this agent lose more money than acceptable in worst-case scenarios?
"""

    # Response parsing methods for trust-focused analysis

    def _parse_key_security_response(self, response: str) -> KeySecurityResult:
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
            return self._generate_fallback_key_security()

    def _parse_transaction_control_response(self, response: str) -> TransactionControlResult:
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
            return self._generate_fallback_transaction_controls()

    def _parse_deception_response(self, response: str) -> DeceptionDetectionResult:
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
            return self._generate_fallback_deception_detection()

    def _parse_capital_risk_response(self, response: str) -> CapitalRiskResult:
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
            return self._generate_fallback_capital_risk()

    # Fallback methods for trust-focused analysis

    def _generate_fallback_key_security(self) -> KeySecurityResult:
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

    def _generate_fallback_transaction_controls(self) -> TransactionControlResult:
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

    def _generate_fallback_deception_detection(self) -> DeceptionDetectionResult:
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

    def _generate_fallback_capital_risk(self) -> CapitalRiskResult:
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

    def _generate_fallback_trust_assessment(self, context: dict[str, Any]) -> TrustFocusedResult:
        """Generate conservative fallback trust assessment."""
        key_security = self._generate_fallback_key_security()
        transaction_controls = self._generate_fallback_transaction_controls()
        deception_analysis = self._generate_fallback_deception_detection()
        capital_risk = self._generate_fallback_capital_risk()

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

    def _generate_mock_anthropic_response(self, prompt: str) -> str:
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

    def _generate_mock_openai_response(self, prompt: str) -> str:
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
