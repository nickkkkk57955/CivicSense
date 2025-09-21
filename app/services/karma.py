from sqlalchemy.orm import Session
from ..models import User, Issue, UserBadge, IssueCategory
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class KarmaService:
    """Service for managing Civic Karma and badges"""
    
    # Badge definitions
    BADGES = {
        "first_report": {"name": "First Steps", "description": "Reported your first issue", "points": 10},
        "pothole_patriot": {"name": "Pothole Patriot", "description": "Reported 5 road maintenance issues", "points": 50},
        "streetlight_saver": {"name": "Streetlight Saver", "description": "Reported 3 streetlight issues", "points": 30},
        "clean_up_crew": {"name": "Clean-Up Crew", "description": "Reported 5 sanitation issues", "points": 50},
        "water_warrior": {"name": "Water Warrior", "description": "Reported 3 water supply issues", "points": 30},
        "power_protector": {"name": "Power Protector", "description": "Reported 3 electricity issues", "points": 30},
        "traffic_tracker": {"name": "Traffic Tracker", "description": "Reported 3 traffic issues", "points": 30},
        "park_patrol": {"name": "Park Patrol", "description": "Reported 3 park issues", "points": 30},
        "community_champion": {"name": "Community Champion", "description": "Earned 500+ civic karma", "points": 100},
        "issue_resolver": {"name": "Issue Resolver", "description": "Had 10 issues resolved", "points": 200},
        "voting_veteran": {"name": "Voting Veteran", "description": "Voted on 50 issues", "points": 100},
        "confirmation_king": {"name": "Confirmation King", "description": "Confirmed 25 issues", "points": 75},
        "social_butterfly": {"name": "Social Butterfly", "description": "Commented on 20 issues", "points": 50}
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def award_karma(self, user_id: int, points: int, reason: str) -> bool:
        """Award karma points to a user"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"User {user_id} not found for karma award")
                return False
            
            user.civic_karma += points
            self.db.commit()
            
            logger.info(f"Awarded {points} karma to user {user_id} for: {reason}")
            
            # Check for new badges
            self.check_and_award_badges(user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error awarding karma to user {user_id}: {str(e)}")
            self.db.rollback()
            return False
    
    def check_and_award_badges(self, user_id: int) -> List[str]:
        """Check if user qualifies for new badges and award them"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return []
            
            new_badges = []
            
            # Get user's existing badges
            existing_badges = {badge.badge_name for badge in user.badges}
            
            # Check each badge type
            badges_to_check = [
                ("first_report", self._check_first_report, user),
                ("pothole_patriot", self._check_pothole_patriot, user),
                ("streetlight_saver", self._check_streetlight_saver, user),
                ("clean_up_crew", self._check_clean_up_crew, user),
                ("water_warrior", self._check_water_warrior, user),
                ("power_protector", self._check_power_protector, user),
                ("traffic_tracker", self._check_traffic_tracker, user),
                ("park_patrol", self._check_park_patrol, user),
                ("community_champion", self._check_community_champion, user),
                ("issue_resolver", self._check_issue_resolver, user),
                ("voting_veteran", self._check_voting_veteran, user),
                ("confirmation_king", self._check_confirmation_king, user),
                ("social_butterfly", self._check_social_butterfly, user)
            ]
            
            for badge_key, check_function, user in badges_to_check:
                if badge_key not in existing_badges and check_function(user):
                    badge_info = self.BADGES[badge_key]
                    self._award_badge(user_id, badge_key, badge_info["name"], badge_info["description"])
                    new_badges.append(badge_key)
            
            return new_badges
            
        except Exception as e:
            logger.error(f"Error checking badges for user {user_id}: {str(e)}")
            return []
    
    def _award_badge(self, user_id: int, badge_key: str, badge_name: str, badge_description: str):
        """Award a badge to a user"""
        badge = UserBadge(
            user_id=user_id,
            badge_name=badge_name,
            badge_description=badge_description
        )
        self.db.add(badge)
        self.db.commit()
        
        logger.info(f"Awarded badge '{badge_name}' to user {user_id}")
    
    # Badge check functions
    def _check_first_report(self, user: User) -> bool:
        """Check if user has reported their first issue"""
        return len(user.issues) >= 1
    
    def _check_pothole_patriot(self, user: User) -> bool:
        """Check if user has reported 5 road maintenance issues"""
        road_issues = [issue for issue in user.issues if issue.category == IssueCategory.ROAD_MAINTENANCE]
        return len(road_issues) >= 5
    
    def _check_streetlight_saver(self, user: User) -> bool:
        """Check if user has reported 3 streetlight issues"""
        streetlight_issues = [issue for issue in user.issues if issue.category == IssueCategory.STREETLIGHT]
        return len(streetlight_issues) >= 3
    
    def _check_clean_up_crew(self, user: User) -> bool:
        """Check if user has reported 5 sanitation issues"""
        sanitation_issues = [issue for issue in user.issues if issue.category == IssueCategory.SANITATION]
        return len(sanitation_issues) >= 5
    
    def _check_water_warrior(self, user: User) -> bool:
        """Check if user has reported 3 water supply issues"""
        water_issues = [issue for issue in user.issues if issue.category == IssueCategory.WATER_SUPPLY]
        return len(water_issues) >= 3
    
    def _check_power_protector(self, user: User) -> bool:
        """Check if user has reported 3 electricity issues"""
        electricity_issues = [issue for issue in user.issues if issue.category == IssueCategory.ELECTRICITY]
        return len(electricity_issues) >= 3
    
    def _check_traffic_tracker(self, user: User) -> bool:
        """Check if user has reported 3 traffic issues"""
        traffic_issues = [issue for issue in user.issues if issue.category == IssueCategory.TRAFFIC]
        return len(traffic_issues) >= 3
    
    def _check_park_patrol(self, user: User) -> bool:
        """Check if user has reported 3 park issues"""
        park_issues = [issue for issue in user.issues if issue.category == IssueCategory.PARKS]
        return len(park_issues) >= 3
    
    def _check_community_champion(self, user: User) -> bool:
        """Check if user has 500+ civic karma"""
        return user.civic_karma >= 500
    
    def _check_issue_resolver(self, user: User) -> bool:
        """Check if user has had 10 issues resolved"""
        resolved_issues = [issue for issue in user.issues if issue.status.value == "resolved"]
        return len(resolved_issues) >= 10
    
    def _check_voting_veteran(self, user: User) -> bool:
        """Check if user has voted on 50 issues"""
        upvotes = [vote for vote in user.votes if vote.vote_type == 'upvote']
        return len(upvotes) >= 50
    
    def _check_confirmation_king(self, user: User) -> bool:
        """Check if user has confirmed 25 issues"""
        confirmations = [vote for vote in user.votes if vote.vote_type == 'confirm']
        return len(confirmations) >= 25
    
    def _check_social_butterfly(self, user: User) -> bool:
        """Check if user has commented on 20 issues"""
        return len(user.comments) >= 20
    
    def get_user_stats(self, user_id: int) -> dict:
        """Get comprehensive user statistics"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}
        
        # Count issues by category
        category_counts = {}
        for category in IssueCategory:
            count = len([issue for issue in user.issues if issue.category == category])
            if count > 0:
                category_counts[category.value] = count
        
        # Count votes
        upvotes_given = len([vote for vote in user.votes if vote.vote_type == 'upvote'])
        confirmations_given = len([vote for vote in user.votes if vote.vote_type == 'confirm'])
        
        # Count resolved issues
        resolved_issues = len([issue for issue in user.issues if issue.status.value == "resolved"])
        
        return {
            "user_id": user.id,
            "name": user.name,
            "civic_karma": user.civic_karma,
            "total_issues": len(user.issues),
            "resolved_issues": resolved_issues,
            "upvotes_given": upvotes_given,
            "confirmations_given": confirmations_given,
            "comments_made": len(user.comments),
            "badges_earned": len(user.badges),
            "category_breakdown": category_counts,
            "badges": [
                {
                    "name": badge.badge_name,
                    "description": badge.badge_description,
                    "earned_at": badge.earned_at
                }
                for badge in user.badges
            ]
        }
    
    def get_leaderboard(self, limit: int = 20) -> List[dict]:
        """Get civic karma leaderboard"""
        users = self.db.query(User).filter(
            User.role == "citizen",
            User.is_active == True
        ).order_by(User.civic_karma.desc()).limit(limit).all()
        
        leaderboard = []
        for i, user in enumerate(users):
            leaderboard.append({
                "rank": i + 1,
                "user_id": user.id,
                "name": user.name,
                "civic_karma": user.civic_karma,
                "badges_count": len(user.badges),
                "issues_reported": len(user.issues)
            })
        
        return leaderboard
