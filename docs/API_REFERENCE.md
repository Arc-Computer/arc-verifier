# Arc-Verifier API Reference

Arc-Verifier provides both command-line and programmatic interfaces for enterprise integration. This reference covers all public APIs for building automated verification pipelines.

## Table of Contents

- [Quick Start](#quick-start)
- [Core Classes](#core-classes)
- [Verification Pipeline](#verification-pipeline)
- [Individual Components](#individual-components)
- [Data Models](#data-models)
- [Configuration](#configuration)
- [Enterprise Integration](#enterprise-integration)
- [Error Handling](#error-handling)

## Quick Start

### Basic Usage

```python
from arc_verifier import VerificationPipeline

# Complete verification with enterprise settings
pipeline = VerificationPipeline()
result = pipeline.verify(
    agent_image="trading-agent:v1.0",
    tier="high",
    enable_llm=True,
    enable_tee=True,
    output_format="json"
)

print(f"Fort Score: {result.fort_score}/180")
print(f"Trust Level: {result.trust_level}")
print(f"Deployment Ready: {result.deployment_ready}")
```

### Enterprise Batch Processing

```python
from arc_verifier import ParallelVerifier

# Verify multiple agents in parallel
verifier = ParallelVerifier(max_workers=4)
agents = [
    "arbitrage-bot:v2.1",
    "market-maker:v1.5", 
    "yield-optimizer:v3.0"
]

results = verifier.verify_batch(
    agents,
    tier="high",
    enable_llm=True,
    timeout_minutes=30
)

for agent, result in results.items():
    if result.fort_score >= 120:  # Enterprise threshold
        print(f"✅ {agent}: Approved (Score: {result.fort_score})")
    else:
        print(f"❌ {agent}: Rejected (Issues: {len(result.critical_issues)})")
```

## Core Classes

### VerificationPipeline

Main orchestrator for complete agent verification.

```python
class VerificationPipeline:
    def __init__(self, config: Optional[VerificationConfig] = None):
        """Initialize verification pipeline.
        
        Args:
            config: Optional configuration override
        """
    
    def verify(
        self,
        agent_image: str,
        tier: str = "medium",
        enable_llm: bool = True,
        enable_tee: bool = False,
        enable_simulation: bool = False,
        output_format: str = "terminal",
        audit_mode: bool = True
    ) -> VerificationResult:
        """Complete agent verification.
        
        Args:
            agent_image: Docker image to verify
            tier: Security tier ("low", "medium", "high")
            enable_llm: Enable AI behavioral analysis
            enable_tee: Enable TEE attestation validation
            enable_simulation: Enable behavioral simulation
            output_format: "terminal", "json", or "detailed"
            audit_mode: Enable comprehensive audit logging
            
        Returns:
            VerificationResult with all analysis results
            
        Raises:
            VerificationError: If verification fails
            SecurityValidationError: If security checks fail
            ConfigurationError: If configuration is invalid
        """
```

### LLMJudge

AI-powered behavioral and security analysis.

```python
class LLMJudge:
    def __init__(
        self,
        primary_provider: str = "anthropic",
        fallback_provider: Optional[str] = None,
        enable_ensemble: bool = False
    ):
        """Initialize LLM Judge.
        
        Args:
            primary_provider: "anthropic", "openai", or "local"
            fallback_provider: Backup provider if primary fails
            enable_ensemble: Use multiple providers for verification
        """
    
    def analyze_agent_security(
        self,
        agent_image: str,
        code_context: Optional[str] = None
    ) -> SecurityAnalysisResult:
        """Analyze agent for security vulnerabilities.
        
        Performs comprehensive security analysis including:
        - Private key usage patterns
        - Transaction control mechanisms  
        - Deception pattern detection
        - Behavioral anomaly identification
        
        Args:
            agent_image: Docker image to analyze
            code_context: Optional source code for analysis
            
        Returns:
            SecurityAnalysisResult with trust assessment
        """
    
    def evaluate_trust_level(
        self,
        security_result: SecurityAnalysisResult,
        performance_data: Optional[Dict] = None
    ) -> TrustEvaluation:
        """Evaluate overall trust level.
        
        Args:
            security_result: Results from security analysis
            performance_data: Optional performance metrics
            
        Returns:
            TrustEvaluation with recommendation
        """
```

### RealBacktester

Strategy verification using real market data.

```python
class RealBacktester:
    def __init__(self):
        """Initialize backtester with real market data provider."""
    
    def run(
        self,
        agent_image: str,
        start_date: str = "2024-05-01",
        end_date: str = "2024-05-31", 
        strategy_type: str = "arbitrage",
        use_cached_regime: Optional[str] = None
    ) -> BacktestResult:
        """Run backtest with real market data.
        
        Args:
            agent_image: Docker image to test
            start_date: ISO format date string
            end_date: ISO format date string
            strategy_type: "arbitrage", "momentum", "market_making"
            use_cached_regime: Use predefined market regime
            
        Returns:
            BacktestResult with performance metrics
        """
    
    def calculate_investment_rating(
        self,
        result: BacktestResult
    ) -> InvestmentRating:
        """Calculate enterprise investment rating.
        
        Args:
            result: Backtest results
            
        Returns:
            InvestmentRating (A-F scale with recommendations)
        """
```

### DockerScanner

Container security and vulnerability scanning.

```python
class DockerScanner:
    def __init__(self, auto_install_trivy: bool = True):
        """Initialize Docker scanner.
        
        Args:
            auto_install_trivy: Automatically install Trivy if missing
        """
    
    def scan_image(
        self,
        image: str,
        severity_threshold: str = "medium"
    ) -> ScanResult:
        """Scan Docker image for vulnerabilities.
        
        Args:
            image: Docker image to scan
            severity_threshold: "low", "medium", "high", "critical"
            
        Returns:
            ScanResult with vulnerability findings
        """
    
    def detect_shade_agent(self, image: str) -> bool:
        """Detect if image contains Shade agent components."""
```

### TEEValidator

Trusted Execution Environment validation.

```python
class TEEValidator:
    def __init__(self):
        """Initialize TEE validator with multiple platform support."""
    
    def validate_attestation(
        self,
        agent_image: str,
        platform: str = "auto"
    ) -> TEEValidationResult:
        """Validate TEE attestation.
        
        Args:
            agent_image: Docker image to validate
            platform: "sgx", "sev", "phala", or "auto"
            
        Returns:
            TEEValidationResult with attestation status
        """
    
    def verify_enclave_security(
        self,
        attestation_data: bytes
    ) -> EnclaveSecurityResult:
        """Verify enclave security properties."""
```

## Data Models

### VerificationResult

```python
class VerificationResult(BaseModel):
    """Complete verification result."""
    
    agent_image: str
    verification_id: str
    timestamp: datetime
    
    # Core scores
    fort_score: int  # 0-180 comprehensive rating
    trust_level: TrustLevel  # CRITICAL, LOW, MEDIUM, HIGH
    deployment_ready: bool
    
    # Component results
    docker_scan: ScanResult
    tee_validation: Optional[TEEValidationResult]
    performance_benchmark: BenchmarkResult
    llm_analysis: Optional[SecurityAnalysisResult]
    strategy_verification: Optional[BacktestResult]
    
    # Enterprise features
    audit_trail: List[AuditEntry]
    compliance_status: ComplianceStatus
    risk_assessment: RiskAssessment
    investment_recommendation: InvestmentRating
    
    # Critical findings
    critical_issues: List[CriticalIssue]
    security_warnings: List[SecurityWarning]
    performance_concerns: List[PerformanceConcern]
```

### SecurityAnalysisResult

```python
class SecurityAnalysisResult(BaseModel):
    """LLM security analysis result."""
    
    trust_score: float  # 0.0-1.0
    confidence: float   # Analysis confidence
    
    # Security findings
    key_security: KeySecurityResult
    transaction_controls: TransactionControlResult  
    behavioral_analysis: BehavioralAnalysisResult
    deception_indicators: List[DeceptionIndicator]
    
    # Trust assessment
    trust_recommendation: TrustRecommendation
    critical_issues: List[str]
    security_concerns: List[str]
    
    # Analysis metadata
    model_used: str
    analysis_timestamp: datetime
    reasoning: str
```

### BacktestResult

```python
class BacktestResult(BaseModel):
    """Strategy verification result."""
    
    agent_id: str
    strategy_type: str
    start_date: str
    end_date: str
    
    # Performance metrics
    initial_capital: float
    final_capital: float
    metrics: PerformanceMetrics
    
    # Market analysis
    regime_performance: Dict[str, Dict[str, float]]
    data_quality: Dict[str, Any]
    
    # Trade history
    trades: List[Dict]
    
    # Investment rating
    investment_rating: InvestmentRating
```

### Fort Score Calculation

```python
class FortScoreCalculator:
    """Calculate comprehensive Fort Score (0-180)."""
    
    @staticmethod
    def calculate(
        security_score: float,      # 0-72 points (40% weight)
        performance_score: float,   # 0-54 points (30% weight) 
        behavioral_score: float,    # 0-36 points (20% weight)
        compliance_score: float     # 0-18 points (10% weight)
    ) -> int:
        """Calculate weighted Fort Score.
        
        Score Breakdown:
        - Security (40%): Vulnerability scan + TEE validation + Key management
        - Performance (30%): Backtest results + Strategy verification
        - Behavioral (20%): LLM analysis + Deception detection
        - Compliance (10%): Audit trail + Regulatory alignment
        
        Returns:
            Integer score from 0-180
        """
```

## Configuration

### Environment Variables

```python
from arc_verifier.config import VerificationConfig

# Load from environment
config = VerificationConfig.from_env()

# Override specific settings
config = VerificationConfig(
    llm_provider="anthropic",
    enable_audit_logging=True,
    strict_security_mode=True,
    max_vulnerability_severity="medium",
    min_fort_score=120,
    parallel_workers=4
)

# Use with pipeline
pipeline = VerificationPipeline(config=config)
```

### Enterprise Configuration

```python
class EnterpriseConfig(BaseModel):
    """Enterprise deployment configuration."""
    
    # Security settings
    strict_security_mode: bool = True
    max_vulnerability_severity: str = "medium"
    require_tee_validation: bool = True
    min_fort_score: int = 120
    
    # Performance settings
    parallel_workers: int = 4
    verification_timeout: int = 1800  # 30 minutes
    enable_performance_monitoring: bool = True
    
    # Compliance settings
    enable_audit_logging: bool = True
    audit_retention_days: int = 2555  # 7 years
    compliance_frameworks: List[str] = ["sox", "gdpr"]
    
    # Risk management
    max_agent_capital: int = 1000000  # $1M
    require_manual_approval_above: int = 100000  # $100K
    circuit_breaker_threshold: float = 0.1  # 10% drawdown
```

## Enterprise Integration

### CI/CD Pipeline Integration

```python
def verify_agent_in_pipeline(
    agent_image: str,
    environment: str = "production"
) -> bool:
    """Verify agent as part of CI/CD pipeline.
    
    Returns:
        True if agent passes verification for deployment
    """
    config = EnterpriseConfig.for_environment(environment)
    pipeline = VerificationPipeline(config=config)
    
    result = pipeline.verify(
        agent_image=agent_image,
        tier="high",
        enable_llm=True,
        enable_tee=True,
        audit_mode=True
    )
    
    # Enterprise deployment criteria
    if result.fort_score >= config.min_fort_score:
        if not result.critical_issues:
            if result.trust_level in [TrustLevel.HIGH, TrustLevel.MEDIUM]:
                return True
    
    # Log rejection reason for audit
    logger.audit(
        event="agent_deployment_rejected",
        agent_image=agent_image,
        fort_score=result.fort_score,
        critical_issues=result.critical_issues,
        environment=environment
    )
    
    return False
```

### Webhook Integration

```python
from arc_verifier.webhooks import WebhookNotifier

# Setup enterprise notifications
notifier = WebhookNotifier()
notifier.add_webhook(
    name="security_alerts",
    url="https://alerts.company.com/security",
    events=["critical_vulnerability", "tee_validation_failed"]
)

notifier.add_webhook(
    name="deployment_decisions", 
    url="https://deploy.company.com/webhook",
    events=["verification_complete", "agent_approved", "agent_rejected"]
)

# Use with verification
pipeline = VerificationPipeline(notifier=notifier)
```

### Database Integration

```python
from arc_verifier.storage import AuditDatabase

# Enterprise audit storage
db = AuditDatabase(
    connection_string="postgresql://user:pass@host/db",
    encryption_key=os.getenv("AUDIT_ENCRYPTION_KEY")
)

# Store verification results
db.store_verification_result(result)

# Query audit trail
compliance_report = db.generate_compliance_report(
    start_date="2024-01-01",
    end_date="2024-12-31",
    framework="sox"
)
```

## Error Handling

### Exception Hierarchy

```python
class ArcVerifierError(Exception):
    """Base exception for Arc-Verifier."""

class VerificationError(ArcVerifierError):
    """Verification process failed."""

class SecurityValidationError(ArcVerifierError):
    """Security validation failed."""
    
class TEEValidationError(ArcVerifierError):
    """TEE validation failed."""
    
class LLMAnalysisError(ArcVerifierError):
    """LLM analysis failed."""
    
class ConfigurationError(ArcVerifierError):
    """Configuration error."""
```

### Error Handling Patterns

```python
from arc_verifier.exceptions import (
    VerificationError, 
    SecurityValidationError,
    TEEValidationError
)

try:
    result = pipeline.verify("agent:latest")
    
except SecurityValidationError as e:
    # Critical security failure
    logger.critical(f"Security validation failed: {e}")
    notify_security_team(agent_image, str(e))
    raise  # Don't deploy
    
except TEEValidationError as e:
    # TEE validation failed - may proceed with warnings
    logger.warning(f"TEE validation failed: {e}")
    if strict_mode:
        raise
    result = pipeline.verify(agent_image, enable_tee=False)
    
except VerificationError as e:
    # General verification failure
    logger.error(f"Verification failed: {e}")
    return VerificationResult.failed(agent_image, reason=str(e))
```

### Retry Logic

```python
from arc_verifier.retry import RetryConfig

# Configure retry behavior
retry_config = RetryConfig(
    max_attempts=3,
    backoff_seconds=5,
    retry_on=[VerificationError, ConnectionError],
    fail_fast_on=[SecurityValidationError]
)

pipeline = VerificationPipeline(retry_config=retry_config)
```

## Performance Optimization

### Caching

```python
from arc_verifier.cache import VerificationCache

# Enable result caching
cache = VerificationCache(
    backend="redis",  # or "memory", "file"
    ttl_seconds=3600,  # 1 hour cache
    cache_key_strategy="agent_hash"  # Cache by agent content hash
)

pipeline = VerificationPipeline(cache=cache)

# Cache invalidation
cache.invalidate_agent("agent:v1.0")
cache.clear_expired()
```

### Parallel Processing

```python
from arc_verifier import ParallelVerifier
import asyncio

async def verify_agent_fleet(agent_images: List[str]) -> Dict[str, VerificationResult]:
    """Verify multiple agents concurrently."""
    
    verifier = ParallelVerifier(max_workers=8)
    
    # Verify in parallel with timeout
    results = await verifier.verify_batch_async(
        agent_images,
        tier="high",
        timeout_seconds=1800  # 30 minutes per agent
    )
    
    return results

# Usage
agent_fleet = ["bot-1:v1", "bot-2:v1", "bot-3:v1"]
results = asyncio.run(verify_agent_fleet(agent_fleet))
```

## Integration Examples

### Complete Enterprise Workflow

```python
from arc_verifier import (
    VerificationPipeline, 
    EnterpriseConfig,
    AuditDatabase,
    WebhookNotifier
)

def enterprise_agent_verification_workflow(
    agent_image: str,
    deployment_target: str = "production"
) -> DeploymentDecision:
    """Complete enterprise verification workflow."""
    
    # 1. Load enterprise configuration
    config = EnterpriseConfig.for_target(deployment_target)
    
    # 2. Setup audit logging and notifications
    audit_db = AuditDatabase.from_config(config)
    notifier = WebhookNotifier.from_config(config)
    
    # 3. Initialize verification pipeline
    pipeline = VerificationPipeline(
        config=config,
        audit_db=audit_db,
        notifier=notifier
    )
    
    # 4. Run comprehensive verification
    try:
        result = pipeline.verify(
            agent_image=agent_image,
            tier="high",
            enable_llm=True,
            enable_tee=True,
            enable_simulation=True,
            audit_mode=True
        )
        
        # 5. Make deployment decision
        decision = make_deployment_decision(result, config)
        
        # 6. Store audit trail
        audit_db.store_decision(
            agent_image=agent_image,
            verification_result=result,
            deployment_decision=decision,
            approver=get_current_user(),
            timestamp=datetime.utcnow()
        )
        
        # 7. Send notifications
        if decision.approved:
            notifier.send_approval_notification(agent_image, result)
        else:
            notifier.send_rejection_notification(agent_image, result)
            
        return decision
        
    except SecurityValidationError as e:
        # Critical security failure - immediate rejection
        decision = DeploymentDecision.reject(
            reason="Critical security validation failure",
            details=str(e)
        )
        
        notifier.send_security_alert(agent_image, e)
        audit_db.store_security_incident(agent_image, e)
        
        return decision

def make_deployment_decision(
    result: VerificationResult,
    config: EnterpriseConfig
) -> DeploymentDecision:
    """Make enterprise deployment decision based on verification result."""
    
    # Check Fort Score threshold
    if result.fort_score < config.min_fort_score:
        return DeploymentDecision.reject(
            reason=f"Fort Score {result.fort_score} below threshold {config.min_fort_score}"
        )
    
    # Check for critical issues
    if result.critical_issues:
        return DeploymentDecision.reject(
            reason=f"Critical issues found: {result.critical_issues}"
        )
    
    # Check trust level
    if result.trust_level == TrustLevel.CRITICAL:
        return DeploymentDecision.reject(
            reason="Critical trust level detected"
        )
    
    # Check capital exposure limits
    if result.risk_assessment.max_capital_exposure > config.max_agent_capital:
        return DeploymentDecision.conditional(
            reason="Requires manual approval for high capital exposure",
            conditions=["manual_approval_required", "reduce_capital_limits"]
        )
    
    # Approve for deployment
    return DeploymentDecision.approve(
        reason="All verification criteria met",
        fort_score=result.fort_score,
        trust_level=result.trust_level
    )
```

---

For additional examples and enterprise integration patterns, see the `/docs/integration/` directory.
EOF < /dev/null