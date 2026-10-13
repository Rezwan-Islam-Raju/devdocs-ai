from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.user_schema import (
    UserRegistrationRequest,
    UserResponse,
    UserLoginRequest,
    UserLoginResponse,
)
from app.services.user_services import (
    register_user_service,
    login_user_service,
)

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

DatabaseSession = Annotated[
    AsyncSession,
    Depends(get_db)
]


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    request: UserRegistrationRequest,
    db: DatabaseSession,
):
    return await register_user_service(
        db=db,
        request=request,
    )


@router.post(
    "/login",
    response_model=UserLoginResponse,
    status_code=status.HTTP_200_OK,
)
async def login(
    request: UserLoginRequest,
    db: DatabaseSession,
):
    return await login_user_service(
        db=db,
        request=request
    )
