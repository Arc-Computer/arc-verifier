#!/bin/bash
# Test runner script with different timeout strategies

set -e

echo "🧪 Arc-Verifier Test Runner"
echo "=========================="

# Function to run tests with specific parameters
run_tests() {
    local test_type="$1"
    local timeout="$2"
    local markers="$3"
    local extra_args="$4"
    
    echo ""
    echo "🔄 Running $test_type tests (timeout: ${timeout}s)..."
    
    if [ -n "$markers" ]; then
        pytest -v --timeout="$timeout" -m "$markers" $extra_args
    else
        pytest -v --timeout="$timeout" $extra_args  
    fi
    
    echo "✅ $test_type tests completed"
}

# Parse command line arguments
case "${1:-fast}" in
    "fast")
        echo "Running fast unit tests only..."
        run_tests "Fast Unit" 120 "not slow" "tests/"
        ;;
    
    "integration") 
        echo "Running integration tests..."
        run_tests "Integration" 600 "" "tests/test_cli_integration.py"
        ;;
        
    "slow")
        echo "Running slow/scaling tests..."
        run_tests "Slow/Scaling" 1800 "slow" ""
        ;;
        
    "all")
        echo "Running complete test suite..."
        run_tests "Complete" 1800 "" "tests/"
        ;;
        
    "parallel")
        echo "Running parallel verification tests..."
        run_tests "Parallel Verification" 1800 "" "tests/test_cli_integration.py::TestParallelVerification"
        ;;
        
    "critical")
        echo "Running critical functionality tests..."
        run_tests "Critical" 300 "" "tests/test_cli.py tests/test_llm_judge.py tests/test_data_fetcher.py"
        ;;
        
    *)
        echo "Usage: $0 [fast|integration|slow|all|parallel|critical]"
        echo ""
        echo "Test categories:"
        echo "  fast        - Quick unit tests (~2 minutes)"
        echo "  integration - CLI integration tests (~10 minutes)"  
        echo "  slow        - Scaling/performance tests (~30 minutes)"
        echo "  all         - Complete test suite (~30 minutes)"
        echo "  parallel    - Parallel verification tests (~30 minutes)"
        echo "  critical    - Core functionality tests (~5 minutes)"
        echo ""
        echo "Examples:"
        echo "  $0 fast      # Quick development feedback"
        echo "  $0 critical  # Pre-commit validation"
        echo "  $0 all       # Full release validation"
        exit 1
        ;;
esac

echo ""
echo "🎉 Test execution completed successfully!"