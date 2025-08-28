import enum
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel
from pydantic import EmailStr

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"

class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True)
    name: str
    role: UserRole = UserRole.USER

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    salt: str
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

class UserCreate(UserBase):
    password: str

class UserLogin(SQLModel):
    email: EmailStr
    password: str

class UserPublic(UserBase):
    id: int
    created_at: datetime
