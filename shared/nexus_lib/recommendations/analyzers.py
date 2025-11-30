"""
Specialized Analyzers for Recommendations
Pattern detection and analysis for different domains
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import statistics

logger = logging.getLogger("nexus.recommendations.analyzers")


class AnalysisResult(BaseModel):
    """Result from an analyzer"""
    analyzer_name: str
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, float] = Field(default_factory=dict)
    patterns_detected: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class ReleasePatternAnalyzer:
    """
    Analyzes release patterns to identify timing and success factors
    """
    
    def __init__(self):
        self.name = "release_pattern_analyzer"
    
    async def analyze(
        self,
        releases: List[Dict[str, Any]],
        current_date: Optional[datetime] = None
    ) -> AnalysisResult:
        """
        Analyze release history for patterns
        
        Args:
            releases: List of past releases with metadata
            current_date: Reference date for analysis
        
        Returns:
            Analysis result with findings
        """
        current_date = current_date or datetime.utcnow()
        result = AnalysisResult(analyzer_name=self.name)
        
        if not releases:
            return result
        
        # Analyze success rates by day of week
        day_stats = {i: {"total": 0, "success": 0} for i in range(7)}
        for release in releases:
            release_date = release.get("date")
            if isinstance(release_date, str):
                release_date = datetime.fromisoformat(release_date)
            if release_date:
                day = release_date.weekday()
                day_stats[day]["total"] += 1
                if release.get("success", True):
                    day_stats[day]["success"] += 1
        
        # Find best and worst days
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        best_day = None
        best_rate = 0
        worst_day = None
        worst_rate = 1.0
        
        for day, stats in day_stats.items():
            if stats["total"] > 0:
                rate = stats["success"] / stats["total"]
                if rate > best_rate:
                    best_rate = rate
                    best_day = day
                if rate < worst_rate:
                    worst_rate = rate
                    worst_day = day
        
        if best_day is not None:
            result.findings.append({
                "type": "best_release_day",
                "day": day_names[best_day],
                "success_rate": best_rate,
            })
            result.patterns_detected.append(f"Best release day: {day_names[best_day]}")
        
        if worst_day is not None and worst_rate < 0.8:
            result.findings.append({
                "type": "risky_release_day",
                "day": day_names[worst_day],
                "success_rate": worst_rate,
            })
            result.patterns_detected.append(f"Risky release day: {day_names[worst_day]}")
        
        # Calculate overall metrics
        total_releases = len(releases)
        successful_releases = sum(1 for r in releases if r.get("success", True))
        
        result.metrics = {
            "total_releases": total_releases,
            "success_rate": successful_releases / total_releases if total_releases > 0 else 0,
            "avg_releases_per_month": total_releases / max(1, self._months_span(releases)),
        }
        
        result.confidence = min(0.95, 0.5 + (total_releases / 20) * 0.45)
        
        return result
    
    def _months_span(self, releases: List[Dict]) -> int:
        """Calculate the number of months spanned by releases"""
        dates = []
        for r in releases:
            d = r.get("date")
            if isinstance(d, str):
                d = datetime.fromisoformat(d)
            if d:
                dates.append(d)
        
        if len(dates) < 2:
            return 1
        
        dates.sort()
        delta = dates[-1] - dates[0]
        return max(1, delta.days // 30)


class HygienePatternAnalyzer:
    """
    Analyzes Jira hygiene patterns over time
    """
    
    def __init__(self):
        self.name = "hygiene_pattern_analyzer"
    
    async def analyze(
        self,
        hygiene_history: List[Dict[str, Any]],
        current_score: Optional[float] = None
    ) -> AnalysisResult:
        """
        Analyze hygiene score patterns
        
        Args:
            hygiene_history: List of hygiene check results over time
            current_score: Current hygiene score
        
        Returns:
            Analysis result with findings
        """
        result = AnalysisResult(analyzer_name=self.name)
        
        if not hygiene_history:
            return result
        
        # Extract scores
        scores = [h.get("score", 0) for h in hygiene_history if h.get("score") is not None]
        
        if not scores:
            return result
        
        # Calculate statistics
        avg_score = statistics.mean(scores)
        recent_scores = scores[-5:] if len(scores) >= 5 else scores
        recent_avg = statistics.mean(recent_scores)
        
        # Detect trend
        if len(scores) >= 3:
            trend = "stable"
            if recent_avg > avg_score + 5:
                trend = "improving"
                result.patterns_detected.append("Hygiene score improving")
            elif recent_avg < avg_score - 5:
                trend = "declining"
                result.patterns_detected.append("Hygiene score declining")
            
            result.findings.append({
                "type": "trend",
                "value": trend,
                "recent_avg": recent_avg,
                "historical_avg": avg_score,
            })
        
        # Identify common violation types
        violation_counts = {}
        for h in hygiene_history:
            for violation_type, count in h.get("violations", {}).items():
                violation_counts[violation_type] = violation_counts.get(violation_type, 0) + count
        
        if violation_counts:
            top_violation = max(violation_counts.items(), key=lambda x: x[1])
            result.findings.append({
                "type": "top_violation",
                "field": top_violation[0],
                "count": top_violation[1],
            })
            result.patterns_detected.append(f"Most common violation: {top_violation[0]}")
        
        result.metrics = {
            "average_score": avg_score,
            "recent_average": recent_avg,
            "score_variance": statistics.variance(scores) if len(scores) > 1 else 0,
            "total_checks": len(hygiene_history),
        }
        
        result.confidence = min(0.9, 0.4 + (len(hygiene_history) / 10) * 0.5)
        
        return result


class VelocityAnalyzer:
    """
    Analyzes sprint velocity patterns
    """
    
    def __init__(self):
        self.name = "velocity_analyzer"
    
    async def analyze(
        self,
        velocity_history: List[Dict[str, Any]],
        team_size: Optional[int] = None
    ) -> AnalysisResult:
        """
        Analyze velocity patterns
        
        Args:
            velocity_history: List of sprint velocity data
            team_size: Current team size
        
        Returns:
            Analysis result with findings
        """
        result = AnalysisResult(analyzer_name=self.name)
        
        if not velocity_history:
            return result
        
        # Extract velocities
        velocities = [v.get("velocity", 0) for v in velocity_history if v.get("velocity") is not None]
        
        if not velocities:
            return result
        
        # Calculate statistics
        avg_velocity = statistics.mean(velocities)
        std_dev = statistics.stdev(velocities) if len(velocities) > 1 else 0
        
        # Predictability score (lower variance = higher predictability)
        cv = std_dev / avg_velocity if avg_velocity > 0 else 1
        predictability = max(0, 1 - cv)
        
        result.metrics = {
            "average_velocity": avg_velocity,
            "std_deviation": std_dev,
            "coefficient_of_variation": cv,
            "predictability_score": predictability,
            "velocity_per_person": avg_velocity / team_size if team_size else 0,
        }
        
        # Detect patterns
        if cv > 0.3:
            result.patterns_detected.append("High velocity variance (unpredictable)")
            result.findings.append({
                "type": "high_variance",
                "cv": cv,
                "recommendation": "Improve estimation practices",
            })
        
        if len(velocities) >= 4:
            recent = velocities[-4:]
            if all(recent[i] < recent[i-1] for i in range(1, len(recent))):
                result.patterns_detected.append("Declining velocity trend")
                result.findings.append({
                    "type": "declining_trend",
                    "recent_velocities": recent,
                })
        
        result.confidence = min(0.85, 0.3 + (len(velocities) / 8) * 0.55)
        
        return result


class RiskAnalyzer:
    """
    Analyzes risk factors for releases
    """
    
    def __init__(self):
        self.name = "risk_analyzer"
    
    async def analyze(
        self,
        risk_data: Dict[str, Any]
    ) -> AnalysisResult:
        """
        Analyze risk factors
        
        Args:
            risk_data: Current risk data including:
                - blockers: List of blocking issues
                - vulnerabilities: Security scan results
                - test_coverage: Coverage percentage
                - build_failures: Recent build failures
        
        Returns:
            Analysis result with risk assessment
        """
        result = AnalysisResult(analyzer_name=self.name)
        
        total_risk_score = 0
        risk_factors = []
        
        # Analyze blockers
        blockers = risk_data.get("blockers", [])
        if blockers:
            blocker_risk = min(30, len(blockers) * 10)
            total_risk_score += blocker_risk
            risk_factors.append({
                "factor": "blockers",
                "count": len(blockers),
                "risk_contribution": blocker_risk,
            })
            result.patterns_detected.append(f"{len(blockers)} active blockers")
        
        # Analyze vulnerabilities
        vulns = risk_data.get("vulnerabilities", {})
        critical_vulns = vulns.get("critical", 0)
        high_vulns = vulns.get("high", 0)
        
        vuln_risk = critical_vulns * 15 + high_vulns * 5
        if vuln_risk > 0:
            total_risk_score += min(40, vuln_risk)
            risk_factors.append({
                "factor": "security",
                "critical": critical_vulns,
                "high": high_vulns,
                "risk_contribution": min(40, vuln_risk),
            })
            if critical_vulns > 0:
                result.patterns_detected.append(f"{critical_vulns} critical vulnerabilities")
        
        # Analyze test coverage
        coverage = risk_data.get("test_coverage", 80)
        if coverage < 80:
            coverage_risk = max(0, (80 - coverage) / 2)
            total_risk_score += coverage_risk
            risk_factors.append({
                "factor": "test_coverage",
                "coverage": coverage,
                "risk_contribution": coverage_risk,
            })
            result.patterns_detected.append(f"Low test coverage: {coverage}%")
        
        # Analyze build failures
        build_failures = risk_data.get("build_failures", 0)
        if build_failures > 0:
            build_risk = min(20, build_failures * 5)
            total_risk_score += build_risk
            risk_factors.append({
                "factor": "build_stability",
                "failures": build_failures,
                "risk_contribution": build_risk,
            })
        
        # Calculate overall risk level
        risk_level = "low"
        if total_risk_score > 50:
            risk_level = "critical"
        elif total_risk_score > 30:
            risk_level = "high"
        elif total_risk_score > 15:
            risk_level = "medium"
        
        result.findings = risk_factors
        result.metrics = {
            "total_risk_score": total_risk_score,
            "risk_level": risk_level,
            "blocker_count": len(blockers),
            "critical_vulnerabilities": critical_vulns,
        }
        
        result.confidence = 0.9
        
        return result

