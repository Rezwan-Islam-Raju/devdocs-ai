import datetime
from typing import Optional

from pydantic import EmailStr, BaseModel,Field


class UserRegistrationRequest(BaseModel):
    name: str = Field(min_length=2,max_length=100)
    email: EmailStr
    password:str = Field(min_length=8,max_length=72)


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8,max_length=72)

class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str


class ChangePasswordResponse(BaseModel):
    message:str

class LogoutResponse(BaseModel):
    message: str

class UserUpdateRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
class UserUpdateResponse(BaseModel):
    message: str

class UserDeleteResponse(BaseModel):
    message: str
