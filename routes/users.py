from fastapi import APIRouter, Depends
from database.connection import get_session
from models import User, Friendship, UserRead
from auth.authenticate import authenticate
from typing import List

friends_router = APIRouter(tags=["friends"])


@friends_router.get("/", response_model=List[UserRead])
async def list_friends(user: User = Depends(authenticate), session=Depends(get_session)):
    current_user = User.one_by_id(session, user.id)
    return current_user.friends


@friends_router.post("/")
async def add_friend(friend_username: str, user: User = Depends(authenticate), session=Depends(get_session)):
    friend = User.first_by_field(session, "username", friend_username)
    new_friendship = Friendship(user_id=user.id, friend_id=friend.id)
    Friendship.create(session, new_friendship)
    return {"message": "User added successfully!"}
