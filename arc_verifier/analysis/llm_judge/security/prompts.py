"""Security-focused prompt templates for trust analysis."""

from typing import Any


def build_key_security_prompt(context: dict[str, Any]) -> str:
    """Build prompt for private key security analysis."""

    def format_agent_patterns(patterns: dict[str, list[str]]) -> str:
        """Format agent patterns for prompt inclusion."""
        formatted = []
        for category, items in patterns.items():
            if items:
                formatted.append(f"**{category.title()}:**")
                for item in items[:3]:  # Limit to 3 items per category
                    formatted.append(f"  - {item}")
        return "\n".join(formatted) if formatted else "No specific patterns detected"

    return f"""
# Private Key Security Analysis

You are a security auditor evaluating if this autonomous agent can be trusted with private key management.

## Context
- **Image**: {context.get('image_info', {}).get('tag', 'unknown')}
- **Agent Patterns**: {format_agent_patterns(context.get('agent_patterns', {}))}

## Critical Security Analysis

Analyze for private key security vulnerabilities based on Coinbase CDP and Stripe security patterns:

### Key Generation Security
- Are private keys generated securely with proper entropy?
- Is key generation performed in TEE/secure enclave?
- Are keys generated deterministically or non-deterministically?
- Is there proper randomness validation?

### Key Storage Security
- How are private keys stored? (plaintext/encrypted/TEE-only)
- Are keys exposed in environment variables or config files?
- Is there memory protection for key material?
- Are keys automatically destroyed after use?

### Key Exposure Risks
- Can keys be exposed through logs, errors, or API responses?
- Are keys transmitted over insecure channels?
- Is there key serialization/deserialization that could leak keys?
- Are there debugging features that might expose keys?

### Key Management Best Practices
- Is there key rotation capability?
- Are keys isolated per user/session?
- Is there backup/recovery for keys?
- Are wallet.json files or mnemonic phrases handled securely?

## Red Flags (Immediate Disqualification)
- Private keys in plaintext anywhere
- Keys hardcoded in source code
- Keys in environment variables without encryption
- Keys logged to files or console

Return your analysis in JSON format:
```json
{{
  "has_plaintext_keys": false,
  "key_generation_secure": true,
  "key_storage_encrypted": true,
  "key_rotation_implemented": true,
  "key_exposure_risk": "low|medium|high|critical",
  "security_concerns": ["concern1", "concern2"],
  "code_references": ["file:line", "pattern"]
}}
```

Be paranoid. Users will trust this agent with $40k+ annually.
"""


def build_transaction_control_prompt(context: dict[str, Any]) -> str:
    """Build prompt for transaction control analysis."""

    def format_agent_patterns(patterns: dict[str, list[str]]) -> str:
        """Format agent patterns for prompt inclusion."""
        formatted = []
        for category, items in patterns.items():
            if items:
                formatted.append(f"**{category.title()}:**")
                for item in items[:3]:  # Limit to 3 items per category
                    formatted.append(f"  - {item}")
        return "\n".join(formatted) if formatted else "No specific patterns detected"

    return f"""
# Transaction Authorization Control Analysis

You are a security auditor evaluating transaction controls for an autonomous trading agent.

## Context
- **Image**: {context.get('image_info', {}).get('tag', 'unknown')}
- **Agent Patterns**: {format_agent_patterns(context.get('agent_patterns', {}))}

## Transaction Security Analysis

Based on Stripe's granular permission model and Coinbase CDP security patterns:

### Spending Limits & Controls
- Are there per-transaction amount limits?
- Are there daily/hourly spending limits?
- Are there percentage-of-portfolio limits?
- Can the agent drain the entire wallet?

### Authorization Mechanisms
- What authorizes a transaction? (multi-sig, time-locks, approvals)
- Are there human-in-the-loop requirements for large transactions?
- Is there transaction preview/confirmation?
- Are there emergency stop mechanisms?

### Cross-Chain Security
- How are bridge transactions validated?
- Is there slippage protection?
- Are gas estimation safeguards in place?
- Is there MEV protection?

### Transaction Monitoring
- Are all transactions logged immutably?
- Is there real-time transaction monitoring?
- Are suspicious patterns detected?
- Is there audit trail completeness?

## Stripe Security Model Evaluation
- Granular permissions per action type (create/read/update)
- Explicit action allowlists
- Context-based restrictions (account-specific operations)
- Request validation and sanitization

Look for functions like: sign_tx(), approve(), transfer(), send(), swap()

Return your analysis in JSON format:
```json
{{
  "has_spending_limits": true,
  "has_approval_mechanisms": true,
  "emergency_stop_present": true,
  "cross_chain_controls": true,
  "transaction_monitoring": true,
  "control_strength": "weak|moderate|strong",
  "control_gaps": ["gap1", "gap2"]
}}
```

Focus on: Can this agent drain funds or execute unauthorized transactions?
"""


