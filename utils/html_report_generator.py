"""
HTML Report Generator - matches dashboard layout exactly
"""

from typing import Dict, Optional
import base64
import io


def generate_html_report(
    test_title: str,
    test_subject: str,
    analytics: Dict,
    ai_insights: Optional[Dict] = None
) -> str:
    """Generate HTML report matching dashboard."""
    
    stats = analytics['statistics']
    readiness = analytics['class_readiness']
    risk_stats = analytics['risk_classification']['stats']
    risk_data = analytics['risk_classification']
    topic_perf = analytics['topic_performance']
    
    # Readiness card colors
    if readiness['status'] == 'Exam Ready':
        readiness_bg = '#d4edda'
        readiness_border = '#28a745'
        readiness_emoji = '🟢'
    elif readiness['status'] == 'Borderline':
        readiness_bg = '#fff3cd'
        readiness_border = '#ffc107'
        readiness_emoji = '🟡'
    else:
        readiness_bg = '#f8d7da'
        readiness_border = '#dc3545'
        readiness_emoji = '🔴'
    
    # Topic rows
    topic_rows = ""
    for topic, stats_data in sorted(topic_perf.items(), key=lambda x: x[1]['accuracy'], reverse=True):
        status = '🟢 Strong' if stats_data['accuracy'] >= 75 else ('🟡 Moderate' if stats_data['accuracy'] >= 60 else '🔴 Weak')
        topic_rows += f"""
        <tr>
            <td>{topic}</td>
            <td>{stats_data['accuracy']:.1f}%</td>
            <td>{stats_data['correct']}/{stats_data['total_attempts']}</td>
            <td>{status}</td>
        </tr>
        """
    
    # Student rows
    all_students = []
    for student in risk_data['high_risk']:
        all_students.append({'name': student['name'], 'percentage': student['percentage'], 'risk': '🔴 High Risk'})
    for student in risk_data['medium_risk']:
        all_students.append({'name': student['name'], 'percentage': student['percentage'], 'risk': '🟡 Medium Risk'})
    for student in risk_data['low_risk']:
        all_students.append({'name': student['name'], 'percentage': student['percentage'], 'risk': '🟢 Low Risk'})
    
    student_rows = ""
    for student in all_students:
        student_rows += f"""
        <tr>
            <td>{student['name']}</td>
            <td>{student['percentage']:.1f}%</td>
            <td>{student['risk']}</td>
        </tr>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Analytics Dashboard - {test_title}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: system-ui, -apple-system, sans-serif;
                background: #f8f9fa;
                padding: 2rem;
                color: #333;
            }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 2rem; border-radius: 12px; }}
            h1 {{ color: #0066cc; text-align: center; margin-bottom: 0.5rem; }}
            .subtitle {{ text-align: center; color: #666; margin-bottom: 2rem; }}
            .section {{ margin: 2rem 0; }}
            .section-title {{ font-size: 1.5rem; font-weight: bold; margin-bottom: 1rem; color: #333; }}
            
            /* Key Metrics */
            .metrics-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; }}
            .metric-card {{ background: white; border: 1px solid #dee2e6; border-radius: 8px; padding: 1.5rem; text-align: center; }}
            .metric-label {{ font-size: 0.9rem; color: #666; margin-bottom: 0.5rem; }}
            .metric-value {{ font-size: 2rem; font-weight: bold; color: #0066cc; }}
            
            /* Readiness Card */
            .readiness-card {{
                background: {readiness_bg};
                border-left: 5px solid {readiness_border};
                padding: 1.5rem;
                border-radius: 10px;
                margin: 1rem 0;
            }}
            .readiness-card h2 {{ margin-bottom: 1rem; }}
            .readiness-card p {{ margin: 0.5rem 0; line-height: 1.6; }}
            .recommendation {{ background: rgba(255,255,255,0.6); padding: 1rem; border-radius: 6px; margin-top: 1rem; }}
            
            /* Risk Grid */
            .risk-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 1.5rem 0; }}
            .risk-card {{ padding: 1.5rem; border-radius: 10px; text-align: center; border: 1px solid #dee2e6; }}
            .risk-card h4 {{ margin-bottom: 0.5rem; font-size: 1rem; }}
            .risk-card h3 {{ font-size: 2rem; margin: 0.5rem 0; }}
            .risk-card p {{ color: #666; font-size: 0.9rem; }}
            .high-risk {{ background: #f8d7da; }}
            .medium-risk {{ background: #fff3cd; }}
            .low-risk {{ background: #d4edda; }}
            
            /* Tables */
            table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
            th {{ background: #0066cc; color: white; padding: 0.75rem; text-align: left; font-size: 0.9rem; }}
            td {{ padding: 0.75rem; border-bottom: 1px solid #dee2e6; font-size: 0.9rem; }}
            tr:nth-child(even) {{ background: #f8f9fa; }}
            
            /* Insights Grid */
            .insight-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 1.5rem; margin: 1.5rem 0; }}
            .insight-box {{ background: #e7f3ff; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #0066cc; }}
            .insight-box h4 {{ color: #0066cc; margin-bottom: 1rem; }}
            .insight-box p {{ line-height: 1.6; }}
            
            @media print {{
                body {{ padding: 0; background: white; }}
                .container {{ box-shadow: none; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Analytics Dashboard</h1>
            <p class="subtitle"><b>Test:</b> {test_title} &nbsp;|&nbsp; <b>Subject:</b> {test_subject}</p>
            
            <!-- Key Metrics -->
            <div class="section">
                <div class="section-title">📈 Key Metrics</div>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">Total Students</div>
                        <div class="metric-value">{analytics['total_submissions']}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Average Score</div>
                        <div class="metric-value">{stats['mean']:.1f}%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Readiness Score</div>
                        <div class="metric-value">{readiness['readiness_score']:.1f}/100</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">High Risk Students</div>
                        <div class="metric-value" style="color: #dc3545;">{risk_stats['high_risk_count']}</div>
                    </div>
                </div>
            </div>
            
            <!-- Readiness Assessment -->
            <div class="section">
                <div class="section-title">🎯 Class Readiness Assessment</div>
                <div class="readiness-card">
                    <h2>{readiness_emoji} {readiness['status']}</h2>
                    <p><strong>Average Performance:</strong> {readiness['average_percentage']:.1f}%</p>
                    <p><strong>Performance Spread:</strong> {readiness['std_deviation']:.1f}% std dev</p>
                    <p><strong>High Performers:</strong> {readiness['high_performers_pct']:.1f}%</p>
                    <p><strong>At Risk:</strong> {readiness['at_risk_pct']:.1f}%</p>
                    <div class="recommendation">
                        <strong>Recommendation:</strong><br/>
                        {readiness['recommendation']}
                    </div>
                </div>
            </div>
            
            <!-- Topic Performance -->
            <div class="section">
                <div class="section-title">📚 Topic Performance Analysis</div>
                <table>
                    <thead>
                        <tr>
                            <th>Topic</th>
                            <th>Accuracy</th>
                            <th>Correct/Total</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {topic_rows}
                    </tbody>
                </table>
            </div>
            
            <!-- Risk Classification -->
            <div class="section">
                <div class="section-title">👥 Student Risk Analysis</div>
                <div class="risk-grid">
                    <div class="risk-card high-risk">
                        <h4>🔴 High Risk</h4>
                        <h3>{risk_stats['high_risk_count']}</h3>
                        <p>Students < 40%</p>
                    </div>
                    <div class="risk-card medium-risk">
                        <h4>🟡 Medium Risk</h4>
                        <h3>{risk_stats['medium_risk_count']}</h3>
                        <p>Students 40-65%</p>
                    </div>
                    <div class="risk-card low-risk">
                        <h4>🟢 Low Risk</h4>
                        <h3>{risk_stats['low_risk_count']}</h3>
                        <p>Students > 65%</p>
                    </div>
                </div>
                
                <h4 style="margin-top: 2rem;">Student Performance Table</h4>
                <table>
                    <thead>
                        <tr>
                            <th>Student</th>
                            <th>Score (%)</th>
                            <th>Risk Level</th>
                        </tr>
                    </thead>
                    <tbody>
                        {student_rows}
                    </tbody>
                </table>
            </div>
            
            <!-- AI Insights -->
            <div class="section">
                <div class="section-title">🤖 AI-Powered Insights</div>
                <div class="insight-grid">
                    <div class="insight-box">
                        <h4>📝 Summary</h4>
                        <p>{ai_insights.get('summary', 'AI insights unavailable') if ai_insights else 'N/A'}</p>
                    </div>
                    <div class="insight-box">
                        <h4>⚠️ Areas of Concern</h4>
                        <p>{ai_insights.get('weaknesses', 'AI insights unavailable') if ai_insights else 'N/A'}</p>
                    </div>
                    <div class="insight-box">
                        <h4>✅ Strengths</h4>
                        <p>{ai_insights.get('strengths', 'AI insights unavailable') if ai_insights else 'N/A'}</p>
                    </div>
                    <div class="insight-box">
                        <h4>🎯 Action Items</h4>
                        <p>{ai_insights.get('action_items', 'AI insights unavailable') if ai_insights else 'N/A'}</p>
                    </div>
                </div>
            </div>
            
            <p style="text-align: center; color: #666; margin-top: 3rem; font-size: 0.9rem;">
                <i>Generated by comPASS - Smart Test Analytics & Decision Support System</i>
            </p>
        </div>
    </body>
    </html>
    """
    
    return html