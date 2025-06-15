#!/usr/bin/env python3
"""Test LLM API integration directly."""

import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from arc_verifier.llm_judge import LLMJudge, LLMProvider
from datetime import datetime

def test_llm_api():
    """Test LLM API calls."""
    print("Testing LLM API Integration")
    print("=" * 50)
    
    # Check for API keys
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    print(f"Anthropic API Key: {'✓ Found' if anthropic_key else '✗ Not found'}")
    print(f"OpenAI API Key: {'✓ Found' if openai_key else '✗ Not found'}")
    print()
    
    # Initialize LLM Judge
    print("Initializing LLM Judge...")
    judge = LLMJudge(
        primary_provider=LLMProvider.ANTHROPIC if anthropic_key else LLMProvider.OPENAI,
        enable_ensemble=False  # Single provider for testing
    )
    
    # Create test image data
    test_image_data = {
        "image_tag": "test-shade-agent:v2",
        "size": 80 * 1024 * 1024,  # 80MB
        "layers": [
            {"command": "RUN npm install -g web3 ethers axios", "size": 50 * 1024 * 1024},
            {"command": "ENV SHADE_API_KEY=placeholder", "size": 1024},
            {"command": "LABEL shade.agent=true", "size": 512}
        ],
        "shade_agent_detected": True,
        "vulnerabilities": [
            {"severity": "HIGH", "cveId": "CVE-2023-1234", "package": "node"},
            {"severity": "LOW", "cveId": "CVE-2023-5678", "package": "npm"}
        ],
        "timestamp": datetime.now()
    }
    
    # Run evaluation
    print("\nRunning LLM evaluation...")
    print("This may take 10-30 seconds depending on API response time...")
    
    try:
        result = judge.evaluate_agent(
            image_data=test_image_data,
            market_context={"tier": "high", "timestamp": datetime.now().isoformat()}
        )
        
        print("\n✓ LLM Evaluation Successful!")
        print("\nResults:")
        print(f"- Strategy: {result.intent_classification.primary_strategy}")
        print(f"- Risk Profile: {result.intent_classification.risk_profile}")
        print(f"- Confidence: {result.confidence_level:.0%}")
        print(f"- Code Quality: {result.code_quality.overall_score:.2f}/1.0")
        
        if result.behavioral_flags:
            print(f"\nBehavioral Flags:")
            for flag in result.behavioral_flags:
                print(f"  - {flag}")
        
        if result.score_adjustments:
            print(f"\nScore Adjustments:")
            for category, adjustment in result.score_adjustments.items():
                print(f"  - {category}: {adjustment:+.1f}")
        
        print(f"\nReasoning:")
        print(f"{result.reasoning[:200]}..." if len(result.reasoning) > 200 else result.reasoning)
        
        return True
        
    except Exception as e:
        print(f"\n✗ LLM Evaluation Failed: {e}")
        print("\nThis likely means:")
        print("1. API keys are not set correctly in .env")
        print("2. API endpoint is unreachable")
        print("3. Invalid API key or insufficient credits")
        return False

if __name__ == "__main__":
    # Load .env file if it exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✓ Loaded .env file")
    except ImportError:
        print("⚠ python-dotenv not available, using system environment")
    
    print()
    success = test_llm_api()
    sys.exit(0 if success else 1)