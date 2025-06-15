#!/usr/bin/env python3
"""
WINCASA Phase 2 - Analytics System
Query-Pattern Analysis, User-Journey Tracking, and Business Metrics
"""

import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re

@dataclass
class QueryPattern:
    """Identified query pattern"""
    pattern_id: str
    pattern_type: str  # "entity_search", "location_query", "report_request", etc.
    regex_pattern: Optional[str]
    keywords: List[str]
    frequency: int
    avg_response_time_ms: float
    success_rate: float
    example_queries: List[str]

@dataclass
class UserJourney:
    """User interaction journey"""
    user_id: str
    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    query_sequence: List[Dict[str, Any]]
    total_queries: int
    successful_queries: int
    avg_response_time_ms: float
    engines_used: Set[str]
    journey_type: str  # "lookup", "analysis", "mixed"

@dataclass
class BusinessMetric:
    """Business-relevant metric"""
    metric_name: str
    metric_type: str  # "count", "rate", "average", "sum"
    value: float
    unit: str
    timeframe: str
    segment: Optional[str]  # e.g., "by_user_type", "by_query_type"

class WincasaAnalyticsSystem:
    """
    Comprehensive Analytics System for WINCASA Phase 2
    
    Features:
    - Query Pattern Mining and Analysis
    - User Journey Tracking and Segmentation
    - Business Metrics Calculation
    - Real-time and Historical Analytics
    - Actionable Insights Generation
    """
    
    def __init__(self, 
                 storage_dir: str = "analytics_data",
                 debug_mode: bool = False):
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.debug_mode = debug_mode
        
        # Analytics Storage
        self.query_logs: List[Dict[str, Any]] = []
        self.identified_patterns: Dict[str, QueryPattern] = {}
        self.user_journeys: Dict[str, UserJourney] = {}
        self.business_metrics: Dict[str, BusinessMetric] = {}
        
        # Pattern Detection
        self._initialize_pattern_detectors()
        
        # Session Management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout_minutes = 30
        
        if self.debug_mode:
            print(f"📊 Analytics System initialized:")
            print(f"   📁 Storage: {self.storage_dir}")
            print(f"   🔍 Pattern Detectors: {len(self.pattern_detectors)}")
    
    def _initialize_pattern_detectors(self):
        """Initialize query pattern detectors"""
        
        self.pattern_detectors = {
            # Entity searches
            "tenant_by_name": {
                "regex": r"(?:wer ist|zeige?|suche?|finde?).*?(mieter|bewohner)",
                "keywords": ["mieter", "bewohner", "tenant"],
                "type": "entity_search"
            },
            "owner_by_name": {
                "regex": r"(?:eigentümer|besitzer|owner).*?(?:von|für|namens)",
                "keywords": ["eigentümer", "besitzer", "owner"],
                "type": "entity_search"
            },
            
            # Location queries
            "by_location": {
                "regex": r"(?:in|bei|auf|an)\s+(?:der\s+)?([A-Za-zäöüÄÖÜß\s]+(?:straße|str\.|weg|platz|allee))",
                "keywords": ["straße", "str.", "weg", "platz"],
                "type": "location_query"
            },
            "by_city": {
                "regex": r"(?:in|aus)\s+([A-Z][a-zäöüÄÖÜß]+)(?:\s|$)",
                "keywords": ["stadt", "ort", "gemeinde"],
                "type": "location_query"
            },
            
            # Financial queries
            "balance_check": {
                "regex": r"(?:kontostand|saldo|guthaben|schulden)",
                "keywords": ["kontostand", "saldo", "balance"],
                "type": "financial_query"
            },
            "payment_status": {
                "regex": r"(?:zahlung|rückstand|mahnung|offene?\s+posten)",
                "keywords": ["zahlung", "rückstand", "payment"],
                "type": "financial_query"
            },
            
            # Portfolio queries
            "portfolio_overview": {
                "regex": r"(?:portfolio|bestand|übersicht|alle\s+objekte)",
                "keywords": ["portfolio", "bestand", "overview"],
                "type": "portfolio_query"
            },
            "vacancy_analysis": {
                "regex": r"(?:leerstand|freie?\s+wohnung|vacant|unbewohnt)",
                "keywords": ["leerstand", "frei", "vacant"],
                "type": "analytics_query"
            },
            
            # Report requests
            "report_generation": {
                "regex": r"(?:bericht|report|auswertung|analyse|erstelle)",
                "keywords": ["bericht", "report", "analyse"],
                "type": "report_request"
            }
        }
    
    def log_query(self, query_data: Dict[str, Any]):
        """Log a query for analytics"""
        
        # Enrich with timestamp if not present
        if "timestamp" not in query_data:
            query_data["timestamp"] = datetime.now().isoformat()
        
        # Detect patterns
        patterns = self._detect_patterns(query_data.get("query", ""))
        query_data["detected_patterns"] = patterns
        
        # Add to logs
        self.query_logs.append(query_data)
        
        # Update session tracking
        user_id = query_data.get("user_id", "anonymous")
        self._update_user_session(user_id, query_data)
        
        # Update pattern statistics
        for pattern in patterns:
            self._update_pattern_stats(pattern, query_data)
        
        if self.debug_mode:
            print(f"📝 Query logged: {query_data.get('query', '')[:50]}...")
            if patterns:
                print(f"   🔍 Patterns: {patterns}")
    
    def _detect_patterns(self, query: str) -> List[str]:
        """Detect patterns in a query"""
        
        detected = []
        query_lower = query.lower()
        
        for pattern_id, detector in self.pattern_detectors.items():
            # Check regex
            if "regex" in detector:
                if re.search(detector["regex"], query_lower):
                    detected.append(pattern_id)
                    continue
            
            # Check keywords
            if "keywords" in detector:
                if any(keyword in query_lower for keyword in detector["keywords"]):
                    detected.append(pattern_id)
        
        return detected
    
    def _update_user_session(self, user_id: str, query_data: Dict[str, Any]):
        """Update user session tracking"""
        
        current_time = datetime.now()
        
        # Check for existing session
        if user_id in self.active_sessions:
            session = self.active_sessions[user_id]
            last_activity = datetime.fromisoformat(session["last_activity"])
            
            # Check if session expired
            if current_time - last_activity > timedelta(minutes=self.session_timeout_minutes):
                # Finalize old session
                self._finalize_user_journey(user_id)
                # Start new session
                self._start_new_session(user_id, query_data)
            else:
                # Update existing session
                session["queries"].append(query_data)
                session["last_activity"] = current_time.isoformat()
        else:
            # Start new session
            self._start_new_session(user_id, query_data)
    
    def _start_new_session(self, user_id: str, query_data: Dict[str, Any]):
        """Start a new user session"""
        
        session_id = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.active_sessions[user_id] = {
            "session_id": session_id,
            "start_time": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "queries": [query_data],
            "user_id": user_id
        }
    
    def _finalize_user_journey(self, user_id: str):
        """Finalize and analyze a user journey"""
        
        if user_id not in self.active_sessions:
            return
        
        session = self.active_sessions[user_id]
        queries = session["queries"]
        
        if not queries:
            return
        
        # Calculate journey metrics
        total_queries = len(queries)
        successful_queries = sum(1 for q in queries if q.get("success", False))
        
        response_times = [q.get("response_time_ms", 0) for q in queries]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        engines_used = set(q.get("engine", "unknown") for q in queries)
        
        # Determine journey type
        patterns = []
        for q in queries:
            patterns.extend(q.get("detected_patterns", []))
        
        journey_type = self._classify_journey_type(patterns)
        
        # Create journey record
        journey = UserJourney(
            user_id=user_id,
            session_id=session["session_id"],
            start_time=datetime.fromisoformat(session["start_time"]),
            end_time=datetime.now(),
            query_sequence=[{
                "query": q.get("query", ""),
                "timestamp": q.get("timestamp", ""),
                "patterns": q.get("detected_patterns", [])
            } for q in queries],
            total_queries=total_queries,
            successful_queries=successful_queries,
            avg_response_time_ms=avg_response_time,
            engines_used=engines_used,
            journey_type=journey_type
        )
        
        self.user_journeys[session["session_id"]] = journey
        
        # Remove from active sessions
        del self.active_sessions[user_id]
        
        if self.debug_mode:
            print(f"📍 Journey finalized: {journey.session_id}")
            print(f"   Type: {journey.journey_type}")
            print(f"   Queries: {journey.total_queries}")
    
    def _classify_journey_type(self, patterns: List[str]) -> str:
        """Classify the type of user journey based on patterns"""
        
        if not patterns:
            return "exploratory"
        
        pattern_types = []
        for pattern in patterns:
            if pattern in self.pattern_detectors:
                pattern_types.append(self.pattern_detectors[pattern]["type"])
        
        type_counts = Counter(pattern_types)
        
        # Classification logic
        if "report_request" in type_counts:
            return "analysis"
        elif "entity_search" in type_counts and len(set(pattern_types)) == 1:
            return "lookup"
        elif "financial_query" in type_counts:
            return "financial"
        elif len(set(pattern_types)) > 2:
            return "mixed"
        else:
            return "focused"
    
    def _update_pattern_stats(self, pattern_id: str, query_data: Dict[str, Any]):
        """Update pattern statistics"""
        
        if pattern_id not in self.identified_patterns:
            # Create new pattern record
            detector = self.pattern_detectors.get(pattern_id, {})
            
            self.identified_patterns[pattern_id] = QueryPattern(
                pattern_id=pattern_id,
                pattern_type=detector.get("type", "unknown"),
                regex_pattern=detector.get("regex"),
                keywords=detector.get("keywords", []),
                frequency=0,
                avg_response_time_ms=0.0,
                success_rate=0.0,
                example_queries=[]
            )
        
        pattern = self.identified_patterns[pattern_id]
        
        # Update frequency
        pattern.frequency += 1
        
        # Update response time (running average)
        response_time = query_data.get("response_time_ms", 0)
        pattern.avg_response_time_ms = (
            (pattern.avg_response_time_ms * (pattern.frequency - 1) + response_time) 
            / pattern.frequency
        )
        
        # Update success rate
        if query_data.get("success", False):
            current_successes = pattern.success_rate * (pattern.frequency - 1)
            pattern.success_rate = (current_successes + 1) / pattern.frequency
        else:
            current_successes = pattern.success_rate * (pattern.frequency - 1)
            pattern.success_rate = current_successes / pattern.frequency
        
        # Add example query (keep last 5)
        query_text = query_data.get("query", "")
        if query_text and query_text not in pattern.example_queries:
            pattern.example_queries.append(query_text)
            if len(pattern.example_queries) > 5:
                pattern.example_queries.pop(0)
    
    def calculate_business_metrics(self, timeframe_hours: int = 24) -> Dict[str, BusinessMetric]:
        """Calculate business-relevant metrics"""
        
        cutoff_time = datetime.now() - timedelta(hours=timeframe_hours)
        
        # Filter recent queries
        recent_queries = [
            q for q in self.query_logs
            if datetime.fromisoformat(q.get("timestamp", datetime.now().isoformat())) >= cutoff_time
        ]
        
        if not recent_queries:
            return {}
        
        metrics = {}
        
        # 1. Query Volume Metrics
        total_queries = len(recent_queries)
        queries_per_hour = total_queries / timeframe_hours
        
        metrics["query_volume"] = BusinessMetric(
            metric_name="Query Volume",
            metric_type="rate",
            value=queries_per_hour,
            unit="queries/hour",
            timeframe=f"{timeframe_hours}h",
            segment=None
        )
        
        # 2. Success Rate
        successful_queries = sum(1 for q in recent_queries if q.get("success", False))
        success_rate = successful_queries / total_queries if total_queries > 0 else 0
        
        metrics["success_rate"] = BusinessMetric(
            metric_name="Query Success Rate",
            metric_type="rate",
            value=success_rate,
            unit="percentage",
            timeframe=f"{timeframe_hours}h",
            segment=None
        )
        
        # 3. Performance Metrics
        response_times = [q.get("response_time_ms", 0) for q in recent_queries]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        metrics["avg_response_time"] = BusinessMetric(
            metric_name="Average Response Time",
            metric_type="average",
            value=avg_response_time,
            unit="ms",
            timeframe=f"{timeframe_hours}h",
            segment=None
        )
        
        # 4. Cost Metrics
        total_cost = sum(q.get("cost", 0) for q in recent_queries)
        avg_cost_per_query = total_cost / total_queries if total_queries > 0 else 0
        
        metrics["query_cost"] = BusinessMetric(
            metric_name="Average Query Cost",
            metric_type="average",
            value=avg_cost_per_query,
            unit="USD",
            timeframe=f"{timeframe_hours}h",
            segment=None
        )
        
        # 5. User Engagement
        unique_users = len(set(q.get("user_id", "anonymous") for q in recent_queries))
        queries_per_user = total_queries / unique_users if unique_users > 0 else 0
        
        metrics["user_engagement"] = BusinessMetric(
            metric_name="Queries per User",
            metric_type="average",
            value=queries_per_user,
            unit="queries/user",
            timeframe=f"{timeframe_hours}h",
            segment=None
        )
        
        # 6. Engine Usage Distribution
        engine_counts = Counter(q.get("engine", "unknown") for q in recent_queries)
        
        for engine, count in engine_counts.items():
            percentage = (count / total_queries) * 100
            metrics[f"engine_usage_{engine}"] = BusinessMetric(
                metric_name=f"Engine Usage - {engine}",
                metric_type="rate",
                value=percentage,
                unit="percentage",
                timeframe=f"{timeframe_hours}h",
                segment="by_engine"
            )
        
        # 7. Pattern Distribution
        all_patterns = []
        for q in recent_queries:
            all_patterns.extend(q.get("detected_patterns", []))
        
        pattern_counts = Counter(all_patterns)
        
        for pattern, count in pattern_counts.most_common(5):  # Top 5 patterns
            percentage = (count / len(all_patterns)) * 100 if all_patterns else 0
            metrics[f"pattern_{pattern}"] = BusinessMetric(
                metric_name=f"Pattern - {pattern}",
                metric_type="rate",
                value=percentage,
                unit="percentage",
                timeframe=f"{timeframe_hours}h",
                segment="by_pattern"
            )
        
        self.business_metrics = metrics
        return metrics
    
    def get_pattern_insights(self) -> Dict[str, Any]:
        """Get insights from query patterns"""
        
        insights = {
            "total_patterns_identified": len(self.identified_patterns),
            "patterns": {},
            "recommendations": []
        }
        
        # Analyze each pattern
        for pattern_id, pattern in self.identified_patterns.items():
            pattern_info = {
                "type": pattern.pattern_type,
                "frequency": pattern.frequency,
                "avg_response_time_ms": round(pattern.avg_response_time_ms, 2),
                "success_rate": round(pattern.success_rate, 3),
                "examples": pattern.example_queries[:3]  # Top 3 examples
            }
            
            insights["patterns"][pattern_id] = pattern_info
            
            # Generate recommendations
            if pattern.success_rate < 0.8:
                insights["recommendations"].append({
                    "pattern": pattern_id,
                    "issue": "low_success_rate",
                    "recommendation": f"Improve handling for '{pattern_id}' queries (current success: {pattern.success_rate:.1%})"
                })
            
            if pattern.avg_response_time_ms > 1000:
                insights["recommendations"].append({
                    "pattern": pattern_id,
                    "issue": "slow_response",
                    "recommendation": f"Optimize performance for '{pattern_id}' queries (current: {pattern.avg_response_time_ms:.0f}ms)"
                })
        
        # Find most common patterns
        sorted_patterns = sorted(
            self.identified_patterns.values(),
            key=lambda p: p.frequency,
            reverse=True
        )
        
        if sorted_patterns:
            top_patterns = [p.pattern_id for p in sorted_patterns[:3]]
            insights["top_patterns"] = top_patterns
        
        return insights
    
    def get_journey_analytics(self) -> Dict[str, Any]:
        """Get user journey analytics"""
        
        if not self.user_journeys:
            return {"error": "No journey data available"}
        
        journeys = list(self.user_journeys.values())
        
        # Journey type distribution
        journey_types = Counter(j.journey_type for j in journeys)
        
        # Average metrics
        avg_queries_per_journey = sum(j.total_queries for j in journeys) / len(journeys)
        avg_journey_duration = sum(
            (j.end_time - j.start_time).total_seconds() for j in journeys if j.end_time
        ) / len(journeys)
        
        # Success metrics
        successful_journeys = sum(
            1 for j in journeys 
            if j.successful_queries == j.total_queries
        )
        
        analytics = {
            "total_journeys": len(journeys),
            "journey_types": dict(journey_types),
            "avg_queries_per_journey": round(avg_queries_per_journey, 2),
            "avg_journey_duration_seconds": round(avg_journey_duration, 2),
            "fully_successful_journeys": successful_journeys,
            "success_rate": round(successful_journeys / len(journeys), 3)
        }
        
        # Identify common paths
        query_sequences = []
        for journey in journeys[:50]:  # Sample first 50
            sequence = [p for q in journey.query_sequence for p in q.get("patterns", [])]
            if sequence:
                query_sequences.append(tuple(sequence))
        
        if query_sequences:
            common_sequences = Counter(query_sequences).most_common(5)
            analytics["common_paths"] = [
                {"sequence": list(seq), "count": count}
                for seq, count in common_sequences
            ]
        
        return analytics
    
    def generate_analytics_report(self, filename: Optional[str] = None) -> str:
        """Generate comprehensive analytics report"""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analytics_report_{timestamp}.json"
        
        filepath = self.storage_dir / filename
        
        # Calculate fresh metrics
        business_metrics = self.calculate_business_metrics(24)  # Last 24h
        pattern_insights = self.get_pattern_insights()
        journey_analytics = self.get_journey_analytics()
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_queries_analyzed": len(self.query_logs),
                "unique_patterns": len(self.identified_patterns),
                "user_journeys": len(self.user_journeys),
                "active_sessions": len(self.active_sessions)
            },
            "business_metrics": {
                name: asdict(metric) for name, metric in business_metrics.items()
            },
            "pattern_insights": pattern_insights,
            "journey_analytics": journey_analytics,
            "top_recommendations": self._generate_top_recommendations()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        if self.debug_mode:
            print(f"📊 Analytics report generated: {filepath}")
        
        return str(filepath)
    
    def _generate_top_recommendations(self) -> List[Dict[str, str]]:
        """Generate top recommendations based on analytics"""
        
        recommendations = []
        
        # Check pattern performance
        slow_patterns = [
            p for p in self.identified_patterns.values()
            if p.avg_response_time_ms > 1000 and p.frequency > 10
        ]
        
        if slow_patterns:
            recommendations.append({
                "priority": "high",
                "area": "performance",
                "recommendation": f"Optimize {len(slow_patterns)} slow query patterns",
                "impact": "Reduce average response time by up to 50%"
            })
        
        # Check success rates
        low_success_patterns = [
            p for p in self.identified_patterns.values()
            if p.success_rate < 0.7 and p.frequency > 5
        ]
        
        if low_success_patterns:
            recommendations.append({
                "priority": "high",
                "area": "accuracy",
                "recommendation": f"Improve handling for {len(low_success_patterns)} low-success patterns",
                "impact": "Increase overall success rate by 10-15%"
            })
        
        # Check user engagement
        if self.business_metrics.get("user_engagement"):
            queries_per_user = self.business_metrics["user_engagement"].value
            if queries_per_user < 2:
                recommendations.append({
                    "priority": "medium",
                    "area": "engagement",
                    "recommendation": "Improve user onboarding to increase engagement",
                    "impact": "Increase queries per user from {:.1f} to 3+".format(queries_per_user)
                })
        
        return recommendations[:5]  # Top 5 recommendations

