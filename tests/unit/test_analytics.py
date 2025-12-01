"""
Unit Tests for Analytics Service
================================

Tests for the Advanced Analytics Dashboard including
DORA metrics, KPIs, trend analysis, and predictions.
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../services/analytics")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../shared")))

# Set test environment
os.environ["NEXUS_ENV"] = "test"


class TestDoraMetrics:
    """Tests for DORA metrics calculation."""
    
    def test_deployment_frequency_daily(self):
        """Test deployment frequency calculation for daily deploys."""
        from main import AnalyticsEngine
        
        # Mock deployment data: 7 deployments in 7 days
        deployments = [
            {"timestamp": datetime.now() - timedelta(days=i)}
            for i in range(7)
        ]
        
        engine = AnalyticsEngine()
        freq = engine._calculate_deployment_frequency(deployments, days=7)
        
        assert freq == 1.0  # 1 per day
    
    def test_deployment_frequency_weekly(self):
        """Test deployment frequency for weekly deploys."""
        from main import AnalyticsEngine
        
        # Mock deployment data: 1 deployment in 7 days
        deployments = [{"timestamp": datetime.now() - timedelta(days=3)}]
        
        engine = AnalyticsEngine()
        freq = engine._calculate_deployment_frequency(deployments, days=7)
        
        assert freq == pytest.approx(1/7, rel=0.1)
    
    def test_lead_time_for_changes(self):
        """Test lead time calculation."""
        from main import AnalyticsEngine
        
        changes = [
            {
                "commit_time": datetime.now() - timedelta(hours=48),
                "deploy_time": datetime.now() - timedelta(hours=24)
            },
            {
                "commit_time": datetime.now() - timedelta(hours=24),
                "deploy_time": datetime.now()
            }
        ]
        
        engine = AnalyticsEngine()
        lead_time = engine._calculate_lead_time(changes)
        
        # Average should be 24 hours
        assert lead_time == pytest.approx(24, rel=0.5)
    
    def test_change_failure_rate(self):
        """Test change failure rate calculation."""
        from main import AnalyticsEngine
        
        # 2 failures out of 10 deployments
        deployments = [
            {"status": "SUCCESS"},
            {"status": "SUCCESS"},
            {"status": "FAILURE"},
            {"status": "SUCCESS"},
            {"status": "SUCCESS"},
            {"status": "SUCCESS"},
            {"status": "SUCCESS"},
            {"status": "FAILURE"},
            {"status": "SUCCESS"},
            {"status": "SUCCESS"},
        ]
        
        engine = AnalyticsEngine()
        rate = engine._calculate_change_failure_rate(deployments)
        
        assert rate == pytest.approx(0.2, rel=0.01)  # 20%
    
    def test_mttr_calculation(self):
        """Test Mean Time to Recovery calculation."""
        from main import AnalyticsEngine
        
        incidents = [
            {
                "start_time": datetime.now() - timedelta(hours=3),
                "end_time": datetime.now() - timedelta(hours=2)
            },
            {
                "start_time": datetime.now() - timedelta(hours=5),
                "end_time": datetime.now() - timedelta(hours=3)
            }
        ]
        
        engine = AnalyticsEngine()
        mttr = engine._calculate_mttr(incidents)
        
        # Average should be 1.5 hours
        assert mttr == pytest.approx(1.5, rel=0.1)


class TestKPIAggregation:
    """Tests for KPI aggregation."""
    
    @pytest.fixture
    def sample_kpis(self):
        """Sample KPI data."""
        return {
            "release_velocity": 12.5,
            "ticket_completion_rate": 94.3,
            "sprint_burndown_accuracy": 88.7,
            "defect_escape_rate": 2.1,
            "code_review_coverage": 98.5,
            "test_automation_rate": 85.0
        }
    
    def test_aggregate_kpis(self, sample_kpis):
        """Test KPI aggregation into categories."""
        from main import AnalyticsEngine
        
        engine = AnalyticsEngine()
        aggregated = engine._aggregate_kpis(sample_kpis)
        
        assert "delivery" in aggregated
        assert "quality" in aggregated
        assert "team" in aggregated
    
    def test_kpi_thresholds(self, sample_kpis):
        """Test KPI threshold evaluation."""
        from main import AnalyticsEngine
        
        engine = AnalyticsEngine()
        evaluation = engine._evaluate_kpi_thresholds(sample_kpis)
        
        # High completion rate should be "green"
        assert evaluation["ticket_completion_rate"]["status"] in ["green", "healthy"]
        
        # All KPIs should have status
        for kpi, result in evaluation.items():
            assert "status" in result
            assert "threshold" in result


class TestTrendAnalysis:
    """Tests for trend analysis."""
    
    @pytest.fixture
    def sample_timeseries(self):
        """Sample time series data."""
        return [
            {"timestamp": datetime.now() - timedelta(days=6), "value": 80},
            {"timestamp": datetime.now() - timedelta(days=5), "value": 82},
            {"timestamp": datetime.now() - timedelta(days=4), "value": 85},
            {"timestamp": datetime.now() - timedelta(days=3), "value": 83},
            {"timestamp": datetime.now() - timedelta(days=2), "value": 88},
            {"timestamp": datetime.now() - timedelta(days=1), "value": 90},
            {"timestamp": datetime.now(), "value": 92},
        ]
    
    def test_detect_upward_trend(self, sample_timeseries):
        """Test detection of upward trend."""
        from main import AnalyticsEngine
        
        engine = AnalyticsEngine()
        trend = engine._detect_trend(sample_timeseries)
        
        assert trend["direction"] == "up"
        assert trend["strength"] > 0
    
    def test_detect_downward_trend(self, sample_timeseries):
        """Test detection of downward trend."""
        from main import AnalyticsEngine
        
        # Reverse the data for downward trend
        reversed_data = [
            {**item, "value": 100 - item["value"] + 80}
            for item in sample_timeseries
        ]
        
        engine = AnalyticsEngine()
        trend = engine._detect_trend(reversed_data)
        
        assert trend["direction"] == "down"
    
    def test_trend_slope_calculation(self, sample_timeseries):
        """Test slope calculation for trend."""
        from main import AnalyticsEngine
        
        engine = AnalyticsEngine()
        slope = engine._calculate_slope(sample_timeseries)
        
        # Positive slope for upward data
        assert slope > 0


class TestAnomalyDetection:
    """Tests for anomaly detection."""
    
    @pytest.fixture
    def normal_data(self):
        """Normal data without anomalies."""
        return [85, 87, 86, 88, 85, 87, 86, 88, 85, 86]
    
    @pytest.fixture
    def anomaly_data(self):
        """Data with an anomaly."""
        return [85, 87, 86, 88, 15, 87, 86, 88, 85, 86]  # 15 is anomaly
    
    def test_no_anomalies_in_normal_data(self, normal_data):
        """Test no anomalies detected in normal data."""
        from main import AnalyticsEngine
        
        engine = AnalyticsEngine()
        anomalies = engine._detect_anomalies(normal_data)
        
        assert len(anomalies) == 0
    
    def test_detect_anomaly(self, anomaly_data):
        """Test anomaly detection."""
        from main import AnalyticsEngine
        
        engine = AnalyticsEngine()
        anomalies = engine._detect_anomalies(anomaly_data, threshold=2.0)
        
        assert len(anomalies) >= 1
        assert 15 in [a["value"] for a in anomalies]
    
    def test_anomaly_severity(self, anomaly_data):
        """Test anomaly severity classification."""
        from main import AnalyticsEngine
        
        engine = AnalyticsEngine()
        anomalies = engine._detect_anomalies(anomaly_data, threshold=2.0)
        
        for anomaly in anomalies:
            assert "severity" in anomaly
            assert anomaly["severity"] in ["low", "medium", "high", "critical"]


class TestPredictions:
    """Tests for predictive analytics."""
    
    @pytest.fixture
    def historical_data(self):
        """Historical data for predictions."""
        base = datetime.now() - timedelta(days=30)
        return [
            {"timestamp": base + timedelta(days=i), "value": 80 + i * 0.5}
            for i in range(30)
        ]
    
    def test_predict_future_values(self, historical_data):
        """Test future value prediction."""
        from main import AnalyticsEngine
        
        engine = AnalyticsEngine()
        predictions = engine._predict_future(
            historical_data,
            days_ahead=7
        )
        
        assert len(predictions) == 7
        # Predictions should continue the trend
        assert predictions[-1]["value"] > predictions[0]["value"]
    
    def test_prediction_confidence(self, historical_data):
        """Test prediction confidence intervals."""
        from main import AnalyticsEngine
        
        engine = AnalyticsEngine()
        predictions = engine._predict_future(
            historical_data,
            days_ahead=7,
            include_confidence=True
        )
        
        for pred in predictions:
            assert "confidence_lower" in pred
            assert "confidence_upper" in pred
            assert pred["confidence_lower"] <= pred["value"] <= pred["confidence_upper"]


class TestTeamPerformance:
    """Tests for team performance metrics."""
    
    @pytest.fixture
    def team_data(self):
        """Sample team performance data."""
        return {
            "team_id": "platform",
            "members": ["alice", "bob", "charlie"],
            "completed_tickets": 45,
            "story_points": 89,
            "bugs_introduced": 3,
            "code_reviews": 67,
            "pr_merge_time_hours": 4.2
        }
    
    def test_calculate_team_velocity(self, team_data):
        """Test team velocity calculation."""
        from main import AnalyticsEngine
        
        engine = AnalyticsEngine()
        velocity = engine._calculate_team_velocity(team_data, sprint_days=14)
        
        assert velocity > 0
        # ~89 points / 14 days ≈ 6.36 per day
        assert velocity == pytest.approx(6.36, rel=0.5)
    
    def test_calculate_team_quality_score(self, team_data):
        """Test team quality score calculation."""
        from main import AnalyticsEngine
        
        engine = AnalyticsEngine()
        quality = engine._calculate_quality_score(team_data)
        
        assert 0 <= quality <= 100
    
    def test_team_comparison(self):
        """Test team comparison metrics."""
        from main import AnalyticsEngine
        
        teams = [
            {"team_id": "platform", "velocity": 6.5, "quality": 92},
            {"team_id": "mobile", "velocity": 5.8, "quality": 88},
            {"team_id": "api", "velocity": 7.2, "quality": 95}
        ]
        
        engine = AnalyticsEngine()
        comparison = engine._compare_teams(teams)
        
        assert "rankings" in comparison
        assert comparison["rankings"]["velocity"][0] == "api"
        assert comparison["rankings"]["quality"][0] == "api"


class TestDataIngestion:
    """Tests for data ingestion."""
    
    def test_ingest_build_data(self):
        """Test ingestion of build data."""
        from main import AnalyticsEngine
        
        build_data = {
            "job_name": "nexus-main",
            "build_number": 142,
            "status": "SUCCESS",
            "duration_seconds": 485,
            "timestamp": datetime.now().isoformat()
        }
        
        engine = AnalyticsEngine()
        result = engine.ingest_data("build", build_data)
        
        assert result["status"] == "ingested"
        assert result["data_type"] == "build"
    
    def test_ingest_ticket_data(self):
        """Test ingestion of ticket data."""
        from main import AnalyticsEngine
        
        ticket_data = {
            "key": "PROJ-123",
            "status": "Done",
            "story_points": 5,
            "cycle_time_days": 3,
            "timestamp": datetime.now().isoformat()
        }
        
        engine = AnalyticsEngine()
        result = engine.ingest_data("ticket", ticket_data)
        
        assert result["status"] == "ingested"
    
    def test_batch_ingest(self):
        """Test batch data ingestion."""
        from main import AnalyticsEngine
        
        batch = [
            {"type": "build", "data": {"status": "SUCCESS"}},
            {"type": "build", "data": {"status": "FAILURE"}},
            {"type": "ticket", "data": {"status": "Done"}},
        ]
        
        engine = AnalyticsEngine()
        results = engine.batch_ingest(batch)
        
        assert len(results) == 3
        assert all(r["status"] == "ingested" for r in results)


class TestMetricsExport:
    """Tests for Prometheus metrics export."""
    
    def test_metrics_format(self):
        """Test metrics are in Prometheus format."""
        from main import generate_prometheus_metrics
        
        metrics = generate_prometheus_metrics()
        
        # Check for expected metric names
        assert "nexus_analytics_deployment_frequency" in metrics
        assert "nexus_analytics_lead_time_seconds" in metrics
        assert "nexus_analytics_change_failure_rate" in metrics
        assert "nexus_analytics_mttr_seconds" in metrics
    
    def test_metrics_have_labels(self):
        """Test metrics include appropriate labels."""
        from main import generate_prometheus_metrics
        
        metrics = generate_prometheus_metrics()
        
        # Check for label patterns
        assert 'team=' in metrics or 'project=' in metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

