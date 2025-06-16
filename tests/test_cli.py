"""Tests for the CLI interface."""

import pytest
from click.testing import CliRunner

from arc_verifier.cli import cli


def test_cli_help():
    """Test that the CLI shows help correctly."""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'Arc-Verifier' in result.output
    assert 'verify' in result.output
    assert 'scan' in result.output
    assert 'benchmark' in result.output


def test_cli_version():
    """Test that the CLI shows version correctly."""
    runner = CliRunner()
    result = runner.invoke(cli, ['--version'])
    assert result.exit_code == 0
    assert '1.0.0b1' in result.output


def test_verify_command_help():
    """Test verify command help."""
    runner = CliRunner()
    result = runner.invoke(cli, ['verify', '--help'])
    assert result.exit_code == 0
    assert 'Comprehensive agent verification' in result.output


def test_scan_command_help():
    """Test scan command help."""
    runner = CliRunner()
    result = runner.invoke(cli, ['scan', '--help'])
    assert result.exit_code == 0
    assert 'Quick vulnerability scan' in result.output


def test_benchmark_command_help():
    """Test benchmark command help."""
    runner = CliRunner()
    result = runner.invoke(cli, ['benchmark', '--help'])
    assert result.exit_code == 0
    assert 'Run performance benchmark' in result.output


def test_verify_basic():
    """Test basic verify command execution."""
    runner = CliRunner()
    result = runner.invoke(cli, ['verify', 'nginx:latest'])
    assert result.exit_code == 0
    assert 'Core Verification' in result.output
    assert 'Fort Score' in result.output


def test_scan_basic():
    """Test basic scan command execution."""
    runner = CliRunner()
    result = runner.invoke(cli, ['scan', 'nginx:latest'])
    assert result.exit_code == 0
    assert 'Scanning image: nginx:latest' in result.output


def test_benchmark_basic():
    """Test basic benchmark command execution."""
    runner = CliRunner()
    result = runner.invoke(cli, ['benchmark', 'nginx:latest'])
    assert result.exit_code == 0
    assert 'Benchmarking image: nginx:latest' in result.output