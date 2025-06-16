"""Arc-Verifier Web UI module.

This module provides a polished web interface for viewing verification results,
analyzing trends, and understanding agent performance across all metrics.
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

from ..security import AuditLogger
from ..api import verify_agent, verify_batch
from ..models import VerificationResult, BatchVerificationResult


def create_app(config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    CORS(app)
    
    if config:
        app.config.update(config)
    
    # Initialize services
    audit_logger = AuditLogger()
    
    @app.route('/')
    def index():
        """Main dashboard view."""
        return render_template('index.html')
    
    @app.route('/verification/<verification_id>')
    def verification_detail(verification_id):
        """Detailed verification view."""
        return render_template('verification.html')
    
    @app.route('/api/verifications')
    def list_verifications():
        """List all verification results with pagination."""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        audits = audit_logger.list_audits()
        
        # Pagination
        start = (page - 1) * per_page
        end = start + per_page
        paginated = audits[start:end]
        
        # Load full results
        results = []
        for audit in paginated:
            try:
                with open(audit['file'], 'r') as f:
                    data = json.load(f)
                    results.append({
                        'verification_id': audit.get('verification_id'),
                        'image': audit['image'],
                        'timestamp': audit['timestamp'],
                        'fort_score': data.get('fort_score', data.get('agent_fort_score', 0)),
                        'status': data.get('overall_status', 'UNKNOWN'),
                        'tier': audit.get('tier', 'medium')
                    })
            except Exception as e:
                print(f"Error loading audit: {e}")
        
        return jsonify({
            'results': results,
            'total': len(audits),
            'page': page,
            'per_page': per_page,
            'pages': (len(audits) + per_page - 1) // per_page
        })
    
    @app.route('/api/verification/<verification_id>')
    def get_verification(verification_id):
        """Get detailed verification result."""
        # Find verification
        for audit in audit_logger.list_audits():
            if audit.get('verification_id') == verification_id:
                try:
                    with open(audit['file'], 'r') as f:
                        data = json.load(f)
                        return jsonify(_transform_verification_data(data))
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
        
        return jsonify({'error': 'Verification not found'}), 404
    
    @app.route('/api/statistics')
    def get_statistics():
        """Get aggregate statistics across all verifications."""
        audits = audit_logger.list_audits()
        
        if not audits:
            return jsonify({
                'total_verifications': 0,
                'average_fort_score': 0,
                'pass_rate': 0,
                'by_status': {},
                'by_tier': {},
                'recent_trends': []
            })
        
        # Load all results for statistics
        fort_scores = []
        statuses = {'PASSED': 0, 'WARNING': 0, 'FAILED': 0}
        tiers = {'high': 0, 'medium': 0, 'low': 0}
        
        for audit in audits[:100]:  # Limit to recent 100
            try:
                with open(audit['file'], 'r') as f:
                    data = json.load(f)
                    score = data.get('fort_score', data.get('agent_fort_score', 0))
                    fort_scores.append(score)
                    
                    # Status counts
                    status = 'PASSED' if score >= 150 else 'WARNING' if score >= 120 else 'FAILED'
                    statuses[status] += 1
                    
                    # Tier counts
                    tier = audit.get('tier', 'medium')
                    if tier in tiers:
                        tiers[tier] += 1
            except:
                pass
        
        # Calculate trends (last 30 verifications)
        recent_trends = []
        for audit in audits[:30]:
            try:
                with open(audit['file'], 'r') as f:
                    data = json.load(f)
                    recent_trends.append({
                        'timestamp': audit['timestamp'],
                        'fort_score': data.get('fort_score', data.get('agent_fort_score', 0))
                    })
            except:
                pass
        
        return jsonify({
            'total_verifications': len(audits),
            'average_fort_score': sum(fort_scores) / len(fort_scores) if fort_scores else 0,
            'pass_rate': (statuses['PASSED'] / len(fort_scores) * 100) if fort_scores else 0,
            'by_status': statuses,
            'by_tier': tiers,
            'recent_trends': recent_trends
        })
    
    @app.route('/api/metrics')
    def get_metrics():
        """Get detailed metrics breakdown."""
        audits = audit_logger.list_audits()
        
        # Aggregate metrics across all components
        security_scores = []
        performance_scores = []
        strategy_scores = []
        trust_scores = []
        vulnerability_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        
        for audit in audits[:50]:  # Recent 50
            try:
                with open(audit['file'], 'r') as f:
                    data = json.load(f)
                    
                    # Security metrics
                    if 'docker_scan' in data:
                        scan = data['docker_scan']
                        security_scores.append(scan.get('security_score', 0))
                        
                        # Count vulnerabilities
                        vulns = scan.get('vulnerabilities', [])
                        if isinstance(vulns, list):
                            for v in vulns:
                                sev = v.get('severity', 'LOW')
                                if sev in vulnerability_counts:
                                    vulnerability_counts[sev] += 1
                    
                    # Performance metrics
                    if 'performance_benchmark' in data:
                        perf = data['performance_benchmark']
                        performance_scores.append(perf.get('performance_score', 0))
                    
                    # Strategy metrics
                    if 'strategy_verification' in data:
                        strat = data['strategy_verification']
                        strategy_scores.append(strat.get('strategy_effectiveness', 0))
                    
                    # Trust metrics
                    if 'llm_analysis' in data:
                        llm = data['llm_analysis']
                        trust_scores.append(llm.get('trust_score', 0))
            except:
                pass
        
        return jsonify({
            'security': {
                'average_score': sum(security_scores) / len(security_scores) if security_scores else 0,
                'vulnerability_distribution': vulnerability_counts,
                'total_vulnerabilities': sum(vulnerability_counts.values())
            },
            'performance': {
                'average_score': sum(performance_scores) / len(performance_scores) if performance_scores else 0,
                'score_distribution': _calculate_distribution(performance_scores)
            },
            'strategy': {
                'average_score': sum(strategy_scores) / len(strategy_scores) if strategy_scores else 0,
                'score_distribution': _calculate_distribution(strategy_scores)
            },
            'trust': {
                'average_score': sum(trust_scores) / len(trust_scores) if trust_scores else 0,
                'score_distribution': _calculate_distribution(trust_scores)
            }
        })
    
    @app.route('/api/agents')
    def list_agents():
        """List unique agents that have been verified."""
        audits = audit_logger.list_audits()
        
        agents = {}
        for audit in audits:
            image = audit['image']
            if image not in agents:
                agents[image] = {
                    'image': image,
                    'verifications': 0,
                    'latest_score': 0,
                    'average_score': 0,
                    'scores': []
                }
            
            try:
                with open(audit['file'], 'r') as f:
                    data = json.load(f)
                    score = data.get('fort_score', data.get('agent_fort_score', 0))
                    agents[image]['scores'].append(score)
                    agents[image]['verifications'] += 1
                    agents[image]['latest_score'] = score
            except:
                pass
        
        # Calculate averages
        for agent in agents.values():
            if agent['scores']:
                agent['average_score'] = sum(agent['scores']) / len(agent['scores'])
            del agent['scores']  # Remove raw scores from response
        
        return jsonify(list(agents.values()))
    
    @app.route('/api/verify', methods=['POST'])
    def verify_agent_endpoint():
        """Run a new verification via the API."""
        data = request.json
        image = data.get('image')
        
        if not image:
            return jsonify({'error': 'Image parameter required'}), 400
        
        try:
            # Run verification asynchronously
            import asyncio
            result = asyncio.run(verify_agent(
                image,
                enable_llm=data.get('enable_llm', True),
                enable_backtesting=data.get('enable_backtesting', True),
                tier=data.get('tier', 'medium')
            ))
            
            return jsonify({
                'verification_id': result.verification_id,
                'fort_score': result.fort_score,
                'status': result.status.value,
                'message': 'Verification completed successfully'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def _transform_verification_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw verification data for web display."""
        # Extract results from various possible locations
        if 'results' in data:
            result = data['results']
        elif 'verification_result' in data:
            result = data['verification_result']
        else:
            result = data
        
        return {
            'verification_id': result.get('verification_id', 'unknown'),
            'image': result.get('image', 'unknown'),
            'timestamp': result.get('timestamp', datetime.now().isoformat()),
            'fort_score': result.get('fort_score', result.get('agent_fort_score', 0)),
            'status': result.get('overall_status', result.get('status', 'UNKNOWN')),
            'tier': result.get('tier', 'medium'),
            'processing_time': result.get('processing_time', 0),
            
            # Component results
            'security': result.get('docker_scan', {}),
            'performance': result.get('performance_benchmark', {}),
            'backtest': result.get('backtest_results', {}),
            'strategy': result.get('strategy_verification', {}),
            'tee': result.get('tee_attestation', {}),
            'llm_analysis': result.get('llm_analysis', {}),
            
            # Recommendations
            'warnings': result.get('warnings', []),
            'recommendations': result.get('recommendations', []),
            
            # Raw data for debugging
            'raw': result
        }
    
    def _calculate_distribution(scores: List[float]) -> Dict[str, int]:
        """Calculate score distribution for metrics."""
        if not scores:
            return {'0-30': 0, '31-60': 0, '61-90': 0, '91-120': 0, '121-150': 0, '151-180': 0}
        
        distribution = {'0-30': 0, '31-60': 0, '61-90': 0, '91-120': 0, '121-150': 0, '151-180': 0}
        for score in scores:
            if score <= 30:
                distribution['0-30'] += 1
            elif score <= 60:
                distribution['31-60'] += 1
            elif score <= 90:
                distribution['61-90'] += 1
            elif score <= 120:
                distribution['91-120'] += 1
            elif score <= 150:
                distribution['121-150'] += 1
            else:
                distribution['151-180'] += 1
        
        return distribution
    
    return app