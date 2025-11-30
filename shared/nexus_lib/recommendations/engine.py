"""
AI-Powered Recommendation Engine
Generates intelligent suggestions based on historical data and patterns
"""
import os
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

logger = logging.getLogger("nexus.recommendations")


class RecommendationType(str, Enum):
    """Types of recommendations"""
    RELEASE_TIMING = "release_timing"
    HYGIENE_IMPROVEMENT = "hygiene_improvement"
    VELOCITY_OPTIMIZATION = "velocity_optimization"
    RISK_MITIGATION = "risk_mitigation"
    RESOURCE_ALLOCATION = "resource_allocation"
    PROCESS_IMPROVEMENT = "process_improvement"
    BLOCKERS_RESOLUTION = "blockers_resolution"


class RecommendationPriority(str, Enum):
    """Priority levels for recommendations"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Recommendation(BaseModel):
    """A single recommendation"""
    id: str
    type: RecommendationType
    priority: RecommendationPriority
    title: str
    description: str
    rationale: str
    
    # Actionable details
    action_items: List[str] = Field(default_factory=list)
    affected_items: List[str] = Field(default_factory=list)  # Ticket keys, repos, etc.
    
    # Impact estimation
    estimated_impact: str = ""
    confidence_score: float = Field(default=0.0, ge=0, le=1)
    
    # Context
    data_sources: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RecommendationContext(BaseModel):
    """Context for generating recommendations"""
    project_key: Optional[str] = None
    release_version: Optional[str] = None
    time_range_days: int = 30
    
    # Current state
    hygiene_score: Optional[float] = None
    sprint_velocity: Optional[float] = None
    active_blockers: int = 0
    open_vulnerabilities: int = 0
    
    # Historical data
    past_releases: List[Dict[str, Any]] = Field(default_factory=list)
    past_hygiene_scores: List[float] = Field(default_factory=list)
    past_velocities: List[float] = Field(default_factory=list)


class RecommendationEngine:
    """
    AI-powered recommendation engine
    
    Analyzes historical data and current state to generate
    actionable recommendations for release management.
    """
    
    def __init__(self, memory_client=None, llm_client=None):
        self.memory = memory_client
        self.llm = llm_client
        self._analyzers = []
        
        logger.info("Recommendation engine initialized")
    
    async def generate_recommendations(
        self,
        context: RecommendationContext,
        max_recommendations: int = 10,
    ) -> List[Recommendation]:
        """
        Generate recommendations based on context
        
        Args:
            context: Current state and historical context
            max_recommendations: Maximum number of recommendations
        
        Returns:
            List of prioritized recommendations
        """
        recommendations = []
        
        # 1. Release timing recommendations
        if context.project_key and context.release_version:
            timing_recs = await self._analyze_release_timing(context)
            recommendations.extend(timing_recs)
        
        # 2. Hygiene improvement recommendations
        if context.hygiene_score is not None:
            hygiene_recs = await self._analyze_hygiene(context)
            recommendations.extend(hygiene_recs)
        
        # 3. Velocity optimization recommendations
        if context.sprint_velocity is not None:
            velocity_recs = await self._analyze_velocity(context)
            recommendations.extend(velocity_recs)
        
        # 4. Risk mitigation recommendations
        risk_recs = await self._analyze_risks(context)
        recommendations.extend(risk_recs)
        
        # 5. Process improvement recommendations
        process_recs = await self._analyze_processes(context)
        recommendations.extend(process_recs)
        
        # Sort by priority and confidence
        priority_order = {
            RecommendationPriority.CRITICAL: 0,
            RecommendationPriority.HIGH: 1,
            RecommendationPriority.MEDIUM: 2,
            RecommendationPriority.LOW: 3,
            RecommendationPriority.INFO: 4,
        }
        
        recommendations.sort(
            key=lambda r: (priority_order[r.priority], -r.confidence_score)
        )
        
        return recommendations[:max_recommendations]
    
    async def _analyze_release_timing(
        self,
        context: RecommendationContext
    ) -> List[Recommendation]:
        """Analyze release timing patterns"""
        recommendations = []
        
        # Check for Friday releases (generally risky)
        today = datetime.now()
        if today.weekday() >= 4:  # Thursday or Friday
            recommendations.append(Recommendation(
                id=f"timing-{today.strftime('%Y%m%d')}-1",
                type=RecommendationType.RELEASE_TIMING,
                priority=RecommendationPriority.MEDIUM,
                title="Consider postponing release to early next week",
                description="Releases on Thursday/Friday have historically higher incident rates due to reduced support availability over weekends.",
                rationale="Based on industry best practices and historical incident data, releases early in the week (Tuesday-Wednesday) allow for better incident response.",
                action_items=[
                    "Evaluate if release can wait until Tuesday",
                    "If urgent, ensure on-call coverage for weekend",
                    "Prepare rollback plan",
                ],
                estimated_impact="Reduces weekend incident risk by ~40%",
                confidence_score=0.85,
                data_sources=["industry_best_practices", "historical_incidents"],
            ))
        
        # Check past release patterns
        if context.past_releases:
            failed_releases = [r for r in context.past_releases if r.get("success") == False]
            if len(failed_releases) / max(len(context.past_releases), 1) > 0.3:
                recommendations.append(Recommendation(
                    id=f"timing-{today.strftime('%Y%m%d')}-2",
                    type=RecommendationType.RELEASE_TIMING,
                    priority=RecommendationPriority.HIGH,
                    title="High release failure rate detected",
                    description=f"{len(failed_releases)} of last {len(context.past_releases)} releases had issues. Consider additional validation.",
                    rationale="Historical failure rate exceeds 30% threshold, indicating systemic issues in release process.",
                    action_items=[
                        "Review common failure patterns",
                        "Add additional pre-release checks",
                        "Consider implementing feature flags",
                        "Increase test coverage in affected areas",
                    ],
                    estimated_impact="Could reduce release failures by 50%+",
                    confidence_score=0.9,
                    data_sources=["release_history"],
                ))
        
        return recommendations
    
    async def _analyze_hygiene(
        self,
        context: RecommendationContext
    ) -> List[Recommendation]:
        """Analyze Jira hygiene patterns"""
        recommendations = []
        
        if context.hygiene_score is None:
            return recommendations
        
        # Low hygiene score
        if context.hygiene_score < 70:
            priority = RecommendationPriority.HIGH if context.hygiene_score < 50 else RecommendationPriority.MEDIUM
            
            recommendations.append(Recommendation(
                id=f"hygiene-score-{datetime.now().strftime('%Y%m%d')}",
                type=RecommendationType.HYGIENE_IMPROVEMENT,
                priority=priority,
                title=f"Jira hygiene score is {context.hygiene_score:.0f}% - below target",
                description="Low hygiene scores indicate incomplete ticket data which affects release planning accuracy and velocity tracking.",
                rationale="Tickets missing Labels, Fix Version, or Story Points cannot be properly tracked for release readiness.",
                action_items=[
                    "Review tickets with missing required fields",
                    "Set up hygiene notifications for team",
                    "Add hygiene check to Definition of Ready",
                    "Consider blocking tickets without required fields from sprints",
                ],
                estimated_impact="Improves release planning accuracy by 25-40%",
                confidence_score=0.95,
                data_sources=["hygiene_agent", "jira_metrics"],
            ))
        
        # Declining hygiene trend
        if len(context.past_hygiene_scores) >= 3:
            recent = context.past_hygiene_scores[-3:]
            if all(recent[i] < recent[i-1] for i in range(1, len(recent))):
                recommendations.append(Recommendation(
                    id=f"hygiene-trend-{datetime.now().strftime('%Y%m%d')}",
                    type=RecommendationType.HYGIENE_IMPROVEMENT,
                    priority=RecommendationPriority.MEDIUM,
                    title="Hygiene score is declining",
                    description=f"Hygiene score has dropped from {recent[0]:.0f}% to {recent[-1]:.0f}% over the past weeks.",
                    rationale="Declining trend suggests process or enforcement issues that will compound over time.",
                    action_items=[
                        "Identify root cause of decline",
                        "Review recent team changes or process updates",
                        "Consider hygiene training session",
                    ],
                    estimated_impact="Prevents further 10-20% decline",
                    confidence_score=0.8,
                    data_sources=["hygiene_history"],
                ))
        
        return recommendations
    
    async def _analyze_velocity(
        self,
        context: RecommendationContext
    ) -> List[Recommendation]:
        """Analyze sprint velocity patterns"""
        recommendations = []
        
        if context.sprint_velocity is None or not context.past_velocities:
            return recommendations
        
        # Calculate average and trend
        avg_velocity = sum(context.past_velocities) / len(context.past_velocities)
        
        # Significant velocity drop
        if context.sprint_velocity < avg_velocity * 0.7:
            recommendations.append(Recommendation(
                id=f"velocity-drop-{datetime.now().strftime('%Y%m%d')}",
                type=RecommendationType.VELOCITY_OPTIMIZATION,
                priority=RecommendationPriority.HIGH,
                title="Sprint velocity significantly below average",
                description=f"Current velocity ({context.sprint_velocity:.0f} pts) is {(1 - context.sprint_velocity/avg_velocity)*100:.0f}% below average ({avg_velocity:.0f} pts).",
                rationale="Large velocity drops often indicate blockers, team changes, or scope creep that need addressing.",
                action_items=[
                    "Review active blockers and impediments",
                    "Check for scope changes mid-sprint",
                    "Assess team capacity (PTO, onboarding)",
                    "Consider sprint scope adjustment",
                ],
                affected_items=[f"Current sprint: {context.sprint_velocity:.0f} pts"],
                estimated_impact="Could recover 15-30% velocity",
                confidence_score=0.85,
                data_sources=["sprint_metrics", "velocity_history"],
            ))
        
        # Highly variable velocity
        if len(context.past_velocities) >= 4:
            import statistics
            std_dev = statistics.stdev(context.past_velocities)
            if std_dev / avg_velocity > 0.3:  # Coefficient of variation > 30%
                recommendations.append(Recommendation(
                    id=f"velocity-variance-{datetime.now().strftime('%Y%m%d')}",
                    type=RecommendationType.VELOCITY_OPTIMIZATION,
                    priority=RecommendationPriority.MEDIUM,
                    title="Sprint velocity is highly variable",
                    description="Velocity varies significantly between sprints, making release planning difficult.",
                    rationale=f"Standard deviation of {std_dev:.0f} pts ({std_dev/avg_velocity*100:.0f}% of average) indicates inconsistent delivery.",
                    action_items=[
                        "Improve story point estimation practices",
                        "Break down large stories more consistently",
                        "Review sprint commitment process",
                        "Consider story point calibration session",
                    ],
                    estimated_impact="Improves release date predictability by 30%",
                    confidence_score=0.75,
                    data_sources=["velocity_history"],
                ))
        
        return recommendations
    
    async def _analyze_risks(
        self,
        context: RecommendationContext
    ) -> List[Recommendation]:
        """Analyze risk factors"""
        recommendations = []
        
        # Active blockers
        if context.active_blockers > 0:
            priority = RecommendationPriority.CRITICAL if context.active_blockers > 3 else RecommendationPriority.HIGH
            
            recommendations.append(Recommendation(
                id=f"blockers-{datetime.now().strftime('%Y%m%d')}",
                type=RecommendationType.BLOCKERS_RESOLUTION,
                priority=priority,
                title=f"{context.active_blockers} active blocker(s) affecting release",
                description="Unresolved blockers will prevent or delay release.",
                rationale="Blockers have cascading effects on dependent work and team productivity.",
                action_items=[
                    "Prioritize blocker resolution in current sprint",
                    "Escalate blockers older than 3 days",
                    "Identify and engage required stakeholders",
                    "Consider temporary workarounds if appropriate",
                ],
                estimated_impact="Unblocks dependent work for 2-5 team members",
                confidence_score=0.95,
                data_sources=["jira_blockers"],
            ))
        
        # Security vulnerabilities
        if context.open_vulnerabilities > 0:
            priority = RecommendationPriority.CRITICAL if context.open_vulnerabilities > 5 else RecommendationPriority.HIGH
            
            recommendations.append(Recommendation(
                id=f"security-{datetime.now().strftime('%Y%m%d')}",
                type=RecommendationType.RISK_MITIGATION,
                priority=priority,
                title=f"{context.open_vulnerabilities} security vulnerabilities require attention",
                description="Open vulnerabilities increase security risk and may block release to production.",
                rationale="Security vulnerabilities should be addressed before release per security policy.",
                action_items=[
                    "Review and prioritize vulnerabilities by severity",
                    "Apply available patches/updates",
                    "Document exceptions for low-risk items",
                    "Schedule remediation for remaining items",
                ],
                estimated_impact="Reduces security risk score by 20-50%",
                confidence_score=0.9,
                data_sources=["security_scan"],
            ))
        
        return recommendations
    
    async def _analyze_processes(
        self,
        context: RecommendationContext
    ) -> List[Recommendation]:
        """Analyze process improvement opportunities"""
        recommendations = []
        
        # This would typically use ML models or more sophisticated analysis
        # For now, provide general best practices based on context
        
        if context.project_key:
            recommendations.append(Recommendation(
                id=f"process-automation-{datetime.now().strftime('%Y%m%d')}",
                type=RecommendationType.PROCESS_IMPROVEMENT,
                priority=RecommendationPriority.LOW,
                title="Consider automating release readiness checks",
                description="Automated checks reduce manual effort and catch issues earlier.",
                rationale="Manual release checks are time-consuming and error-prone.",
                action_items=[
                    "Set up scheduled hygiene checks",
                    "Configure automated security scans",
                    "Add release readiness to CI pipeline",
                    "Create automated release notes generation",
                ],
                estimated_impact="Saves 2-4 hours per release cycle",
                confidence_score=0.7,
                data_sources=["best_practices"],
            ))
        
        return recommendations
    
    async def get_recommendation_summary(
        self,
        recommendations: List[Recommendation]
    ) -> Dict[str, Any]:
        """
        Get a summary of recommendations
        
        Returns:
            Summary statistics and key insights
        """
        if not recommendations:
            return {
                "total": 0,
                "by_priority": {},
                "by_type": {},
                "top_actions": [],
            }
        
        # Count by priority
        by_priority = {}
        for rec in recommendations:
            priority = rec.priority.value
            by_priority[priority] = by_priority.get(priority, 0) + 1
        
        # Count by type
        by_type = {}
        for rec in recommendations:
            rtype = rec.type.value
            by_type[rtype] = by_type.get(rtype, 0) + 1
        
        # Get top action items
        top_actions = []
        for rec in recommendations[:3]:
            if rec.action_items:
                top_actions.append({
                    "title": rec.title,
                    "action": rec.action_items[0],
                    "priority": rec.priority.value,
                })
        
        return {
            "total": len(recommendations),
            "by_priority": by_priority,
            "by_type": by_type,
            "top_actions": top_actions,
            "critical_count": by_priority.get("critical", 0),
            "high_count": by_priority.get("high", 0),
        }

