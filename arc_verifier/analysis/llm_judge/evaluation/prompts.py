"""General evaluation prompt templates."""

from typing import Any


def build_evaluation_prompt(context: dict[str, Any]) -> str:
    """Build trust-focused evaluation prompt for LLM."""

    def format_agent_patterns(patterns: dict[str, list[str]]) -> str:
        """Format agent patterns for prompt inclusion."""
        formatted = []
        for category, items in patterns.items():
            if items:
                formatted.append(f"**{category.title()}:**")
                for item in items[:3]:  # Limit to 3 items per category
                    formatted.append(f"  - {item}")
        return "\n".join(formatted) if formatted else "No specific patterns detected"

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
{format_agent_patterns(context.get('agent_patterns', {}))}

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
