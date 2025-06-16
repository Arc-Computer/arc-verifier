"""Core Arc Verifier - Phase 1 lightweight verification pipeline.

This module implements the core value layer for immediate deployment on laptops
and small teams. Focuses on high-value, low-resource verification components.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import logging

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.panel import Panel

from ..security.scanner import DockerScanner
from ..security.tee_validator import TEEValidator
from ..data.backtester import RealBacktester
from ..analysis.strategy import StrategyVerifier
from ..analysis.llm_judge import LLMJudge
from ..security.audit import AuditLogger


@dataclass
class ResourceLimits:
    """Resource allocation limits for concurrent operations."""
    
    max_concurrent_backtests: int = 8
    max_concurrent_scans: int = 12
    max_concurrent_llm: int = 6
    max_concurrent_tee: int = 10
    max_threads_per_component: int = 4


@dataclass
class CoreVerificationResult:
    """Result from core verification pipeline."""
    
    agent_id: str
    fort_score: float
    security_score: float
    strategy_score: float
    trust_score: float
    tee_score: float
    
    # Component results
    scan_result: Dict[str, Any]
    backtest_result: Optional[Dict[str, Any]] = None
    strategy_result: Optional[Dict[str, Any]] = None
    llm_result: Optional[Dict[str, Any]] = None
    tee_result: Optional[Dict[str, Any]] = None
    
    # Metadata
    processing_time: float = 0.0
    timestamp: datetime = None
    warnings: List[str] = None
    recommendations: List[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.warnings is None:
            self.warnings = []
        if self.recommendations is None:
            self.recommendations = []


@dataclass
class BatchVerificationResult:
    """Results from batch verification of multiple agents."""
    
    total_agents: int
    successful_verifications: int
    failed_verifications: int
    average_fort_score: float
    processing_time: float
    
    results: List[CoreVerificationResult]
    failures: List[Dict[str, Any]]
    
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class CoreArcVerifier:
    """Core Arc Verifier for lightweight, resource-efficient verification.
    
    This is the Phase 1 implementation focused on immediate value:
    - Real market data backtesting (unique value proposition)
    - Security scanning with Trivy (baseline protection)
    - Strategy classification (competitive differentiation)
    - LLM trust analysis (trust-focused scoring)
    - TEE attestation (production-grade security)
    
    Designed to run efficiently on 4-core/8GB hardware while scaling
    to handle 100+ agents in 15-20 minutes.
    """
    
    def __init__(self, 
                 resource_limits: Optional[ResourceLimits] = None,
                 console: Optional[Console] = None):
        self.console = console or Console()
        self.resource_limits = resource_limits or ResourceLimits()
        self.audit_logger = AuditLogger()
        
        # Initialize components (lightweight instantiation)
        self.scanner = DockerScanner(console=self.console)
        self.validator = TEEValidator(console=self.console)
        self.real_backtester = RealBacktester()
        self.strategy_verifier = StrategyVerifier()
        
        # LLM components (lazy initialization)
        self._llm_judge = None
        
        # Semaphores for resource control
        self._backtest_semaphore = asyncio.Semaphore(
            self.resource_limits.max_concurrent_backtests
        )
        self._scan_semaphore = asyncio.Semaphore(
            self.resource_limits.max_concurrent_scans
        )
        self._llm_semaphore = asyncio.Semaphore(
            self.resource_limits.max_concurrent_llm
        )
        self._tee_semaphore = asyncio.Semaphore(
            self.resource_limits.max_concurrent_tee
        )
        
        # Thread pool for CPU-bound operations
        self._thread_pool = ThreadPoolExecutor(
            max_workers=self.resource_limits.max_threads_per_component
        )
    
    @property
    def llm_judge(self) -> LLMJudge:
        """Lazy initialization of LLM judge to avoid startup overhead."""
        if self._llm_judge is None:
            self._llm_judge = LLMJudge()
        return self._llm_judge
    
    async def verify_agent(self, 
                          agent_image: str,
                          enable_llm: bool = True,
                          enable_backtesting: bool = True,
                          backtest_period: str = "2024-10-01:2024-10-07") -> CoreVerificationResult:
        """Verify a single agent with core components.
        
        Args:
            agent_image: Docker image to verify
            enable_llm: Whether to run LLM analysis
            enable_backtesting: Whether to run backtesting
            backtest_period: Date range for backtesting (start:end)
            
        Returns:
            CoreVerificationResult with all component scores
        """
        start_time = time.time()
        
        try:
            # Parse backtest period
            start_date, end_date = backtest_period.split(":")
            
            # Create concurrent tasks for all components
            tasks = []
            
            # Security scanning (required baseline)
            tasks.append(self._run_security_scan(agent_image))
            
            # TEE validation (required for production)
            tasks.append(self._run_tee_validation(agent_image))
            
            # Backtesting (core value proposition)
            if enable_backtesting:
                tasks.append(self._run_backtesting(agent_image, start_date, end_date))
            else:
                tasks.append(asyncio.create_task(self._mock_backtest_result()))
            
            # Strategy verification (depends on backtesting)
            if enable_backtesting:
                tasks.append(self._run_strategy_verification(agent_image, start_date, end_date))
            else:
                tasks.append(asyncio.create_task(self._mock_strategy_result()))
            
            # LLM analysis (trust scoring)
            if enable_llm:
                tasks.append(self._run_llm_analysis(agent_image))
            else:
                tasks.append(asyncio.create_task(self._mock_llm_result()))
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Unpack results
            scan_result = results[0] if not isinstance(results[0], Exception) else None
            tee_result = results[1] if not isinstance(results[1], Exception) else None
            backtest_result = results[2] if not isinstance(results[2], Exception) else None
            strategy_result = results[3] if not isinstance(results[3], Exception) else None
            llm_result = results[4] if not isinstance(results[4], Exception) else None
            
            # Calculate component scores
            security_score = self._calculate_security_score(scan_result, tee_result)
            strategy_score = self._calculate_strategy_score(backtest_result, strategy_result)
            trust_score = self._calculate_trust_score(llm_result)
            tee_score = self._calculate_tee_score(tee_result)
            
            # Calculate final Fort Score
            fort_score = self._calculate_fort_score(
                security_score, strategy_score, trust_score, tee_score
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                scan_result, backtest_result, strategy_result, llm_result, tee_result
            )
            
            # Collect warnings
            warnings = self._collect_warnings(results)
            
            processing_time = time.time() - start_time
            
            # Log successful verification
            self.audit_logger.log_action(
                action="core_verification",
                details={
                    "agent_id": agent_image,
                    "fort_score": fort_score,
                    "processing_time": processing_time,
                    "components_enabled": {
                        "llm": enable_llm,
                        "backtesting": enable_backtesting
                    }
                }
            )
            
            return CoreVerificationResult(
                agent_id=agent_image,
                fort_score=fort_score,
                security_score=security_score,
                strategy_score=strategy_score,
                trust_score=trust_score,
                tee_score=tee_score,
                scan_result=scan_result,
                backtest_result=backtest_result,
                strategy_result=strategy_result,
                llm_result=llm_result,
                tee_result=tee_result,
                processing_time=processing_time,
                warnings=warnings,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.console.print(f"[red]Verification failed for {agent_image}: {e}[/red]")
            processing_time = time.time() - start_time
            
            # Return minimal result for failed verification
            return CoreVerificationResult(
                agent_id=agent_image,
                fort_score=0.0,
                security_score=0.0,
                strategy_score=0.0,
                trust_score=0.0,
                tee_score=0.0,
                scan_result={},
                processing_time=processing_time,
                warnings=[f"Verification failed: {str(e)}"]
            )
    
    async def verify_batch(self, 
                          agent_images: List[str],
                          enable_llm: bool = True,
                          enable_backtesting: bool = True,
                          backtest_period: str = "2024-10-01:2024-10-07") -> BatchVerificationResult:
        """Verify multiple agents concurrently with resource management.
        
        Args:
            agent_images: List of Docker images to verify
            enable_llm: Whether to run LLM analysis
            enable_backtesting: Whether to run backtesting
            backtest_period: Date range for backtesting
            
        Returns:
            BatchVerificationResult with aggregated results
        """
        start_time = time.time()
        
        self.console.print(f"[blue]Starting batch verification of {len(agent_images)} agents[/blue]")
        
        # Create verification tasks for all agents
        tasks = []
        for agent_image in agent_images:
            task = self.verify_agent(
                agent_image=agent_image,
                enable_llm=enable_llm,
                enable_backtesting=enable_backtesting,
                backtest_period=backtest_period
            )
            tasks.append(task)
        
        # Execute with progress tracking
        results = []
        failures = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console,
        ) as progress:
            task_progress = progress.add_task(
                "[cyan]Verifying agents...", total=len(tasks)
            )
            
            # Process in batches to avoid overwhelming the system
            batch_size = min(20, len(tasks))  # Process max 20 agents at once
            
            for i in range(0, len(tasks), batch_size):
                batch_tasks = tasks[i:i + batch_size]
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        failures.append({
                            "agent": agent_images[len(results) + len(failures)],
                            "error": str(result),
                            "timestamp": datetime.now()
                        })
                    else:
                        results.append(result)
                    
                    progress.update(task_progress, advance=1)
        
        processing_time = time.time() - start_time
        
        # Calculate batch statistics
        successful_verifications = len(results)
        failed_verifications = len(failures)
        average_fort_score = (
            sum(r.fort_score for r in results) / successful_verifications
            if successful_verifications > 0 else 0.0
        )
        
        # Log batch completion
        self.audit_logger.log_action(
            action="batch_verification",
            details={
                "total_agents": len(agent_images),
                "successful": successful_verifications,
                "failed": failed_verifications,
                "average_fort_score": average_fort_score,
                "processing_time": processing_time
            }
        )
        
        return BatchVerificationResult(
            total_agents=len(agent_images),
            successful_verifications=successful_verifications,
            failed_verifications=failed_verifications,
            average_fort_score=average_fort_score,
            processing_time=processing_time,
            results=results,
            failures=failures
        )
    
    async def _run_security_scan(self, agent_image: str) -> Dict[str, Any]:
        """Run security scan with resource control."""
        async with self._scan_semaphore:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self._thread_pool, 
                self.scanner.scan,
                agent_image
            )
    
    async def _run_tee_validation(self, agent_image: str) -> Dict[str, Any]:
        """Run TEE validation with resource control."""
        async with self._tee_semaphore:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self._thread_pool,
                self.validator.validate,
                agent_image
            )
    
    async def _run_backtesting(self, agent_image: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Run backtesting with resource control."""
        async with self._backtest_semaphore:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self._thread_pool,
                self.real_backtester.run,
                agent_image,
                start_date,
                end_date
            )
            return result.model_dump() if hasattr(result, 'model_dump') else result
    
    async def _run_strategy_verification(self, agent_image: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Run strategy verification with resource control."""
        async with self._backtest_semaphore:  # Share semaphore with backtesting
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self._thread_pool,
                self.strategy_verifier.verify_strategy,
                agent_image,
                start_date,
                end_date
            )
            return result.model_dump() if hasattr(result, 'model_dump') else result
    
    async def _run_llm_analysis(self, agent_image: str) -> Dict[str, Any]:
        """Run LLM analysis with resource control."""
        async with self._llm_semaphore:
            # LLM calls are I/O bound, don't use thread pool
            return await asyncio.to_thread(
                self.llm_judge.evaluate_agent,
                {"image_tag": agent_image},
                {"timestamp": datetime.now()}
            )
    
    async def _mock_backtest_result(self) -> Dict[str, Any]:
        """Return mock backtest result when backtesting is disabled."""
        return {
            "metrics": {
                "total_return": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "win_rate": 0.0
            },
            "strategy_type": "unknown",
            "disabled": True
        }
    
    async def _mock_strategy_result(self) -> Dict[str, Any]:
        """Return mock strategy result when strategy verification is disabled."""
        return {
            "detected_strategy": "unknown",
            "classification_confidence": 0.0,
            "strategy_effectiveness": 0.0,
            "verification_status": "disabled"
        }
    
    async def _mock_llm_result(self) -> Dict[str, Any]:
        """Return mock LLM result when LLM analysis is disabled."""
        return {
            "overall_trust_score": 50.0,
            "security_analysis": {"score": 50.0},
            "disabled": True
        }
    
    def _calculate_security_score(self, scan_result: Dict, tee_result: Dict) -> float:
        """Calculate security score from scan and TEE results."""
        if not scan_result:
            return 0.0
        
        # Base security score from vulnerabilities
        vulnerabilities = scan_result.get("vulnerabilities", [])
        if not vulnerabilities:
            scan_score = 100.0
        else:
            # Deduct points based on severity
            critical = len([v for v in vulnerabilities if v.get("severity") == "CRITICAL"])
            high = len([v for v in vulnerabilities if v.get("severity") == "HIGH"])
            medium = len([v for v in vulnerabilities if v.get("severity") == "MEDIUM"])
            
            scan_score = max(0, 100 - (critical * 20) - (high * 10) - (medium * 5))
        
        # TEE attestation bonus
        tee_bonus = 0.0
        if tee_result:
            if tee_result.get("is_valid") or tee_result.get("attestation_valid"):
                tee_bonus = 20.0
            elif tee_result.get("platform"):  # Has TEE capability but not valid
                tee_bonus = 5.0  # Small bonus for TEE capability
        
        return min(100.0, scan_score + tee_bonus)
    
    def _calculate_strategy_score(self, backtest_result: Dict, strategy_result: Dict) -> float:
        """Calculate strategy score from backtesting and strategy verification."""
        if not backtest_result or backtest_result.get("disabled"):
            return 50.0  # Neutral score when disabled
        
        # Base score from backtest metrics
        metrics = backtest_result.get("metrics", {})
        
        # Sharpe ratio component (0-40 points)
        sharpe = metrics.get("sharpe_ratio", 0)
        sharpe_score = min(40, max(0, sharpe * 20))
        
        # Return component (0-30 points)
        total_return = metrics.get("total_return", 0)
        return_score = min(30, max(0, total_return * 100))
        
        # Win rate component (0-20 points)
        win_rate = metrics.get("win_rate", 0)
        win_rate_score = win_rate * 20
        
        # Strategy verification bonus (0-10 points)
        strategy_bonus = 0.0
        if strategy_result and not strategy_result.get("disabled"):
            effectiveness = strategy_result.get("strategy_effectiveness", 0)
            strategy_bonus = min(10, effectiveness / 10)
        
        return min(100.0, sharpe_score + return_score + win_rate_score + strategy_bonus)
    
    def _calculate_trust_score(self, llm_result: Dict) -> float:
        """Calculate trust score from LLM analysis."""
        if not llm_result or llm_result.get("disabled"):
            return 50.0  # Neutral score when disabled
        
        # Extract trust score from LLM result
        trust_score = llm_result.get("overall_trust_score", 50.0)
        
        # Security analysis component
        security_analysis = llm_result.get("security_analysis", {})
        security_score = security_analysis.get("score", 50.0)
        
        # Weighted average
        return (trust_score * 0.7) + (security_score * 0.3)
    
    def _calculate_tee_score(self, tee_result: Dict) -> float:
        """Calculate TEE score from attestation validation."""
        if not tee_result:
            return 0.0
        
        base_score = 50.0  # Base score for having TEE capability
        
        # Check for valid attestation (supports both old and new field names)
        if tee_result.get("is_valid") or tee_result.get("attestation_valid"):
            base_score += 30.0
        
        # Platform-specific bonuses
        platform = tee_result.get("platform", "").lower()
        if "sgx" in platform or tee_result.get("sgx_enabled"):
            base_score += 10.0
        elif "tdx" in platform:
            base_score += 15.0  # Higher bonus for TDX (newer, more secure)
        
        # Measurement validation bonus
        measurements = tee_result.get("measurements", {})
        if measurements or tee_result.get("measurement_valid"):
            base_score += 10.0
        
        return min(100.0, base_score)
    
    def _calculate_fort_score(self, security: float, strategy: float, trust: float, tee: float) -> float:
        """Calculate Fort Score using weighted components.
        
        Fort Score Formula (0-180):
        - Security: 25% weight (max 45 points)
        - Strategy: 40% weight (max 72 points)  
        - Trust: 25% weight (max 45 points)
        - TEE: 10% weight (max 18 points)
        """
        weighted_security = (security / 100) * 45
        weighted_strategy = (strategy / 100) * 72
        weighted_trust = (trust / 100) * 45
        weighted_tee = (tee / 100) * 18
        
        return weighted_security + weighted_strategy + weighted_trust + weighted_tee
    
    def _generate_recommendations(self, scan_result: Dict, backtest_result: Dict, 
                                strategy_result: Dict, llm_result: Dict, tee_result: Dict) -> List[str]:
        """Generate actionable recommendations based on verification results."""
        recommendations = []
        
        # Security recommendations
        if scan_result:
            vulnerabilities = scan_result.get("vulnerabilities", [])
            critical_vulns = [v for v in vulnerabilities if v.get("severity") == "CRITICAL"]
            if critical_vulns:
                recommendations.append(f"Address {len(critical_vulns)} critical vulnerabilities immediately")
        
        # Strategy recommendations
        if backtest_result and not backtest_result.get("disabled"):
            metrics = backtest_result.get("metrics", {})
            
            if metrics.get("sharpe_ratio", 0) < 1:
                recommendations.append("Improve risk-adjusted returns - Sharpe ratio below 1.0")
            
            if metrics.get("max_drawdown", 0) < -0.2:
                recommendations.append("Implement better risk management - high drawdown detected")
        
        # TEE recommendations
        if tee_result:
            if not (tee_result.get("is_valid") or tee_result.get("attestation_valid")):
                # Check for simulation indicators
                quote = tee_result.get("quote", {})
                signature = quote.get("signature", "")
                
                if "simulated" in signature.lower():
                    recommendations.append("Deploy on TEE-enabled hardware for production (currently in simulation mode)")
                elif tee_result.get("trust_level") == "UNTRUSTED":
                    recommendations.append("Deploy on trusted TEE hardware with valid attestation for production")
                else:
                    recommendations.append("Fix TEE attestation issues for secure deployment")
        else:
            recommendations.append("Enable TEE attestation for production deployment")
        
        return recommendations
    
    def _collect_warnings(self, results: List[Any]) -> List[str]:
        """Collect warnings from component results."""
        warnings = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                component_names = ["security", "tee", "backtesting", "strategy", "llm"]
                component = component_names[i] if i < len(component_names) else f"component_{i}"
                warnings.append(f"{component} verification failed: {str(result)}")
        
        return warnings
    
    def display_result(self, result: CoreVerificationResult):
        """Display verification result in rich terminal format."""
        
        # Main results panel
        status_color = "green" if result.fort_score > 120 else "yellow" if result.fort_score > 80 else "red"
        
        panel_content = f"""
[bold]Agent:[/bold] {result.agent_id}
[bold]Fort Score:[/bold] [{status_color}]{result.fort_score:.1f}/180[/{status_color}]
[bold]Processing Time:[/bold] {result.processing_time:.1f}s

[bold]Component Scores:[/bold]
  Security:  {result.security_score:.1f}/100
  Strategy:  {result.strategy_score:.1f}/100  
  Trust:     {result.trust_score:.1f}/100
  TEE:       {result.tee_score:.1f}/100
"""
        
        self.console.print(Panel(
            panel_content,
            title="Core Verification Result",
            border_style="blue"
        ))
        
        # Warnings
        if result.warnings:
            self.console.print("\n[bold yellow]⚠️  Warnings:[/bold yellow]")
            for warning in result.warnings:
                self.console.print(f"  • {warning}")
        
        # Recommendations
        if result.recommendations:
            self.console.print("\n[bold cyan]💡 Recommendations:[/bold cyan]")
            for rec in result.recommendations:
                self.console.print(f"  • {rec}")
    
    def display_batch_results(self, batch_result: BatchVerificationResult):
        """Display batch verification results."""
        
        # Summary table
        summary_table = Table(title="Batch Verification Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green")
        
        summary_table.add_row("Total Agents", str(batch_result.total_agents))
        summary_table.add_row("Successful", str(batch_result.successful_verifications))
        summary_table.add_row("Failed", str(batch_result.failed_verifications))
        summary_table.add_row("Success Rate", f"{(batch_result.successful_verifications/batch_result.total_agents)*100:.1f}%")
        summary_table.add_row("Average Fort Score", f"{batch_result.average_fort_score:.1f}/180")
        summary_table.add_row("Processing Time", f"{batch_result.processing_time:.1f}s")
        
        self.console.print(summary_table)
        
        # Top performers
        if batch_result.results:
            top_performers = sorted(batch_result.results, key=lambda x: x.fort_score, reverse=True)[:5]
            
            top_table = Table(title="Top Performers")
            top_table.add_column("Agent", style="cyan")
            top_table.add_column("Fort Score", style="green")
            top_table.add_column("Security", style="yellow")
            top_table.add_column("Strategy", style="blue")
            top_table.add_column("Trust", style="magenta")
            
            for result in top_performers:
                top_table.add_row(
                    result.agent_id[:30] + "..." if len(result.agent_id) > 30 else result.agent_id,
                    f"{result.fort_score:.1f}",
                    f"{result.security_score:.0f}",
                    f"{result.strategy_score:.0f}",
                    f"{result.trust_score:.0f}"
                )
            
            self.console.print(top_table)
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, '_thread_pool'):
            self._thread_pool.shutdown(wait=False)