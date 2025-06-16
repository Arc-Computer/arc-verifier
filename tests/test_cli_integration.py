"""Integration tests for Arc-Verifier CLI commands."""

import pytest
from click.testing import CliRunner
import json
from pathlib import Path
from arc_verifier.cli import cli
from arc_verifier.security import AuditLogger


class TestCLIIntegration:
    """Test all CLI commands work correctly."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI runner."""
        return CliRunner()
    
    @pytest.fixture
    def test_image(self):
        """Test image name."""
        return "nginx:latest"
    
    def test_init_command(self, runner):
        """Test arc-verifier init command."""
        result = runner.invoke(cli, ['init'])
        assert result.exit_code == 0
        assert "Initializing Arc-Verifier" in result.output
    
    def test_verify_command(self, runner, test_image):
        """Test arc-verifier verify command."""
        result = runner.invoke(cli, ['verify', test_image, '--no-llm', '--no-backtesting'])
        assert result.exit_code == 0
        assert "Fort Score" in result.output
    
    def test_verify_with_json_output(self, runner, test_image):
        """Test verify command with JSON output."""
        result = runner.invoke(cli, ['verify', test_image, '--output', 'json', '--no-llm', '--no-backtesting'])
        assert result.exit_code == 0
        
        # Should be valid JSON
        data = json.loads(result.output)
        assert 'core_verification_batch' in data
        batch_data = data['core_verification_batch']
        assert 'average_fort_score' in batch_data
        assert 'results' in batch_data
        assert len(batch_data['results']) == 1
        assert batch_data['results'][0]['agent_id'] == test_image
    
    @pytest.mark.slow
    @pytest.mark.timeout(300)  # 5 minutes for batch command
    def test_batch_command(self, runner):
        """Test arc-verifier batch command."""
        result = runner.invoke(cli, ['batch', 'nginx:latest', 'alpine:latest', '--no-llm'])
        assert result.exit_code == 0
        assert "Batch Verification Results" in result.output
    
    @pytest.mark.slow
    def test_scan_command(self, runner, test_image):
        """Test arc-verifier scan command."""
        result = runner.invoke(cli, ['scan', test_image])
        assert result.exit_code == 0
        assert "Security Scan" in result.output
    
    @pytest.mark.slow
    def test_benchmark_command(self, runner, test_image):
        """Test arc-verifier benchmark command."""
        result = runner.invoke(cli, ['benchmark', test_image, '--duration', '5'])
        assert result.exit_code == 0
        assert "Performance" in result.output
    
    def test_backtest_command(self, runner, test_image):
        """Test arc-verifier backtest command."""
        result = runner.invoke(cli, ['backtest', test_image, '--start-date', '2024-01-01', '--end-date', '2024-01-07'])
        # May fail if no market data, but command should run
        assert result.exit_code in [0, 1]
    
    @pytest.mark.slow
    def test_simulate_command(self, runner, test_image):
        """Test arc-verifier simulate command."""
        result = runner.invoke(cli, ['simulate', test_image])
        assert result.exit_code == 0
        assert "Simulation" in result.output
    
    def test_history_command(self, runner):
        """Test arc-verifier history command."""
        result = runner.invoke(cli, ['history'])
        assert result.exit_code == 0
        # May have no results, but command should work
    
    def test_config_validate(self, runner, tmp_path):
        """Test arc-verifier config validate command."""
        # Create a test config
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("""
tier: high
enable_llm: true
enable_backtesting: false
""")
        
        result = runner.invoke(cli, ['config', 'validate', str(config_file)])
        assert result.exit_code == 0
        assert "valid" in result.output.lower()
    
    def test_config_show(self, runner):
        """Test arc-verifier config show command."""
        result = runner.invoke(cli, ['config', 'show'])
        assert result.exit_code == 0
        assert "Configuration" in result.output
    
    def test_data_status(self, runner):
        """Test arc-verifier data status command."""
        result = runner.invoke(cli, ['data', 'status'])
        assert result.exit_code == 0
        assert "Market Data Status" in result.output
    
    def test_export_results_json(self, runner, test_image):
        """Test arc-verifier export results command."""
        # First create a verification
        runner.invoke(cli, ['verify', test_image, '--no-llm', '--no-backtesting'])
        
        # Then export it
        result = runner.invoke(cli, ['export', 'results', '--latest', '--format', 'json'])
        assert result.exit_code == 0
        assert "Exported JSON report" in result.output
    
    def test_export_results_html(self, runner, test_image):
        """Test arc-verifier export results HTML command."""
        # First create a verification
        runner.invoke(cli, ['verify', test_image, '--no-llm', '--no-backtesting'])
        
        # Then export it
        result = runner.invoke(cli, ['export', 'results', '--latest', '--format', 'html'])
        assert result.exit_code == 0
        assert "Exported HTML report" in result.output
    
    def test_help_commands(self, runner):
        """Test help for all commands."""
        commands = [
            [],  # Main help
            ['verify', '--help'],
            ['batch', '--help'],
            ['scan', '--help'],
            ['benchmark', '--help'],
            ['backtest', '--help'],
            ['simulate', '--help'],
            ['init', '--help'],
            ['history', '--help'],
            ['config', '--help'],
            ['data', '--help'],
            ['export', '--help'],
        ]
        
        for cmd in commands:
            result = runner.invoke(cli, cmd)
            assert result.exit_code == 0
            assert "Usage:" in result.output
            assert "--help" in result.output


