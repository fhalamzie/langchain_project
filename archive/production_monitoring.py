#!/usr/bin/env python3
"""
WINCASA Production Monitoring
Real-time monitoring and alerting for production deployment.
"""

import json
import logging
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil
import requests


@dataclass
class SystemMetrics:
    """System performance metrics."""

    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    active_connections: int
    streamlit_status: str
    database_accessible: bool
    api_response_time: Optional[float]


@dataclass
class QueryMetrics:
    """Query performance metrics."""

    timestamp: str
    query_text: str
    processing_time: float
    success: bool
    error_message: Optional[str]
    sql_generated: Optional[str]
    result_count: Optional[int]


class ProductionMonitor:
    """Production monitoring and alerting system."""

    def __init__(
        self,
        log_dir: Path = Path("logs"),
        metrics_file: str = "production_metrics.json",
        alert_thresholds: Dict[str, float] = None,
    ):

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        self.metrics_file = self.log_dir / metrics_file
        self.query_log_file = self.log_dir / "query_metrics.json"

        # Default alert thresholds
        self.alert_thresholds = alert_thresholds or {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_usage_percent": 90.0,
            "api_response_time": 5.0,  # seconds
            "error_rate_threshold": 0.1,  # 10% error rate
        }

        # Setup logging
        self._setup_logging()

        # Initialize metrics storage
        self.system_metrics: List[SystemMetrics] = []
        self.query_metrics: List[QueryMetrics] = []

        # Load existing metrics
        self._load_metrics()

    def _setup_logging(self):
        """Setup monitoring logging."""
        log_file = self.log_dir / "monitoring.log"

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
        )

        self.logger = logging.getLogger("ProductionMonitor")

    def _load_metrics(self):
        """Load existing metrics from disk."""
        # Load system metrics
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, "r") as f:
                    data = json.load(f)
                    self.system_metrics = [SystemMetrics(**item) for item in data]
            except Exception as e:
                self.logger.warning(f"Could not load system metrics: {e}")

        # Load query metrics
        if self.query_log_file.exists():
            try:
                with open(self.query_log_file, "r") as f:
                    data = json.load(f)
                    self.query_metrics = [QueryMetrics(**item) for item in data]
            except Exception as e:
                self.logger.warning(f"Could not load query metrics: {e}")

    def _save_metrics(self):
        """Save metrics to disk."""
        # Save system metrics (keep last 1000 entries)
        recent_system = (
            self.system_metrics[-1000:]
            if len(self.system_metrics) > 1000
            else self.system_metrics
        )
        with open(self.metrics_file, "w") as f:
            json.dump([asdict(m) for m in recent_system], f, indent=2)

        # Save query metrics (keep last 500 entries)
        recent_queries = (
            self.query_metrics[-500:]
            if len(self.query_metrics) > 500
            else self.query_metrics
        )
        with open(self.query_log_file, "w") as f:
            json.dump([asdict(m) for m in recent_queries], f, indent=2)

    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        timestamp = datetime.now().isoformat()

        # System resource usage
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        # Check Streamlit process
        streamlit_status = self._check_streamlit_status()

        # Check database accessibility
        database_accessible = self._check_database_accessibility()

        # Measure API response time
        api_response_time = self._measure_api_response_time()

        # Count active connections (approximate)
        active_connections = len(
            [
                conn
                for conn in psutil.net_connections()
                if conn.status == psutil.CONN_ESTABLISHED
            ]
        )

        metrics = SystemMetrics(
            timestamp=timestamp,
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_usage_percent=(disk.used / disk.total) * 100,
            active_connections=active_connections,
            streamlit_status=streamlit_status,
            database_accessible=database_accessible,
            api_response_time=api_response_time,
        )

        self.system_metrics.append(metrics)
        self._check_system_alerts(metrics)

        return metrics

    def _check_streamlit_status(self) -> str:
        """Check if Streamlit is running."""
        try:
            # Check if Streamlit process is running on port 8501
            response = requests.get("http://localhost:8501/health", timeout=5)
            if response.status_code == 200:
                return "healthy"
            else:
                return "unhealthy"
        except requests.exceptions.RequestException:
            # Check for Streamlit process
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                if proc.info["name"] == "streamlit" or (
                    proc.info["cmdline"]
                    and "streamlit" in " ".join(proc.info["cmdline"])
                ):
                    return "running"
            return "stopped"

    def _check_database_accessibility(self) -> bool:
        """Check if database is accessible."""
        try:
            # Quick test using production config
            from production_config import ProductionConfig

            config = ProductionConfig.setup_production_environment()

            # Check if database file exists and is accessible
            db_path = Path(config["database"]["path"])
            return db_path.exists() and db_path.is_file()
        except Exception:
            return False

    def _measure_api_response_time(self) -> Optional[float]:
        """Measure API response time."""
        try:
            # Simple health check to measure response time
            start_time = time.time()
            response = requests.get("http://localhost:8501", timeout=10)
            response_time = time.time() - start_time

            if response.status_code == 200:
                return response_time
            else:
                return None
        except Exception:
            return None

    def _check_system_alerts(self, metrics: SystemMetrics):
        """Check for system alerts based on thresholds."""
        alerts = []

        if metrics.cpu_percent > self.alert_thresholds["cpu_percent"]:
            alerts.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")

        if metrics.memory_percent > self.alert_thresholds["memory_percent"]:
            alerts.append(f"High memory usage: {metrics.memory_percent:.1f}%")

        if metrics.disk_usage_percent > self.alert_thresholds["disk_usage_percent"]:
            alerts.append(f"High disk usage: {metrics.disk_usage_percent:.1f}%")

        if (
            metrics.api_response_time
            and metrics.api_response_time > self.alert_thresholds["api_response_time"]
        ):
            alerts.append(f"Slow API response: {metrics.api_response_time:.2f}s")

        if metrics.streamlit_status in ["stopped", "unhealthy"]:
            alerts.append(f"Streamlit service issue: {metrics.streamlit_status}")

        if not metrics.database_accessible:
            alerts.append("Database not accessible")

        # Log alerts
        for alert in alerts:
            self.logger.warning(f"ALERT: {alert}")

    def log_query_metrics(
        self,
        query_text: str,
        processing_time: float,
        success: bool,
        error_message: Optional[str] = None,
        sql_generated: Optional[str] = None,
        result_count: Optional[int] = None,
    ):
        """Log query performance metrics."""

        metrics = QueryMetrics(
            timestamp=datetime.now().isoformat(),
            query_text=query_text,
            processing_time=processing_time,
            success=success,
            error_message=error_message,
            sql_generated=sql_generated,
            result_count=result_count,
        )

        self.query_metrics.append(metrics)

        # Check query performance alerts
        if processing_time > 10.0:  # 10 second threshold
            self.logger.warning(
                f"Slow query detected: {processing_time:.2f}s - {query_text[:50]}..."
            )

        if not success:
            self.logger.error(f"Query failed: {error_message} - {query_text[:50]}...")

    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Generate performance summary for the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        cutoff_str = cutoff_time.isoformat()

        # Filter recent metrics
        recent_system = [m for m in self.system_metrics if m.timestamp > cutoff_str]
        recent_queries = [m for m in self.query_metrics if m.timestamp > cutoff_str]

        if not recent_system:
            return {"error": "No metrics available for the specified time period"}

        # System performance summary
        avg_cpu = sum(m.cpu_percent for m in recent_system) / len(recent_system)
        avg_memory = sum(m.memory_percent for m in recent_system) / len(recent_system)
        avg_api_time = sum(
            m.api_response_time for m in recent_system if m.api_response_time
        ) / max(1, len([m for m in recent_system if m.api_response_time]))

        # Query performance summary
        total_queries = len(recent_queries)
        successful_queries = len([q for q in recent_queries if q.success])
        avg_query_time = sum(q.processing_time for q in recent_queries) / max(
            1, total_queries
        )
        error_rate = (total_queries - successful_queries) / max(1, total_queries)

        # System health status
        latest_metrics = recent_system[-1] if recent_system else None
        health_status = "healthy"

        if latest_metrics:
            if (
                latest_metrics.cpu_percent > self.alert_thresholds["cpu_percent"]
                or latest_metrics.memory_percent
                > self.alert_thresholds["memory_percent"]
                or not latest_metrics.database_accessible
                or latest_metrics.streamlit_status in ["stopped", "unhealthy"]
            ):
                health_status = "degraded"

        if error_rate > self.alert_thresholds["error_rate_threshold"]:
            health_status = "critical"

        return {
            "time_period_hours": hours,
            "health_status": health_status,
            "system_metrics": {
                "average_cpu_percent": round(avg_cpu, 2),
                "average_memory_percent": round(avg_memory, 2),
                "average_api_response_time": round(avg_api_time, 3),
                "database_accessible": (
                    latest_metrics.database_accessible if latest_metrics else False
                ),
                "streamlit_status": (
                    latest_metrics.streamlit_status if latest_metrics else "unknown"
                ),
            },
            "query_metrics": {
                "total_queries": total_queries,
                "successful_queries": successful_queries,
                "error_rate": round(error_rate, 3),
                "average_processing_time": round(avg_query_time, 3),
            },
        }

    def start_monitoring(self, interval: int = 60):
        """Start continuous monitoring with specified interval (seconds)."""
        self.logger.info(f"Starting production monitoring (interval: {interval}s)")

        try:
            while True:
                metrics = self.collect_system_metrics()
                self._save_metrics()

                # Log current status
                self.logger.info(
                    f"System: CPU {metrics.cpu_percent:.1f}%, "
                    f"Memory {metrics.memory_percent:.1f}%, "
                    f"Streamlit {metrics.streamlit_status}, "
                    f"DB {'✓' if metrics.database_accessible else '✗'}"
                )

                time.sleep(interval)

        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Monitoring error: {e}")
        finally:
            self._save_metrics()


