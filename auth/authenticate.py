from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from auth.jwt_handler import verify_access_token
from database.connection import engine_url
from models import User
from sqlmodel import select, Session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


async def authenticate(token: str = Depends(oauth2_scheme)) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sign in for access"
        )
    decoded_token = verify_access_token(token)
    user = get_current_user(decoded_token["user"])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    return user


def get_current_user(email) -> User:
    with Session(engine_url) as session:
        query = select(User).where(User.email == email)
        user = session.exec(query).first()
        return user