class AnalyticsDashboard:
    """Simple analytics dashboard generator"""
    
    def __init__(self, analytics_system: WincasaAnalyticsSystem):
        self.analytics = analytics_system
    
    def generate_dashboard_html(self, output_file: str = "analytics_dashboard.html"):
        """Generate HTML dashboard"""
        
        # Get current data
        metrics = self.analytics.calculate_business_metrics(24)
        patterns = self.analytics.get_pattern_insights()
        journeys = self.analytics.get_journey_analytics()
        
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>WINCASA Analytics Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .metric-card { background: white; padding: 20px; margin: 10px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric-value { font-size: 2em; font-weight: bold; color: #2c3e50; }
        .metric-label { color: #7f8c8d; margin-top: 5px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        h1, h2 { color: #2c3e50; }
        .chart { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ecf0f1; }
        th { background-color: #3498db; color: white; }
        .recommendation { background: #e8f4f8; padding: 15px; margin: 10px 0; border-left: 4px solid #3498db; }
    </style>
</head>
<body>
    <div class="container">
        <h1>WINCASA Analytics Dashboard</h1>
        <p>Generated: {timestamp}</p>
        
        <h2>Key Metrics (Last 24h)</h2>
        <div class="grid">
            <div class="metric-card">
                <div class="metric-value">{queries_per_hour:.1f}</div>
                <div class="metric-label">Queries per Hour</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{success_rate:.1%}</div>
                <div class="metric-label">Success Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{avg_response_time:.0f}ms</div>
                <div class="metric-label">Avg Response Time</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${avg_cost:.3f}</div>
                <div class="metric-label">Avg Cost per Query</div>
            </div>
        </div>
        
        <h2>Query Patterns</h2>
        <div class="chart">
            <table>
                <tr>
                    <th>Pattern</th>
                    <th>Type</th>
                    <th>Frequency</th>
                    <th>Success Rate</th>
                    <th>Avg Time</th>
                </tr>
                {pattern_rows}
            </table>
        </div>
        
        <h2>User Journey Analytics</h2>
        <div class="grid">
            <div class="metric-card">
                <div class="metric-value">{total_journeys}</div>
                <div class="metric-label">Total User Journeys</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{avg_queries_per_journey:.1f}</div>
                <div class="metric-label">Avg Queries per Journey</div>
            </div>
        </div>
        
        <h2>Recommendations</h2>
        {recommendations}
    </div>
</body>
</html>
        """
        
        # Fill in values
        pattern_rows = ""
        if patterns and "patterns" in patterns:
            for pattern_id, pattern_data in list(patterns["patterns"].items())[:10]:
                pattern_rows += f"""
                <tr>
                    <td>{pattern_id}</td>
                    <td>{pattern_data['type']}</td>
                    <td>{pattern_data['frequency']}</td>
                    <td>{pattern_data['success_rate']:.1%}</td>
                    <td>{pattern_data['avg_response_time_ms']:.0f}ms</td>
                </tr>
                """
        
        recommendations_html = ""
        recommendations = self.analytics._generate_top_recommendations()
        for rec in recommendations:
            recommendations_html += f"""
            <div class="recommendation">
                <strong>{rec['area'].title()} - {rec['priority'].title()} Priority</strong><br>
                {rec['recommendation']}<br>
                <em>Impact: {rec.get('impact', 'N/A')}</em>
            </div>
            """
        
        # Format the HTML
        html_content = html_content.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            queries_per_hour=metrics.get("query_volume", BusinessMetric("", "", 0, "", "", "")).value,
            success_rate=metrics.get("success_rate", BusinessMetric("", "", 0, "", "", "")).value,
            avg_response_time=metrics.get("avg_response_time", BusinessMetric("", "", 0, "", "", "")).value,
            avg_cost=metrics.get("query_cost", BusinessMetric("", "", 0, "", "", "")).value,
            pattern_rows=pattern_rows,
            total_journeys=journeys.get("total_journeys", 0),
            avg_queries_per_journey=journeys.get("avg_queries_per_journey", 0),
            recommendations=recommendations_html
        )
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_file

def test_analytics_system():
    """Test the analytics system"""
    print("🧪 Testing WINCASA Analytics System...")
    
    analytics = WincasaAnalyticsSystem(debug_mode=True)
    
    # Simulate some queries
    test_queries = [
        {
            "query": "Wer wohnt in der Bergstraße 15?",
            "user_id": "user_123",
            "response_time_ms": 45.2,
            "success": True,
            "engine": "unified_v2",
            "cost": 0.0
        },
        {
            "query": "Zeige alle Mieter in Essen",
            "user_id": "user_123",
            "response_time_ms": 1250.5,
            "success": True,
            "engine": "legacy_v1",
            "cost": 0.05
        },
        {
            "query": "Portfolio von Bona Casa GmbH",
            "user_id": "user_456",
            "response_time_ms": 89.3,
            "success": True,
            "engine": "unified_v2",
            "cost": 0.0
        },
        {
            "query": "Erstelle Bericht über Rückstände",
            "user_id": "user_456",
            "response_time_ms": 3500.0,
            "success": False,
            "engine": "legacy_v1",
            "cost": 0.05
        },
        {
            "query": "Kontostand Weber",
            "user_id": "user_789",
            "response_time_ms": 125.8,
            "success": True,
            "engine": "unified_v2",
            "cost": 0.0
        }
    ]
    
    print("\n📊 Logging test queries...")
    for query_data in test_queries:
        analytics.log_query(query_data)
        time.sleep(0.1)  # Simulate time between queries
    
    # Calculate metrics
    print("\n📈 Calculating business metrics...")
    metrics = analytics.calculate_business_metrics(1)  # Last hour
    
    for name, metric in metrics.items():
        print(f"   {metric.metric_name}: {metric.value:.2f} {metric.unit}")
    
    # Get pattern insights
    print("\n🔍 Pattern insights:")
    insights = analytics.get_pattern_insights()
    
    print(f"   Total patterns: {insights['total_patterns_identified']}")
    if "top_patterns" in insights:
        print(f"   Top patterns: {insights['top_patterns']}")
    
    # Generate report
    print("\n📄 Generating analytics report...")
    report_path = analytics.generate_analytics_report()
    print(f"   Report saved: {report_path}")
    
    # Create dashboard
    dashboard = AnalyticsDashboard(analytics)
    dashboard_path = dashboard.generate_dashboard_html()
    print(f"   Dashboard saved: {dashboard_path}")
    
    print("\n✅ Analytics System Test Complete")

if __name__ == "__main__":
    test_analytics_system()