import datetime

import bcrypt
import jwt

from app.core.config import settings


# PASSWORD HASH


def hash_password(password: str):
    password_bytes = password.encode("utf-8")

    salt = bcrypt.gensalt()

    password_hash = bcrypt.hashpw(
        password_bytes,
        salt
    )

    return password_hash.decode("utf-8")



# VERIFY PASSWORD


def verify_password(
    password: str,
    hashed_password: str
) :

    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )

    except (ValueError, TypeError, AttributeError):
        return False



# CREATE ACCESS TOKEN


def encode_access_token(
    user_id: int,
    email: str
) :

    now = datetime.datetime.now(
        datetime.timezone.utc
    )

    expires_at = now + datetime.timedelta(
        hours=settings.ACCESS_TOKEN_EXPIRE_HOURS
    )

    payload = {
        "user_id": user_id,
        "email": email,
        "token_type": "access",
        "iat": now,
        "exp": expires_at
    }

    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return token



# DECODE ACCESS TOKEN


def decode_access_token(token: str):

    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )

    if payload.get("token_type") != "access":
        raise jwt.InvalidTokenError(
            "Invalid token type"
        )

    return payload

