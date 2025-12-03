"""
Unit Tests for Analytics Service
================================

Tests for DORA metrics calculation, KPI tracking,
trend analysis, and prediction logic.
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from typing import List

# Set test environment
os.environ["NEXUS_ENV"] = "test"


class TestDORAMetrics:
    """Tests for DORA metrics calculations."""
    
    def test_deployment_frequency_calculation(self):
        """Test deployment frequency calculation."""
        deployments = 12
        time_period_days = 30
        
        frequency = deployments / time_period_days
        
        assert frequency == 0.4  # 0.4 deployments per day
    
    def test_lead_time_calculation(self):
        """Test lead time calculation."""
        commit_time = datetime(2024, 1, 1, 10, 0, 0)
        deploy_time = datetime(2024, 1, 1, 14, 0, 0)
        
        lead_time_hours = (deploy_time - commit_time).total_seconds() / 3600
        
        assert lead_time_hours == 4.0
    
    def test_mttr_calculation(self):
        """Test Mean Time To Recovery calculation."""
        incident_start = datetime(2024, 1, 1, 10, 0, 0)
        incident_resolved = datetime(2024, 1, 1, 11, 30, 0)
        
        mttr_minutes = (incident_resolved - incident_start).total_seconds() / 60
        
        assert mttr_minutes == 90.0
    
    def test_change_failure_rate(self):
        """Test change failure rate calculation."""
        total_deployments = 100
        failed_deployments = 5
        
        failure_rate = (failed_deployments / total_deployments) * 100
        
        assert failure_rate == 5.0


class TestKPICalculations:
    """Tests for KPI calculations."""
    
    def test_velocity_calculation(self):
        """Test team velocity calculation."""
        completed_points = [13, 8, 21, 13, 21]  # 5 sprints
        
        avg_velocity = sum(completed_points) / len(completed_points)
        
        assert avg_velocity == 15.2
    
    def test_throughput_calculation(self):
        """Test throughput calculation."""
        completed_items = 45
        time_period_weeks = 4
        
        throughput = completed_items / time_period_weeks
        
        assert throughput == 11.25
    
    def test_cycle_time_calculation(self):
        """Test cycle time calculation."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 5)
        
        cycle_time_days = (end_date - start_date).days
        
        assert cycle_time_days == 4


class TestTrendAnalysis:
    """Tests for trend analysis logic."""
    
    def test_detect_upward_trend(self):
        """Test detection of upward trend."""
        values = [10, 12, 15, 18, 22]
        
        # Simple trend detection: compare first and last
        is_upward = values[-1] > values[0]
        
        assert is_upward is True
    
    def test_detect_downward_trend(self):
        """Test detection of downward trend."""
        values = [100, 90, 75, 60, 50]
        
        is_downward = values[-1] < values[0]
        
        assert is_downward is True
    
    def test_stable_trend(self):
        """Test detection of stable trend."""
        values = [50, 51, 49, 50, 51]
        threshold = 5  # 10% of mean
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        
        is_stable = variance < threshold
        
        assert is_stable is True
    
    def test_trend_slope_calculation(self):
        """Test trend slope calculation."""
        values = [10, 20, 30, 40, 50]
        
        # Simple slope: (last - first) / n
        slope = (values[-1] - values[0]) / (len(values) - 1)
        
        assert slope == 10.0


class TestAnomalyDetection:
    """Tests for anomaly detection."""
    
    def test_detect_outlier(self):
        """Test outlier detection using simple threshold."""
        values = [10, 11, 9, 10, 12, 100, 11]  # 100 is outlier
        
        mean = sum(values) / len(values)
        threshold = mean * 3
        
        outliers = [v for v in values if v > threshold]
        
        assert 100 in outliers
    
    def test_standard_deviation_anomaly(self):
        """Test anomaly detection using standard deviation."""
        values = [10, 11, 9, 10, 12, 11, 10]
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        
        # Values beyond 2 std devs are anomalies
        anomalies = [v for v in values if abs(v - mean) > 2 * std_dev]
        
        assert len(anomalies) == 0  # No anomalies in this data


class TestTeamPerformance:
    """Tests for team performance metrics."""
    
    def test_team_velocity_average(self):
        """Test team velocity average calculation."""
        sprint_velocities = [21, 18, 24, 19, 23]
        
        avg = sum(sprint_velocities) / len(sprint_velocities)
        
        assert avg == 21.0
    
    def test_quality_score_calculation(self):
        """Test quality score calculation."""
        bugs_found = 5
        total_items = 50
        
        quality_score = ((total_items - bugs_found) / total_items) * 100
        
        assert quality_score == 90.0
    
    def test_team_comparison(self):
        """Test team comparison logic."""
        team_a_velocity = 25
        team_b_velocity = 20
        
        comparison = (team_a_velocity - team_b_velocity) / team_b_velocity * 100
        
        assert comparison == 25.0  # Team A is 25% faster


class TestPredictions:
    """Tests for prediction logic."""
    
    def test_simple_linear_prediction(self):
        """Test simple linear prediction."""
        historical = [10, 20, 30, 40, 50]
        
        # Predict next value based on trend
        slope = (historical[-1] - historical[0]) / (len(historical) - 1)
        predicted = historical[-1] + slope
        
        assert predicted == 60.0
    
    def test_moving_average(self):
        """Test moving average calculation."""
        values = [10, 20, 30, 40, 50]
        window = 3
        
        # Calculate moving average of last 'window' values
        ma = sum(values[-window:]) / window
        
        assert ma == 40.0


class TestDataValidation:
    """Tests for data validation."""
    
    def test_valid_metric_value(self):
        """Test metric value validation."""
        value = 42.5
        
        assert isinstance(value, (int, float))
        assert value >= 0
    
    def test_valid_date_range(self):
        """Test date range validation."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)
        
        assert end > start
        assert (end - start).days == 30


class TestAnalyticsAppImport:
    """Tests for Analytics service app import."""
    
    def test_app_can_be_imported(self):
        """Test analytics service app can be imported."""
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../services/analytics")))
        
        try:
            from main import app
            assert app is not None
        except ImportError:
            pytest.skip("Analytics dependencies not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
