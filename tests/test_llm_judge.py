"""Tests for LLM Judge functionality."""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch

from arc_verifier.llm_judge import (
    LLMJudge, 
    LLMJudgeResult, 
    AgentIntentClassification,
    CodeQualityAnalysis,
    RiskAssessment,
    LLMProvider
)


class TestLLMJudge:
    """Test suite for LLM Judge functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.judge = LLMJudge(primary_provider=LLMProvider.ANTHROPIC, enable_ensemble=False)
        
        self.sample_image_data = {
            "image_tag": "shade/arbitrage-agent:latest",
            "size": 128 * 1024 * 1024,  # 128MB
            "layers": [
                {"command": "pip install web3 numpy", "size": 1024},
                {"command": "copy requirements.txt", "size": 512}
            ],
            "shade_agent_detected": True,
            "vulnerabilities": [
                {"severity": "MEDIUM", "cveId": "CVE-2023-1234", "package": "openssl"},
                {"severity": "LOW", "cveId": "CVE-2023-5678", "package": "zlib"}
            ],
            "timestamp": datetime.now()
        }
        
        self.sample_market_context = {
            "tier": "high",
            "timestamp": datetime.now().isoformat()
        }
    
    def test_llm_judge_initialization(self):
        """Test LLM Judge initialization."""
        judge = LLMJudge()
        assert judge.primary_provider == LLMProvider.ANTHROPIC
        assert judge.fallback_provider == LLMProvider.OPENAI
        assert judge.enable_ensemble is True
        
        # Test custom initialization
        judge_custom = LLMJudge(
            primary_provider=LLMProvider.OPENAI,
            fallback_provider=None,
            enable_ensemble=False
        )
        assert judge_custom.primary_provider == LLMProvider.OPENAI
        assert judge_custom.fallback_provider is None
        assert judge_custom.enable_ensemble is False
    
    def test_prepare_evaluation_context(self):
        """Test evaluation context preparation."""
        context = self.judge._prepare_evaluation_context(
            self.sample_image_data, 
            None, 
            self.sample_market_context
        )
        
        assert "image_info" in context
        assert context["image_info"]["tag"] == "shade/arbitrage-agent:latest"
        assert context["image_info"]["shade_agent_detected"] is True
        assert context["image_info"]["vulnerabilities"]["MEDIUM"] == 1
        assert context["image_info"]["vulnerabilities"]["LOW"] == 1
        assert context["image_info"]["vulnerabilities"]["HIGH"] == 0
        assert context["image_info"]["vulnerabilities"]["CRITICAL"] == 0
        
        assert "deployment_context" in context
        assert context["deployment_context"]["market_conditions"]["tier"] == "high"
        
        assert "agent_patterns" in context
        assert "dependencies" in context["agent_patterns"]
    
    def test_extract_agent_patterns(self):
        """Test agent pattern extraction from layers."""
        layers = [
            {"command": "pip install web3 pandas numpy"},
            {"command": "npm install @shade/trading-bot"},
            {"command": "export SHADE_API_KEY=secret"},
            {"command": "run trading_agent.py"},
            {"command": "copy config.yaml /app/"}
        ]
        
        patterns = self.judge._extract_agent_patterns(layers)
        
        assert len(patterns["dependencies"]) == 2  # pip and npm commands
        assert len(patterns["configurations"]) == 2  # export and config commands
        assert len(patterns["commands"]) == 1       # run command
        
        # Check specific patterns
        assert any("pip install" in dep for dep in patterns["dependencies"])
        assert any("npm install" in dep for dep in patterns["dependencies"])
        assert any("export" in cfg for cfg in patterns["configurations"])
        assert any("run" in cmd for cmd in patterns["commands"])
    
    def test_summarize_vulnerabilities(self):
        """Test vulnerability summarization."""
        vulnerabilities = [
            {"severity": "CRITICAL", "cveId": "CVE-2023-0001"},
            {"severity": "CRITICAL", "cveId": "CVE-2023-0002"},
            {"severity": "HIGH", "cveId": "CVE-2023-0003"},
            {"severity": "MEDIUM", "cveId": "CVE-2023-0004"},
            {"severity": "LOW", "cveId": "CVE-2023-0005"},
            {"severity": "LOW", "cveId": "CVE-2023-0006"}
        ]
        
        summary = self.judge._summarize_vulnerabilities(vulnerabilities)
        
        assert summary["CRITICAL"] == 2
        assert summary["HIGH"] == 1
        assert summary["MEDIUM"] == 1
        assert summary["LOW"] == 2
    
    def test_build_evaluation_prompt(self):
        """Test evaluation prompt building."""
        context = self.judge._prepare_evaluation_context(
            self.sample_image_data, None, self.sample_market_context
        )
        
        prompt = self.judge._build_evaluation_prompt(context)
        
        # Check that key elements are included
        assert "shade/arbitrage-agent:latest" in prompt
        assert "128.0 MB" in prompt  # Size formatting
        assert "**Shade Agent Detected**: True" in prompt
        assert "behavioral_flags" in prompt
        assert "score_adjustments" in prompt
        assert "intent_classification" in prompt
    
    def test_parse_llm_response_valid_json(self):
        """Test parsing valid LLM response."""
        mock_response = '''```json
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
    "key_findings": ["Well-structured trading logic", "Good security practices"]
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
  "reasoning": "This appears to be a well-designed arbitrage agent with solid risk management practices."
}
```'''
        
        context = {"image_info": {"tag": "test"}}
        result = self.judge._parse_llm_response(mock_response, context)
        
        assert isinstance(result, LLMJudgeResult)
        assert result.intent_classification.primary_strategy == "arbitrage"
        assert result.intent_classification.risk_profile == "moderate"
        assert result.code_quality.overall_score == 0.76
        assert result.risk_assessment.liquidity_requirements == "medium"
        assert len(result.behavioral_flags) == 1
        assert result.score_adjustments["innovative_strategy"] == 5.0
        assert result.confidence_level == 0.8
    
    def test_parse_llm_response_invalid_json(self):
        """Test parsing invalid LLM response falls back gracefully."""
        invalid_response = "This is not valid JSON"
        context = self.sample_image_data
        
        result = self.judge._parse_llm_response(invalid_response, context)
        
        # Should return fallback assessment
        assert isinstance(result, LLMJudgeResult)
        assert result.intent_classification.primary_strategy == "unknown"
        assert result.intent_classification.risk_profile == "conservative"
        assert result.confidence_level == 0.1
        assert "LLM evaluation failed" in result.reasoning
    
    def test_generate_fallback_assessment(self):
        """Test fallback assessment generation."""
        context = {"image_info": {"tag": "test-agent"}}
        result = self.judge._generate_fallback_assessment(context)
        
        assert isinstance(result, LLMJudgeResult)
        assert result.intent_classification.primary_strategy == "unknown"
        assert result.intent_classification.risk_profile == "conservative"
        assert result.code_quality.overall_score == 0.5
        assert result.risk_assessment.systemic_risk_score == 0.8  # Conservative
        assert result.confidence_level == 0.1
        assert "manual review" in result.reasoning.lower()
    
    def test_combine_evaluations(self):
        """Test ensemble evaluation combination."""
        # Create two mock results
        primary = LLMJudgeResult(
            intent_classification=AgentIntentClassification(
                primary_strategy="arbitrage",
                risk_profile="moderate",
                complexity_score=0.7,
                confidence=0.8
            ),
            code_quality=CodeQualityAnalysis(
                architecture_score=0.8,
                error_handling_score=0.7,
                security_practices_score=0.9,
                maintainability_score=0.75,
                test_coverage_score=0.6,
                overall_score=0.76,
                key_findings=["Primary finding"]
            ),
            risk_assessment=RiskAssessment(
                volatility_sensitivity=0.6,
                liquidity_requirements="medium",
                systemic_risk_score=0.3,
                market_impact_score=0.4,
                operational_risk_score=0.25,
                regulatory_risk_score=0.2
            ),
            behavioral_flags=["Primary flag"],
            score_adjustments={"innovation": 5.0, "risk": 3.0},
            confidence_level=0.8,
            reasoning="Primary reasoning",
            timestamp=datetime.now()
        )
        
        secondary = LLMJudgeResult(
            intent_classification=AgentIntentClassification(
                primary_strategy="market_making",
                risk_profile="aggressive", 
                complexity_score=0.9,
                confidence=0.7
            ),
            code_quality=CodeQualityAnalysis(
                architecture_score=0.6,
                error_handling_score=0.8,
                security_practices_score=0.7,
                maintainability_score=0.65,
                test_coverage_score=0.8,
                overall_score=0.72,
                key_findings=["Secondary finding"]
            ),
            risk_assessment=RiskAssessment(
                volatility_sensitivity=0.8,
                liquidity_requirements="high",
                systemic_risk_score=0.5,
                market_impact_score=0.6,
                operational_risk_score=0.35,
                regulatory_risk_score=0.4
            ),
            behavioral_flags=["Secondary flag"],
            score_adjustments={"innovation": 3.0, "risk": 7.0},
            confidence_level=0.7,
            reasoning="Secondary reasoning",
            timestamp=datetime.now()
        )
        
        combined = self.judge._combine_evaluations(primary, secondary, 0.7, 0.3)
        
        # Test weighted averaging
        assert combined.code_quality.architecture_score == pytest.approx(0.74, rel=1e-2)  # 0.7*0.8 + 0.3*0.6
        assert combined.risk_assessment.volatility_sensitivity == pytest.approx(0.66, rel=1e-2)  # 0.7*0.6 + 0.3*0.8
        assert combined.score_adjustments["innovation"] == pytest.approx(4.4, rel=1e-2)  # 0.7*5 + 0.3*3
        assert combined.confidence_level == pytest.approx(0.77, rel=1e-2)  # 0.7*0.8 + 0.3*0.7
        
        # Test set combinations
        assert len(combined.behavioral_flags) == 2
        assert "Primary flag" in combined.behavioral_flags
        assert "Secondary flag" in combined.behavioral_flags
        
        # Test text combinations
        assert "Primary finding" in combined.code_quality.key_findings
        assert "Secondary finding" in combined.code_quality.key_findings
        assert "Ensemble evaluation" in combined.reasoning
    
    @patch('arc_verifier.llm_judge.LLMJudge._call_anthropic')
    def test_evaluate_agent_success(self, mock_anthropic):
        """Test successful agent evaluation."""
        # Mock the Anthropic response
        mock_anthropic.return_value = self.judge._generate_mock_anthropic_response("")
        
        result = self.judge.evaluate_agent(
            self.sample_image_data,
            market_context=self.sample_market_context
        )
        
        assert isinstance(result, LLMJudgeResult)
        assert result.intent_classification.primary_strategy == "arbitrage"
        assert result.confidence_level > 0.5
        mock_anthropic.assert_called_once()
    
    @patch('arc_verifier.llm_judge.LLMJudge._call_anthropic')
    def test_evaluate_agent_failure_fallback(self, mock_anthropic):
        """Test agent evaluation with API failure falls back gracefully."""
        # Mock API failure
        mock_anthropic.side_effect = Exception("API Error")
        
        result = self.judge.evaluate_agent(self.sample_image_data)
        
        # Should return fallback assessment
        assert isinstance(result, LLMJudgeResult)
        assert result.intent_classification.primary_strategy == "unknown"
        assert result.confidence_level == 0.1
        assert "LLM evaluation failed" in result.reasoning
    
    def test_format_agent_patterns(self):
        """Test agent pattern formatting for prompts."""
        patterns = {
            "dependencies": ["pip install web3", "npm install trading-lib"],
            "configurations": ["export API_KEY=secret"],
            "commands": ["run agent.py", "start monitoring"]
        }
        
        formatted = self.judge._format_agent_patterns(patterns)
        
        assert "**Dependencies:**" in formatted
        assert "pip install web3" in formatted
        assert "npm install trading-lib" in formatted
        assert "**Configurations:**" in formatted
        assert "export API_KEY=secret" in formatted
        assert "**Commands:**" in formatted
        assert "run agent.py" in formatted
    
    def test_format_agent_patterns_empty(self):
        """Test agent pattern formatting with no patterns."""
        patterns = {"dependencies": [], "configurations": [], "commands": []}
        
        formatted = self.judge._format_agent_patterns(patterns)
        
        assert formatted == "No specific patterns detected"


class TestLLMJudgeModels:
    """Test LLM Judge data models."""
    
    def test_agent_intent_classification_validation(self):
        """Test AgentIntentClassification model validation."""
        # Valid classification
        classification = AgentIntentClassification(
            primary_strategy="arbitrage",
            risk_profile="moderate",
            complexity_score=0.7,
            confidence=0.85
        )
        
        assert classification.primary_strategy == "arbitrage"
        assert classification.risk_profile == "moderate"
        assert classification.complexity_score == 0.7
        assert classification.confidence == 0.85
    
    def test_code_quality_analysis_validation(self):
        """Test CodeQualityAnalysis model validation."""
        analysis = CodeQualityAnalysis(
            architecture_score=0.8,
            error_handling_score=0.7,
            security_practices_score=0.9,
            maintainability_score=0.75,
            test_coverage_score=0.6,
            overall_score=0.76,
            key_findings=["Finding 1", "Finding 2"]
        )
        
        assert analysis.overall_score == 0.76
        assert len(analysis.key_findings) == 2
    
    def test_risk_assessment_validation(self):
        """Test RiskAssessment model validation."""
        assessment = RiskAssessment(
            volatility_sensitivity=0.6,
            liquidity_requirements="medium",
            systemic_risk_score=0.3,
            market_impact_score=0.4,
            operational_risk_score=0.25,
            regulatory_risk_score=0.2
        )
        
        assert assessment.volatility_sensitivity == 0.6
        assert assessment.liquidity_requirements == "medium"
        assert assessment.systemic_risk_score == 0.3
    
    def test_llm_judge_result_serialization(self):
        """Test LLMJudgeResult serialization."""
        result = LLMJudgeResult(
            intent_classification=AgentIntentClassification(
                primary_strategy="arbitrage",
                risk_profile="moderate",
                complexity_score=0.7,
                confidence=0.85
            ),
            code_quality=CodeQualityAnalysis(
                architecture_score=0.8,
                error_handling_score=0.7,
                security_practices_score=0.9,
                maintainability_score=0.75,
                test_coverage_score=0.6,
                overall_score=0.76,
                key_findings=["Test finding"]
            ),
            risk_assessment=RiskAssessment(
                volatility_sensitivity=0.6,
                liquidity_requirements="medium",
                systemic_risk_score=0.3,
                market_impact_score=0.4,
                operational_risk_score=0.25,
                regulatory_risk_score=0.2
            ),
            behavioral_flags=["Test flag"],
            score_adjustments={"test": 5.0},
            confidence_level=0.8,
            reasoning="Test reasoning",
            timestamp=datetime.now()
        )
        
        # Test JSON serialization
        json_data = result.model_dump(mode='json')
        assert json_data['intent_classification']['primary_strategy'] == "arbitrage"
        assert json_data['confidence_level'] == 0.8
        assert json_data['score_adjustments']['test'] == 5.0