from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from ..models import Issue, User, IssueStatus, IssueCategory, IssueUpdate, Department
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service for generating analytics and reports"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_overview_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get overview statistics for the specified period"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total issues
        total_issues = self.db.query(Issue).filter(Issue.created_at >= start_date).count()
        
        # Issues by status
        status_counts = {}
        for status in IssueStatus:
            count = self.db.query(Issue).filter(
                and_(Issue.created_at >= start_date, Issue.status == status)
            ).count()
            status_counts[status.value] = count
        
        # Issues by category
        category_counts = {}
        for category in IssueCategory:
            count = self.db.query(Issue).filter(
                and_(Issue.created_at >= start_date, Issue.category == category)
            ).count()
            category_counts[category.value] = count
        
        # Issues by priority
        priority_counts = {}
        for priority in ["low", "medium", "high", "urgent"]:
            count = self.db.query(Issue).filter(
                and_(Issue.created_at >= start_date, Issue.priority == priority)
            ).count()
            priority_counts[priority] = count
        
        # Resolution rate
        resolved_issues = self.db.query(Issue).filter(
            and_(
                Issue.created_at >= start_date,
                Issue.status == IssueStatus.RESOLVED
            )
        ).count()
        
        resolution_rate = (resolved_issues / total_issues * 100) if total_issues > 0 else 0
        
        return {
            'period_days': days,
            'total_issues': total_issues,
            'status_breakdown': status_counts,
            'category_breakdown': category_counts,
            'priority_breakdown': priority_counts,
            'resolved_issues': resolved_issues,
            'resolution_rate': round(resolution_rate, 2)
        }
    
    def get_trend_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Get trend analysis for issues over time"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Daily issue creation trend
        daily_issues = self.db.query(
            func.date(Issue.created_at).label('date'),
            func.count(Issue.id).label('count')
        ).filter(
            Issue.created_at >= start_date
        ).group_by(func.date(Issue.created_at)).order_by('date').all()
        
        # Daily resolution trend
        daily_resolutions = self.db.query(
            func.date(Issue.resolved_at).label('date'),
            func.count(Issue.id).label('count')
        ).filter(
            and_(
                Issue.resolved_at >= start_date,
                Issue.status == IssueStatus.RESOLVED
            )
        ).group_by(func.date(Issue.resolved_at)).order_by('date').all()
        
        # Weekly trends
        weekly_issues = self.db.query(
            func.year(Issue.created_at).label('year'),
            func.week(Issue.created_at).label('week'),
            func.count(Issue.id).label('count')
        ).filter(
            Issue.created_at >= start_date
        ).group_by(
            func.year(Issue.created_at),
            func.week(Issue.created_at)
        ).order_by('year', 'week').all()
        
        return {
            'daily_issues': [{'date': str(stat.date), 'count': stat.count} for stat in daily_issues],
            'daily_resolutions': [{'date': str(stat.date), 'count': stat.count} for stat in daily_resolutions],
            'weekly_issues': [{'year': stat.year, 'week': stat.week, 'count': stat.count} for stat in weekly_issues]
        }
    
    def get_performance_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get performance metrics for the system"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Average response time (time from submission to acknowledgment)
        response_times = self.db.query(
            func.avg(
                func.julianday(Issue.acknowledged_at) - func.julianday(Issue.created_at)
            ).label('avg_response_hours')
        ).filter(
            and_(
                Issue.created_at >= start_date,
                Issue.acknowledged_at.isnot(None)
            )
        ).scalar()
        
        # Average resolution time (time from submission to resolution)
        resolution_times = self.db.query(
            func.avg(
                func.julianday(Issue.resolved_at) - func.julianday(Issue.created_at)
            ).label('avg_resolution_hours')
        ).filter(
            and_(
                Issue.created_at >= start_date,
                Issue.status == IssueStatus.RESOLVED,
                Issue.resolved_at.isnot(None)
            )
        ).scalar()
        
        # Department performance
        dept_performance = self.db.query(
            Department.name,
            func.count(Issue.id).label('total_issues'),
            func.avg(
                func.julianday(Issue.resolved_at) - func.julianday(Issue.created_at)
            ).label('avg_resolution_hours')
        ).join(Issue, Department.id == Issue.department_id).filter(
            and_(
                Issue.created_at >= start_date,
                Issue.status == IssueStatus.RESOLVED
            )
        ).group_by(Department.id, Department.name).all()
        
        # Staff performance
        staff_performance = self.db.query(
            User.name,
            func.count(Issue.id).label('assigned_issues'),
            func.count(
                func.case([(Issue.status == IssueStatus.RESOLVED, 1)], else_=0)
            ).label('resolved_issues')
        ).join(Issue, User.id == Issue.assigned_to_id).filter(
            Issue.created_at >= start_date
        ).group_by(User.id, User.name).all()
        
        return {
            'avg_response_time_hours': round(response_times * 24, 2) if response_times else None,
            'avg_resolution_time_hours': round(resolution_times * 24, 2) if resolution_times else None,
            'department_performance': [
                {
                    'department': perf.name,
                    'total_issues': perf.total_issues,
                    'avg_resolution_hours': round(perf.avg_resolution_hours * 24, 2) if perf.avg_resolution_hours else None
                }
                for perf in dept_performance
            ],
            'staff_performance': [
                {
                    'staff_name': perf.name,
                    'assigned_issues': perf.assigned_issues,
                    'resolved_issues': perf.resolved_issues,
                    'resolution_rate': round((perf.resolved_issues / perf.assigned_issues * 100), 2) if perf.assigned_issues > 0 else 0
                }
                for perf in staff_performance
            ]
        }
    
    def get_geographic_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Get geographic analysis of issues"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Issues by location (address)
        location_counts = self.db.query(
            Issue.address,
            func.count(Issue.id).label('count')
        ).filter(
            and_(
                Issue.created_at >= start_date,
                Issue.address.isnot(None)
            )
        ).group_by(Issue.address).order_by(desc('count')).limit(10).all()
        
        # Geographic distribution
        bounds_query = self.db.query(
            func.min(Issue.latitude).label('min_lat'),
            func.max(Issue.latitude).label('max_lat'),
            func.min(Issue.longitude).label('min_lon'),
            func.max(Issue.longitude).label('max_lon')
        ).filter(Issue.created_at >= start_date).first()
        
        # Hotspot analysis (areas with high issue density)
        hotspots = self.db.query(
            Issue.address,
            func.count(Issue.id).label('issue_count'),
            func.avg(Issue.latitude).label('avg_lat'),
            func.avg(Issue.longitude).label('avg_lon')
        ).filter(
            and_(
                Issue.created_at >= start_date,
                Issue.address.isnot(None)
            )
        ).group_by(Issue.address).having(
            func.count(Issue.id) >= 3  # Minimum 3 issues to be considered a hotspot
        ).order_by(desc('issue_count')).limit(5).all()
        
        return {
            'top_locations': [
                {'address': loc.address, 'count': loc.count}
                for loc in location_counts
            ],
            'geographic_bounds': {
                'min_lat': bounds_query.min_lat,
                'max_lat': bounds_query.max_lat,
                'min_lon': bounds_query.min_lon,
                'max_lon': bounds_query.max_lon
            } if bounds_query else None,
            'hotspots': [
                {
                    'address': hotspot.address,
                    'issue_count': hotspot.issue_count,
                    'center_lat': float(hotspot.avg_lat),
                    'center_lon': float(hotspot.avg_lon)
                }
                for hotspot in hotspots
            ]
        }
    
    def get_user_engagement_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get user engagement metrics"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Top reporters
        top_reporters = self.db.query(
            User.name,
            User.email,
            func.count(Issue.id).label('issue_count')
        ).join(Issue, User.id == Issue.reporter_id).filter(
            Issue.created_at >= start_date
        ).group_by(User.id, User.name, User.email).order_by(desc('issue_count')).limit(10).all()
        
        # User activity levels
        user_activity = self.db.query(
            func.count(Issue.id).label('issue_count'),
            func.count(func.distinct(Issue.reporter_id)).label('active_users')
        ).filter(Issue.created_at >= start_date).first()
        
        # New user registrations
        new_users = self.db.query(User).filter(User.created_at >= start_date).count()
        
        return {
            'top_reporters': [
                {
                    'name': reporter.name,
                    'email': reporter.email,
                    'issue_count': reporter.issue_count
                }
                for reporter in top_reporters
            ],
            'total_issues': user_activity.issue_count,
            'active_users': user_activity.active_users,
            'new_users': new_users,
            'avg_issues_per_user': round(user_activity.issue_count / user_activity.active_users, 2) if user_activity.active_users > 0 else 0
        }
    
    def get_category_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Get detailed analysis by issue category"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        category_stats = []
        
        for category in IssueCategory:
            # Basic counts
            total_issues = self.db.query(Issue).filter(
                and_(Issue.created_at >= start_date, Issue.category == category)
            ).count()
            
            resolved_issues = self.db.query(Issue).filter(
                and_(
                    Issue.created_at >= start_date,
                    Issue.category == category,
                    Issue.status == IssueStatus.RESOLVED
                )
            ).count()
            
            # Average resolution time for this category
            avg_resolution = self.db.query(
                func.avg(
                    func.julianday(Issue.resolved_at) - func.julianday(Issue.created_at)
                ).label('avg_resolution_hours')
            ).filter(
                and_(
                    Issue.created_at >= start_date,
                    Issue.category == category,
                    Issue.status == IssueStatus.RESOLVED,
                    Issue.resolved_at.isnot(None)
                )
            ).scalar()
            
            # Priority distribution for this category
            priority_dist = {}
            for priority in ["low", "medium", "high", "urgent"]:
                count = self.db.query(Issue).filter(
                    and_(
                        Issue.created_at >= start_date,
                        Issue.category == category,
                        Issue.priority == priority
                    )
                ).count()
                priority_dist[priority] = count
            
            category_stats.append({
                'category': category.value,
                'total_issues': total_issues,
                'resolved_issues': resolved_issues,
                'resolution_rate': round((resolved_issues / total_issues * 100), 2) if total_issues > 0 else 0,
                'avg_resolution_hours': round(avg_resolution * 24, 2) if avg_resolution else None,
                'priority_distribution': priority_dist
            })
        
        return {
            'category_analysis': category_stats,
            'period_days': days
        }
    
    def generate_comprehensive_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate a comprehensive analytics report"""
        return {
            'report_period': f"Last {days} days",
            'generated_at': datetime.utcnow().isoformat(),
            'overview': self.get_overview_stats(days),
            'trends': self.get_trend_analysis(days),
            'performance': self.get_performance_metrics(days),
            'geographic': self.get_geographic_analysis(days),
            'user_engagement': self.get_user_engagement_metrics(days),
            'category_analysis': self.get_category_analysis(days)
        }
