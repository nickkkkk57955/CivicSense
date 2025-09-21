from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from .database import Base

class UserRole(str, enum.Enum):
    CITIZEN = "citizen"
    ADMIN = "admin"
    DEPARTMENT_STAFF = "department_staff"

class IssueStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REJECTED = "rejected"

class IssuePriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class IssueCategory(str, enum.Enum):
    ROAD_MAINTENANCE = "road_maintenance"
    STREETLIGHT = "streetlight"
    SANITATION = "sanitation"
    WATER_SUPPLY = "water_supply"
    ELECTRICITY = "electricity"
    TRAFFIC = "traffic"
    PARKS = "parks"
    OTHER = "other"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(20))
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CITIZEN)
    is_active = Column(Boolean, default=True)
    civic_karma = Column(Integer, default=0)
    profile_picture_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    issues = relationship("Issue", back_populates="reporter")
    assigned_issues = relationship("Issue", back_populates="assigned_to")
    votes = relationship("IssueVote", back_populates="user")
    badges = relationship("UserBadge", back_populates="user")
    comments = relationship("IssueComment", back_populates="user")

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    contact_email = Column(String(100))
    contact_phone = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    issues = relationship("Issue", back_populates="department")

class Issue(Base):
    __tablename__ = "issues"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(Enum(IssueCategory), nullable=False)
    status = Column(Enum(IssueStatus), default=IssueStatus.SUBMITTED)
    priority = Column(Enum(IssuePriority), default=IssuePriority.MEDIUM)
    
    # Location data
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String(500))
    
    # Media
    photo_urls = Column(Text)  # JSON string of photo URLs
    voice_note_url = Column(String(500))
    
    # Social features
    upvotes = Column(Integer, default=0)
    confirmations = Column(Integer, default=0)
    urgency_score = Column(Float, default=0.0)
    
    # Relationships
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to_id = Column(Integer, ForeignKey("users.id"))
    department_id = Column(Integer, ForeignKey("departments.id"))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    acknowledged_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    
    # Relationships
    reporter = relationship("User", back_populates="issues", foreign_keys=[reporter_id])
    assigned_to = relationship("User", back_populates="assigned_issues", foreign_keys=[assigned_to_id])
    department = relationship("Department", back_populates="issues")
    updates = relationship("IssueUpdate", back_populates="issue")
    votes = relationship("IssueVote", back_populates="issue")
    comments = relationship("IssueComment", back_populates="issue")

class IssueUpdate(Base):
    __tablename__ = "issue_updates"
    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(IssueStatus), nullable=False)
    comment = Column(Text)
    photo_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    issue = relationship("Issue", back_populates="updates")
    user = relationship("User")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    issue_id = Column(Integer, ForeignKey("issues.id"))
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User")
    issue = relationship("Issue")

class IssueVote(Base):
    __tablename__ = "issue_votes"
    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    vote_type = Column(String(20), nullable=False)  # 'upvote' or 'confirm'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    issue = relationship("Issue")
    user = relationship("User")

class UserBadge(Base):
    __tablename__ = "user_badges"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    badge_name = Column(String(100), nullable=False)
    badge_description = Column(Text)
    earned_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User")

class IssueComment(Base):
    __tablename__ = "issue_comments"
    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    issue = relationship("Issue")
    user = relationship("User")
