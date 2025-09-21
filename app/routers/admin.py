from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ..database import SessionLocal
from ..models import User, Issue, IssueStatus, IssueCategory, Department, Notification, IssueUpdate
from ..auth import get_current_user
from ..services.analytics import AnalyticsService
from ..services.routing import IssueRoutingService
from ..services.notifications import NotificationService
from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["admin"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class DepartmentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None

class DepartmentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class DashboardStats(BaseModel):
    total_issues: int
    issues_by_status: Dict[str, int]
    issues_by_category: Dict[str, int]
    issues_by_priority: Dict[str, int]
    recent_issues: List[Dict[str, Any]]
    response_time_avg: Optional[float]

@router.get("/dashboard")
async def get_dashboard_stats(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive admin dashboard statistics"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can access dashboard")
    
    analytics_service = AnalyticsService(db)
    
    # Get comprehensive analytics
    overview = analytics_service.get_overview_stats(days)
    trends = analytics_service.get_trend_analysis(days)
    performance = analytics_service.get_performance_metrics(days)
    geographic = analytics_service.get_geographic_analysis(days)
    user_engagement = analytics_service.get_user_engagement_metrics(days)
    
    # Recent issues (last 10)
    recent_issues = db.query(Issue).order_by(desc(Issue.created_at)).limit(10).all()
    recent_issues_data = []
    for issue in recent_issues:
        recent_issues_data.append({
            "id": issue.id,
            "title": issue.title,
            "status": issue.status.value,
            "priority": issue.priority.value,
            "category": issue.category.value,
            "created_at": issue.created_at,
            "reporter_name": issue.reporter.name,
            "assigned_to": issue.assigned_to.name if issue.assigned_to else None
        })
    
    return {
        "overview": overview,
        "trends": trends,
        "performance": performance,
        "geographic": geographic,
        "user_engagement": user_engagement,
        "recent_issues": recent_issues_data,
        "generated_at": datetime.utcnow().isoformat()
    }

@router.get("/issues/analytics")
async def get_issues_analytics(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed analytics for issues"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can access analytics")
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Issues created in the last N days
    issues_created = db.query(Issue).filter(Issue.created_at >= start_date).count()
    
    # Issues resolved in the last N days
    issues_resolved = db.query(Issue).filter(
        Issue.status == IssueStatus.RESOLVED,
        Issue.resolved_at >= start_date
    ).count()
    
    # Daily breakdown
    daily_stats = db.query(
        func.date(Issue.created_at).label('date'),
        func.count(Issue.id).label('count')
    ).filter(
        Issue.created_at >= start_date
    ).group_by(func.date(Issue.created_at)).all()
    
    # Top reporters
    top_reporters = db.query(
        User.name,
        func.count(Issue.id).label('issue_count')
    ).join(Issue, User.id == Issue.reporter_id).filter(
        Issue.created_at >= start_date
    ).group_by(User.id, User.name).order_by(desc('issue_count')).limit(10).all()
    
    # Issues by location (simplified - in production, use proper geospatial analysis)
    location_stats = db.query(
        Issue.address,
        func.count(Issue.id).label('count')
    ).filter(
        Issue.created_at >= start_date,
        Issue.address.isnot(None)
    ).group_by(Issue.address).order_by(desc('count')).limit(10).all()
    
    return {
        "period_days": days,
        "issues_created": issues_created,
        "issues_resolved": issues_resolved,
        "resolution_rate": (issues_resolved / issues_created * 100) if issues_created > 0 else 0,
        "daily_breakdown": [{"date": str(stat.date), "count": stat.count} for stat in daily_stats],
        "top_reporters": [{"name": reporter.name, "count": reporter.issue_count} for reporter in top_reporters],
        "location_hotspots": [{"address": loc.address, "count": loc.count} for loc in location_stats]
    }

@router.post("/departments", response_model=DepartmentResponse)
async def create_department(
    dept_data: DepartmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new department"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create departments")
    
    department = Department(
        name=dept_data.name,
        description=dept_data.description,
        contact_email=dept_data.contact_email,
        contact_phone=dept_data.contact_phone
    )
    
    db.add(department)
    db.commit()
    db.refresh(department)
    
    return department

@router.get("/departments", response_model=List[DepartmentResponse])
async def get_departments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all departments"""
    if current_user.role not in ["admin", "department_staff"]:
        raise HTTPException(status_code=403, detail="Not authorized to view departments")
    
    departments = db.query(Department).all()
    return departments

@router.get("/notifications")
async def get_all_notifications(
    skip: int = 0,
    limit: int = 100,
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all notifications (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view all notifications")
    
    query = db.query(Notification)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    notifications = query.offset(skip).limit(limit).order_by(desc(Notification.created_at)).all()
    return notifications

@router.post("/issues/{issue_id}/assign")
async def assign_issue(
    issue_id: int,
    assigned_to_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Assign an issue to a staff member"""
    if current_user.role not in ["admin", "department_staff"]:
        raise HTTPException(status_code=403, detail="Not authorized to assign issues")
    
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    assigned_user = db.query(User).filter(User.id == assigned_to_id).first()
    if not assigned_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if assigned_user.role == "citizen":
        raise HTTPException(status_code=400, detail="Cannot assign issues to citizens")
    
    issue.assigned_to_id = assigned_to_id
    issue.status = IssueStatus.ACKNOWLEDGED
    issue.acknowledged_at = datetime.utcnow()
    
    # Create notification for assigned user
    notification = Notification(
        user_id=assigned_to_id,
        issue_id=issue_id,
        title="Issue Assigned",
        message=f"You have been assigned to issue: {issue.title}"
    )
    db.add(notification)
    
    # Create notification for reporter
    reporter_notification = Notification(
        user_id=issue.reporter_id,
        issue_id=issue_id,
        title="Issue Acknowledged",
        message=f"Your issue '{issue.title}' has been acknowledged and assigned to a staff member"
    )
    db.add(reporter_notification)
    
    db.commit()
    
    return {"message": "Issue assigned successfully"}

@router.get("/issues/priority-queue")
async def get_priority_queue(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get issues sorted by urgency score for staff to work on"""
    if current_user.role not in ["admin", "department_staff"]:
        raise HTTPException(status_code=403, detail="Not authorized to view priority queue")
    
    # Get issues sorted by urgency score (community-driven priority)
    issues = db.query(Issue).filter(
        Issue.status.in_(["submitted", "acknowledged"])
    ).order_by(desc(Issue.urgency_score), desc(Issue.created_at)).all()
    
    return [
        {
            "id": issue.id,
            "title": issue.title,
            "description": issue.description,
            "category": issue.category.value,
            "priority": issue.priority.value,
            "status": issue.status.value,
            "created_at": issue.created_at,
            "reporter_name": issue.reporter.name,
            "reporter_karma": issue.reporter.civic_karma,
            "location": {
                "latitude": issue.latitude,
                "longitude": issue.longitude,
                "address": issue.address
            },
            "urgency_score": issue.urgency_score,
            "upvotes": issue.upvotes,
            "confirmations": issue.confirmations,
            "time_since_created": (datetime.utcnow() - issue.created_at).total_seconds() / 3600  # hours
        }
        for issue in issues
    ]

@router.post("/issues/{issue_id}/auto-route")
async def auto_route_issue(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Automatically route an issue to appropriate department and assign staff"""
    if current_user.role not in ["admin", "department_staff"]:
        raise HTTPException(status_code=403, detail="Not authorized to auto-route issues")
    
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    routing_service = IssueRoutingService(db)
    notification_service = NotificationService(db)
    
    # Auto-route to department
    department = routing_service.route_issue(issue)
    if not department:
        raise HTTPException(status_code=400, detail="Could not route issue to department")
    
    # Auto-assign to staff
    assigned_staff = routing_service.auto_assign_issue(issue)
    if not assigned_staff:
        raise HTTPException(status_code=400, detail="Could not assign issue to staff")
    
    # Send notifications
    notification_service.notify_issue_assigned(issue, assigned_staff)
    notification_service.notify_issue_status_change(issue, "submitted", "acknowledged")
    
    return {
        "message": "Issue auto-routed successfully",
        "department": department.name,
        "assigned_to": assigned_staff.name,
        "status": issue.status.value
    }

@router.get("/comprehensive-report")
async def get_comprehensive_report(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive analytics report"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can access comprehensive reports")
    
    analytics_service = AnalyticsService(db)
    return analytics_service.generate_comprehensive_report(days)

@router.get("/system-health")
async def get_system_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get system health metrics"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can access system health")
    
    # Get basic system metrics
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    total_issues = db.query(Issue).count()
    pending_issues = db.query(Issue).filter(Issue.status == IssueStatus.SUBMITTED).count()
    
    # Recent activity (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_issues = db.query(Issue).filter(Issue.created_at >= yesterday).count()
    recent_users = db.query(User).filter(User.created_at >= yesterday).count()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_issues": total_issues,
        "pending_issues": pending_issues,
        "recent_activity": {
            "issues_last_24h": recent_issues,
            "new_users_last_24h": recent_users
        },
        "system_status": "healthy",
        "last_updated": datetime.utcnow().isoformat()
    }

