"""Docker image scanner for vulnerability detection and Shade agent analysis."""

import docker
import subprocess
import json
import hashlib
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from pydantic import BaseModel


class Vulnerability(BaseModel):
    """Vulnerability information from security scan."""

    severity: str
    cve_id: str
    package: str
    version: str
    fixed_version: Optional[str] = None
    description: Optional[str] = None


class LayerInfo(BaseModel):
    """Docker layer analysis information."""

    index: int
    digest: str
    size: int
    command: str


class ScanResult(BaseModel):
    """Complete Docker scan results."""

    image_tag: str
    image_id: str
    vulnerabilities: List[Vulnerability]
    layers: List[LayerInfo]
    shade_agent_detected: bool
    checksum: str
    size: int
    timestamp: datetime


class DockerScanner:
    """Docker image scanner for vulnerability detection and analysis."""

    def __init__(self, force_mock=False, console=None):
        self.console = console or Console()
        if force_mock:
            self.client = None
            self.docker_available = False
            self._force_mock = True
        else:
            try:
                self.client = docker.from_env(timeout=30)
                # Test connection with longer timeout for production readiness
                self.client.ping()
                self.docker_available = True
                self.console.print("[green]✓ Docker daemon connected[/green]")
            except Exception as e:
                self.console.print(
                    f"[red]❌ Docker daemon connection failed: {e}[/red]"
                )
                self.console.print(
                    "[red]Arc-Verifier requires Docker to be running.[/red]"
                )
                self.console.print(
                    "[yellow]Please ensure Docker daemon is started and accessible.[/yellow]"
                )
                raise RuntimeError(
                    f"Docker is required for Arc-Verifier operation. Error: {e}"
                )

    def scan(self, image_tag: str) -> Dict[str, Any]:
        """Scan Docker image for vulnerabilities and compliance.

        Args:
            image_tag: Docker image tag to scan (e.g., 'nginx:latest')

        Returns:
            Dictionary containing scan results
        """
        self.console.print(f"[blue]Starting scan for {image_tag}[/blue]")

        if not self.docker_available:
            # Only allow mock data in force_mock mode (for testing)
            if hasattr(self, "_force_mock") and self._force_mock:
                return self._get_mock_scan_result(image_tag)
            raise RuntimeError(
                "Docker daemon is not available. Cannot proceed with scanning."
            )

        try:
            # Pull image if needed
            image = self._pull_image(image_tag)

            # Run vulnerability scan
            vulnerabilities = self._run_trivy_scan(image_tag)

            # Analyze layers
            layers = self._analyze_layers(image)

            # Detect Shade agent patterns
            shade_detected = self._detect_shade_agent(image)

            # Get image metadata
            checksum = self._get_image_checksum(image)

            result = ScanResult(
                image_tag=image_tag,
                image_id=image.id,
                vulnerabilities=vulnerabilities,
                layers=layers,
                shade_agent_detected=shade_detected,
                checksum=checksum,
                size=image.attrs.get("Size", 0),
                timestamp=datetime.now(),
            )

            return result.model_dump(mode="json")

        except Exception as e:
            self.console.print(f"[red]Scan failed: {e}[/red]")
            raise RuntimeError(f"Docker scan operation failed: {e}")

    def _pull_image(self, image_tag: str) -> docker.models.images.Image:
        """Pull Docker image if not present locally."""
        try:
            # Check if image exists locally
            return self.client.images.get(image_tag)
        except docker.errors.ImageNotFound:
            # Pull image
            self.console.print(f"[blue]Pulling image: {image_tag}[/blue]")
            try:
                image = self.client.images.pull(image_tag)
                self.console.print(f"[green]✓ Image pulled successfully[/green]")
                return image
            except docker.errors.APIError as e:
                self.console.print(f"[red]✗ Failed to pull image: {e}[/red]")
                raise

    def _run_trivy_scan(self, image_tag: str) -> List[Vulnerability]:
        """Run Trivy vulnerability scanner."""
        try:
            # Check if Trivy is installed
            subprocess.run(["trivy", "--version"], capture_output=True, check=True)

            # Run Trivy scan
            result = subprocess.run(
                ["trivy", "image", "--format", "json", "--no-progress", image_tag],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                scan_data = json.loads(result.stdout)
                return self._parse_trivy_results(scan_data)
            else:
                self.console.print(f"[red]Trivy scan failed: {result.stderr}[/red]")
                raise RuntimeError(f"Trivy vulnerability scan failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            self.console.print("[red]Trivy scan timed out[/red]")
            raise RuntimeError("Vulnerability scan timed out after 5 minutes")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.console.print("[red]Trivy scanner not available[/red]")
            self.console.print(
                "[yellow]Install Trivy: https://aquasecurity.github.io/trivy/latest/getting-started/installation/[/yellow]"
            )
            raise RuntimeError(
                "Trivy vulnerability scanner is required but not installed"
            )
        except json.JSONDecodeError:
            self.console.print("[red]Invalid Trivy output format[/red]")
            raise RuntimeError("Failed to parse Trivy scan results")

    def _parse_trivy_results(self, scan_data: Dict[str, Any]) -> List[Vulnerability]:
        """Parse Trivy JSON output into Vulnerability objects."""
        vulnerabilities = []

        results = scan_data.get("Results", [])
        for result in results:
            vulns = result.get("Vulnerabilities", [])
            for vuln in vulns:
                vulnerabilities.append(
                    Vulnerability(
                        severity=vuln.get("Severity", "UNKNOWN"),
                        cve_id=vuln.get("VulnerabilityID", ""),
                        package=vuln.get("PkgName", ""),
                        version=vuln.get("InstalledVersion", ""),
                        fixed_version=vuln.get("FixedVersion"),
                        description=vuln.get("Description", "")[
                            :200
                        ],  # Truncate long descriptions
                    )
                )

        return vulnerabilities

    def _analyze_layers(self, image: docker.models.images.Image) -> List[LayerInfo]:
        """Analyze Docker image layers."""
        try:
            image_data = image.attrs
            layers = []

            # Get layer information from RootFS
            root_fs = image_data.get("RootFS", {})
            layer_digests = root_fs.get("Layers", [])

            # Get history for commands
            history = image_data.get("History", [])

            for i, layer_digest in enumerate(layer_digests):
                # Try to get corresponding history entry
                command = "N/A"
                if i < len(history):
                    created_by = history[i].get("CreatedBy", "")
                    # Clean up command for display
                    if created_by.startswith("/bin/sh -c"):
                        command = created_by[11:60] + (
                            "..." if len(created_by) > 60 else ""
                        )
                    else:
                        command = created_by[:60] + (
                            "..." if len(created_by) > 60 else ""
                        )

                layers.append(
                    LayerInfo(
                        index=i,
                        digest=layer_digest,
                        size=0,  # Size calculation would require more complex inspection
                        command=command,
                    )
                )

            return layers

        except Exception as e:
            self.console.print(f"[yellow]Layer analysis failed: {e}[/yellow]")
            return []

    def _detect_shade_agent(self, image: docker.models.images.Image) -> bool:
        """Detect if image contains agentic protocol patterns (Shade agents and others)."""
        try:
            image_data = image.attrs
            config = image_data.get("Config", {})

            # Enhanced environment variable patterns for broader agentic protocol support
            env_vars = config.get("Env", [])
            agentic_env_patterns = [
                # NEAR/Shade specific
                "SHADE_",
                "ARC_AGENT",
                "NEAR_",
                "TEE_",
                # General agentic patterns
                "AGENT_",
                "BOT_",
                "TRADING_",
                "DEFI_",
                # Protocol specific
                "ETHEREUM_",
                "SOLANA_",
                "POLYGON_",
                "AVALANCHE_",
                # AI/ML agent patterns
                "MODEL_",
                "INFERENCE_",
                "OPENAI_",
                "ANTHROPIC_",
                # Trading/finance specific
                "PRIVATE_KEY",
                "WALLET_",
                "STRATEGY_",
                "RISK_",
            ]

            for env_var in env_vars:
                for pattern in agentic_env_patterns:
                    if pattern in env_var.upper():
                        return True

            # Enhanced label patterns
            labels = config.get("Labels") or {}
            agentic_label_patterns = [
                # Core patterns
                "shade",
                "arc",
                "near",
                "agent",
                "bot",
                # Trading/DeFi
                "trading",
                "defi",
                "finance",
                "swap",
                "liquidity",
                # Protocols
                "ethereum",
                "solana",
                "polygon",
                "arbitrum",
                # AI/ML
                "ai",
                "ml",
                "model",
                "inference",
                "gpt",
                # Agentic frameworks
                "autogen",
                "langchain",
                "crewai",
                "llamaindex",
            ]

            for key, value in labels.items():
                label_text = f"{key} {value}".lower()
                for pattern in agentic_label_patterns:
                    if pattern in label_text:
                        return True

            # Enhanced file/dependency patterns in layer commands
            history = image_data.get("History", [])
            agentic_file_patterns = [
                # NEAR/Shade specific
                "@neardefi/shade-agent-js",
                "shade-agent",
                "near-api-js",
                "chainsig.js",
                # Web3 libraries
                "web3.js",
                "ethers.js",
                "viem",
                "@solana/web3.js",
                # Trading/DeFi libraries
                "ccxt",
                "1inch",
                "uniswap",
                "pancakeswap",
                "sushiswap",
                # AI/ML libraries
                "openai",
                "anthropic",
                "langchain",
                "autogen",
                "crewai",
                "transformers",
                "torch",
                "tensorflow",
                # Agentic frameworks
                "agent-framework",
                "multi-agent",
                "swarm",
                # Common patterns
                "/app/pages",
                "/app/agents",
                "/app/strategies",
                "yarn dev",
                "npm run dev",
                "npm run agent",
                # Config files
                "agent.config",
                "strategy.config",
                "trading.config",
                ".env.agent",
                ".env.trading",
            ]

            for hist_entry in history:
                created_by = hist_entry.get("CreatedBy", "").lower()
                for pattern in agentic_file_patterns:
                    if pattern in created_by:
                        return True

            # Check image tag/name patterns
            image_tags = image.tags if image.tags else []
            for tag in image_tags:
                tag_lower = tag.lower()
                tag_patterns = [
                    "shade",
                    "agent",
                    "bot",
                    "trading",
                    "defi",
                    "finance",
                    "swap",
                    "arbitrage",
                    "market-maker",
                    "ai",
                    "ml",
                    "gpt",
                    "claude",
                    "llm",
                ]
                for pattern in tag_patterns:
                    if pattern in tag_lower:
                        return True

            return False

        except Exception as e:
            self.console.print(
                f"[yellow]Agentic protocol detection failed: {e}[/yellow]"
            )
            return False

    def _get_image_checksum(self, image: docker.models.images.Image) -> str:
        """Get image checksum/digest."""
        try:
            # Get the image ID (which is a SHA256 hash)
            return image.id
        except Exception:
            return "unknown"

    def _get_mock_vulnerabilities(self) -> List[Vulnerability]:
        """Return mock vulnerability data for demo purposes."""
        return [
            Vulnerability(
                severity="LOW",
                cve_id="CVE-2023-1234",
                package="libssl",
                version="1.1.1",
                fixed_version="1.1.2",
                description="Low severity SSL vulnerability",
            ),
            Vulnerability(
                severity="MEDIUM",
                cve_id="CVE-2023-5678",
                package="nodejs",
                version="16.0.0",
                fixed_version="16.1.0",
                description="Medium severity Node.js vulnerability",
            ),
        ]

    def _get_mock_scan_result(self, image_tag: str) -> Dict[str, Any]:
        """Return complete mock scan result for demo purposes."""
        # Determine if it's an agentic protocol based on image name
        agentic_keywords = [
            # NEAR/Shade specific
            "shade",
            "near",
            "pivortex",
            # General agentic
            "agent",
            "bot",
            "trading",
            "defi",
            "finance",
            # AI/ML
            "ai",
            "ml",
            "gpt",
            "claude",
            "llm",
            # DeFi/Trading
            "swap",
            "arbitrage",
            "market-maker",
            "liquidity",
        ]
        shade_detected = any(
            keyword in image_tag.lower() for keyword in agentic_keywords
        )

        mock_result = ScanResult(
            image_tag=image_tag,
            image_id=f"sha256:{'a' * 12}...",
            vulnerabilities=self._get_mock_vulnerabilities(),
            layers=[
                LayerInfo(
                    index=0,
                    digest="sha256:abc123",
                    size=5242880,
                    command="FROM node:18-alpine",
                ),
                LayerInfo(
                    index=1,
                    digest="sha256:def456",
                    size=1048576,
                    command="COPY package.json .",
                ),
                LayerInfo(
                    index=2,
                    digest="sha256:ghi789",
                    size=52428800,
                    command="RUN npm install",
                ),
            ],
            shade_agent_detected=shade_detected,
            checksum=f"sha256:{'b' * 64}",
            size=268435456,  # 256 MB
            timestamp=datetime.now(),
        )

        return mock_result.model_dump(mode="json")
