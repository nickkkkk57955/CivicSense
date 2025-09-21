from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import SessionLocal
from ..models import User, UserBadge, Issue, IssueVote, IssueComment
from ..auth import get_current_user
from ..services.karma import KarmaService
from pydantic import BaseModel

router = APIRouter(prefix="/profile", tags=["profile"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ProfileResponse(BaseModel):
    id: int
    name: str
    email: str
    civic_karma: int
    profile_picture_url: str
    badges: List[dict]
    stats: dict
    
    class Config:
        from_attributes = True

@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile with karma and badges"""
    karma_service = KarmaService(db)
    stats = karma_service.get_user_stats(current_user.id)
    
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "civic_karma": current_user.civic_karma,
        "profile_picture_url": current_user.profile_picture_url or "",
        "badges": [
            {
                "name": badge.badge_name,
                "description": badge.badge_description,
                "earned_at": badge.earned_at
            }
            for badge in current_user.badges
        ],
        "stats": stats
    }

@router.get("/{user_id}")
async def get_user_profile(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get another user's public profile"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Only show public information
    return {
        "id": user.id,
        "name": user.name,
        "civic_karma": user.civic_karma,
        "profile_picture_url": user.profile_picture_url or "",
        "badges": [
            {
                "name": badge.badge_name,
                "description": badge.badge_description,
                "earned_at": badge.earned_at
            }
            for badge in user.badges
        ],
        "public_stats": {
            "total_issues": len(user.issues),
            "badges_earned": len(user.badges),
            "member_since": user.created_at
        }
    }

@router.get("/me/activity")
async def get_my_activity(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's recent activity"""
    # Get recent issues reported
    recent_issues = db.query(Issue).filter(
        Issue.reporter_id == current_user.id
    ).order_by(Issue.created_at.desc()).limit(limit).all()
    
    # Get recent votes
    recent_votes = db.query(IssueVote).filter(
        IssueVote.user_id == current_user.id
    ).order_by(IssueVote.created_at.desc()).limit(limit).all()
    
    # Get recent comments
    recent_comments = db.query(IssueComment).filter(
        IssueComment.user_id == current_user.id
    ).order_by(IssueComment.created_at.desc()).limit(limit).all()
    
    activity = []
    
    # Add issues to activity
    for issue in recent_issues:
        activity.append({
            "type": "issue_reported",
            "timestamp": issue.created_at,
            "description": f"Reported issue: {issue.title}",
            "issue_id": issue.id,
            "status": issue.status.value,
            "karma_earned": 10
        })
    
    # Add votes to activity
    for vote in recent_votes:
        activity.append({
            "type": f"issue_{vote.vote_type}",
            "timestamp": vote.created_at,
            "description": f"{vote.vote_type.title()}d issue: {vote.issue.title}",
            "issue_id": vote.issue_id,
            "karma_earned": 1
        })
    
    # Add comments to activity
    for comment in recent_comments:
        activity.append({
            "type": "issue_comment",
            "timestamp": comment.created_at,
            "description": f"Commented on issue: {comment.issue.title}",
            "issue_id": comment.issue_id,
            "karma_earned": 1
        })
    
    # Sort by timestamp
    activity.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return activity[:limit]

@router.get("/me/achievements")
async def get_my_achievements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's achievements and progress"""
    karma_service = KarmaService(db)
    
    # Get all possible badges and check progress
    all_badges = karma_service.BADGES
    user_badges = {badge.badge_name for badge in current_user.badges}
    
    achievements = []
    for badge_key, badge_info in all_badges.items():
        earned = badge_key in user_badges
        progress = 0
        max_progress = 1
        
        # Calculate progress for specific badges
        if badge_key == "pothole_patriot":
            road_issues = len([issue for issue in current_user.issues if issue.category.value == "road_maintenance"])
            progress = min(road_issues, 5)
            max_progress = 5
        elif badge_key == "community_champion":
            progress = min(current_user.civic_karma, 500)
            max_progress = 500
        elif badge_key == "voting_veteran":
            upvotes = len([vote for vote in current_user.votes if vote.vote_type == 'upvote'])
            progress = min(upvotes, 50)
            max_progress = 50
        elif badge_key == "confirmation_king":
            confirmations = len([vote for vote in current_user.votes if vote.vote_type == 'confirm'])
            progress = min(confirmations, 25)
            max_progress = 25
        elif badge_key == "social_butterfly":
            progress = min(len(current_user.comments), 20)
            max_progress = 20
        
        achievements.append({
            "badge_key": badge_key,
            "name": badge_info["name"],
            "description": badge_info["description"],
            "earned": earned,
            "progress": progress,
            "max_progress": max_progress,
            "progress_percent": (progress / max_progress * 100) if max_progress > 0 else 0
        })
    
    return {
        "achievements": achievements,
        "total_badges": len(user_badges),
        "total_possible": len(all_badges),
        "completion_percent": (len(user_badges) / len(all_badges) * 100) if all_badges else 0
    }

@router.get("/leaderboard")
async def get_leaderboard(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get civic karma leaderboard"""
    karma_service = KarmaService(db)
    return karma_service.get_leaderboard(limit)

@router.get("/badges/all")
async def get_all_badges(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all available badges in the system"""
    karma_service = KarmaService(db)
    return {
        "badges": [
            {
                "key": key,
                "name": info["name"],
                "description": info["description"],
                "points": info["points"]
            }
            for key, info in karma_service.BADGES.items()
        ]
    }