if __name__ == "__main__":
    """Run production monitoring."""
    import argparse

    parser = argparse.ArgumentParser(description="WINCASA Production Monitoring")
    parser.add_argument(
        "--interval", type=int, default=60, help="Monitoring interval in seconds"
    )
    parser.add_argument(
        "--summary", action="store_true", help="Show performance summary and exit"
    )
    parser.add_argument(
        "--hours", type=int, default=24, help="Hours for summary report"
    )

    args = parser.parse_args()

    monitor = ProductionMonitor()

    if args.summary:
        print("📊 WINCASA Production Performance Summary")
        print("=" * 50)

        summary = monitor.get_performance_summary(hours=args.hours)

        if "error" in summary:
            print(f"❌ {summary['error']}")
        else:
            status_icon = {"healthy": "✅", "degraded": "⚠️", "critical": "❌"}
            print(
                f"Health Status: {status_icon.get(summary['health_status'], '❓')} {summary['health_status'].upper()}"
            )
            print(f"Time Period: Last {summary['time_period_hours']} hours")
            print()

            print("🖥️  System Metrics:")
            sys_metrics = summary["system_metrics"]
            print(f"   CPU Usage: {sys_metrics['average_cpu_percent']}%")
            print(f"   Memory Usage: {sys_metrics['average_memory_percent']}%")
            print(f"   API Response Time: {sys_metrics['average_api_response_time']}s")
            print(
                f"   Database: {'✅ Accessible' if sys_metrics['database_accessible'] else '❌ Not Accessible'}"
            )
            print(f"   Streamlit: {sys_metrics['streamlit_status']}")
            print()

            print("💬 Query Metrics:")
            query_metrics = summary["query_metrics"]
            print(f"   Total Queries: {query_metrics['total_queries']}")
            print(f"   Successful: {query_metrics['successful_queries']}")
            print(f"   Error Rate: {query_metrics['error_rate']*100:.1f}%")
            print(
                f"   Avg Processing Time: {query_metrics['average_processing_time']}s"
            )
    else:
        monitor.start_monitoring(interval=args.interval)
