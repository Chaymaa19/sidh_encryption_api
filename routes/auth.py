from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from auth.hash_password import create_hash, verify_hash
from auth.jwt_handler import create_access_token, generate_password_reset_token, verify_password_reset_token
from utils.config import get_settings
from models import UserCreate, ConventionalUserCreate, User, UserParams, Result, TokenResponse
from database.connection import get_session
from utils.send_email import send_email_background
from utils.utils import create_params, setup
from datetime import datetime
import random

auth_router = APIRouter(tags=["auth"])
settings = get_settings()


@auth_router.post("/signup", response_model=Result)
async def sign_new_user(background_tasks: BackgroundTasks, user: UserCreate = Body(...), session=Depends(get_session)):
    user_exist = User.first_by_field(session, "email", user.email)
    if user_exist:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with supplied email already exists"
        )
    username_exist = User.first_by_field(session, "username", user.username)
    if username_exist:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with supplied username already exists"
        )
    # Create new user
    hashed_password = create_hash(user.password)
    user.password = hashed_password
    user_create = ConventionalUserCreate(**user.dict())
    new_user = User.create(session, user_create)

    # Create user's SIDH parameters
    result1, result2 = setup()
    UserParams.create(session, create_params(result1, receiver_id=new_user.id))
    UserParams.create(session, create_params(result2, sender_id=new_user.id))

    send_email_background(background_tasks, "Verify your email", user_create.email,
                          {'redirect': f"{settings.SERVER_HOST}/auth/verify-email/{user_create.verification_code}",
                           'new_link': f"{settings.SERVER_HOST}/auth/resend-verification-email/{user_create.verification_code}"},
                          template_name="email.html")

    return {"message": "User signed up successfully!"}


@auth_router.get("/verify-email/{verification_code}", response_model=Result)
async def verify_user(verification_code: str, session=Depends(get_session)) -> dict:
    user_to_verify = User.first_by_field(session, "verification_code", verification_code)
    if not user_to_verify:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid verification code or account already verified"
        )

    time_passed = datetime.now() - user_to_verify.code_creation_date
    if time_passed.days >= settings.DAYS_TO_VERIFY_EMAIL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verification code expired"
        )

    user_to_verify.update(session, {"verification_code": "", "is_verified": True})

    return {"message": "Account verified successfully"}


@auth_router.get("/resend-verification-email/{verification_code}", response_model=Result)
async def resend_verification_email(verification_code: str, background_tasks: BackgroundTasks,
                                    session=Depends(get_session)):
    current_user = User.first_by_field(session, "verification_code", verification_code)
    new_verification_code = random.randbytes(5).hex()
    current_user.update(session, {"verification_code": new_verification_code})

    send_email_background(background_tasks, 'Verify your email', current_user.email, {
        'redirect': f"{settings.SERVER_HOST}/auth/verify-email/{current_user.verification_code}",
        'new_link': f"{settings.SERVER_HOST}/auth/resend-verification-email/{current_user.verification_code}"
    }, template_name="email.html")
    return {"message": "Re sent verification email"}


@auth_router.post("/login", response_model=TokenResponse)
def login(user: OAuth2PasswordRequestForm = Depends(), session=Depends(get_session)) -> dict:
    user_exist = User.first_by_field(session, "email", user.username)
    if not user_exist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with email does not exist"
        )
    if not user_exist.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not verified. Please, verify your account with the email received."
        )

    if verify_hash(user.password, user_exist.password):
        access_token = create_access_token(user_exist.email)
        return {
            "access_token": access_token,
            "token_type": "Bearer"
        }
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid details passed."
    )


@auth_router.post("/password-recovery", response_model=Result)
async def change_password(background_tasks: BackgroundTasks, email: str = Body(...), new_password: str = Body(...),
                          session=Depends(get_session)):
    current_user = User.first_by_field(session, "email", email)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user with this email does not exist in the system.",
        )
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not verified. Please, verify your account with the email received."
        )

    password_reset_token = generate_password_reset_token(email=email)
    hashed_password = create_hash(new_password)
    send_email_background(background_tasks, 'Reset your password', current_user.email, {
        'redirect': f"{settings.SERVER_HOST}/auth/reset-password?token={password_reset_token}&new_password={hashed_password}",
    }, template_name="reset-password.html")

    return {"message": "Password recovery email sent"}


@auth_router.get("/reset-password", response_model=Result)
def reset_password(token: str = Query(...), new_password: str = Query(...), session=Depends(get_session)):
    email = verify_password_reset_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid token",
        )
    current_user = User.first_by_field(session, "email", email)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user with this username does not exist.",
        )

    current_user.update(session, {"password": new_password})
    return {"message": "Password updated successfully"}
