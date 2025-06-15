#!/usr/bin/env python3
"""
WINCASA Business Metrics Dashboard - Simple HTML Version
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from wincasa_analytics_system import BusinessMetric, WincasaAnalyticsSystem
from wincasa_query_engine import WincasaQueryEngine


class SimpleBusinessDashboard:
    """Simple HTML Business Dashboard Generator"""
    
    def __init__(self):
        self.analytics = WincasaAnalyticsSystem(debug_mode=False)
        self.query_engine = WincasaQueryEngine(debug_mode=False)
        
    def generate_sample_data(self, num_queries: int = 200):
        """Generate sample data for demonstration"""
        
        print("📊 Generating sample business data...")
        
        # Sample query patterns
        query_templates = [
            ("Wer wohnt in {location}?", ["Essen", "Köln", "Hamburg", "Berlin"]),
            ("Zeige Mieter {name}", ["Weber", "Müller", "Schmidt", "Meyer"]),
            ("Portfolio von {company}", ["Bona Casa GmbH", "ABC Immobilien", "XYZ Holding"]),
            ("Leerstand in {city}", ["Essen", "Dortmund", "Düsseldorf"]),
            ("Kontaktdaten {name}", ["Fischer", "Wagner", "Becker"]),
            ("Kontostand {name}", ["Schulz", "Hoffmann", "Schäfer"]),
            ("Rückstände {property}", ["Hauptstr. 1", "Bahnhofstr. 10", "Marktplatz 5"]),
            ("Mieterliste {address}", ["Bergstr.", "Kirchweg", "Gartenstr."])
        ]
        
        # User segments
        users = {
            "power_user": ["admin", "manager_1", "manager_2"],
            "regular_user": ["user_" + str(i) for i in range(1, 11)],
            "occasional_user": ["guest_" + str(i) for i in range(1, 6)]
        }
        
        # Generate queries
        for i in range(num_queries):
            template, values = query_templates[i % len(query_templates)]
            value = values[i % len(values)]
            query = template.format(
                location=value, name=value, company=value, 
                city=value, property=value, address=value
            )
            
            # Determine user
            if i % 10 < 3:
                user_type = "power_user"
            elif i % 10 < 8:
                user_type = "regular_user"
            else:
                user_type = "occasional_user"
            
            user_list = users[user_type]
            user_id = user_list[i % len(user_list)]
            
            # Determine performance and success
            if "Rückstände" in query or "Leerstand" in query:
                # Complex queries
                response_time = 500 + (i * 50) % 2000
                success = i % 5 != 0
                engine = "legacy_v1"
                cost = 0.05
            else:
                # Simple queries
                response_time = 5 + (i * 2) % 50
                success = i % 20 != 0
                engine = "unified_v2" if i % 3 != 0 else "legacy_v1"
                cost = 0.0 if engine == "unified_v2" else 0.02
            
            # Create query log
            query_data = {
                "query": query,
                "user_id": user_id,
                "response_time_ms": response_time,
                "success": success,
                "engine": engine,
                "cost": cost,
                "timestamp": (datetime.now() - timedelta(hours=num_queries-i)).isoformat()
            }
            
            self.analytics.log_query(query_data)
        
        print(f"✅ Generated {num_queries} sample queries")
    
    def generate_dashboard_html(self, output_file: str = "business_dashboard.html"):
        """Generate comprehensive business dashboard"""
        
        # Calculate all metrics
        metrics_24h = self.analytics.calculate_business_metrics(24)
        metrics_7d = self.analytics.calculate_business_metrics(168)
        patterns = self.analytics.get_pattern_insights()
        journeys = self.analytics.get_journey_analytics()
        
        # Generate HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>WINCASA Business Metrics Dashboard</title>
    <meta charset="utf-8">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            color: #2c3e50;
            line-height: 1.6;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header h1 {{ margin: 0; font-size: 2.5rem; }}
        .header p {{ opacity: 0.9; margin-top: 0.5rem; }}
        
        .container {{ max-width: 1400px; margin: 0 auto; padding: 2rem; }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .metric-card {{
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .metric-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        }}
        
        .metric-value {{
            font-size: 2.5rem;
            font-weight: 700;
            color: #667eea;
            margin: 0.5rem 0;
        }}
        
        .metric-label {{
            color: #718096;
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .metric-delta {{
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.875rem;
            font-weight: 500;
            margin-top: 0.5rem;
        }}
        
        .delta-positive {{
            background: #d4f8e8;
            color: #276749;
        }}
        
        .delta-negative {{
            background: #fef2f2;
            color: #991b1b;
        }}
        
        .chart-container {{
            background: white;
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        
        .chart-container h2 {{
            margin-bottom: 1.5rem;
            color: #2d3748;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}
        
        th {{
            background: #f7fafc;
            padding: 0.75rem;
            text-align: left;
            font-weight: 600;
            color: #4a5568;
            border-bottom: 2px solid #e2e8f0;
        }}
        
        td {{
            padding: 0.75rem;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        tr:hover {{
            background: #f7fafc;
        }}
        
        .progress-bar {{
            width: 100%;
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
            margin: 0.5rem 0;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s ease;
        }}
        
        .insights-box {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 4px;
        }}
        
        .insights-box h3 {{
            color: #92400e;
            margin-bottom: 0.5rem;
        }}
        
        .recommendation {{
            background: #dbeafe;
            border-left: 4px solid #3b82f6;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 4px;
        }}
        
        .footer {{
            text-align: center;
            padding: 2rem;
            color: #718096;
            border-top: 1px solid #e2e8f0;
            margin-top: 3rem;
        }}
        
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            margin: 0 0.25rem;
        }}
        
        .badge-success {{ background: #d4f8e8; color: #276749; }}
        .badge-warning {{ background: #fef3c7; color: #92400e; }}
        .badge-info {{ background: #dbeafe; color: #1e40af; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 WINCASA Business Metrics Dashboard</h1>
        <p>Real-time analytics and business intelligence | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="container">
        {self._generate_key_metrics_section(metrics_24h, metrics_7d)}
        {self._generate_performance_section(metrics_24h)}
        {self._generate_pattern_analysis_section(patterns)}
        {self._generate_cost_analysis_section(metrics_24h, metrics_7d)}
        {self._generate_user_insights_section(journeys)}
        {self._generate_recommendations_section()}
    </div>
    
    <div class="footer">
        <p>WINCASA Phase 2 Analytics System | Generated by Business Dashboard</p>
    </div>
</body>
</html>
        """
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return output_file
    
    def _generate_key_metrics_section(self, metrics_24h: Dict, metrics_7d: Dict) -> str:
        """Generate key metrics section"""
        
        # Extract values
        qph_24h = metrics_24h.get("query_volume", BusinessMetric("", "", 0, "", "", "")).value
        qph_7d = metrics_7d.get("query_volume", BusinessMetric("", "", 0, "", "", "")).value
        
        success_24h = metrics_24h.get("success_rate", BusinessMetric("", "", 0, "", "", "")).value
        success_7d = metrics_7d.get("success_rate", BusinessMetric("", "", 0, "", "", "")).value
        
        response_24h = metrics_24h.get("avg_response_time", BusinessMetric("", "", 0, "", "", "")).value
        response_7d = metrics_7d.get("avg_response_time", BusinessMetric("", "", 0, "", "", "")).value
        
        cost_24h = metrics_24h.get("query_cost", BusinessMetric("", "", 0, "", "", "")).value
        cost_7d = metrics_7d.get("query_cost", BusinessMetric("", "", 0, "", "", "")).value
        
        return f"""
        <section>
            <h2>📈 Key Business Metrics</h2>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Query Volume</div>
                    <div class="metric-value">{qph_24h:.1f}</div>
                    <div class="metric-label">queries/hour</div>
                    {self._generate_delta(qph_24h, qph_7d, "vs 7-day avg")}
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">Success Rate</div>
                    <div class="metric-value">{success_24h:.1%}</div>
                    <div class="metric-label">last 24 hours</div>
                    {self._generate_delta(success_24h, success_7d, "vs 7-day avg", is_percentage=True)}
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">Avg Response Time</div>
                    <div class="metric-value">{response_24h:.0f}ms</div>
                    <div class="metric-label">last 24 hours</div>
                    {self._generate_delta(response_24h, response_7d, "vs 7-day avg", reverse=True)}
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">Avg Cost per Query</div>
                    <div class="metric-value">${cost_24h:.3f}</div>
                    <div class="metric-label">last 24 hours</div>
                    {self._generate_delta(cost_24h, cost_7d, "vs 7-day avg", reverse=True)}
                </div>
            </div>
        </section>
        """
    
    def _generate_delta(self, current: float, previous: float, label: str, 
                       is_percentage: bool = False, reverse: bool = False) -> str:
        """Generate delta indicator"""
        
        if previous == 0:
            return ""
        
        delta = current - previous
        delta_pct = (delta / previous) * 100
        
        if is_percentage:
            delta_str = f"{delta:.1%}"
        else:
            delta_str = f"{delta_pct:+.1f}%"
        
        # Determine if positive or negative (considering reverse)
        is_positive = (delta > 0 and not reverse) or (delta < 0 and reverse)
        
        css_class = "delta-positive" if is_positive else "delta-negative"
        
        return f'<div class="metric-delta {css_class}">{delta_str} {label}</div>'
    
    def _generate_performance_section(self, metrics: Dict) -> str:
        """Generate performance analysis section"""
        
        # Engine distribution
        engine_data = []
        for key, metric in metrics.items():
            if key.startswith("engine_usage_"):
                engine = key.replace("engine_usage_", "")
                engine_data.append((engine, metric.value))
        
        return f"""
        <section class="chart-container">
            <h2>⚡ Performance Analysis</h2>
            
            <div class="insights-box">
                <h3>System Performance</h3>
                <p>The system is processing queries with an average response time of 
                {metrics.get('avg_response_time', BusinessMetric('', '', 0, '', '', '')).value:.0f}ms.</p>
            </div>
            
            <h3>Engine Usage Distribution</h3>
            <div style="margin: 1rem 0;">
                {self._generate_engine_bars(engine_data)}
            </div>
            
            <h3>Performance Metrics by Engine</h3>
            <table>
                <tr>
                    <th>Engine</th>
                    <th>Usage %</th>
                    <th>Avg Response Time</th>
                    <th>Cost Impact</th>
                </tr>
                {self._generate_engine_table_rows(engine_data, metrics)}
            </table>
        </section>
        """
    
    def _generate_engine_bars(self, engine_data: List[tuple]) -> str:
        """Generate engine usage bars"""
        
        bars = []
        for engine, percentage in engine_data:
            bars.append(f"""
            <div style="margin: 0.5rem 0;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <span>{engine}</span>
                    <span>{percentage:.1f}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {percentage}%"></div>
                </div>
            </div>
            """)
        
        return "".join(bars)
    
    def _generate_engine_table_rows(self, engine_data: List[tuple], metrics: Dict) -> str:
        """Generate engine comparison table rows"""
        
        rows = []
        for engine, percentage in engine_data:
            # Estimate performance based on engine type
            if "unified" in engine:
                avg_time = "5-50ms"
                cost = "$0.00"
                badge = '<span class="badge badge-success">Optimized</span>'
            else:
                avg_time = "500-2000ms"
                cost = "$0.05"
                badge = '<span class="badge badge-warning">Legacy</span>'
            
            rows.append(f"""
            <tr>
                <td>{engine} {badge}</td>
                <td>{percentage:.1f}%</td>
                <td>{avg_time}</td>
                <td>{cost}</td>
            </tr>
            """)
        
        return "".join(rows)
    
    def _generate_pattern_analysis_section(self, patterns: Dict) -> str:
        """Generate pattern analysis section"""
        
        if not patterns.get("patterns"):
            return ""
        
        pattern_rows = []
        for pattern_id, data in list(patterns["patterns"].items())[:10]:
            pattern_rows.append(f"""
            <tr>
                <td>{pattern_id.replace('_', ' ').title()}</td>
                <td>{data['type']}</td>
                <td>{data['frequency']}</td>
                <td>{data['success_rate']:.1%}</td>
                <td>{data['avg_response_time_ms']:.0f}ms</td>
            </tr>
            """)
        
        return f"""
        <section class="chart-container">
            <h2>🔍 Query Pattern Analysis</h2>
            
            <p>Identified <strong>{patterns['total_patterns_identified']}</strong> unique query patterns.</p>
            
            <table>
                <tr>
                    <th>Pattern</th>
                    <th>Type</th>
                    <th>Frequency</th>
                    <th>Success Rate</th>
                    <th>Avg Response</th>
                </tr>
                {"".join(pattern_rows)}
            </table>
        </section>
        """
    
    def _generate_cost_analysis_section(self, metrics_24h: Dict, metrics_7d: Dict) -> str:
        """Generate cost analysis section"""
        
        cost_24h = metrics_24h.get("query_cost", BusinessMetric("", "", 0, "", "", "")).value
        volume_24h = metrics_24h.get("query_volume", BusinessMetric("", "", 0, "", "", "")).value
        
        # Calculate daily costs
        daily_cost = cost_24h * volume_24h * 24
        monthly_cost = daily_cost * 30
        
        # Calculate savings
        legacy_cost = 0.05  # Average legacy cost
        savings_per_query = legacy_cost - cost_24h
        daily_savings = savings_per_query * volume_24h * 24
        
        return f"""
        <section class="chart-container">
            <h2>💰 Cost Analysis & Savings</h2>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Daily Cost</div>
                    <div class="metric-value">${daily_cost:.2f}</div>
                    <div class="metric-label">current run rate</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">Monthly Projection</div>
                    <div class="metric-value">${monthly_cost:.2f}</div>
                    <div class="metric-label">at current usage</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">Daily Savings</div>
                    <div class="metric-value">${daily_savings:.2f}</div>
                    <div class="metric-label">vs legacy system</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">Savings Rate</div>
                    <div class="metric-value">{(savings_per_query/legacy_cost)*100:.0f}%</div>
                    <div class="metric-label">cost reduction</div>
                </div>
            </div>
            
            <div class="insights-box">
                <h3>Cost Optimization Impact</h3>
                <p>The unified system is saving approximately <strong>${daily_savings:.2f}</strong> per day 
                compared to legacy system costs. At current usage rates, this translates to 
                <strong>${daily_savings * 365:.2f}</strong> in annual savings.</p>
            </div>
        </section>
        """
    
    def _generate_user_insights_section(self, journeys: Dict) -> str:
        """Generate user insights section"""
        
        if "error" in journeys:
            return ""
        
        return f"""
        <section class="chart-container">
            <h2>👥 User Behavior Insights</h2>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">User Sessions</div>
                    <div class="metric-value">{journeys.get('total_journeys', 0)}</div>
                    <div class="metric-label">analyzed</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">Avg Queries/Session</div>
                    <div class="metric-value">{journeys.get('avg_queries_per_journey', 0):.1f}</div>
                    <div class="metric-label">per user</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">Session Success Rate</div>
                    <div class="metric-value">{journeys.get('success_rate', 0):.1%}</div>
                    <div class="metric-label">fully successful</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">Avg Session Duration</div>
                    <div class="metric-value">{journeys.get('avg_journey_duration_seconds', 0)/60:.1f}m</div>
                    <div class="metric-label">minutes</div>
                </div>
            </div>
        </section>
        """
    
    def _generate_recommendations_section(self) -> str:
        """Generate recommendations section"""
        
        recommendations = self.analytics._generate_top_recommendations()
        
        if not recommendations:
            return """
            <section class="chart-container">
                <h2>🎯 System Status</h2>
                <div class="insights-box" style="background: #d4f8e8; border-color: #276749;">
                    <h3 style="color: #276749;">Optimal Performance</h3>
                    <p>The system is performing optimally with no immediate action items.</p>
                </div>
            </section>
            """
        
        rec_html = []
        for rec in recommendations:
            priority_emoji = {
                "high": "🔴",
                "medium": "🟡", 
                "low": "🟢"
            }.get(rec["priority"], "⚪")
            
            rec_html.append(f"""
            <div class="recommendation">
                <strong>{priority_emoji} {rec['area'].title()} - {rec['priority'].title()} Priority</strong><br>
                {rec['recommendation']}<br>
                <em>Expected Impact: {rec.get('impact', 'Performance improvement')}</em>
            </div>
            """)
        
        return f"""
        <section class="chart-container">
            <h2>🎯 Recommendations</h2>
            {"".join(rec_html)}
        </section>
        """

def test_business_dashboard():
    """Test the business metrics dashboard"""
    
    print("🧪 Testing Business Metrics Dashboard...")
    
    # Create dashboard
    dashboard = SimpleBusinessDashboard()
    
    # Generate sample data
    dashboard.generate_sample_data(200)
    
    # Generate HTML dashboard
    output_file = dashboard.generate_dashboard_html()
    
    print(f"✅ Business dashboard created: {output_file}")
    
    # Also generate analytics report
    report_path = dashboard.analytics.generate_analytics_report()
    print(f"📊 Analytics report created: {report_path}")
    
    print("\n✅ Business Metrics Dashboard Test Complete")

if __name__ == "__main__":
    test_business_dashboard()