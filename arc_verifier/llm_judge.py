"""LLM-as-Judge Integration for Advanced Fort Scoring."""

import json
import re
import hashlib
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

import httpx
from rich.console import Console
from pydantic import BaseModel


class LLMProvider(str, Enum):
    """Supported LLM providers for agent evaluation."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic" 
    COHERE = "cohere"
    LOCAL = "local"


class AgentIntentClassification(BaseModel):
    """Agent intent classification result."""
    primary_strategy: str  # e.g., "arbitrage", "market_making", "yield_farming"
    risk_profile: str     # "conservative", "moderate", "aggressive"
    complexity_score: float  # 0.0 - 1.0
    confidence: float     # 0.0 - 1.0


class CodeQualityAnalysis(BaseModel):
    """Code quality evaluation result."""
    architecture_score: float      # 0.0 - 1.0
    error_handling_score: float    # 0.0 - 1.0
    security_practices_score: float # 0.0 - 1.0
    maintainability_score: float   # 0.0 - 1.0
    test_coverage_score: float     # 0.0 - 1.0
    overall_score: float           # 0.0 - 1.0
    key_findings: List[str]


class RiskAssessment(BaseModel):
    """Contextual risk assessment result."""
    volatility_sensitivity: float    # 0.0 - 1.0 (higher = more sensitive)
    liquidity_requirements: str      # "low", "medium", "high"
    systemic_risk_score: float      # 0.0 - 1.0 (higher = more systemic risk)
    market_impact_score: float      # 0.0 - 1.0 (higher = more market impact)
    operational_risk_score: float   # 0.0 - 1.0
    regulatory_risk_score: float    # 0.0 - 1.0


class LLMJudgeResult(BaseModel):
    """Complete LLM judge evaluation result."""
    intent_classification: AgentIntentClassification
    code_quality: CodeQualityAnalysis
    risk_assessment: RiskAssessment
    behavioral_flags: List[str]
    score_adjustments: Dict[str, float]  # category -> adjustment (-50 to +50)
    confidence_level: float              # Overall confidence in assessment
    reasoning: str                       # Detailed explanation
    timestamp: datetime


class LLMJudge:
    """LLM-as-Judge integration for advanced agent evaluation."""
    
    def __init__(self, 
                 primary_provider: LLMProvider = LLMProvider.ANTHROPIC,
                 fallback_provider: Optional[LLMProvider] = LLMProvider.OPENAI,
                 enable_ensemble: bool = True):
        self.console = Console()
        
        # Load from environment variables if available
        env_provider = os.getenv('LLM_PRIMARY_PROVIDER')
        self.primary_provider = LLMProvider(env_provider) if env_provider else primary_provider
        fallback_env = os.getenv('LLM_FALLBACK_PROVIDER')
        self.fallback_provider = LLMProvider(fallback_env) if fallback_env else fallback_provider
        ensemble_env = os.getenv('LLM_ENABLE_ENSEMBLE')
        self.enable_ensemble = ensemble_env.lower() == 'true' if ensemble_env else enable_ensemble
        
        # Initialize HTTP client for API calls
        timeout = float(os.getenv('LLM_TIMEOUT_SECONDS', '30'))
        self.client = httpx.Client(timeout=timeout)
        
        # Load prompts and templates
        self._load_evaluation_templates()
    
    def evaluate_agent(self, 
                      image_data: Dict[str, Any],
                      code_analysis: Optional[Dict[str, Any]] = None,
                      market_context: Optional[Dict[str, Any]] = None) -> LLMJudgeResult:
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
    
    def _prepare_evaluation_context(self,
                                  image_data: Dict[str, Any],
                                  code_analysis: Optional[Dict[str, Any]],
                                  market_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare comprehensive context for LLM evaluation."""
        
        context = {
            "image_info": {
                "tag": image_data.get("image_tag", "unknown"),
                "size": image_data.get("size", 0),
                "layers": len(image_data.get("layers", [])),
                "shade_agent_detected": image_data.get("shade_agent_detected", False),
                "vulnerabilities": self._summarize_vulnerabilities(
                    image_data.get("vulnerabilities", [])
                )
            },
            "deployment_context": {
                "timestamp": datetime.now().isoformat(),
                "evaluation_version": "2.0",
                "market_conditions": market_context or {"status": "unknown"}
            }
        }
        
        # Add code analysis if available
        if code_analysis:
            context["code_analysis"] = code_analysis
        
        # Extract agent patterns from image layers
        context["agent_patterns"] = self._extract_agent_patterns(
            image_data.get("layers", [])
        )
        
        return context
    
    def _run_evaluation(self, 
                       context: Dict[str, Any], 
                       provider: LLMProvider) -> LLMJudgeResult:
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
    
    def _run_ensemble_evaluation(self,
                                context: Dict[str, Any],
                                primary_result: LLMJudgeResult) -> LLMJudgeResult:
        """Run ensemble evaluation with multiple models."""
        try:
            # Get secondary evaluation
            secondary_result = self._run_evaluation(context, self.fallback_provider)
            
            # Combine results using weighted averaging
            ensemble_result = self._combine_evaluations(
                primary_result, secondary_result, 
                primary_weight=0.7, secondary_weight=0.3
            )
            
            self.console.print("[green]✓ Ensemble evaluation completed[/green]")
            return ensemble_result
            
        except Exception as e:
            self.console.print(f"[yellow]Ensemble evaluation failed: {e}, using primary result[/yellow]")
            return primary_result
    
    def _build_evaluation_prompt(self, context: Dict[str, Any]) -> str:
        """Build comprehensive evaluation prompt for LLM."""
        
        prompt = f"""
# Agent Evaluation Task

You are an expert in evaluating autonomous trading agents and DeFi protocols. Analyze the provided agent and return a comprehensive assessment.

## Agent Context
- **Image**: {context['image_info']['tag']}
- **Size**: {context['image_info']['size'] / 1024 / 1024:.1f} MB
- **Layers**: {context['image_info']['layers']}
- **Shade Agent Detected**: {context['image_info']['shade_agent_detected']}
- **Vulnerabilities**: {context['image_info']['vulnerabilities']}

## Agent Patterns Detected
{self._format_agent_patterns(context.get('agent_patterns', {}))}

## Evaluation Requirements

Provide a comprehensive analysis covering:

### 1. Intent Classification
- Primary strategy (arbitrage, market_making, yield_farming, etc.)
- Risk profile (conservative, moderate, aggressive)
- Complexity assessment (0.0-1.0)

### 2. Code Quality Analysis
- Architecture design quality (0.0-1.0)
- Error handling completeness (0.0-1.0)  
- Security best practices (0.0-1.0)
- Maintainability score (0.0-1.0)
- Key findings and recommendations

### 3. Risk Assessment
- Volatility sensitivity (0.0-1.0)
- Liquidity requirements (low/medium/high)
- Systemic risk potential (0.0-1.0)
- Market impact assessment (0.0-1.0)

### 4. Behavioral Analysis
- Identify any red flags or concerning patterns
- Assess strategy sophistication
- Evaluate risk management quality

### 5. Score Adjustments
Provide score adjustments (-50 to +50 points) for:
- innovative_strategy: Recognition of novel approaches
- risk_management: Quality of risk controls
- code_architecture: Technical implementation quality
- market_impact: Potential market effects

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
    "innovative_strategy": 0.0,
    "risk_management": 0.0,
    "code_architecture": 0.0,
    "market_impact": 0.0
  }},
  "confidence_level": 0.0,
  "reasoning": "Detailed explanation of your assessment..."
}}
```

Focus on providing actionable insights for protocol operators making deployment decisions.
"""
        return prompt.strip()
    
    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude API."""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            self.console.print("[yellow]ANTHROPIC_API_KEY not found, using mock response[/yellow]")
            return self._generate_mock_anthropic_response(prompt)
        
        try:
            response = self.client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": int(os.getenv('LLM_MAX_TOKENS', '2048')),
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=float(os.getenv('LLM_TIMEOUT_SECONDS', '30'))
            )
            response.raise_for_status()
            
            result = response.json()
            return result['content'][0]['text']
            
        except Exception as e:
            self.console.print(f"[red]Anthropic API call failed: {e}[/red]")
            self.console.print("[yellow]Falling back to mock response[/yellow]")
            return self._generate_mock_anthropic_response(prompt)
    
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API.""" 
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            self.console.print("[yellow]OPENAI_API_KEY not found, using mock response[/yellow]")
            return self._generate_mock_openai_response(prompt)
        
        try:
            response = self.client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                },
                json={
                    "model": "gpt-4.1",
                    "max_tokens": int(os.getenv('LLM_MAX_TOKENS', '2048')),
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1
                },
                timeout=float(os.getenv('LLM_TIMEOUT_SECONDS', '30'))
            )
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except Exception as e:
            self.console.print(f"[red]OpenAI API call failed: {e}[/red]")
            self.console.print("[yellow]Falling back to mock response[/yellow]")
            return self._generate_mock_openai_response(prompt)
    
    def _parse_llm_response(self, response: str, context: Dict[str, Any]) -> LLMJudgeResult:
        """Parse and validate LLM response."""
        try:
            # Extract JSON from response
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                response_data = json.loads(json_match.group(1))
            else:
                # Try to parse entire response as JSON
                response_data = json.loads(response)
            
            # Validate and construct result
            return LLMJudgeResult(
                intent_classification=AgentIntentClassification(**response_data["intent_classification"]),
                code_quality=CodeQualityAnalysis(**response_data["code_quality"]),
                risk_assessment=RiskAssessment(**response_data["risk_assessment"]),
                behavioral_flags=response_data.get("behavioral_flags", []),
                score_adjustments=response_data.get("score_adjustments", {}),
                confidence_level=response_data.get("confidence_level", 0.5),
                reasoning=response_data.get("reasoning", ""),
                timestamp=datetime.now()
            )
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            self.console.print(f"[red]Failed to parse LLM response: {e}[/red]")
            return self._generate_fallback_assessment(context)
    
    def _combine_evaluations(self,
                           primary: LLMJudgeResult,
                           secondary: LLMJudgeResult,
                           primary_weight: float = 0.7,
                           secondary_weight: float = 0.3) -> LLMJudgeResult:
        """Combine multiple LLM evaluations using weighted averaging."""
        
        # Weighted average for numerical scores
        def weighted_avg(p_val: float, s_val: float) -> float:
            return primary_weight * p_val + secondary_weight * s_val
        
        # Combine code quality scores
        combined_code_quality = CodeQualityAnalysis(
            architecture_score=weighted_avg(
                primary.code_quality.architecture_score,
                secondary.code_quality.architecture_score
            ),
            error_handling_score=weighted_avg(
                primary.code_quality.error_handling_score,
                secondary.code_quality.error_handling_score
            ),
            security_practices_score=weighted_avg(
                primary.code_quality.security_practices_score,
                secondary.code_quality.security_practices_score
            ),
            maintainability_score=weighted_avg(
                primary.code_quality.maintainability_score,
                secondary.code_quality.maintainability_score
            ),
            test_coverage_score=weighted_avg(
                primary.code_quality.test_coverage_score,
                secondary.code_quality.test_coverage_score
            ),
            overall_score=weighted_avg(
                primary.code_quality.overall_score,
                secondary.code_quality.overall_score
            ),
            key_findings=list(set(primary.code_quality.key_findings + secondary.code_quality.key_findings))
        )
        
        # Combine risk assessment
        combined_risk = RiskAssessment(
            volatility_sensitivity=weighted_avg(
                primary.risk_assessment.volatility_sensitivity,
                secondary.risk_assessment.volatility_sensitivity
            ),
            liquidity_requirements=primary.risk_assessment.liquidity_requirements,  # Use primary
            systemic_risk_score=weighted_avg(
                primary.risk_assessment.systemic_risk_score,
                secondary.risk_assessment.systemic_risk_score
            ),
            market_impact_score=weighted_avg(
                primary.risk_assessment.market_impact_score,
                secondary.risk_assessment.market_impact_score
            ),
            operational_risk_score=weighted_avg(
                primary.risk_assessment.operational_risk_score,
                secondary.risk_assessment.operational_risk_score
            ),
            regulatory_risk_score=weighted_avg(
                primary.risk_assessment.regulatory_risk_score,
                secondary.risk_assessment.regulatory_risk_score
            )
        )
        
        # Combine score adjustments
        combined_adjustments = {}
        for key in set(primary.score_adjustments.keys()).union(secondary.score_adjustments.keys()):
            p_val = primary.score_adjustments.get(key, 0)
            s_val = secondary.score_adjustments.get(key, 0)
            combined_adjustments[key] = weighted_avg(p_val, s_val)
        
        return LLMJudgeResult(
            intent_classification=primary.intent_classification,  # Use primary
            code_quality=combined_code_quality,
            risk_assessment=combined_risk,
            behavioral_flags=list(set(primary.behavioral_flags + secondary.behavioral_flags)),
            score_adjustments=combined_adjustments,
            confidence_level=weighted_avg(primary.confidence_level, secondary.confidence_level),
            reasoning=f"Ensemble evaluation:\n\nPrimary: {primary.reasoning}\n\nSecondary: {secondary.reasoning}",
            timestamp=datetime.now()
        )
    
    # Helper methods for processing and mock responses
    
    def _summarize_vulnerabilities(self, vulnerabilities: List[Dict]) -> Dict[str, int]:
        """Summarize vulnerability counts by severity."""
        counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "UNKNOWN")
            if severity in counts:
                counts[severity] += 1
        return counts
    
    def _extract_agent_patterns(self, layers: List[Dict]) -> Dict[str, List[str]]:
        """Extract agent-related patterns from Docker layers."""
        patterns = {
            "dependencies": [],
            "configurations": [],
            "commands": []
        }
        
        for layer in layers:
            command = layer.get("command", "").lower()
            
            # Look for agent-related dependencies
            if any(dep in command for dep in ["npm install", "pip install", "yarn add"]):
                patterns["dependencies"].append(command[:100])
            
            # Look for configuration patterns
            if any(cfg in command for cfg in ["config", "env", "secret"]):
                patterns["configurations"].append(command[:100])
            
            # Look for execution commands
            if any(cmd in command for cmd in ["run", "start", "exec"]):
                patterns["commands"].append(command[:100])
        
        return patterns
    
    def _format_agent_patterns(self, patterns: Dict[str, List[str]]) -> str:
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
            "risk_assessment": "Evaluate market and operational risks"
        }
    
    def _generate_mock_anthropic_response(self, prompt: str) -> str:
        """Generate mock Anthropic response for development/testing."""
        return '''```json
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
    "innovative_strategy": 5.0,
    "risk_management": 8.0,
    "code_architecture": 6.0,
    "market_impact": -2.0
  },
  "confidence_level": 0.8,
  "reasoning": "This appears to be a well-designed arbitrage agent with solid risk management practices. The code architecture shows good separation of concerns and proper error handling. Risk profile is moderate with appropriate safeguards for volatile market conditions."
}
```'''
    
    def _generate_mock_openai_response(self, prompt: str) -> str:
        """Generate mock OpenAI response for development/testing."""
        return '''```json
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
    "innovative_strategy": 3.0,
    "risk_management": 7.0,
    "code_architecture": 8.0,
    "market_impact": -1.0
  },
  "confidence_level": 0.78,
  "reasoning": "Solid arbitrage implementation with good architectural patterns. Strong security focus but could benefit from enhanced testing. Risk management appears well-thought-out for the intended strategy."
}
```'''
    
    def _generate_fallback_assessment(self, context: Dict[str, Any]) -> LLMJudgeResult:
        """Generate conservative fallback assessment when LLM evaluation fails."""
        return LLMJudgeResult(
            intent_classification=AgentIntentClassification(
                primary_strategy="unknown",
                risk_profile="conservative",
                complexity_score=0.5,
                confidence=0.3
            ),
            code_quality=CodeQualityAnalysis(
                architecture_score=0.5,
                error_handling_score=0.5,
                security_practices_score=0.5,
                maintainability_score=0.5,
                test_coverage_score=0.5,
                overall_score=0.5,
                key_findings=["LLM evaluation unavailable - manual review recommended"]
            ),
            risk_assessment=RiskAssessment(
                volatility_sensitivity=0.7,  # Conservative assumption
                liquidity_requirements="high",
                systemic_risk_score=0.8,     # Conservative assumption
                market_impact_score=0.6,
                operational_risk_score=0.7,
                regulatory_risk_score=0.8
            ),
            behavioral_flags=["LLM evaluation failed - requires manual review"],
            score_adjustments={},  # No adjustments when evaluation fails
            confidence_level=0.1,  # Very low confidence
            reasoning="LLM evaluation failed. Conservative assessment applied. Manual review strongly recommended.",
            timestamp=datetime.now()
        )