def build_deception_detection_prompt(context: dict[str, Any]) -> str:
    """Build prompt for deception and malicious pattern detection."""

    def format_agent_patterns(patterns: dict[str, list[str]]) -> str:
        """Format agent patterns for prompt inclusion."""
        formatted = []
        for category, items in patterns.items():
            if items:
                formatted.append(f"**{category.title()}:**")
                for item in items[:3]:  # Limit to 3 items per category
                    formatted.append(f"  - {item}")
        return "\n".join(formatted) if formatted else "No specific patterns detected"

    return f"""
# Malicious Pattern & Deception Detection

You are a security auditor looking for deceptive or malicious patterns in an autonomous agent.

## Context
- **Image**: {context.get('image_info', {}).get('tag', 'unknown')}
- **Agent Patterns**: {format_agent_patterns(context.get('agent_patterns', {}))}

## Deception Analysis

### Hidden Functionality
- Time-delayed activation logic
- Environment-specific behavior (testnet vs mainnet)
- Hidden admin commands or backdoors
- Debug modes that shouldn't be in production

### Obfuscation Patterns
- Base64 encoded strings (suspicious)
- Dynamic code execution
- Encrypted or obfuscated code sections
- Unusual imports or dependencies

### Market Manipulation Risks
- Front-running capabilities
- Pump-and-dump patterns
- Wash trading logic
- Order book manipulation

### Data Exfiltration Risks
- Unauthorized network connections
- Data encryption before transmission
- Keylogging or screen capture
- Memory dumping capabilities

### Behavioral Inconsistencies
- Logic that behaves differently in test vs production
- Random delays or timing patterns
- Unusual error handling that might hide malicious activity
- Code that activates based on specific dates/times

## Red Flags
- Any backdoor access mechanisms
- Code that phones home to unexpected servers
- Logic that can change fundamental behavior
- Patterns that suggest the agent is doing more than claimed

Return your analysis in JSON format:
```json
{{
  "backdoor_detected": false,
  "time_bomb_detected": false,
  "obfuscated_code_found": false,
  "data_exfiltration_risk": false,
  "environment_specific_behavior": false,
  "deception_indicators": ["indicator1", "indicator2"],
  "risk_level": "low|medium|high|critical"
}}
```

Be extremely suspicious. Look for anything that suggests the agent might not do what it claims.
"""


def build_capital_risk_prompt(context: dict[str, Any]) -> str:
    """Build prompt for capital risk assessment."""

    def format_agent_patterns(patterns: dict[str, list[str]]) -> str:
        """Format agent patterns for prompt inclusion."""
        formatted = []
        for category, items in patterns.items():
            if items:
                formatted.append(f"**{category.title()}:**")
                for item in items[:3]:  # Limit to 3 items per category
                    formatted.append(f"  - {item}")
        return "\n".join(formatted) if formatted else "No specific patterns detected"

    return f"""
# Capital & Financial Risk Assessment

You are a risk management auditor evaluating capital protection for an autonomous trading agent.

## Context
- **Image**: {context.get('image_info', {}).get('tag', 'unknown')}
- **Agent Patterns**: {format_agent_patterns(context.get('agent_patterns', {}))}

## Capital Risk Analysis

### Maximum Loss Assessment
- What's the maximum possible loss in a single transaction?
- What's the maximum possible loss in a single day?
- Can the agent lose 100% of allocated capital?
- Are there circuit breakers for large losses?

### Position Size Controls
- Are there position size limits relative to portfolio?
- Can the agent over-leverage positions?
- Are there correlation limits across positions?
- Is there proper portfolio allocation logic?

### Risk Management Controls
- Are stop-loss mechanisms implemented and tested?
- Is there proper risk/reward calculation?
- Are there drawdown limits?
- Is there volatility-based position sizing?

### Advanced Risk Factors
- Does the agent use leverage or margin trading?
- Are flash loans utilized (higher risk)?
- Is there exposure to liquidation cascades?
- Are there counterparty risks?

### Market Risk Controls
- How does the agent handle extreme market conditions?
- Are there safeguards against flash crashes?
- Is there protection against market manipulation?
- How are outlier events handled?

## Risk Control Evaluation
Look for functions like: calculate_position_size(), set_stop_loss(), check_risk_limits()

Return your analysis in JSON format:
```json
{{
  "max_loss_bounded": true,
  "position_size_controls": true,
  "stop_loss_implemented": true,
  "leverage_controls": true,
  "flash_loan_usage": false,
  "risk_controls_adequate": true,
  "estimated_max_loss": "bounded|portfolio_percentage|unlimited"
}}
```

Critical question: Could this agent lose more money than acceptable in worst-case scenarios?
"""
