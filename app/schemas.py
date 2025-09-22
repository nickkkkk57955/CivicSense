from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    name: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    civic_karma: int
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[EmailStr] = None


# ---- Issue Schemas (for responses) ----
class Issue(BaseModel):
    id: int
    title: str
    description: str
    category: str
    status: str
    priority: str
    latitude: float
    longitude: float
    address: Optional[str] = None
    photo_urls: Optional[str] = None
    voice_note_url: Optional[str] = None
    reporter_id: int
    assigned_to_id: Optional[int] = None
    department_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True
class IssueBase(BaseModel):
    title: str
    description: str
    category: str # We can use the Enum here later
    latitude: float
    longitude: float

class IssueCreate(IssueBase):
    pass

class Issue(IssueBase):
    id: int
    reporter_id: int
    status: str
    upvotes: int
    created_at: datetime
    reporter: User # This will nest the reporter's user info

    class Config:
        orm_mode = True


