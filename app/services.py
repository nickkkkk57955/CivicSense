from sqlalchemy.orm import Session
from . import models


class KarmaService:
    def __init__(self, db: Session):
        self.db = db

    def award_karma(self, user_id: int, points: int, reason: str):
        user = self.db.query(models.User).filter(models.User.id == user_id).first()
        if user:
            user.civic_karma += points
            self.db.commit()

