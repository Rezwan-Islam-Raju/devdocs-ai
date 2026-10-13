import datetime


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
    refresh_token: str
    token_type: str = 'bearer'

