from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    hash_password,
    verify_password,
    encode_access_token
)
from app.models.user_model import User
from app.schemas.user_schema import (
    UserRegistrationRequest,
    UserLoginRequest,
    UserLoginResponse
)


async def register_user_service(
    db: AsyncSession,
    request: UserRegistrationRequest,
):
    #  Check whether email already exists
    email = str(request.email).lower().strip()

    result = await db.execute(
        select(User).where(User.email == email)
    )

    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    #  Validate bcrypt password byte length
    password_bytes = request.password.encode("utf-8")

    if len(password_bytes) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must not exceed 72 UTF-8 bytes",
        )

    #  Hash password
    hashed_password = hash_password(request.password)

    #  Create user
    new_user = User(
        name=request.name,
        email=email,
        password_hash=hashed_password,
    )

    db.add(new_user)

    #  Save user to database
    try:
        await db.commit()
        await db.refresh(new_user)

    except IntegrityError:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    except Exception:
        await db.rollback()
        raise

    return new_user


async def login_user_service(
    db: AsyncSession,
    request: UserLoginRequest
):
    #  Find user by email
    email = str(request.email).lower().strip()

    result = await db.execute(
        select(User).where(User.email == email)
    )

    user = result.scalar_one_or_none()

    #  Verify email and password
    if not user or not verify_password(
        request.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    #  Check account status
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    #  Generate access token
    access_token = encode_access_token(
        user.id,
        user.email,
    )

    #  Return access token only
    return UserLoginResponse(
        access_token=access_token,
        token_type="bearer"
    )

