"""Tests for the new LLM Judge architecture."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from arc_verifier.analysis.llm_judge import (
    LLMJudge, 
    LLMProvider,
    AgentIntentClassification,
    CodeQualityAnalysis,
    RiskAssessment,
    KeySecurityResult,
    TransactionControlResult,
    DeceptionDetectionResult,
    CapitalRiskResult,
    TrustFocusedResult,
    LLMJudgeResult
)


class TestLLMJudgeNewArchitecture:
    """Test suite for the new LLM Judge architecture."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.judge = LLMJudge(
            primary_provider=LLMProvider.ANTHROPIC, 
            enable_ensemble=False
        )
        
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
        """Test LLM Judge initialization with new architecture."""
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
    
    def test_llm_judge_has_required_components(self):
        """Test that LLM Judge has all required analyzers."""
        assert hasattr(self.judge, 'key_security_analyzer')
        assert hasattr(self.judge, 'transaction_control_analyzer')
        assert hasattr(self.judge, 'deception_detector')
        assert hasattr(self.judge, 'capital_risk_analyzer')
        assert hasattr(self.judge, 'trust_score_calculator')
        assert hasattr(self.judge, 'ensemble_evaluator')
    
    @patch('arc_verifier.analysis.llm_judge.core.prepare_evaluation_context')
    def test_evaluate_agent_security_success(self, mock_prepare_context):
        """Test successful trust-focused security evaluation."""
        # Mock evaluation context
        mock_context = {"image_info": {"tag": "test:latest"}}
        mock_prepare_context.return_value = mock_context
        
        # Mock analyzer results
        with patch.object(self.judge.key_security_analyzer, 'analyze') as mock_key_sec, \
             patch.object(self.judge.transaction_control_analyzer, 'analyze') as mock_tx_ctrl, \
             patch.object(self.judge.deception_detector, 'analyze') as mock_deception, \
             patch.object(self.judge.capital_risk_analyzer, 'analyze') as mock_capital, \
             patch.object(self.judge.trust_score_calculator, 'calculate_trust_assessment') as mock_trust:
            
            # Configure mock returns
            mock_key_sec.return_value = KeySecurityResult(
                has_plaintext_keys=False,
                key_generation_secure=True,
                key_storage_encrypted=True,
                key_rotation_implemented=True,
                key_exposure_risk="low",
                security_concerns=[],
                code_references=[]
            )
            
            mock_tx_ctrl.return_value = TransactionControlResult(
                has_spending_limits=True,
                has_approval_mechanisms=True,
                emergency_stop_present=True,
                cross_chain_controls=True,
                transaction_monitoring=True,
                control_strength="strong",
                control_gaps=[]
            )
            
            mock_deception.return_value = DeceptionDetectionResult(
                backdoor_detected=False,
                time_bomb_detected=False,
                obfuscated_code_found=False,
                data_exfiltration_risk=False,
                environment_specific_behavior=False,
                deception_indicators=[],
                risk_level="low"
            )
            
            mock_capital.return_value = CapitalRiskResult(
                max_loss_bounded=True,
                position_size_controls=True,
                stop_loss_implemented=True,
                leverage_controls=True,
                flash_loan_usage=False,
                risk_controls_adequate=True,
                estimated_max_loss="bounded"
            )
            
            mock_trust_result = TrustFocusedResult(
                can_trust_with_capital=True,
                trust_score=0.85,
                key_security=mock_key_sec.return_value,
                transaction_controls=mock_tx_ctrl.return_value,
                deception_analysis=mock_deception.return_value,
                capital_risk=mock_capital.return_value,
                critical_vulnerabilities=[],
                security_recommendations=["Continue monitoring"],
                confidence_level=0.9,
                reasoning="Strong security controls with no major risks detected"
            )
            mock_trust.return_value = mock_trust_result
            
            # Run the evaluation
            result = self.judge.evaluate_agent_security(
                self.sample_image_data,
                market_context=self.sample_market_context
            )
            
            # Verify result
            assert isinstance(result, TrustFocusedResult)
            assert result.trust_score == 0.85
            assert result.can_trust_with_capital == True
            assert result.confidence_level == 0.9
            
            # Verify all analyzers were called
            mock_key_sec.assert_called_once()
            mock_tx_ctrl.assert_called_once()
            mock_deception.assert_called_once()
            mock_capital.assert_called_once()
            mock_trust.assert_called_once()
    
    @patch('arc_verifier.analysis.llm_judge.core.prepare_evaluation_context')
    def test_evaluate_agent_security_failure_fallback(self, mock_prepare_context):
        """Test security evaluation with failure falls back gracefully."""
        # Mock context preparation to raise exception
        mock_prepare_context.side_effect = Exception("Context preparation failed")
        
        # Mock fallback trust assessment
        with patch.object(self.judge.trust_score_calculator, 'generate_fallback_trust_assessment') as mock_fallback:
            fallback_result = TrustFocusedResult(
                can_trust_with_capital=False,
                trust_score=0.2,
                key_security=KeySecurityResult(
                    has_plaintext_keys=True,
                    key_generation_secure=False,
                    key_storage_encrypted=False,
                    key_rotation_implemented=False,
                    key_exposure_risk="critical",
                    security_concerns=["Unable to evaluate - system error"],
                    code_references=[]
                ),
                transaction_controls=TransactionControlResult(
                    has_spending_limits=False,
                    has_approval_mechanisms=False,
                    emergency_stop_present=False,
                    cross_chain_controls=False,
                    transaction_monitoring=False,
                    control_strength="weak",
                    control_gaps=["Unable to evaluate"]
                ),
                deception_analysis=DeceptionDetectionResult(
                    backdoor_detected=False,
                    time_bomb_detected=False,
                    obfuscated_code_found=False,
                    data_exfiltration_risk=True,
                    environment_specific_behavior=False,
                    deception_indicators=["Evaluation failed - assume risk"],
                    risk_level="critical"
                ),
                capital_risk=CapitalRiskResult(
                    max_loss_bounded=False,
                    position_size_controls=False,
                    stop_loss_implemented=False,
                    leverage_controls=False,
                    flash_loan_usage=True,
                    risk_controls_adequate=False,
                    estimated_max_loss="unlimited"
                ),
                critical_vulnerabilities=["System evaluation failure"],
                security_recommendations=["Manual security review required"],
                confidence_level=0.1,
                reasoning="Evaluation failed - conservative fallback assessment"
            )
            mock_fallback.return_value = fallback_result
            
            result = self.judge.evaluate_agent_security(self.sample_image_data)
            
            # Should return conservative fallback assessment
            assert isinstance(result, TrustFocusedResult)
            assert result.trust_score == 0.2
            assert result.can_trust_with_capital == False
            assert result.confidence_level == 0.1
            assert "Evaluation failed" in result.reasoning
            
            mock_fallback.assert_called_once()
    
    @patch('arc_verifier.analysis.llm_judge.core.prepare_evaluation_context')
    def test_evaluate_agent_comprehensive(self, mock_prepare_context):
        """Test comprehensive agent evaluation (non-security focused)."""
        # Mock evaluation context
        mock_context = {"image_info": {"tag": "test:latest"}}
        mock_prepare_context.return_value = mock_context
        
        # Mock ensemble evaluator
        with patch.object(self.judge.ensemble_evaluator, 'run_evaluation') as mock_evaluation:
            mock_result = LLMJudgeResult(
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
                    key_findings=["Well-structured codebase", "Good error handling"]
                ),
                risk_assessment=RiskAssessment(
                    volatility_sensitivity=0.6,
                    liquidity_requirements="medium",
                    systemic_risk_score=0.3,
                    market_impact_score=0.4,
                    operational_risk_score=0.25,
                    regulatory_risk_score=0.2
                ),
                behavioral_flags=["Standard arbitrage patterns"],
                score_adjustments={"innovation": 5.0, "risk_management": 8.0},
                confidence_level=0.8,
                reasoning="Well-designed arbitrage agent with solid risk management",
                timestamp=datetime.now()
            )
            mock_evaluation.return_value = mock_result
            
            result = self.judge.evaluate_agent(
                self.sample_image_data,
                market_context=self.sample_market_context
            )
            
            assert isinstance(result, LLMJudgeResult)
            assert result.intent_classification.primary_strategy == "arbitrage"
            assert result.confidence_level == 0.8
            assert result.code_quality.overall_score == 0.76
            
            mock_evaluation.assert_called_once()


