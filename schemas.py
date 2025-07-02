from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class ParameterBase(BaseModel):
    name: str
    value: str
    unit: Optional[str] = None
    reference_range: Optional[str] = None

class Parameter(ParameterBase):
    id: int
    status: str | None = None
    class Config:
        from_attributes = True

class ReportBase(BaseModel):
    filename: str

class Report(ReportBase):
    id: int
    upload_time: datetime
    extracted_text: Optional[str]
    parameters: List[Parameter] = []
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None 