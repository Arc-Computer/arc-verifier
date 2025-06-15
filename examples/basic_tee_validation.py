#!/usr/bin/env python3
"""
Basic TEE Validation Example

This example shows how to use arc-verifier's TEE validation
to verify agent containers in your own environment.
"""

import asyncio
from arc_verifier.tee import PhalaCloudValidator, CodeHashRegistry, TEEConfig


async def basic_validation_example():
    """Example of basic TEE validation workflow."""
    
    print("=== Basic TEE Validation Example ===\\n")
    
    # 1. Create configuration for development
    config = TEEConfig(
        auto_register_local_images=True,
        allow_simulation_mode=True,
        allow_arm64_development=True,
        strict_architecture_check=False
    )
    
    # 2. Initialize TEE validator with config
    validator = PhalaCloudValidator(config=config)
    
    # 3. List of agents to validate (replace with your own)
    test_agents = [
        "my-trading-agent:latest",
        "my-analytics-agent:v1.0.0", 
        "python:3.9-slim"  # This will show how non-agent images are handled
    ]
    
    print("🔐 Validating agents...")
    
    for agent_image in test_agents:
        print(f"\\n--- Validating {agent_image} ---")
        
        try:
            # Validate the agent
            result = await validator.validate(agent_image)
            
            # Display results
            status = "✅ VALID" if result.is_valid else "❌ INVALID"
            print(f"Status: {status}")
            print(f"Trust Level: {result.trust_level}")
            print(f"Platform: {result.platform.value}")
            print(f"Code Hash: {result.code_hash[:16]}...")
            
            if result.measurements:
                print("Key Measurements:")
                for key in ['mr_td', 'mr_seam', 'rtmr3']:
                    if key in result.measurements:
                        value = result.measurements[key]
                        print(f"  {key}: {value[:16]}...")
            
            if result.warnings:
                print("⚠️  Warnings:")
                for warning in result.warnings:
                    print(f"  • {warning}")
                    
            if result.errors:
                print("❌ Errors:")
                for error in result.errors:
                    print(f"  • {error}")
                    
        except Exception as e:
            print(f"❌ Validation failed: {e}")
    
    await validator.close()
    print("\\n✅ Validation complete!")


async def registry_management_example():
    """Example of agent registry management."""
    
    print("\\n=== Agent Registry Management Example ===\\n")
    
    # 1. Initialize registry with auto-discovery
    config = TEEConfig(auto_register_local_images=True)
    registry = CodeHashRegistry(config=config)
    
    # 2. List all registered agents
    agents = registry.list_agents()
    print(f"📋 Found {len(agents)} registered agents:")
    
    for agent in agents:
        print(f"  • {agent.agent_name} ({agent.image_tag})")
        print(f"    Status: {agent.status.value}")
        print(f"    Risk: {agent.risk_level}")
        print(f"    Hash: {agent.code_hash[:16]}...")
        print()
    
    # 3. Add a custom agent (example - this won't work without the actual image)
    print("➕ Adding custom agent example...")
    
    from arc_verifier.tee import ApprovedAgent, AgentStatus
    from datetime import datetime
    
    # Calculate hash for a hypothetical agent
    example_hash = registry.calculate_code_hash("my-custom-agent:v1.0.0")
    
    custom_agent = ApprovedAgent(
        code_hash=example_hash,
        image_tag="my-custom-agent:v1.0.0",
        agent_name="My Custom Trading Agent",
        description="Custom agent for DeFi trading strategies",
        status=AgentStatus.PENDING,
        approved_date=datetime.now(),
        risk_level="medium",
        capabilities=["trading", "defi", "analytics"],
        metadata={
            "version": "1.0.0",
            "author": "example-developer",
            "max_position_size": "10000"
        }
    )
    
    # Add to registry
    if registry.add_agent(custom_agent):
        print(f"✅ Added custom agent: {custom_agent.agent_name}")
    else:
        print("❌ Failed to add custom agent")
    
    # 4. Verify an agent
    print("\\n🔍 Verifying agent...")
    test_hash = example_hash
    is_approved, agent_info, warnings = registry.verify_code_hash(test_hash)
    
    print(f"Hash: {test_hash[:16]}...")
    print(f"Approved: {'✅ YES' if is_approved else '❌ NO'}")
    
    if agent_info:
        print(f"Agent: {agent_info.agent_name}")
        print(f"Risk Level: {agent_info.risk_level}")
        print(f"Capabilities: {', '.join(agent_info.capabilities)}")
    
    if warnings:
        print("⚠️  Warnings:")
        for warning in warnings:
            print(f"  • {warning}")


def configuration_example():
    """Example of different configuration scenarios."""
    
    print("\\n=== Configuration Examples ===\\n")
    
    # Development configuration
    dev_config = TEEConfig(
        auto_register_local_images=True,
        allow_simulation_mode=True,
        allow_arm64_development=True,
        strict_architecture_check=False,
        default_trust_level="LOW"
    )
    
    print("🧪 Development Configuration:")
    print(f"  • Auto-register local images: {dev_config.auto_register_local_images}")
    print(f"  • Allow simulation mode: {dev_config.allow_simulation_mode}")
    print(f"  • Allow ARM64 development: {dev_config.allow_arm64_development}")
    print(f"  • Strict architecture check: {dev_config.strict_architecture_check}")
    
    # Production configuration  
    prod_config = TEEConfig(
        auto_register_local_images=False,
        allow_simulation_mode=False,
        allow_arm64_development=False,
        strict_architecture_check=True,
        default_trust_level="UNTRUSTED",
        intel_root_ca_path="/etc/ssl/certs/intel_root_ca.pem",
        custom_ca_paths=["/etc/ssl/certs/company_ca.pem"]
    )
    
    print("\\n🏭 Production Configuration:")
    print(f"  • Auto-register local images: {prod_config.auto_register_local_images}")
    print(f"  • Allow simulation mode: {prod_config.allow_simulation_mode}")
    print(f"  • Allow ARM64 development: {prod_config.allow_arm64_development}")
    print(f"  • Strict architecture check: {prod_config.strict_architecture_check}")
    print(f"  • Intel Root CA: {prod_config.intel_root_ca_path}")
    
    # Save example configurations
    from arc_verifier.tee.config import save_config
    
    dev_path = "example_dev_config.json"
    prod_path = "example_prod_config.json"
    
    if save_config(dev_config, dev_path):
        print(f"\\n💾 Saved development config to: {dev_path}")
    
    if save_config(prod_config, prod_path):
        print(f"💾 Saved production config to: {prod_path}")


async def main():
    """Run all examples."""
    
    print("🚀 Arc-Verifier TEE Validation Examples")
    print("=" * 50)
    
    # Run examples
    await basic_validation_example()
    await registry_management_example()
    configuration_example()
    
    print("\\n🎉 All examples completed!")
    print("\\nNext steps:")
    print("1. Customize the configuration for your environment")
    print("2. Add your own agent images to the registry")
    print("3. Integrate TEE validation into your deployment pipeline")
    print("4. See docs/TEE_SETUP_GUIDE.md for detailed setup instructions")


if __name__ == "__main__":
    asyncio.run(main())