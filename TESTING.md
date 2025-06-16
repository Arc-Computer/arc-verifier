# Testing Guide for Arc-Verifier

This document provides comprehensive testing strategies for Arc-Verifier, including how to handle long-running integration tests.

## Quick Test Suite (Recommended for CI/CD)

Run fast unit tests excluding slow integration tests:

```bash
# Run all tests except slow ones (completes in ~2 minutes)
pytest -v -m "not slow"

# Run specific test categories
pytest tests/test_cli.py tests/test_llm_judge.py tests/test_data_fetcher.py -v
```

## Full Test Suite (Extended Timeouts)

Run complete test suite including long-running integration tests:

```bash
# Install with timeout support
pip install -e ".[dev]"

# Run all tests with extended timeouts (may take 30+ minutes)
pytest -v --timeout=1800

# Run only slow/integration tests
pytest -v -m "slow" --timeout=1800
```

## Test Categories

### Unit Tests (Fast - 30 seconds)
- `test_cli.py` - CLI command validation
- `test_llm_judge.py` - LLM analysis components  
- `test_scanner.py` - Security scanning
- `test_validator.py` - TEE validation
- `test_benchmarker.py` - Performance benchmarking
- `test_backtester.py` - Strategy backtesting
- `test_data_fetcher.py` - Market data fetching

### Integration Tests (Slow - 5-30 minutes)
- `test_cli_integration.py` - End-to-end CLI workflows
- Parallel verification tests (10-100 agents)
- Market data integration tests
- Full verification pipeline tests

## Timeout Configuration

The project includes timeout configurations in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
timeout = 600  # 10 minutes default
addopts = ["--timeout=600"]
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests", 
    "unit: marks tests as unit tests",
]
```

### Individual Test Timeouts

Long-running tests have specific timeout markers:

```python
@pytest.mark.timeout(300)    # 5 minutes
@pytest.mark.timeout(900)    # 15 minutes  
@pytest.mark.timeout(1800)   # 30 minutes
```

## CI/CD Strategy

### Development (Fast feedback)
```bash
# Run during development (~1-2 minutes)
pytest -v -m "not slow" --timeout=300
```

### Pre-commit (Medium coverage)
```bash  
# Run before committing (~5 minutes)
pytest tests/test_cli.py tests/test_cli_integration.py::TestCLIIntegration::test_verify_command -v --timeout=600
```

### Full Integration (Complete coverage)
```bash
# Run for releases (~30 minutes)
pytest -v --timeout=1800
```

## Performance Testing

### Scaling Tests
```bash
# Test 10 agents (15 minutes)
pytest tests/test_cli_integration.py::TestParallelVerification::test_parallel_verification_10_agents -v --timeout=900

# Test 100 agents (30 minutes) 
pytest tests/test_cli_integration.py::TestParallelVerification::test_parallel_verification_100_agents -v --timeout=1800
```

### Resource Monitoring
```bash
# Monitor system resources during tests
pytest -v --timeout=1800 & 
top -pid $! -l 5
```

## Troubleshooting

### Timeout Issues
1. **Increase timeout**: Use `--timeout=X` where X is seconds
2. **Run subset**: Use `-m "not slow"` to skip long tests
3. **Parallel execution**: Use `-n auto` with pytest-xdist for speed

### Memory Issues  
1. **Monitor usage**: Check system memory during long tests
2. **Reduce concurrency**: Lower `max_concurrent` in test configs
3. **Clean resources**: Ensure Docker containers are cleaned up

### Docker Issues
1. **Check daemon**: Ensure Docker is running and accessible
2. **Clean images**: Run `docker system prune` before testing
3. **Resource limits**: Ensure adequate Docker memory allocation

## Coverage Reporting

```bash
# Run tests with coverage
pytest --cov=arc_verifier --cov-report=html --timeout=600

# View coverage report
open htmlcov/index.html
```

## Best Practices

1. **Use test markers**: Mark slow tests appropriately
2. **Set realistic timeouts**: Based on expected execution time  
3. **Clean resources**: Ensure tests clean up Docker containers
4. **Monitor performance**: Track test execution times
5. **Isolate failures**: Run failing tests individually with extended timeouts

## Example Commands

```bash
# Fast development cycle
pytest -v -x -m "not slow"

# Single test with debugging
pytest tests/test_cli_integration.py::TestCLIIntegration::test_verify_command -xvs --timeout=300

# Full suite for CI
pytest -v --timeout=1800 --maxfail=5

# Parallel execution (if pytest-xdist installed)
pytest -v -n auto --timeout=600 -m "not slow"
```