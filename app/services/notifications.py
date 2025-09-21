from sqlalchemy.orm import Session
from ..models import Notification, Issue, User, IssueStatus
from typing import List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for managing notifications"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_notification(
        self, 
        user_id: int, 
        title: str, 
        message: str, 
        issue_id: Optional[int] = None
    ) -> Notification:
        """Create a new notification"""
        notification = Notification(
            user_id=user_id,
            issue_id=issue_id,
            title=title,
            message=message
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        
        logger.info(f"Notification created for user {user_id}: {title}")
        return notification
    
    def notify_issue_submitted(self, issue: Issue) -> List[Notification]:
        """Notify admins about a new issue submission"""
        notifications = []
        
        # Get all admin users
        admin_users = self.db.query(User).filter(User.role == "admin").all()
        
        for admin in admin_users:
            notification = self.create_notification(
                user_id=admin.id,
                title="New Issue Reported",
                message=f"New issue '{issue.title}' has been reported by {issue.reporter.name}",
                issue_id=issue.id
            )
            notifications.append(notification)
        
        return notifications
    
    def notify_issue_status_change(self, issue: Issue, old_status: str, new_status: str) -> List[Notification]:
        """Notify relevant users about issue status changes"""
        notifications = []
        
        # Notify the reporter
        reporter_notification = self.create_notification(
            user_id=issue.reporter_id,
            title="Issue Status Update",
            message=f"Your issue '{issue.title}' status has changed from {old_status} to {new_status}",
            issue_id=issue.id
        )
        notifications.append(reporter_notification)
        
        # Notify assigned staff if different from reporter
        if issue.assigned_to_id and issue.assigned_to_id != issue.reporter_id:
            staff_notification = self.create_notification(
                user_id=issue.assigned_to_id,
                title="Issue Status Update",
                message=f"Issue '{issue.title}' status has changed to {new_status}",
                issue_id=issue.id
            )
            notifications.append(staff_notification)
        
        return notifications
    
    def notify_issue_assigned(self, issue: Issue, assigned_user: User) -> Notification:
        """Notify user that they've been assigned to an issue"""
        return self.create_notification(
            user_id=assigned_user.id,
            title="Issue Assigned",
            message=f"You have been assigned to issue: {issue.title}",
            issue_id=issue.id
        )
    
    def notify_issue_comment(self, issue: Issue, commenter: User, comment: str) -> List[Notification]:
        """Notify relevant users about new comments on an issue"""
        notifications = []
        
        # Notify reporter if commenter is not the reporter
        if commenter.id != issue.reporter_id:
            reporter_notification = self.create_notification(
                user_id=issue.reporter_id,
                title="New Comment on Your Issue",
                message=f"{commenter.name} commented on your issue '{issue.title}': {comment}",
                issue_id=issue.id
            )
            notifications.append(reporter_notification)
        
        # Notify assigned staff if different from commenter and reporter
        if (issue.assigned_to_id and 
            issue.assigned_to_id != commenter.id and 
            issue.assigned_to_id != issue.reporter_id):
            
            staff_notification = self.create_notification(
                user_id=issue.assigned_to_id,
                title="New Comment on Assigned Issue",
                message=f"{commenter.name} commented on issue '{issue.title}': {comment}",
                issue_id=issue.id
            )
            notifications.append(staff_notification)
        
        return notifications
    
    def get_user_notifications(
        self, 
        user_id: int, 
        limit: int = 50, 
        unread_only: bool = False
    ) -> List[Notification]:
        """Get notifications for a user"""
        query = self.db.query(Notification).filter(Notification.user_id == user_id)
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        return query.order_by(Notification.created_at.desc()).limit(limit).all()
    
    def mark_notification_read(self, notification_id: int, user_id: int) -> bool:
        """Mark a notification as read"""
        notification = self.db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        
        if notification:
            notification.is_read = True
            self.db.commit()
            return True
        
        return False
    
    def mark_all_notifications_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user"""
        updated_count = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update({"is_read": True})
        
        self.db.commit()
        return updated_count
    
    def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications for a user"""
        return self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).count()
    
    def send_bulk_notification(
        self, 
        user_ids: List[int], 
        title: str, 
        message: str
    ) -> List[Notification]:
        """Send the same notification to multiple users"""
        notifications = []
        
        for user_id in user_ids:
            notification = self.create_notification(
                user_id=user_id,
                title=title,
                message=message
            )
            notifications.append(notification)
        
        return notifications
    
    def cleanup_old_notifications(self, days_old: int = 30) -> int:
        """Delete notifications older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        deleted_count = self.db.query(Notification).filter(
            Notification.created_at < cutoff_date
        ).delete()
        
        self.db.commit()
        
        logger.info(f"Cleaned up {deleted_count} old notifications")
        return deleted_count
