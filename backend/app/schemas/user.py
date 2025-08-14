from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
class UserLogin(BaseModel):
    email: EmailStr
    password: str
class UserPublic(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
