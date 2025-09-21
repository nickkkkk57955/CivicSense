from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import List, Optional
from datetime import datetime, timedelta
from ..database import SessionLocal
from ..models import User, Issue, IssueVote, IssueComment, UserBadge, IssueStatus, IssueCategory
from ..auth import get_current_user
from ..services.karma import KarmaService
from pydantic import BaseModel

router = APIRouter(prefix="/social", tags=["social"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class VoteRequest(BaseModel):
    vote_type: str  # 'upvote' or 'confirm'

class CommentRequest(BaseModel):
    comment: str

class IssueFeedResponse(BaseModel):
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
    upvotes: int
    confirmations: int
    urgency_score: float
    reporter_name: str
    reporter_karma: int
    created_at: datetime
    updated_at: Optional[datetime]
    user_voted: bool = False
    user_confirmed: bool = False
    
    class Config:
        from_attributes = True

@router.get("/feed/trending", response_model=List[IssueFeedResponse])
async def get_trending_feed(
    limit: int = Query(20, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trending issues (most upvotes in last 24 hours)"""
    yesterday = datetime.utcnow() - timedelta(hours=24)
    
    issues = db.query(Issue).filter(
        Issue.created_at >= yesterday
    ).order_by(desc(Issue.upvotes)).limit(limit).all()
    
    return _format_issues_for_feed(issues, current_user.id, db)

@router.get("/feed/newest", response_model=List[IssueFeedResponse])
async def get_newest_feed(
    limit: int = Query(20, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get newest issues"""
    issues = db.query(Issue).order_by(desc(Issue.created_at)).limit(limit).all()
    return _format_issues_for_feed(issues, current_user.id, db)

@router.get("/feed/nearby", response_model=List[IssueFeedResponse])
async def get_nearby_feed(
    latitude: float,
    longitude: float,
    radius_km: float = Query(5.0, le=50.0),
    limit: int = Query(20, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get nearby issues using location"""
    # Simple distance calculation (for production, use PostGIS)
    issues = db.query(Issue).all()
    nearby_issues = []
    
    for issue in issues:
        # Calculate distance (simplified)
        lat_diff = abs(issue.latitude - latitude)
        lon_diff = abs(issue.longitude - longitude)
        distance = ((lat_diff ** 2) + (lon_diff ** 2)) ** 0.5 * 111  # Rough km conversion
        
        if distance <= radius_km:
            nearby_issues.append(issue)
    
    # Sort by urgency score
    nearby_issues.sort(key=lambda x: x.urgency_score, reverse=True)
    return _format_issues_for_feed(nearby_issues[:limit], current_user.id, db)

@router.post("/issues/{issue_id}/vote")
async def vote_on_issue(
    issue_id: int,
    vote_request: VoteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Vote on an issue (upvote or confirm)"""
    if vote_request.vote_type not in ['upvote', 'confirm']:
        raise HTTPException(status_code=400, detail="Invalid vote type")
    
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    # Check if user already voted
    existing_vote = db.query(IssueVote).filter(
        IssueVote.issue_id == issue_id,
        IssueVote.user_id == current_user.id,
        IssueVote.vote_type == vote_request.vote_type
    ).first()
    
    if existing_vote:
        raise HTTPException(status_code=400, detail="Already voted on this issue")
    
    # Create vote
    vote = IssueVote(
        issue_id=issue_id,
        user_id=current_user.id,
        vote_type=vote_request.vote_type
    )
    db.add(vote)
    
    # Update issue counts
    if vote_request.vote_type == 'upvote':
        issue.upvotes += 1
    else:  # confirm
        issue.confirmations += 1
    
    # Recalculate urgency score
    issue.urgency_score = (issue.upvotes * 2) + issue.confirmations
    
    db.commit()
    
    # Award karma to voter
    karma_service = KarmaService(db)
    karma_service.award_karma(current_user.id, 1, f"Voted on issue: {issue.title}")
    
    return {"message": f"Successfully {vote_request.vote_type}d issue", "new_score": issue.urgency_score}

@router.delete("/issues/{issue_id}/vote")
async def remove_vote(
    issue_id: int,
    vote_type: str = Query(..., regex="^(upvote|confirm)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a vote from an issue"""
    vote = db.query(IssueVote).filter(
        IssueVote.issue_id == issue_id,
        IssueVote.user_id == current_user.id,
        IssueVote.vote_type == vote_type
    ).first()
    
    if not vote:
        raise HTTPException(status_code=404, detail="Vote not found")
    
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    
    # Update issue counts
    if vote_type == 'upvote':
        issue.upvotes = max(0, issue.upvotes - 1)
    else:  # confirm
        issue.confirmations = max(0, issue.confirmations - 1)
    
    # Recalculate urgency score
    issue.urgency_score = (issue.upvotes * 2) + issue.confirmations
    
    db.delete(vote)
    db.commit()
    
    return {"message": f"Vote removed successfully", "new_score": issue.urgency_score}

@router.post("/issues/{issue_id}/comment")
async def add_comment(
    issue_id: int,
    comment_request: CommentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a comment to an issue"""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    comment = IssueComment(
        issue_id=issue_id,
        user_id=current_user.id,
        comment=comment_request.comment
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    # Award karma for commenting
    karma_service = KarmaService(db)
    karma_service.award_karma(current_user.id, 1, f"Commented on issue: {issue.title}")
    
    return {"message": "Comment added successfully", "comment_id": comment.id}

@router.get("/issues/{issue_id}/comments")
async def get_issue_comments(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all comments for an issue"""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    comments = db.query(IssueComment).filter(
        IssueComment.issue_id == issue_id
    ).order_by(IssueComment.created_at.desc()).all()
    
    return [
        {
            "id": comment.id,
            "comment": comment.comment,
            "user_name": comment.user.name,
            "user_karma": comment.user.civic_karma,
            "created_at": comment.created_at
        }
        for comment in comments
    ]

@router.get("/map/issues")
async def get_issues_for_map(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all issues for map display with color coding"""
    issues = db.query(Issue).all()
    
    map_issues = []
    for issue in issues:
        # Determine pin color based on status
        status_colors = {
            "submitted": "red",
            "acknowledged": "orange", 
            "in_progress": "yellow",
            "resolved": "green",
            "closed": "blue",
            "rejected": "gray"
        }
        
        # Pin size based on urgency score
        pin_size = min(20, max(5, issue.urgency_score / 10))
        
        map_issues.append({
            "id": issue.id,
            "title": issue.title,
            "category": issue.category.value,
            "status": issue.status.value,
            "latitude": issue.latitude,
            "longitude": issue.longitude,
            "address": issue.address,
            "upvotes": issue.upvotes,
            "confirmations": issue.confirmations,
            "urgency_score": issue.urgency_score,
            "pin_color": status_colors.get(issue.status.value, "gray"),
            "pin_size": pin_size,
            "created_at": issue.created_at
        })
    
    return map_issues

@router.get("/leaderboard")
async def get_leaderboard(
    limit: int = Query(20, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get civic karma leaderboard"""
    users = db.query(User).filter(
        User.role == "citizen",
        User.is_active == True
    ).order_by(desc(User.civic_karma)).limit(limit).all()
    
    return [
        {
            "rank": i + 1,
            "user_id": user.id,
            "name": user.name,
            "civic_karma": user.civic_karma,
            "badges": [badge.badge_name for badge in user.badges],
            "issues_reported": len(user.issues)
        }
        for i, user in enumerate(users)
    ]

def _format_issues_for_feed(issues: List[Issue], user_id: int, db: Session) -> List[dict]:
    """Format issues for the social feed"""
    formatted_issues = []
    
    for issue in issues:
        # Check if user has voted on this issue
        user_votes = db.query(IssueVote).filter(
            IssueVote.issue_id == issue.id,
            IssueVote.user_id == user_id
        ).all()
        
        user_voted = any(vote.vote_type == 'upvote' for vote in user_votes)
        user_confirmed = any(vote.vote_type == 'confirm' for vote in user_votes)
        
        formatted_issues.append({
            "id": issue.id,
            "title": issue.title,
            "description": issue.description,
            "category": issue.category.value,
            "status": issue.status.value,
            "priority": issue.priority.value,
            "latitude": issue.latitude,
            "longitude": issue.longitude,
            "address": issue.address,
            "photo_urls": issue.photo_urls,
            "upvotes": issue.upvotes,
            "confirmations": issue.confirmations,
            "urgency_score": issue.urgency_score,
            "reporter_name": issue.reporter.name,
            "reporter_karma": issue.reporter.civic_karma,
            "created_at": issue.created_at,
            "updated_at": issue.updated_at,
            "user_voted": user_voted,
            "user_confirmed": user_confirmed
        })
    
    return formatted_issues
