from sqlalchemy.orm import Session
from ..models import Issue, IssueCategory, Department, User, UserRole
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class IssueRoutingService:
    """Service for automatically routing issues to appropriate departments"""
    
    # Category to department mapping
    CATEGORY_DEPARTMENT_MAPPING = {
        IssueCategory.ROAD_MAINTENANCE: "Public Works",
        IssueCategory.STREETLIGHT: "Public Works", 
        IssueCategory.SANITATION: "Sanitation Department",
        IssueCategory.WATER_SUPPLY: "Water Department",
        IssueCategory.ELECTRICITY: "Electricity Department",
        IssueCategory.TRAFFIC: "Traffic Department",
        IssueCategory.PARKS: "Parks and Recreation",
        IssueCategory.OTHER: "General Administration"
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def route_issue(self, issue: Issue) -> Optional[Department]:
        """Route an issue to the appropriate department based on category and location"""
        try:
            # Get department by category mapping
            department_name = self.CATEGORY_DEPARTMENT_MAPPING.get(issue.category)
            if not department_name:
                logger.warning(f"No department mapping found for category: {issue.category}")
                return None
            
            # Find the department
            department = self.db.query(Department).filter(
                Department.name == department_name
            ).first()
            
            if not department:
                logger.warning(f"Department not found: {department_name}")
                return None
            
            # Update issue with department assignment
            issue.department_id = department.id
            self.db.commit()
            
            logger.info(f"Issue {issue.id} routed to department: {department.name}")
            return department
            
        except Exception as e:
            logger.error(f"Error routing issue {issue.id}: {str(e)}")
            return None
    
    def get_available_staff(self, department_id: int) -> List[User]:
        """Get available staff members for a department"""
        return self.db.query(User).filter(
            User.role == UserRole.DEPARTMENT_STAFF,
            User.is_active == True
        ).all()
    
    def auto_assign_issue(self, issue: Issue) -> Optional[User]:
        """Automatically assign issue to available staff member"""
        try:
            if not issue.department_id:
                # First route the issue to a department
                department = self.route_issue(issue)
                if not department:
                    return None
            
            # Get available staff for the department
            available_staff = self.get_available_staff(issue.department_id)
            
            if not available_staff:
                logger.warning(f"No available staff for department {issue.department_id}")
                return None
            
            # Simple round-robin assignment (in production, use more sophisticated logic)
            # For now, assign to the first available staff member
            assigned_staff = available_staff[0]
            
            issue.assigned_to_id = assigned_staff.id
            issue.status = "acknowledged"
            self.db.commit()
            
            logger.info(f"Issue {issue.id} auto-assigned to staff member {assigned_staff.name}")
            return assigned_staff
            
        except Exception as e:
            logger.error(f"Error auto-assigning issue {issue.id}: {str(e)}")
            return None
    
    def calculate_priority_score(self, issue: Issue) -> int:
        """Calculate priority score for an issue based on various factors"""
        score = 0
        
        # Base priority scoring
        priority_scores = {
            "urgent": 10,
            "high": 7,
            "medium": 4,
            "low": 1
        }
        score += priority_scores.get(issue.priority.value, 4)
        
        # Category-based scoring (some categories are more critical)
        critical_categories = [
            IssueCategory.WATER_SUPPLY,
            IssueCategory.ELECTRICITY,
            IssueCategory.ROAD_MAINTENANCE
        ]
        if issue.category in critical_categories:
            score += 3
        
        # Location-based scoring (could be enhanced with historical data)
        # For now, just add a small bonus for any location data
        if issue.latitude and issue.longitude:
            score += 1
        
        return score
    
    def get_priority_queue(self, department_id: Optional[int] = None) -> List[Issue]:
        """Get issues sorted by priority for staff to work on"""
        query = self.db.query(Issue).filter(
            Issue.status.in_(["submitted", "acknowledged"])
        )
        
        if department_id:
            query = query.filter(Issue.department_id == department_id)
        
        issues = query.all()
        
        # Sort by priority score (descending)
        return sorted(issues, key=self.calculate_priority_score, reverse=True)
