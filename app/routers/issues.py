from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json
import os
from ..database import SessionLocal
from ..models import Issue, User, IssueStatus, IssuePriority, IssueCategory, IssueUpdate, Notification
from ..auth import get_current_user
from ..services.karma import KarmaService
from pydantic import BaseModel

router = APIRouter(prefix="/issues", tags=["issues"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class IssueCreate(BaseModel):
    title: str
    description: str
    category: IssueCategory
    latitude: float
    longitude: float
    address: Optional[str] = None
    priority: Optional[IssuePriority] = IssuePriority.MEDIUM

class IssueUpdateRequest(BaseModel):
    status: Optional[IssueStatus] = None
    priority: Optional[IssuePriority] = None
    assigned_to_id: Optional[int] = None
    comment: Optional[str] = None

class IssueResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    status: str
    priority: str
    latitude: float
    longitude: float
    address: Optional[str]
    photo_urls: Optional[str]
    voice_note_url: Optional[str]
    reporter_id: int
    assigned_to_id: Optional[int]
    department_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    
    class Config:
        from_attributes = True

@router.post("/", response_model=IssueResponse)
async def create_issue(
    issue_data: IssueCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new civic issue report"""
    issue = Issue(
        title=issue_data.title,
        description=issue_data.description,
        category=issue_data.category,
        latitude=issue_data.latitude,
        longitude=issue_data.longitude,
        address=issue_data.address,
        priority=issue_data.priority,
        reporter_id=current_user.id
    )
    
    db.add(issue)
    db.commit()
    db.refresh(issue)
    
    # Award karma for reporting issue
    karma_service = KarmaService(db)
    karma_service.award_karma(current_user.id, 10, f"Reported issue: {issue.title}")
    
    # Create notification for admins
    admin_users = db.query(User).filter(User.role == "admin").all()
    for admin in admin_users:
        notification = Notification(
            user_id=admin.id,
            issue_id=issue.id,
            title="New Issue Reported",
            message=f"New issue '{issue.title}' has been reported by {current_user.name}"
        )
        db.add(notification)
    
    db.commit()
    
    return issue

@router.get("/", response_model=List[IssueResponse])
async def get_issues(
    skip: int = 0,
    limit: int = 100,
    status: Optional[IssueStatus] = None,
    category: Optional[IssueCategory] = None,
    priority: Optional[IssuePriority] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get issues with optional filtering"""
    query = db.query(Issue)
    
    # Citizens can only see their own issues, admins and staff can see all
    if current_user.role == "citizen":
        query = query.filter(Issue.reporter_id == current_user.id)
    
    if status:
        query = query.filter(Issue.status == status)
    if category:
        query = query.filter(Issue.category == category)
    if priority:
        query = query.filter(Issue.priority == priority)
    
    issues = query.offset(skip).limit(limit).all()
    return issues

@router.get("/{issue_id}", response_model=IssueResponse)
async def get_issue(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific issue by ID"""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    # Citizens can only see their own issues
    if current_user.role == "citizen" and issue.reporter_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this issue")
    
    return issue

@router.put("/{issue_id}", response_model=IssueResponse)
async def update_issue(
    issue_id: int,
    update_data: IssueUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an issue (admin/staff only)"""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    # Only admins and department staff can update issues
    if current_user.role == "citizen":
        raise HTTPException(status_code=403, detail="Not authorized to update issues")
    
    # Update issue fields
    if update_data.status:
        issue.status = update_data.status
        if update_data.status == IssueStatus.ACKNOWLEDGED and not issue.acknowledged_at:
            issue.acknowledged_at = datetime.utcnow()
        elif update_data.status == IssueStatus.RESOLVED and not issue.resolved_at:
            issue.resolved_at = datetime.utcnow()
    
    if update_data.priority:
        issue.priority = update_data.priority
    
    if update_data.assigned_to_id:
        issue.assigned_to_id = update_data.assigned_to_id
    
    # Create issue update record
    if update_data.comment or update_data.status:
        old_status = issue.status.value
        issue_update = IssueUpdate(
            issue_id=issue.id,
            user_id=current_user.id,
            status=update_data.status or issue.status,
            comment=update_data.comment
        )
        db.add(issue_update)
        
        # Create notification for reporter
        status_message = ""
        if update_data.status and update_data.status.value != old_status:
            status_message = f"Status changed from {old_status} to {update_data.status.value}"
        
        comment_message = ""
        if update_data.comment:
            comment_message = f"New comment: {update_data.comment}"
        
        full_message = " | ".join(filter(None, [status_message, comment_message]))
        
        notification = Notification(
            user_id=issue.reporter_id,
            issue_id=issue.id,
            title="Issue Update",
            message=f"Your issue '{issue.title}' has been updated: {full_message}"
        )
        db.add(notification)
        
        # Award karma to reporter if issue is resolved
        if update_data.status and update_data.status.value == "resolved":
            karma_service = KarmaService(db)
            karma_service.award_karma(issue.reporter_id, 50, f"Issue resolved: {issue.title}")
    
    db.commit()
    db.refresh(issue)
    
    return issue

@router.post("/{issue_id}/upload-photo")
async def upload_issue_photo(
    issue_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a photo for an issue"""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    # Citizens can only upload to their own issues
    if current_user.role == "citizen" and issue.reporter_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to upload photos to this issue")
    
    # Create uploads directory if it doesn't exist
    upload_dir = "uploads/issues"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"issue_{issue_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
    file_path = os.path.join(upload_dir, filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Update issue with photo URL
    photo_url = f"/uploads/issues/{filename}"
    existing_photos = json.loads(issue.photo_urls) if issue.photo_urls else []
    existing_photos.append(photo_url)
    issue.photo_urls = json.dumps(existing_photos)
    
    db.commit()
    
    return {"message": "Photo uploaded successfully", "photo_url": photo_url}

@router.get("/{issue_id}/updates")
async def get_issue_updates(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all updates for an issue"""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    # Citizens can only see updates for their own issues
    if current_user.role == "citizen" and issue.reporter_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this issue")
    
    updates = db.query(IssueUpdate).filter(IssueUpdate.issue_id == issue_id).order_by(IssueUpdate.created_at.desc()).all()
    
    return updates

@router.get("/nearby/{latitude}/{longitude}")
async def get_nearby_issues(
    latitude: float,
    longitude: float,
    radius_km: float = 5.0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get issues within a specified radius of given coordinates"""
    # Simple distance calculation (for production, consider using PostGIS or similar)
    # This is a basic implementation - for production, use proper geospatial queries
    issues = db.query(Issue).all()
    
    nearby_issues = []
    for issue in issues:
        # Calculate distance (simplified - for production use proper geospatial calculations)
        lat_diff = abs(issue.latitude - latitude)
        lon_diff = abs(issue.longitude - longitude)
        distance = ((lat_diff ** 2) + (lon_diff ** 2)) ** 0.5 * 111  # Rough km conversion
        
        if distance <= radius_km:
            nearby_issues.append(issue)
    
    return nearby_issues
