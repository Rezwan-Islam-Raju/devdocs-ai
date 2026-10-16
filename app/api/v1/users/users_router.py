from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth_dependecy import require_user_id
from app.schemas.user_schema import (
    UserRegistrationRequest,
    UserResponse,
    UserLoginRequest,
    UserLoginResponse, ChangePasswordRequest, UserUpdateRequest,
)
from app.services.user_service import (
    register_user_service,
    login_user_service, get_current_service, change_password_service, logout_service,
    user_update_all_service, user_delete_service,
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
        request=request
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

@router.get("/")
async def me(
     user_id:int=Depends(require_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await get_current_service(
        db=db,
        user_id=user_id
    )
    return result



@router.put("/")
async def user_all_update(
        request: UserUpdateRequest,
        user_id:int=Depends(require_user_id),
        db: AsyncSession = Depends(get_db)
):
    result= await user_update_all_service(
        db=db,
        request=request,
        user_id=user_id
    )
    return result

@router.patch("/",)
async def change_password(
        request:ChangePasswordRequest,
        user_id=Depends(require_user_id),
        db:AsyncSession = Depends(get_db)
):
    result = await change_password_service(
        db=db,
        request=request,
        user_id=user_id
    )
    return result

@router.post("/logout")
async def logout(user_id:int=Depends(require_user_id),db:AsyncSession = Depends(get_db)):
    result = await logout_service(
        db=db,
        user_id=user_id
    )
    return result

@router.delete("/")
async def delete_user(user_id:int=Depends(require_user_id),db:AsyncSession = Depends(get_db)):
    result = await user_delete_service(
        db=db,
        user_id=user_id
    )
    return result