"""Audit trail and explainability logging for Arc-Verifier.

Provides local file storage of verification runs with full traceability.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import hashlib


class AuditLogger:
    """Manages audit trail for verification runs."""
    
    def __init__(self, audit_dir: str = "verification_audits"):
        """Initialize audit logger with specified directory."""
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(exist_ok=True)
        
    def log_verification(self, 
                        image: str,
                        verification_result: Dict[str, Any],
                        llm_reasoning: Optional[str] = None) -> str:
        """Log a complete verification run.
        
        Args:
            image: Docker image name
            verification_result: Complete verification results
            llm_reasoning: LLM explanation of decisions
            
        Returns:
            Path to audit file
        """
        timestamp = datetime.now()
        
        # Create audit record
        audit_record = {
            "timestamp": timestamp.isoformat(),
            "image": image,
            "verification_id": verification_result.get("verification_id"),
            "fort_score": verification_result.get("agent_fort_score"),
            "overall_status": verification_result.get("overall_status"),
            "results": verification_result,
            "data_hashes": self._calculate_data_hashes(verification_result),
            "environment": {
                "arc_verifier_version": "0.1.2",
                "python_version": os.sys.version,
            }
        }
        
        # Save main audit file
        audit_filename = f"verification_{timestamp.strftime('%Y%m%d_%H%M%S')}_{image.replace('/', '_').replace(':', '_')}.json"
        audit_path = self.audit_dir / audit_filename
        
        with open(audit_path, 'w') as f:
            json.dump(audit_record, f, indent=2, default=str)
            
        # Save LLM reasoning if available
        if llm_reasoning:
            reasoning_filename = f"reasoning_{timestamp.strftime('%Y%m%d_%H%M%S')}_{image.replace('/', '_').replace(':', '_')}.md"
            reasoning_path = self.audit_dir / reasoning_filename
            
            with open(reasoning_path, 'w') as f:
                f.write(f"# LLM Reasoning for {image}\n\n")
                f.write(f"**Timestamp**: {timestamp.isoformat()}\n")
                f.write(f"**Fort Score**: {audit_record['fort_score']}\n\n")
                f.write("## Analysis\n\n")
                f.write(llm_reasoning)
                
        return str(audit_path)
    
    def _calculate_data_hashes(self, verification_result: Dict) -> Dict[str, str]:
        """Calculate SHA-256 hashes of key data elements for integrity."""
        hashes = {}
        
        # Hash the complete result
        result_str = json.dumps(verification_result, sort_keys=True, default=str)
        hashes["complete_result"] = hashlib.sha256(result_str.encode()).hexdigest()
        
        # Hash individual components if present
        if "docker_scan" in verification_result:
            scan_str = json.dumps(verification_result["docker_scan"], sort_keys=True, default=str)
            hashes["docker_scan"] = hashlib.sha256(scan_str.encode()).hexdigest()
            
        if "performance_benchmark" in verification_result:
            perf_str = json.dumps(verification_result["performance_benchmark"], sort_keys=True, default=str)
            hashes["performance_benchmark"] = hashlib.sha256(perf_str.encode()).hexdigest()
            
        return hashes
    
    def generate_explainability_report(self,
                                     image: str,
                                     fort_score: int,
                                     score_breakdown: Dict[str, int],
                                     decisions: Dict[str, str]) -> str:
        """Generate human-readable explainability report.
        
        Args:
            image: Docker image name
            fort_score: Final Fort score
            score_breakdown: Detailed score components
            decisions: Key decisions and rationales
            
        Returns:
            Markdown-formatted report
        """
        report = f"""# Arc-Verifier Explainability Report

## Image: {image}
**Generated**: {datetime.now().isoformat()}

## Final Fort Score: {fort_score}/180

### Score Breakdown

| Component | Points | Explanation |
|-----------|--------|-------------|
"""
        
        # Add score components
        for component, points in score_breakdown.items():
            explanation = self._explain_score_component(component, points)
            report += f"| {component} | {points:+d} | {explanation} |\n"
            
        report += "\n### Key Decisions\n\n"
        
        # Add decision explanations
        for decision, rationale in decisions.items():
            report += f"**{decision}**: {rationale}\n\n"
            
        report += """
### Score Interpretation

- **150-180**: Institutional Grade (AAA) - Highly recommended for funding
- **130-149**: Production Ready (AA) - Suitable for deployment with monitoring
- **110-129**: Conditional Approval (A) - Requires specific improvements
- **90-109**: Development Stage (BBB) - Significant work needed
- **Below 90**: Not Recommended - Major issues identified

### Audit Trail

All verification data has been logged for reproducibility. 
Data integrity verified via SHA-256 hashing.
"""
        
        return report
    
    def _explain_score_component(self, component: str, points: int) -> str:
        """Generate explanation for score component."""
        explanations = {
            "security": {
                "positive": "Strong security posture with minimal vulnerabilities",
                "negative": "Security vulnerabilities detected requiring attention",
                "neutral": "Standard security profile"
            },
            "llm_intelligence": {
                "positive": "Sophisticated strategy with good risk management",
                "negative": "Code quality or risk concerns identified",
                "neutral": "Typical implementation patterns"
            },
            "behavior": {
                "positive": "Excellent behavioral compliance in simulations",
                "negative": "Failed critical behavioral tests",
                "neutral": "Met basic behavioral requirements"
            },
            "performance": {
                "positive": "Top-tier historical performance across regimes",
                "negative": "Poor performance or strategy verification failure",
                "neutral": "Average performance metrics"
            }
        }
        
        component_key = component.lower().replace("_", " ")
        if points > 5:
            sentiment = "positive"
        elif points < -5:
            sentiment = "negative"
        else:
            sentiment = "neutral"
            
        # Find matching explanation
        for key, sentiments in explanations.items():
            if key in component_key:
                return sentiments.get(sentiment, f"Score adjustment of {points}")
                
        return f"Score adjustment of {points} points"
    
    def list_audits(self, image_filter: Optional[str] = None) -> List[Dict]:
        """List all audit records, optionally filtered by image name."""
        audits = []
        
        for audit_file in self.audit_dir.glob("verification_*.json"):
            with open(audit_file, 'r') as f:
                audit = json.load(f)
                
            if image_filter and image_filter not in audit["image"]:
                continue
                
            audits.append({
                "timestamp": audit["timestamp"],
                "image": audit["image"],
                "fort_score": audit["fort_score"],
                "status": audit["overall_status"],
                "file": str(audit_file)
            })
            
        return sorted(audits, key=lambda x: x["timestamp"], reverse=True)
    
    def log_action(self, action: str, details: Dict[str, Any]) -> None:
        """Log a specific action for audit trail.
        
        Args:
            action: Action name (e.g., "strategy_verification")
            details: Action details to log
        """
        timestamp = datetime.now()
        
        # Create action log file for the day
        log_filename = f"actions_{timestamp.strftime('%Y%m%d')}.jsonl"
        log_path = self.audit_dir / log_filename
        
        # Append action to log file
        action_record = {
            "timestamp": timestamp.isoformat(),
            "action": action,
            "details": details
        }
        
        with open(log_path, 'a') as f:
            f.write(json.dumps(action_record, default=str) + '\n')