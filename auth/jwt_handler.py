import time
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from jose import jwt, JWTError
from utils.config import get_settings
from typing import Optional

settings = get_settings()
SECRET_KEY = settings.SECRET_KEY


def create_access_token(user: str) -> str:
    payload = {
        "user": user,
        "expires": time.time() + 3600
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


def verify_access_token(token: str) -> str:
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        expire = data.get("expires")
        if expire is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token supplied"
            )
        if datetime.utcnow() > datetime.utcfromtimestamp(expire):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token expired!"
            )
        return data
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_BAD_REQUEST,
            detail="Invalid Token"
        )


def generate_password_reset_token(email: str) -> str:
    delta = timedelta(hours=24)
    now = datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "email": email}, settings.SECRET_KEY, algorithm="HS256",
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return decoded_token["email"]
    except jwt.JWTError:
        return None
