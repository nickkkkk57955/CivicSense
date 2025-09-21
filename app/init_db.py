"""
Database initialization script with sample data
"""
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from .models import Base, User, Department, Issue, IssueCategory, IssueStatus, IssuePriority, UserRole
from .auth import get_password_hash
from datetime import datetime, timedelta
import random

def create_sample_data():
    """Create sample data for development and testing"""
    db = SessionLocal()
    
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Check if data already exists
        if db.query(User).first():
            print("Sample data already exists. Skipping initialization.")
            return
        
        print("Creating sample data...")
        
        # Create departments
        departments = [
            Department(
                name="Public Works",
                description="Handles road maintenance, streetlights, and infrastructure",
                contact_email="publicworks@city.gov",
                contact_phone="555-0101"
            ),
            Department(
                name="Sanitation Department",
                description="Manages waste collection and sanitation services",
                contact_email="sanitation@city.gov",
                contact_phone="555-0102"
            ),
            Department(
                name="Water Department",
                description="Water supply and distribution services",
                contact_email="water@city.gov",
                contact_phone="555-0103"
            ),
            Department(
                name="Electricity Department",
                description="Electrical infrastructure and power services",
                contact_email="electricity@city.gov",
                contact_phone="555-0104"
            ),
            Department(
                name="Parks and Recreation",
                description="Parks, playgrounds, and recreational facilities",
                contact_email="parks@city.gov",
                contact_phone="555-0105"
            )
        ]
        
        for dept in departments:
            db.add(dept)
        db.commit()
        
        # Create admin user
        admin_user = User(
            name="System Administrator",
            email="admin@city.gov",
            phone="555-0000",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.ADMIN
        )
        db.add(admin_user)
        
        # Create department staff
        staff_users = [
            User(
                name="John Smith",
                email="john.smith@city.gov",
                phone="555-1001",
                hashed_password=get_password_hash("staff123"),
                role=UserRole.DEPARTMENT_STAFF
            ),
            User(
                name="Sarah Johnson",
                email="sarah.johnson@city.gov",
                phone="555-1002",
                hashed_password=get_password_hash("staff123"),
                role=UserRole.DEPARTMENT_STAFF
            ),
            User(
                name="Mike Wilson",
                email="mike.wilson@city.gov",
                phone="555-1003",
                hashed_password=get_password_hash("staff123"),
                role=UserRole.DEPARTMENT_STAFF
            )
        ]
        
        for staff in staff_users:
            db.add(staff)
        
        # Create citizen users with initial karma
        citizen_users = [
            User(
                name="Alice Brown",
                email="alice.brown@email.com",
                phone="555-2001",
                hashed_password=get_password_hash("citizen123"),
                role=UserRole.CITIZEN,
                civic_karma=150
            ),
            User(
                name="Bob Davis",
                email="bob.davis@email.com",
                phone="555-2002",
                hashed_password=get_password_hash("citizen123"),
                role=UserRole.CITIZEN,
                civic_karma=75
            ),
            User(
                name="Carol Miller",
                email="carol.miller@email.com",
                phone="555-2003",
                hashed_password=get_password_hash("citizen123"),
                role=UserRole.CITIZEN,
                civic_karma=200
            ),
            User(
                name="David Garcia",
                email="david.garcia@email.com",
                phone="555-2004",
                hashed_password=get_password_hash("citizen123"),
                role=UserRole.CITIZEN,
                civic_karma=100
            )
        ]
        
        for citizen in citizen_users:
            db.add(citizen)
        
        db.commit()
        
        # Create sample issues
        sample_issues = [
            {
                "title": "Large Pothole on Main Street",
                "description": "Deep pothole causing damage to vehicles. Located near the intersection with Oak Avenue.",
                "category": IssueCategory.ROAD_MAINTENANCE,
                "priority": IssuePriority.HIGH,
                "status": IssueStatus.IN_PROGRESS,
                "latitude": 40.7128,
                "longitude": -74.0060,
                "address": "123 Main Street, Downtown"
            },
            {
                "title": "Broken Streetlight",
                "description": "Streetlight has been out for 3 days. Makes the area unsafe at night.",
                "category": IssueCategory.STREETLIGHT,
                "priority": IssuePriority.MEDIUM,
                "status": IssueStatus.ACKNOWLEDGED,
                "latitude": 40.7138,
                "longitude": -74.0070,
                "address": "456 Oak Avenue, Downtown"
            },
            {
                "title": "Overflowing Trash Bin",
                "description": "Trash bin is overflowing and attracting pests. Needs immediate attention.",
                "category": IssueCategory.SANITATION,
                "priority": IssuePriority.HIGH,
                "status": IssueStatus.SUBMITTED,
                "latitude": 40.7148,
                "longitude": -74.0080,
                "address": "789 Pine Street, Residential Area"
            },
            {
                "title": "Water Leak in Park",
                "description": "Water is leaking from a broken pipe in the central park fountain area.",
                "category": IssueCategory.WATER_SUPPLY,
                "priority": IssuePriority.URGENT,
                "status": IssueStatus.RESOLVED,
                "latitude": 40.7158,
                "longitude": -74.0090,
                "address": "Central Park, Downtown"
            },
            {
                "title": "Damaged Playground Equipment",
                "description": "Swing set is broken and unsafe for children to use.",
                "category": IssueCategory.PARKS,
                "priority": IssuePriority.MEDIUM,
                "status": IssueStatus.IN_PROGRESS,
                "latitude": 40.7168,
                "longitude": -74.0100,
                "address": "321 Elm Street, Park District"
            },
            {
                "title": "Traffic Light Malfunction",
                "description": "Traffic light at busy intersection is stuck on red, causing traffic backup.",
                "category": IssueCategory.TRAFFIC,
                "priority": IssuePriority.URGENT,
                "status": IssueStatus.ACKNOWLEDGED,
                "latitude": 40.7178,
                "longitude": -74.0110,
                "address": "Main Street & Oak Avenue Intersection"
            },
            {
                "title": "Power Outage in Residential Area",
                "description": "Several houses have been without power for 2 hours.",
                "category": IssueCategory.ELECTRICITY,
                "priority": IssuePriority.URGENT,
                "status": IssueStatus.RESOLVED,
                "latitude": 40.7188,
                "longitude": -74.0120,
                "address": "555 Maple Street, Residential"
            },
            {
                "title": "Graffiti on City Hall",
                "description": "Vandalism on the side of the city hall building needs to be cleaned.",
                "category": IssueCategory.OTHER,
                "priority": IssuePriority.LOW,
                "status": IssueStatus.SUBMITTED,
                "latitude": 40.7198,
                "longitude": -74.0130,
                "address": "City Hall, Government District"
            }
        ]
        
        # Get user IDs for assignment
        citizens = db.query(User).filter(User.role == UserRole.CITIZEN).all()
        staff = db.query(User).filter(User.role == UserRole.DEPARTMENT_STAFF).all()
        depts = db.query(Department).all()
        
        for i, issue_data in enumerate(sample_issues):
            # Assign to random citizen
            reporter = random.choice(citizens)
            
            # Assign to appropriate department based on category
            dept_mapping = {
                IssueCategory.ROAD_MAINTENANCE: "Public Works",
                IssueCategory.STREETLIGHT: "Public Works",
                IssueCategory.SANITATION: "Sanitation Department",
                IssueCategory.WATER_SUPPLY: "Water Department",
                IssueCategory.ELECTRICITY: "Electricity Department",
                IssueCategory.TRAFFIC: "Public Works",
                IssueCategory.PARKS: "Parks and Recreation",
                IssueCategory.OTHER: "Public Works"
            }
            
            dept_name = dept_mapping.get(issue_data["category"])
            department = next((d for d in depts if d.name == dept_name), depts[0])
            
            # Create timestamps
            created_at = datetime.utcnow() - timedelta(days=random.randint(1, 30))
            acknowledged_at = None
            resolved_at = None
            
            if issue_data["status"] in [IssueStatus.ACKNOWLEDGED, IssueStatus.IN_PROGRESS, IssueStatus.RESOLVED]:
                acknowledged_at = created_at + timedelta(hours=random.randint(1, 24))
            
            if issue_data["status"] == IssueStatus.RESOLVED:
                resolved_at = acknowledged_at + timedelta(hours=random.randint(1, 72))
            
            issue = Issue(
                title=issue_data["title"],
                description=issue_data["description"],
                category=issue_data["category"],
                priority=issue_data["priority"],
                status=issue_data["status"],
                latitude=issue_data["latitude"],
                longitude=issue_data["longitude"],
                address=issue_data["address"],
                reporter_id=reporter.id,
                department_id=department.id,
                created_at=created_at,
                acknowledged_at=acknowledged_at,
                resolved_at=resolved_at
            )
            
            # Assign to staff if status is not submitted
            if issue_data["status"] != IssueStatus.SUBMITTED:
                issue.assigned_to_id = random.choice(staff).id
            
            db.add(issue)
        
        db.commit()
        
        # Add some sample votes and badges
        from .models import IssueVote, UserBadge
        
        # Add some votes to issues
        issues = db.query(Issue).all()
        citizens = db.query(User).filter(User.role == UserRole.CITIZEN).all()
        
        for issue in issues[:5]:  # Add votes to first 5 issues
            # Add some upvotes
            for i in range(min(3, len(citizens))):
                if citizens[i].id != issue.reporter_id:  # Don't vote on own issue
                    vote = IssueVote(
                        issue_id=issue.id,
                        user_id=citizens[i].id,
                        vote_type='upvote'
                    )
                    db.add(vote)
                    issue.upvotes += 1
            
            # Add some confirmations
            for i in range(min(2, len(citizens))):
                if citizens[i].id != issue.reporter_id:
                    vote = IssueVote(
                        issue_id=issue.id,
                        user_id=citizens[i].id,
                        vote_type='confirm'
                    )
                    db.add(vote)
                    issue.confirmations += 1
            
            # Update urgency score
            issue.urgency_score = (issue.upvotes * 2) + issue.confirmations
        
        # Add some badges
        badges_to_award = [
            (citizens[0].id, "First Steps", "Reported your first issue"),
            (citizens[0].id, "Community Champion", "Earned 500+ civic karma"),
            (citizens[2].id, "Pothole Patriot", "Reported 5 road maintenance issues"),
            (citizens[2].id, "Clean-Up Crew", "Reported 5 sanitation issues")
        ]
        
        for user_id, badge_name, badge_description in badges_to_award:
            badge = UserBadge(
                user_id=user_id,
                badge_name=badge_name,
                badge_description=badge_description
            )
            db.add(badge)
        
        db.commit()
        
        print("Sample data created successfully!")
        print("\nSample users created:")
        print("Admin: admin@city.gov / admin123")
        print("Staff: john.smith@city.gov / staff123")
        print("Citizens: alice.brown@email.com / citizen123")
        print("\nSample issues created with various statuses and categories.")
        print("Sample votes and badges added for gamification features.")
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data()
