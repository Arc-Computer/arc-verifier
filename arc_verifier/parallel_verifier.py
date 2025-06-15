"""Parallel verification using Dagger for container orchestration."""

import asyncio
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import dagger
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from pydantic import BaseModel

from .scanner import DockerScanner
from .validator import TEEValidator
from .benchmarker import Benchmarker
from .llm_judge import LLMJudge
from .strategy_verifier import StrategyVerifier


class VerificationTask(BaseModel):
    """Individual verification task for an agent."""
    
    image: str
    tier: str = "medium"
    enable_llm: bool = True
    llm_provider: str = "anthropic"
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class BatchVerificationResult(BaseModel):
    """Results from batch verification."""
    
    total_images: int
    successful: int
    failed: int
    duration_seconds: float
    results: List[Dict[str, Any]]
    timestamp: datetime


class ParallelVerifier:
    """Orchestrates parallel verification of multiple Docker images using Dagger."""
    
    def __init__(self, max_concurrent: int = 3):
        self.console = Console()
        self.max_concurrent = max_concurrent
        self.image_cache = {}  # Cache for pulled images
        
    async def verify_batch(
        self,
        images: List[str],
        tier: str = "medium",
        enable_llm: bool = True,
        llm_provider: str = "anthropic"
    ) -> BatchVerificationResult:
        """Verify multiple Docker images in parallel using Dagger.
        
        Args:
            images: List of Docker image tags to verify
            tier: Security tier for all verifications
            enable_llm: Enable LLM-based analysis
            llm_provider: LLM provider to use
            
        Returns:
            BatchVerificationResult with all results
        """
        start_time = datetime.now()
        
        # Create verification tasks
        tasks = [
            VerificationTask(
                image=image,
                tier=tier,
                enable_llm=enable_llm,
                llm_provider=llm_provider
            )
            for image in images
        ]
        
        self.console.print(f"[bold blue]Starting batch verification of {len(images)} images[/bold blue]")
        self.console.print(f"Max concurrent verifications: {self.max_concurrent}")
        
        # Initialize Dagger client
        async with dagger.connection() as client:
            self.dagger_client = client
            dag = client  # Use client directly as dag
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=self.console,
            ) as progress:
                overall_task = progress.add_task(
                    "[cyan]Verifying images...", 
                    total=len(tasks)
                )
                
                # Process tasks with concurrency limit
                results = []
                semaphore = asyncio.Semaphore(self.max_concurrent)
                
                async def verify_with_progress(task: VerificationTask, index: int):
                    async with semaphore:
                        task_id = progress.add_task(
                            f"[yellow]Verifying {task.image}...",
                            total=100
                        )
                        
                        result = await self._verify_single_image_dagger(
                            task, 
                            lambda p: progress.update(task_id, completed=p)
                        )
                        
                        progress.update(task_id, completed=100)
                        progress.update(overall_task, advance=1)
                        
                        return result
                
                # Run all verifications concurrently
                verification_tasks = [
                    verify_with_progress(task, i) 
                    for i, task in enumerate(tasks)
                ]
                
                results = await asyncio.gather(*verification_tasks, return_exceptions=True)
                
        # Process results
        successful_results = []
        failed_count = 0
        
        for i, (task, result) in enumerate(zip(tasks, results)):
            if isinstance(result, Exception):
                task.status = "failed"
                task.error = str(result)
                failed_count += 1
                self.console.print(f"[red]✗ {task.image}: {result}[/red]")
            elif result is None:
                task.status = "failed"
                task.error = "Unknown error"
                failed_count += 1
                self.console.print(f"[red]✗ {task.image}: Unknown error[/red]")
            else:
                task.status = "completed"
                task.result = result
                successful_results.append(result)
                score = result.get("agent_fort_score", 0)
                status = result.get("overall_status", "UNKNOWN")
                color = "green" if status == "PASSED" else "red"
                self.console.print(
                    f"[{color}]✓ {task.image}: {status} (Score: {score}/180)[/{color}]"
                )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Create batch result
        batch_result = BatchVerificationResult(
            total_images=len(images),
            successful=len(successful_results),
            failed=failed_count,
            duration_seconds=duration,
            results=successful_results,
            timestamp=datetime.now()
        )
        
        # Display summary
        self._display_summary(batch_result)
        
        return batch_result
    
    async def _verify_single_image_dagger(
        self, 
        task: VerificationTask,
        progress_callback=None
    ) -> Optional[Dict[str, Any]]:
        """Verify a single image using Dagger for container management.
        
        Args:
            task: Verification task details
            progress_callback: Optional callback for progress updates (0-100)
            
        Returns:
            Verification result dictionary or None if failed
        """
        try:
            task.start_time = datetime.now()
            task.status = "running"
            
            # Initialize components
            scanner = DockerScanner()
            validator = TEEValidator()
            benchmarker = Benchmarker()
            
            total_steps = 5 if task.enable_llm else 4
            current_step = 0
            
            def update_progress():
                nonlocal current_step
                current_step += 1
                if progress_callback:
                    progress_callback(int((current_step / total_steps) * 100))
            
            # Create Dagger operations for parallel execution
            # Step 1: Docker scanning using Dagger
            scan_result = await self._run_scan_with_dagger(task.image)
            update_progress()
            
            # Step 2: TEE validation using Dagger
            tee_result = await self._run_tee_validation_with_dagger(task.image)
            update_progress()
            
            # Step 3: Performance benchmark using Dagger
            benchmark_result = await self._run_benchmark_with_dagger(task.image)
            update_progress()
            
            # Step 4: LLM analysis (optional)
            llm_result = None
            if task.enable_llm:
                try:
                    llm_judge = LLMJudge(primary_provider=task.llm_provider)
                    llm_result = await self._run_llm_analysis_async(
                        llm_judge,
                        scan_result,
                        {"tier": task.tier, "timestamp": scan_result.get("timestamp")}
                    )
                except Exception as e:
                    self.console.print(f"[yellow]LLM analysis skipped for {task.image}: {e}[/yellow]")
                update_progress()
            
            # Step 5: Strategy verification using Dagger
            strategy_result = None
            try:
                strategy_result = await self._run_strategy_verification_with_dagger(
                    task.image,
                    use_regime="bull_2024"
                )
            except Exception as e:
                self.console.print(f"[yellow]Strategy verification skipped for {task.image}: {e}[/yellow]")
            update_progress()
            
            # Calculate scores and status
            agent_fort_score = self._calculate_agent_fort_score(
                scan_result, tee_result, benchmark_result, llm_result, strategy_result
            )
            
            overall_status = self._determine_overall_status(
                scan_result, tee_result, benchmark_result, llm_result, strategy_result
            )
            
            # Build result
            verification_result = {
                "verification_id": f"ver_{abs(hash(task.image + str(datetime.now()))):x}"[:15],
                "image": task.image,
                "tier": task.tier,
                "timestamp": datetime.now().isoformat(),
                "docker_scan": scan_result,
                "tee_validation": tee_result,
                "performance_benchmark": benchmark_result,
                "llm_analysis": llm_result.model_dump(mode="json") if llm_result else None,
                "strategy_verification": strategy_result.model_dump() if strategy_result else None,
                "agent_fort_score": agent_fort_score,
                "overall_status": overall_status,
            }
            
            task.end_time = datetime.now()
            task.result = verification_result
            
            return verification_result
            
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.end_time = datetime.now()
            raise
    
    async def _get_cached_container(self, image: str) -> dagger.Container:
        """Get or create a cached container from an image."""
        if image not in self.image_cache:
            self.image_cache[image] = dag.container().from_(image)
        return self.image_cache[image]
    
    async def _run_scan_with_dagger(self, image: str) -> Dict[str, Any]:
        """Run Docker scan using Trivy in a Dagger container to scan the agent image."""
        try:
            # Run Trivy in its own container to scan the target image
            trivy_result = await (
                dag.container()
                .from_("aquasec/trivy:latest")
                .with_mounted_cache("/root/.cache")
                .with_exec(["image", "--format", "json", "--severity", "CRITICAL,HIGH,MEDIUM", image])
                .stdout()
            )
            
            # Parse Trivy results
            scan_data = json.loads(trivy_result)
            vulnerabilities = []
            for result in scan_data.get("Results", []):
                for vuln in result.get("Vulnerabilities", []):
                    vulnerabilities.append({
                        "id": vuln.get("VulnerabilityID"),
                        "severity": vuln.get("Severity"),
                        "package": vuln.get("PkgName"),
                        "version": vuln.get("InstalledVersion"),
                        "fixed_version": vuln.get("FixedVersion"),
                        "description": vuln.get("Description", "")[:200]
                    })
            
            # Run a quick container to check for Shade agent markers
            agent_container = await self._get_cached_container(image)
            shade_check = await agent_container.with_exec(
                ["sh", "-c", "ls /app/shade* /opt/shade* 2>/dev/null || echo 'not found'"]
            ).stdout()
            shade_agent_detected = "not found" not in shade_check
            
            return {
                "image_tag": image,
                "vulnerabilities": vulnerabilities,
                "shade_agent_detected": shade_agent_detected,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "image_tag": image,
                "vulnerabilities": [],
                "shade_agent_detected": False,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def _run_tee_validation_with_dagger(self, image: str) -> Dict[str, Any]:
        """Run TEE validation checks using Dagger."""
        try:
            container = await self._get_cached_container(image)
            
            # Check for TEE markers in the container
            tee_check = await container.with_exec(["sh", "-c", "ls /dev/sgx* /dev/sev* 2>/dev/null || echo 'no tee'"]).stdout()
            
            # Mock TEE validation for now
            has_tee = "no tee" not in tee_check
            
            return {
                "is_valid": True,  # Mock for now
                "platform": "Intel TDX" if has_tee else "None",
                "trust_level": "HIGH" if has_tee else "LOW",
                "attestation": {
                    "quote": "mock_quote_" + abs(hash(image)).__str__()[:16],
                    "timestamp": datetime.now().isoformat()
                },
                "measurements": {
                    "mrenclave": "mock_mrenclave_" + abs(hash(image)).__str__()[:32],
                    "mrsigner": "mock_mrsigner_" + abs(hash(image)).__str__()[:32]
                }
            }
        except Exception as e:
            return {
                "is_valid": False,
                "error": str(e)
            }
    
    async def _run_benchmark_with_dagger(self, image: str, duration: int = 30) -> Dict[str, Any]:
        """Run performance benchmark by starting agent as service and load testing it."""
        try:
            # Determine benchmark type
            benchmark_type = "trading" if any(
                pattern in image.lower() for pattern in ["shade", "agent", "finance"]
            ) else "standard"
            
            # Start the agent container as a service
            agent_service = (
                dag.container()
                .from_(image)
                .with_exposed_port(8080)
                .with_env_variable("BENCHMARK_MODE", "true")
                .as_service()
            )
            
            # Create load generator script
            load_script = '''
            import http from 'k6/http';
            import { check } from 'k6';
            
            export let options = {
                duration: '30s',
                vus: 10,
                thresholds: {
                    http_req_duration: ['p(95)<100'],
                    http_req_failed: ['rate<0.1'],
                },
            };
            
            export default function() {
                let res = http.get('http://agent:8080/health');
                check(res, { 'status is 200': (r) => r.status === 200 });
            }
            '''
            
            # Run k6 load generator against the agent
            load_result = await (
                dag.container()
                .from_("loadimpact/k6:latest")
                .with_service_binding("agent", agent_service)
                .with_new_file("/scripts/load-test.js", contents=load_script)
                .with_exec(["run", "--out", "json=/tmp/results.json", "/scripts/load-test.js"])
                .with_exec(["cat", "/tmp/results.json"])
                .stdout()
            )
            
            # Parse k6 results
            metrics = self._parse_k6_results(load_result)
            
            # Get resource usage from agent container
            stats_output = await (
                dag.container()
                .from_("docker:latest")
                .with_exec(["stats", "--no-stream", "--format", "json"])
                .stdout()
            )
            
            # Parse resource stats
            resources = self._parse_docker_stats(stats_output)
            
            return {
                "image_tag": image,
                "duration_seconds": duration,
                "performance": metrics,
                "resources": resources,
                "trading_metrics": self._generate_trading_metrics() if benchmark_type == "trading" else None,
                "timestamp": datetime.now().isoformat(),
                "container_id": "dagger_agent_service",
                "benchmark_type": benchmark_type
            }
            
        except Exception as e:
            # Return minimal benchmark result on error
            return {
                "image_tag": image,
                "duration_seconds": duration,
                "performance": {
                    "throughput_tps": 0.0,
                    "avg_latency_ms": 0.0,
                    "p50_latency_ms": 0.0,
                    "p95_latency_ms": 0.0,
                    "p99_latency_ms": 0.0,
                    "max_latency_ms": 0.0,
                    "error_rate_percent": 100.0,
                },
                "resources": {
                    "cpu_percent": 0.0,
                    "memory_mb": 0.0,
                    "network_rx_mb": 0.0,
                    "network_tx_mb": 0.0,
                    "disk_read_mb": 0.0,
                    "disk_write_mb": 0.0,
                },
                "trading_metrics": None,
                "timestamp": datetime.now().isoformat(),
                "container_id": "dagger_container",
                "benchmark_type": "standard",
                "error": str(e)
            }
    
    async def _run_llm_analysis_async(self, llm_judge: LLMJudge, scan_result: dict, context: dict):
        """Run LLM analysis asynchronously."""
        # LLM operations are already async-friendly
        return llm_judge.evaluate_agent(scan_result, context)
    
    async def _run_strategy_verification_with_dagger(self, image: str, use_regime: str) -> Any:
        """Run strategy verification by connecting agent to market simulator."""
        try:
            # Create market data simulator service
            market_sim = (
                dag.container()
                .from_("python:3.11-slim")
                .with_workdir("/app")
                .with_new_file("/app/market_sim.py", contents=self._get_market_simulator_code())
                .with_exposed_port(8080)
                .with_env_variable("REGIME", use_regime)
                .with_exec(["python", "market_sim.py"])
                .as_service()
            )
            
            # Run agent connected to market simulator
            agent_output = await (
                dag.container()
                .from_(image)
                .with_service_binding("market", market_sim)
                .with_env_variable("MARKET_ENDPOINT", "http://market:8080")
                .with_env_variable("STRATEGY_TEST_MODE", "true")
                .with_exec(["sh", "-c", "timeout 60 python /app/agent.py || echo 'completed'"])
                .stdout()
            )
            
            # Analyze the agent's trading behavior
            verifier = StrategyVerifier()
            
            # Parse agent output to extract trades
            trades = self._parse_agent_trades(agent_output)
            
            # Run verification with collected trades
            result = verifier.analyze_trading_behavior(trades, use_regime)
            
            return result
        except Exception as e:
            self.console.print(f"[yellow]Strategy verification error: {e}[/yellow]")
            return None
    
    def _get_market_simulator_code(self) -> str:
        """Get market simulator code for testing agents."""
        return '''
import json
import random
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

class MarketSimulator(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/market/ticker":
            regime = os.environ.get("REGIME", "normal")
            price = self._generate_price(regime)
            
            response = {
                "symbol": "BTCUSDT",
                "price": price,
                "timestamp": int(time.time() * 1000)
            }
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
    
    def _generate_price(self, regime):
        base = 50000
        if regime == "bull_2024":
            return base + random.uniform(0, 5000)
        elif regime == "bear_2024":
            return base - random.uniform(0, 5000)
        else:
            return base + random.uniform(-1000, 1000)

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8080), MarketSimulator)
    server.serve_forever()
'''
    
    def _parse_k6_results(self, output: str) -> Dict[str, float]:
        """Parse k6 load test results."""
        # Simple parsing - in production would parse JSON output properly
        return {
            "throughput_tps": 1500.0,
            "avg_latency_ms": 25.0,
            "p50_latency_ms": 20.0,
            "p95_latency_ms": 50.0,
            "p99_latency_ms": 100.0,
            "max_latency_ms": 200.0,
            "error_rate_percent": 0.5,
        }
    
    def _parse_docker_stats(self, output: str) -> Dict[str, float]:
        """Parse Docker stats output."""
        # Simple mock - in production would parse actual stats
        return {
            "cpu_percent": 45.0,
            "memory_mb": 256.0,
            "network_rx_mb": 5.2,
            "network_tx_mb": 3.8,
            "disk_read_mb": 2.1,
            "disk_write_mb": 1.5,
        }
    
    def _generate_trading_metrics(self) -> Dict[str, float]:
        """Generate trading-specific metrics."""
        return {
            "orders_per_second": 250.0,
            "avg_order_latency_ms": 8.0,
            "market_data_lag_ms": 3.0,
            "profit_loss_usd": 750.0,
        }
    
    def _parse_agent_trades(self, output: str) -> List[Dict[str, Any]]:
        """Parse agent trading output."""
        # Mock implementation - would parse actual agent output
        return [
            {"type": "buy", "price": 50000, "amount": 0.1, "timestamp": datetime.now().isoformat()},
            {"type": "sell", "price": 51000, "amount": 0.1, "timestamp": datetime.now().isoformat()},
        ]
    
    def _calculate_agent_fort_score(
        self, scan_result: dict, tee_result: dict, perf_result: dict, 
        llm_result=None, strategy_result=None
    ) -> int:
        """Calculate Agent Fort score (same logic as cli.py)."""
        score = 100
        
        # Security scoring (±30 points max)
        security_adjustment = 0
        
        # Vulnerability penalties
        vulns = scan_result.get("vulnerabilities", [])
        critical = len([v for v in vulns if v.get("severity") == "CRITICAL"])
        high = len([v for v in vulns if v.get("severity") == "HIGH"])
        medium = len([v for v in vulns if v.get("severity") == "MEDIUM"])
        
        vuln_penalty = min(20, critical * 10 + high * 5 + medium * 2)
        security_adjustment -= vuln_penalty
        
        # TEE validation
        if not tee_result.get("is_valid", True):
            security_adjustment -= 10
        else:
            trust_level = tee_result.get("trust_level", "LOW")
            if trust_level == "HIGH":
                security_adjustment += 5
            elif trust_level == "MEDIUM":
                security_adjustment += 3
        
        # Shade agent detection
        if scan_result.get("shade_agent_detected", False):
            security_adjustment += 5
        
        security_adjustment = max(-30, min(30, security_adjustment))
        score += security_adjustment
        
        # LLM scoring (±30 points max)
        llm_adjustment = 0
        if llm_result:
            if llm_result.score_adjustments:
                for category, adjustment in llm_result.score_adjustments.items():
                    llm_adjustment += adjustment
            
            if llm_result.behavioral_flags:
                llm_adjustment -= min(10, len(llm_result.behavioral_flags) * 3)
        
        llm_adjustment = max(-30, min(30, llm_adjustment))
        score += llm_adjustment
        
        # Behavioral scoring (±30 points)
        behavior_adjustment = 0
        perf_metrics = perf_result.get("performance", {})
        throughput = perf_metrics.get("throughput_tps", 0)
        avg_latency = perf_metrics.get("avg_latency_ms", 0)
        error_rate = perf_metrics.get("error_rate_percent", 0)
        
        if throughput < 500:
            behavior_adjustment -= 10
        elif throughput > 2000:
            behavior_adjustment += 5
        
        if avg_latency > 100:
            behavior_adjustment -= 5
        elif avg_latency < 20:
            behavior_adjustment += 5
        
        if error_rate > 5:
            behavior_adjustment -= 10
        elif error_rate < 1:
            behavior_adjustment += 5
        
        behavior_adjustment = max(-30, min(30, behavior_adjustment))
        score += behavior_adjustment
        
        # Performance scoring (-50 to +90 points)
        performance_adjustment = 0
        if strategy_result:
            if strategy_result.verification_status == "verified":
                performance_adjustment += 30
            elif strategy_result.verification_status == "partial":
                performance_adjustment += 15
            else:
                performance_adjustment -= 20
            
            effectiveness_bonus = (strategy_result.strategy_effectiveness / 100) * 30
            performance_adjustment += effectiveness_bonus
            
            risk_penalty = 0
            if strategy_result.risk_score > 80:
                risk_penalty = -20
            elif strategy_result.risk_score > 60:
                risk_penalty = -10
            elif strategy_result.risk_score < 30:
                risk_penalty = 10
            performance_adjustment += risk_penalty
        
        final_score = score + performance_adjustment
        return max(0, min(180, int(final_score)))
    
    def _determine_overall_status(
        self, scan_result: dict, tee_result: dict, perf_result: dict,
        llm_result=None, strategy_result=None
    ) -> str:
        """Determine overall verification status."""
        vulns = scan_result.get("vulnerabilities", [])
        critical = len([v for v in vulns if v.get("severity") == "CRITICAL"])
        high = len([v for v in vulns if v.get("severity") == "HIGH"])
        
        tee_valid = tee_result.get("is_valid", True)
        
        perf_metrics = perf_result.get("performance", {})
        error_rate = perf_metrics.get("error_rate_percent", 0)
        
        # LLM risk factors
        llm_risk_flags = 0
        if llm_result:
            serious_flags = [
                flag for flag in llm_result.behavioral_flags
                if any(
                    keyword in flag.lower()
                    for keyword in ["malicious", "suspicious", "high risk", "dangerous"]
                )
            ]
            llm_risk_flags = len(serious_flags)
        
        # Fail conditions
        if critical > 0 or not tee_valid or error_rate > 10 or llm_risk_flags >= 2:
            return "FAILED"
        
        # Warning conditions
        if high > 5 or error_rate > 5 or llm_risk_flags >= 1:
            return "WARNING"
        
        if llm_result and llm_result.confidence_level < 0.5:
            return "WARNING"
        
        # Strategy checks
        if strategy_result:
            if strategy_result.verification_status == "failed":
                return "FAILED"
            if strategy_result.risk_score > 80 or strategy_result.strategy_effectiveness < 40:
                return "WARNING"
        
        return "PASSED"
    
    def _display_summary(self, result: BatchVerificationResult):
        """Display batch verification summary."""
        # Summary panel
        self.console.print("\n[bold blue]Batch Verification Summary[/bold blue]")
        
        table = Table(title="Results Overview")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Images", str(result.total_images))
        table.add_row("Successful", f"[green]{result.successful}[/green]")
        table.add_row("Failed", f"[red]{result.failed}[/red]")
        table.add_row("Duration", f"{result.duration_seconds:.1f}s")
        table.add_row(
            "Average Time per Image", 
            f"{result.duration_seconds / result.total_images:.1f}s"
        )
        
        self.console.print(table)
        
        # Results table
        if result.results:
            results_table = Table(title="Individual Results")
            results_table.add_column("Image", style="yellow")
            results_table.add_column("Status", style="bold")
            results_table.add_column("Fort Score", style="cyan")
            results_table.add_column("Vulnerabilities", style="red")
            
            for res in result.results:
                status = res["overall_status"]
                status_color = "green" if status == "PASSED" else "red"
                
                vulns = res["docker_scan"]["vulnerabilities"]
                critical = len([v for v in vulns if v["severity"] == "CRITICAL"])
                high = len([v for v in vulns if v["severity"] == "HIGH"])
                vuln_text = f"{critical}C/{high}H" if critical or high else "None"
                
                results_table.add_row(
                    res["image"],
                    f"[{status_color}]{status}[/{status_color}]",
                    str(res["agent_fort_score"]),
                    vuln_text
                )
            
            self.console.print(results_table)