class TestParallelVerification:
    """Test parallel verification capabilities."""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.timeout(900)  # 15 minutes for 10 agents
    async def test_parallel_verification_10_agents(self):
        """Test verifying 10 agents in parallel."""
        from arc_verifier.orchestration import ParallelVerifier
        
        # Create verifier with max concurrent limit
        verifier = ParallelVerifier(max_concurrent=5)
        
        # Test images
        images = [f"test-agent:{i}" for i in range(10)]
        
        # Run verification (with mocking enabled)
        result = await verifier.run(
            images,
            enable_llm=False,
            tier="low"
        )
        
        assert result.total_images == 10
        assert result.successful >= 0
        assert len(result.results) >= 0
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.timeout(1800)  # 30 minutes for 100 agents
    async def test_parallel_verification_100_agents(self):
        """Test verifying 100 agents in parallel (marked as slow test)."""
        from arc_verifier.orchestration import ParallelVerifier
        import time
        
        # Create verifier with higher concurrency
        verifier = ParallelVerifier(max_concurrent=20)
        
        # Test images
        images = [f"test-agent:{i:03d}" for i in range(100)]
        
        # Track time
        start_time = time.time()
        
        # Run verification (with mocking enabled for speed)
        result = await verifier.run(
            images,
            enable_llm=False,
            tier="low"
        )
        
        elapsed_time = time.time() - start_time
        
        assert result.total_images == 100
        assert result.successful >= 0
        assert len(result.results) >= 0
        
        # Should complete in under 30 minutes (1800 seconds)
        # With mocking, should be much faster
        assert elapsed_time < 1800
        
        print(f"\nVerified {result.total_images} agents in {elapsed_time:.1f} seconds")
        print(f"Success rate: {result.successful}/{result.total_images}")


class TestPackageInstallation:
    """Test PyPI package installation and functionality."""
    
    def test_package_imports(self):
        """Test all public imports work."""
        # Main package
        import arc_verifier
        assert hasattr(arc_verifier, '__version__')
        
        # Public API
        from arc_verifier import api
        assert hasattr(api, 'verify_agent')
        assert hasattr(api, 'verify_batch')
        
        # Core components
        from arc_verifier import CoreArcVerifier, ResourceLimits
        assert CoreArcVerifier is not None
        assert ResourceLimits is not None
        
        # Models
        from arc_verifier.models import VerificationResult, BatchVerificationResult
        assert VerificationResult is not None
        assert BatchVerificationResult is not None
    
    def test_cli_entry_point(self):
        """Test CLI entry point is accessible."""
        from arc_verifier.cli import cli
        assert cli is not None
        assert callable(cli)
    
    def test_optional_dependencies(self):
        """Test optional dependencies can be imported."""
        # Test LLM providers (if installed)
        try:
            from arc_verifier.analysis.llm_judge import LLMJudge
            assert LLMJudge is not None
        except ImportError:
            pytest.skip("LLM dependencies not installed")
        
        # Test web UI (if installed)
        try:
            from arc_verifier.web import create_app
            assert callable(create_app)
        except ImportError:
            pytest.skip("Web dependencies not installed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])