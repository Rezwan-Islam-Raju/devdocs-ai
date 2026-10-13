import datetime

import algorithm
import bcrypt
import jwt

from app.core.config import settings






class Settings(BaseSettings):

    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_HOURS: int = 8
    ALGORITHM: str = "HS256"


# ACCESS TOKEN

def encode_access_token(user_id:int,email:str):

    now = datetime.datetime.now(datetime.timezone.utc)


    exp = now + datetime.timedelta(
        hours=8
    )

    payload = {
        "user_id":user_id,
        "email":email,
        "token_type":"Bearer",
        'iat':now,
        'exp':exp
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    return token

# DECODE ACCESS TOKEN


def decode_access_token(token:str):

    result = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[Algorithm]
    )
    return result


#  VERIFY PASSWORD

def verify_password(password:str,hash_password):

    try:
        return bcrypt.checkpq(
            password.encode("utf-8"),
            hash_password.decode("utf-8")
        )
    except(ValueError,AttributeError):
        return False

#    PASSWORD HASH


def hash_password(password:str):
    salt=bcrypt.gensalt()

    password_hash= bcrypt.hashpw(password.encode("utf-8"),salt)

    result = password_hash.decode("utf-8")

    return result



# ACTIVATION TOKEN


def generate_activation_token():

    return secrets.token_urlsafe(32)



def hash_refresh_token(token: str):

    result= hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()
    return result


# REFRESH TOKEN HASH


def generate_refresh_token():

    return secrets.token_urlsafe(64)