@router.get("/hotspots")
async def get_issue_hotspots(
    days: int = Query(30, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get geographic hotspots where issues cluster"""
    if current_user.role not in ["admin", "department_staff"]:
        raise HTTPException(status_code=403, detail="Not authorized to view hotspots")
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get issues with location data
    issues = db.query(Issue).filter(
        Issue.created_at >= start_date,
        Issue.latitude.isnot(None),
        Issue.longitude.isnot(None)
    ).all()
    
    # Simple clustering by address (in production, use proper clustering algorithms)
    location_groups = {}
    for issue in issues:
        if issue.address:
            # Group by address (simplified)
            key = issue.address.split(',')[0] if ',' in issue.address else issue.address
            if key not in location_groups:
                location_groups[key] = {
                    'address': issue.address,
                    'issues': [],
                    'total_urgency': 0,
                    'avg_lat': 0,
                    'avg_lon': 0
                }
            
            location_groups[key]['issues'].append(issue)
            location_groups[key]['total_urgency'] += issue.urgency_score
    
    # Calculate averages and sort by urgency
    hotspots = []
    for key, group in location_groups.items():
        if len(group['issues']) >= 2:  # Only show locations with 2+ issues
            avg_lat = sum(issue.latitude for issue in group['issues']) / len(group['issues'])
            avg_lon = sum(issue.longitude for issue in group['issues']) / len(group['issues'])
            
            hotspots.append({
                'address': group['address'],
                'issue_count': len(group['issues']),
                'total_urgency': group['total_urgency'],
                'avg_urgency': group['total_urgency'] / len(group['issues']),
                'latitude': avg_lat,
                'longitude': avg_lon,
                'categories': list(set(issue.category.value for issue in group['issues']))
            })
    
    # Sort by total urgency
    hotspots.sort(key=lambda x: x['total_urgency'], reverse=True)
    
    return {
        'hotspots': hotspots[:10],  # Top 10 hotspots
        'period_days': days,
        'total_locations_analyzed': len(location_groups)
    }

@router.get("/weekly-briefing")
async def get_weekly_briefing(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate weekly briefing report with trends and insights"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can access weekly briefing")
    
    # Get data for last 7 days vs previous 7 days
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)
    
    # Current week data
    current_week_issues = db.query(Issue).filter(Issue.created_at >= week_ago).all()
    current_week_resolved = db.query(Issue).filter(
        Issue.resolved_at >= week_ago,
        Issue.status == IssueStatus.RESOLVED
    ).count()
    
    # Previous week data
    previous_week_issues = db.query(Issue).filter(
        Issue.created_at >= two_weeks_ago,
        Issue.created_at < week_ago
    ).all()
    previous_week_resolved = db.query(Issue).filter(
        Issue.resolved_at >= two_weeks_ago,
        Issue.resolved_at < week_ago,
        Issue.status == IssueStatus.RESOLVED
    ).count()
    
    # Calculate trends
    issue_trend = ((len(current_week_issues) - len(previous_week_issues)) / max(len(previous_week_issues), 1)) * 100
    resolution_trend = ((current_week_resolved - previous_week_resolved) / max(previous_week_resolved, 1)) * 100
    
    # Category trends
    current_categories = {}
    for issue in current_week_issues:
        cat = issue.category.value
        current_categories[cat] = current_categories.get(cat, 0) + 1
    
    previous_categories = {}
    for issue in previous_week_issues:
        cat = issue.category.value
        previous_categories[cat] = previous_categories.get(cat, 0) + 1
    
    category_trends = []
    for cat in set(list(current_categories.keys()) + list(previous_categories.keys())):
        current_count = current_categories.get(cat, 0)
        previous_count = previous_categories.get(cat, 0)
        trend = ((current_count - previous_count) / max(previous_count, 1)) * 100 if previous_count > 0 else 100
        
        category_trends.append({
            'category': cat,
            'current_week': current_count,
            'previous_week': previous_count,
            'trend_percent': round(trend, 1)
        })
    
    # Top reporters this week
    top_reporters = db.query(
        User.name,
        func.count(Issue.id).label('issue_count')
    ).join(Issue, User.id == Issue.reporter_id).filter(
        Issue.created_at >= week_ago
    ).group_by(User.id, User.name).order_by(desc('issue_count')).limit(5).all()
    
    # Most urgent issues
    urgent_issues = db.query(Issue).filter(
        Issue.created_at >= week_ago,
        Issue.urgency_score > 10
    ).order_by(desc(Issue.urgency_score)).limit(5).all()
    
    return {
        'period': f"Week of {week_ago.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}",
        'summary': {
            'total_issues_this_week': len(current_week_issues),
            'total_issues_last_week': len(previous_week_issues),
            'issues_trend_percent': round(issue_trend, 1),
            'resolved_this_week': current_week_resolved,
            'resolved_last_week': previous_week_resolved,
            'resolution_trend_percent': round(resolution_trend, 1)
        },
        'category_trends': category_trends,
        'top_reporters': [
            {'name': reporter.name, 'issues_reported': reporter.issue_count}
            for reporter in top_reporters
        ],
        'most_urgent_issues': [
            {
                'id': issue.id,
                'title': issue.title,
                'urgency_score': issue.urgency_score,
                'upvotes': issue.upvotes,
                'confirmations': issue.confirmations,
                'category': issue.category.value
            }
            for issue in urgent_issues
        ],
        'generated_at': now.isoformat()
    }
