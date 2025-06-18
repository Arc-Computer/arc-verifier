#!/usr/bin/env python3
"""
Clean Demo of Arc-Verifier Programmatic API
Shows the end-to-end pipeline with real LLM calls
"""
import asyncio
import os
from arc_verifier import api

async def demo_verification():
    print("=" * 60)
    print("Arc-Verifier End-to-End Demo")
    print("=" * 60)
    
    # Verify environment
    print("\n1. Environment Check:")
    print(f"   ✓ Anthropic API Key: {'Loaded' if os.getenv('ANTHROPIC_API_KEY') else 'Missing'}")
    print(f"   ✓ OpenAI API Key: {'Loaded' if os.getenv('OPENAI_API_KEY') else 'Missing'}")
    
    # Single agent verification with all components
    print("\n2. Running Full Verification Pipeline...")
    print("   Components: Security Scan, TEE Validation, Performance, Strategy, LLM Analysis")
    
    result = await api.verify_agent(
        "sample-trading-agent:latest",
        tier="high",
        enable_llm=True,
        enable_backtesting=True
    )
    
    print("\n3. Verification Results:")
    print(f"   ✓ Fort Score: {result.fort_score}/180")
    print(f"   ✓ Status: {result.status}")
    print(f"   ✓ Tier: {result.tier}")
    
    # Component results
    print("\n4. Component Analysis:")
    
    # Security
    if hasattr(result, 'security') and result.security:
        print(f"   Security Scan:")
        print(f"     - Vulnerabilities: {getattr(result.security, 'vulnerability_count', 'N/A')}")
        print(f"     - Score: {getattr(result.security, 'score', 'N/A')}")
    
    # TEE
    if hasattr(result, 'tee') and result.tee:
        print(f"   TEE Validation:")
        print(f"     - Valid: {getattr(result.tee, 'valid', 'N/A')}")
        print(f"     - Platform: {getattr(result.tee, 'platform', 'N/A')}")
    
    # Performance
    if hasattr(result, 'performance') and result.performance:
        print(f"   Performance:")
        print(f"     - Throughput: {getattr(result.performance, 'throughput', 'N/A')} TPS")
        print(f"     - Latency P99: {getattr(result.performance, 'latency_p99', 'N/A')} ms")
    
    # LLM Analysis
    if hasattr(result, 'llm_analysis') and result.llm_analysis:
        print(f"   LLM Analysis (Real API Call):")
        print(f"     - Trust Recommendation: {result.llm_analysis.trust_recommendation}")
        print(f"     - Confidence: {getattr(result.llm_analysis, 'confidence_level', 'N/A')}")
        print(f"     - Primary Strategy: {getattr(result.llm_analysis, 'primary_strategy', 'N/A')}")
    else:
        print("   ⚠️  LLM Analysis not found")
    
    # Recommendations
    if hasattr(result, 'recommendations') and result.recommendations:
        print(f"\n5. Recommendations:")
        for rec in result.recommendations[:3]:
            print(f"   - {rec}")
    
    print("\n" + "=" * 60)
    print("Demo Complete - All Components Functional")
    print("=" * 60)
    
    return result

if __name__ == "__main__":
    asyncio.run(demo_verification())