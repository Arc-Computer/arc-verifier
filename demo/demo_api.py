#!/usr/bin/env python3
"""
Demo of Arc-Verifier Programmatic API
"""
import asyncio
from arc_verifier import api

async def verify_my_agents():
    # Single agent verification
    result = await api.verify_agent(
        "sample-trading-agent:latest",
        tier="high",
        enable_llm=True
    )
    
    print(f"Fort Score: {result.fort_score}/180")
    if hasattr(result, 'recommendations') and result.recommendations:
        print("Recommendations:")
        for rec in result.recommendations:
            print(f"  - {rec}")
    
    # Access detailed results
    if hasattr(result, 'security') and hasattr(result.security, 'vulnerabilities'):
        vulns = result.security.vulnerabilities
        if vulns:
            print("Security issues found:")
            for vuln in vulns[:5]:  # Show first 5
                print(f"  - {vuln.cve_id}: {vuln.severity}")
    
    # Batch verification
    agents = ["sample-trading-agent:latest", "arbitrage-agent:latest", "market-maker:prod"]
    results = await api.verify_batch(agents, max_concurrent=10)
    
    # Filter passing agents
    passing = [r for r in results if r.fort_score >= 120]
    print(f"Agents ready for deployment: {len(passing)}/{len(agents)}")

# Run the demo
if __name__ == "__main__":
    asyncio.run(verify_my_agents())