class TestLLMJudgeModels:
    """Test LLM Judge data models."""
    
    def test_agent_intent_classification_validation(self):
        """Test AgentIntentClassification model."""
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
    
    def test_key_security_result_validation(self):
        """Test KeySecurityResult model."""
        result = KeySecurityResult(
            has_plaintext_keys=False,
            key_generation_secure=True,
            key_storage_encrypted=True,
            key_rotation_implemented=True,
            key_exposure_risk="low",
            security_concerns=[],
            code_references=[]
        )
        
        assert result.has_plaintext_keys is False
        assert result.key_exposure_risk == "low"
        assert len(result.security_concerns) == 0
    
    def test_trust_focused_result_validation(self):
        """Test TrustFocusedResult model."""
        key_security = KeySecurityResult(
            has_plaintext_keys=False,
            key_generation_secure=True,
            key_storage_encrypted=True,
            key_rotation_implemented=True,
            key_exposure_risk="low",
            security_concerns=[],
            code_references=[]
        )
        
        transaction_controls = TransactionControlResult(
            has_spending_limits=True,
            has_approval_mechanisms=True,
            emergency_stop_present=True,
            cross_chain_controls=True,
            transaction_monitoring=True,
            control_strength="strong",
            control_gaps=[]
        )
        
        deception_analysis = DeceptionDetectionResult(
            backdoor_detected=False,
            time_bomb_detected=False,
            obfuscated_code_found=False,
            data_exfiltration_risk=False,
            environment_specific_behavior=False,
            deception_indicators=[],
            risk_level="low"
        )
        
        capital_risk = CapitalRiskResult(
            max_loss_bounded=True,
            position_size_controls=True,
            stop_loss_implemented=True,
            leverage_controls=True,
            flash_loan_usage=False,
            risk_controls_adequate=True,
            estimated_max_loss="bounded"
        )
        
        result = TrustFocusedResult(
            can_trust_with_capital=True,
            trust_score=0.85,
            key_security=key_security,
            transaction_controls=transaction_controls,
            deception_analysis=deception_analysis,
            capital_risk=capital_risk,
            critical_vulnerabilities=[],
            security_recommendations=["Continue monitoring"],
            confidence_level=0.9,
            reasoning="Strong security controls"
        )
        
        assert result.trust_score == 0.85
        assert result.can_trust_with_capital == True
        assert result.confidence_level == 0.9
        assert isinstance(result.key_security, KeySecurityResult)
        assert result.reasoning == "Strong security controls"
    
    def test_llm_judge_result_serialization(self):
        """Test LLMJudgeResult JSON serialization."""
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